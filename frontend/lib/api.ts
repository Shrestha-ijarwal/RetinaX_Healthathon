// RetinaX Care - Typed API Client
// Connected to IndexedDB Offline Mutation Layer with Concurrency Conflict Detection
// Secure Cookie-Based Architecture: No access tokens stored in localStorage.

import { queueOfflineMutation, generateSecureUUID } from './offline-store';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

export interface User {
  id: number;
  email: string;
  username: string;
  role: 'Specialist' | 'Care Coordinator' | 'Administrator';
  full_name: string;
  title?: string;
  facility?: string;
  registration_number?: string;
}

export function getCsrfTokenFromCookie(): string | null {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(new RegExp('(^| )retinax_csrf_token=([^;]+)'));
  return match ? decodeURIComponent(match[2]) : null;
}

export function getCurrentUser(): User | null {
  if (typeof window === 'undefined') return null;
  const raw = localStorage.getItem('retinax_user');
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function setCurrentUser(user: User): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem('retinax_user', JSON.stringify(user));
  }
}

export function clearCurrentUser(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('retinax_user');
  }
}

// Dual-auth token helpers supporting both HttpOnly cookies and cross-origin Bearer tokens
export function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('retinax_token');
}

export function setAuthToken(token: string): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem('retinax_token', token);
  }
}

export function clearAuthToken(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('retinax_token');
  }
  clearCurrentUser();
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const method = (options.method || 'GET').toUpperCase();
  const isMutation = ['POST', 'PATCH', 'PUT', 'DELETE'].includes(method);
  const isAuth = endpoint.startsWith('/api/v1/auth/');

  // If client is offline and attempting an operational mutation, queue in IndexedDB
  if (typeof window !== 'undefined' && !navigator.onLine && isMutation && !isAuth) {
    let payload = {};
    try {
      payload = options.body ? JSON.parse(options.body as string) : {};
    } catch {
      // ignore
    }
    const queued = await queueOfflineMutation(
      'MUTATION',
      endpoint,
      method as 'POST' | 'PATCH' | 'PUT',
      payload,
      `Offline update for ${endpoint}`
    );
    return {
      offline: true,
      status: 'queued',
      mutationId: queued.id,
      message: 'Saved locally — pending synchronization'
    } as unknown as T;
  }

  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> || {}),
  };

  const authToken = getAuthToken();
  if (authToken && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }

  // Attach CSRF token on mutating requests
  const csrf = getCsrfTokenFromCookie();
  if (csrf && isMutation && !headers['X-CSRF-Token']) {
    headers['X-CSRF-Token'] = csrf;
  }

  // Attach unique UUID idempotency key on mutations if not present
  if (isMutation && !isAuth && !headers['X-Idempotency-Key']) {
    headers['X-Idempotency-Key'] = generateSecureUUID();
  }

  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  try {
    const res = await fetch(`${BASE_URL}${endpoint}`, {
      ...options,
      headers,
      credentials: 'include', // Transmits HttpOnly retinax_session cookie across domains
    });

    if (!res.ok) {
      let errorDetail = `HTTP ${res.status}`;
      let errJson: any = null;
      try {
        errJson = await res.json();
        errorDetail = errJson.detail || errJson.message || JSON.stringify(errJson);
      } catch {
        errorDetail = res.statusText || errorDetail;
      }

      // Concurrency conflict detection (HTTP 409)
      if (res.status === 409) {
        const conflictErr = new Error(typeof errorDetail === 'object' ? JSON.stringify(errorDetail) : errorDetail);
        (conflictErr as any).isConflict = true;
        (conflictErr as any).conflictData = errJson?.detail || errJson;
        throw conflictErr;
      }

      throw new Error(typeof errorDetail === 'object' ? JSON.stringify(errorDetail) : errorDetail);
    }

    return res.json() as Promise<T>;
  } catch (err: any) {
    // If network connection dropped during mutation, fallback to IndexedDB queue
    if (typeof window !== 'undefined' && isMutation && !isAuth && err.name === 'TypeError') {
      let payload = {};
      try {
        payload = options.body ? JSON.parse(options.body as string) : {};
      } catch {
        // ignore
      }
      const queued = await queueOfflineMutation(
        'MUTATION_NETWORK_FALLBACK',
        endpoint,
        method as 'POST' | 'PATCH' | 'PUT',
        payload,
        `Network-failed update for ${endpoint}`
      );
      return {
        offline: true,
        status: 'queued',
        mutationId: queued.id,
        message: 'Saved locally — pending synchronization'
      } as unknown as T;
    }
    throw err;
  }
}

export const api = {
  // Auth (Strict HttpOnly Cookie Session)
  async login(credentials: { email: string; password: string }) {
    const data = await request<{ access_token?: string; user: User }>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
    if (data.access_token) {
      setAuthToken(data.access_token);
    }
    setCurrentUser(data.user);
    return data;
  },

  async logout() {
    try {
      await request('/api/v1/auth/logout', { method: 'POST' });
    } catch {
      // ignore
    } finally {
      clearAuthToken();
    }
  },

  async getMe() {
    return request<User>('/api/v1/auth/me');
  },

  // Patients
  async getPatients(params?: { search?: string; filter?: string; facility?: string; limit?: number; skip?: number }) {
    const q = new URLSearchParams();
    if (params?.search) q.append('search', params.search);
    if (params?.filter) q.append('filter', params.filter);
    if (params?.facility) q.append('facility', params.facility);
    if (params?.limit !== undefined) q.append('limit', String(params.limit));
    if (params?.skip !== undefined) q.append('skip', String(params.skip));
    return request<{ patients: any[]; metrics: any; total: number }>(`/api/v1/patients?${q.toString()}`);
  },

  async getPatient(id: string) {
    return request<any>(`/api/v1/patients/${id}`);
  },

  async createPatient(payload: any) {
    return request<any>('/api/v1/patients', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async getPatientCompleteness(id: string) {
    return request<any>(`/api/v1/patients/${id}/completeness`);
  },

  // Care Journeys
  async getCareJourneys(params?: { search?: string; stage?: string; completed?: boolean }) {
    const q = new URLSearchParams();
    if (params?.search) q.append('search', params.search);
    if (params?.stage) q.append('stage', params.stage);
    if (params?.completed !== undefined) q.append('completed', String(params.completed));
    return request<any[]>(`/api/v1/journeys?${q.toString()}`);
  },

  async getPatientJourney(patientId: string) {
    return request<any>(`/api/v1/journeys/${patientId}`);
  },

  async updatePatientJourney(patientId: string, payload: any) {
    return request<any>(`/api/v1/journeys/${patientId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  },

  // Specialist Reviews
  async getReviewQueue(statusFilter?: string, search?: string) {
    const q = new URLSearchParams();
    if (statusFilter) q.append('status_filter', statusFilter);
    if (search) q.append('search', search);
    return request<any[]>(`/api/v1/reviews/queue?${q.toString()}`);
  },

  async getPatientReview(patientId: string) {
    return request<any>(`/api/v1/reviews/${patientId}`);
  },

  async submitSpecialistReview(patientId: string, payload: any) {
    return request<any>(`/api/v1/reviews/${patientId}`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  // Follow-Ups
  async getFollowupsWorklist(statusFilter?: string, search?: string) {
    const q = new URLSearchParams();
    if (statusFilter) q.append('status_filter', statusFilter);
    if (search) q.append('search', search);
    return request<any[]>(`/api/v1/followups?${q.toString()}`);
  },

  async getPatientFollowup(patientId: string) {
    return request<any>(`/api/v1/followups/${patientId}`);
  },

  async updatePatientFollowup(patientId: string, payload: any) {
    return request<any>(`/api/v1/followups/${patientId}`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async addContactAttempt(patientId: string, payload: any) {
    return request<any>(`/api/v1/followups/${patientId}/attempts`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  // Tasks
  async getTasks(statusFilter?: string, patientId?: string) {
    const q = new URLSearchParams();
    if (statusFilter) q.append('status_filter', statusFilter);
    if (patientId) q.append('patient_id', patientId);
    return request<any[]>(`/api/v1/tasks?${q.toString()}`);
  },

  async createTask(patientId: string, payload: any) {
    return request<any>(`/api/v1/tasks/${patientId}`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async completeTask(patientId: string, taskId: string, completionNote?: string) {
    return request<any>(`/api/v1/tasks/${patientId}/tasks/${taskId}/complete`, {
      method: 'POST',
      body: JSON.stringify({ completion_note: completionNote }),
    });
  },

  // Documents
  async getDocuments(params?: { docType?: string; patientId?: string; search?: string }) {
    const q = new URLSearchParams();
    if (params?.docType) q.append('doc_type', params.docType);
    if (params?.patientId) q.append('patient_id', params.patientId);
    if (params?.search) q.append('search', params.search);
    return request<any[]>(`/api/v1/documents?${q.toString()}`);
  },

  async uploadDocument(patientId: string, file: File, title: string, docType: string, source: string) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    formData.append('doc_type', docType);
    formData.append('source', source);

    const headers: Record<string, string> = {
      'X-Idempotency-Key': generateSecureUUID()
    };
    const csrf = getCsrfTokenFromCookie();
    if (csrf) {
      headers['X-CSRF-Token'] = csrf;
    }

    const authToken = getAuthToken();
    if (authToken && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${authToken}`;
    }

    const res = await fetch(`${BASE_URL}/api/v1/documents/${patientId}`, {
      method: 'POST',
      headers,
      credentials: 'include',
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Document upload failed');
    }
    return res.json();
  },

  getDocumentDownloadUrl(docId: string) {
    const token = getAuthToken();
    const q = token ? `?token=${encodeURIComponent(token)}` : '';
    return `${BASE_URL}/api/v1/documents/${docId}/download${q}`;
  },

  // Reminders
  async getReminders(patientId?: string) {
    const q = new URLSearchParams();
    if (patientId) q.append('patient_id', patientId);
    return request<any[]>(`/api/v1/reminders?${q.toString()}`);
  },

  async sendReminder(patientId: string, payload: any) {
    return request<any>(`/api/v1/reminders/${patientId}/dispatch`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  async sendSimulatedReminder(patientId: string, payload: any) {
    return this.sendReminder(patientId, payload);
  },

  // Analytics & Cohort
  async getAnalytics() {
    return request<any>('/api/v1/analytics/overview');
  },

  async getGapRadar() {
    return request<any>('/api/v1/analytics/gap-radar');
  },

  async getReconciliation() {
    return request<any[]>('/api/v1/analytics/reconciliation');
  },

  async resolveReconciliation(patientId: string) {
    return request<any>(`/api/v1/analytics/reconciliation/${patientId}/resolve`, {
      method: 'POST',
    });
  },

  async resetCohort() {
    return request<any>('/api/v1/analytics/reset-cohort', {
      method: 'POST',
    });
  },

  // Audit Logs (Admin only)
  async getAuditLogs(params?: { skip?: number; limit?: number }) {
    const q = new URLSearchParams();
    if (params?.skip) q.append('skip', String(params.skip));
    if (params?.limit) q.append('limit', String(params.limit));
    return request<any[]>(`/api/v1/audit?${q.toString()}`);
  },
};
