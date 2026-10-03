/**
 * RetinaX Care - Frontend Application Controller
 * Simplified Information Architecture & Demo Role / Profile System
 * "Simple on the Surface, Powerful Underneath"
 */

class RetinaXCareApp {
  constructor() {
    this.patients = [];
    this.metrics = {};
    this.currentPatientId = null;
    this.currentFilter = 'all';
    this.searchQuery = '';
    this.activeScreen = 'screen-overview';
    this.viewMode = 'cards'; // 'cards' | 'table'
    this.selectedJourneyNodeIndex = 4;
    this.currentDemoStep = 1;
    this.isOfflineMode = false;
    this.offlineQueue = [];
    this.allDocuments = [];

    // Care Journeys & Specialist Reviews State
    this.journeyFilter = 'all';
    this.journeySearchQuery = '';
    this.currentJourneyPatientId = null;
    this.reviewFilter = 'awaiting_review';
    this.reviewSearchQuery = '';
    this.currentReviewPatientId = null;
    this.reviewDrafts = {};

    // Preset Demo Roles
    this.presetRoles = {
      coordinator: {
        id: 'coordinator',
        name: 'Dr. Ananya Sharma',
        title: 'Dr.',
        fullName: 'Ananya Sharma',
        role: 'coordinator',
        roleLabel: 'Care Coordinator',
        specialty: 'Diabetic Eye Care Coordination',
        dept: 'Care Continuity & Outreach',
        facility: 'District Diabetic Care Centre',
        regNumber: '',
        email: 'sharma.ananya@health.org',
        phone: '+91 98765 11223',
        language: 'en',
        avatar: 'AS',
        clinicalAuthoring: false
      },
      specialist: {
        id: 'specialist',
        name: 'Dr. Suresh Chandran, MS',
        title: 'Dr.',
        fullName: 'Suresh Chandran',
        role: 'specialist',
        roleLabel: 'Ophthalmologist / Eye-Care Specialist',
        specialty: 'Ophthalmology',
        dept: 'Department of Ophthalmology & Retina',
        facility: 'District Eye Hospital',
        regNumber: 'MCI-2016-849201',
        email: 'suresh.chandran@eyecare.org',
        phone: '+91 98123 45678',
        language: 'en',
        avatar: 'SC',
        clinicalAuthoring: true
      },
      admin: {
        id: 'admin',
        name: 'Priya Varma',
        title: 'Ms.',
        fullName: 'Priya Varma',
        role: 'admin',
        roleLabel: 'Program Administrator',
        specialty: 'Health Informatics & Quality',
        dept: 'Health Informatics & Quality',
        facility: 'State Health Services',
        regNumber: '',
        email: 'priya.varma@statehealth.gov.in',
        phone: '+91 99001 22334',
        language: 'en',
        avatar: 'PV',
        clinicalAuthoring: false
      }
    };

    // User profile state
    this.currentUserProfile = { ...this.presetRoles.coordinator };
    this.currentRole = this.currentUserProfile;
    this.currentTheme = 'light';
    this.currentLang = 'en';

    this.init();
  }

  async init() {
    this.initProfile();
    this.setupEventListeners();
    this.initTheme();
    this.updateRoleUI();
    await this.fetchPatients();
    await this.fetchAnalytics();
    await this.fetchGapRadar();
    this.handleUrlParams();
  }

  handleUrlParams() {
    const params = new URLSearchParams(window.location.search);
    const hash = window.location.hash.replace('#', '');
    const screen = params.get('screen') || hash;
    const patientId = params.get('patient');
    const filter = params.get('filter');
    const role = params.get('role');
    const nodeIdx = params.get('node');
    const submitted = params.get('submitted');

    if (role && this.presetRoles[role]) {
      this.switchRole(role);
    }

    if (screen === 'screen-journeys') {
      this.navigateToScreen('screen-journeys');
      if (filter) {
        this.journeyFilter = filter;
        this.syncJourneyFilterPills(filter);
        this.renderCareJourneysDirectory();
      }
      if (patientId) {
        this.openCareJourneyWorkspace(patientId);
        if (nodeIdx !== null && nodeIdx !== undefined) {
          this.inspectJourneyNode(patientId, parseInt(nodeIdx, 10));
        }
      }
    } else if (screen === 'screen-reviews') {
      this.navigateToScreen('screen-reviews');
      if (filter) {
        this.reviewFilter = filter;
        this.syncReviewFilterPills(filter);
        this.renderSpecialistReviewQueue();
      }
      if (patientId) {
        this.openSpecialistReviewWorkspace(patientId);
        if (submitted === '1') {
          const banner = document.getElementById('wsReviewSuccessBanner');
          if (banner) banner.style.display = 'block';
        }
      }
    } else if (screen === 'screen-patients') {
      this.navigateToScreen('screen-patients');
      if (filter) {
        this.currentFilter = filter;
        this.syncFilterPills(filter);
        this.renderPatientsList();
      }
    }
  }

  /* =========================================================================
     EVENT LISTENERS & NAVIGATION
     ========================================================================= */
  setupEventListeners() {
    // Top Navigation Tabs (3 Primary Items)
    const navButtons = [
      { id: 'brandHomeBtn', target: 'screen-overview' },
      { id: 'navOverviewBtn', target: 'screen-overview' },
      { id: 'navPatientsBtn', target: 'screen-patients' },
      { id: 'navFollowupsBtn', target: 'screen-followups' }
    ];

    navButtons.forEach(item => {
      const el = document.getElementById(item.id);
      if (el) {
        el.addEventListener('click', () => this.navigateToScreen(item.target));
        el.addEventListener('keydown', (e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            this.navigateToScreen(item.target);
          }
        });
      }
    });

    // "More" Dropdown Menu Toggle
    const moreMenuBtn = document.getElementById('moreMenuBtn');
    const moreDropdown = document.getElementById('moreDropdownMenu');

    if (moreMenuBtn && moreDropdown) {
      moreMenuBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.toggleProfilePopover(false);
        const isOpen = moreDropdown.classList.toggle('show');
        moreMenuBtn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
      });

      document.addEventListener('click', () => {
        moreDropdown.classList.remove('show');
        moreMenuBtn.setAttribute('aria-expanded', 'false');
      });

      moreDropdown.querySelectorAll('.dropdown-item[data-target]').forEach(item => {
        item.addEventListener('click', (e) => {
          const target = e.currentTarget.dataset.target;
          if (target) this.navigateToScreen(target);
          moreDropdown.classList.remove('show');
        });
      });

      const resetDemoItem = document.getElementById('menuResetDemoBtn');
      if (resetDemoItem) {
        resetDemoItem.addEventListener('click', () => {
          this.resetDemoData();
          moreDropdown.classList.remove('show');
        });
      }
    }

    // Interactive Demo Profile Control & Popover
    const profileBtn = document.getElementById('userProfileBtn');
    const profilePopover = document.getElementById('profilePopoverMenu');

    if (profileBtn && profilePopover) {
      profileBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        if (moreDropdown) moreDropdown.classList.remove('show');
        this.toggleProfilePopover();
      });

      profileBtn.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          e.stopPropagation();
          this.toggleProfilePopover();
        } else if (e.key === 'Escape') {
          this.toggleProfilePopover(false);
        }
      });

      document.addEventListener('click', () => {
        this.toggleProfilePopover(false);
      });

      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
          this.toggleProfilePopover(false);
          if (moreDropdown) moreDropdown.classList.remove('show');
        }
      });

      // Popover Menu Item Actions
      const openProfileMenuBtn = document.getElementById('menuOpenProfileBtn');
      if (openProfileMenuBtn) {
        openProfileMenuBtn.addEventListener('click', () => {
          this.toggleProfilePopover(false);
          this.showDemoProfileModal();
        });
      }

      const editProfileMenuBtn = document.getElementById('menuEditProfileBtn');
      if (editProfileMenuBtn) {
        editProfileMenuBtn.addEventListener('click', () => {
          this.toggleProfilePopover(false);
          this.openProfileFormModal('edit');
        });
      }

      const switchRoleMenuBtn = document.getElementById('menuSwitchRoleBtn');
      if (switchRoleMenuBtn) {
        switchRoleMenuBtn.addEventListener('click', () => {
          this.toggleProfilePopover(false);
          this.openModal('roleSwitcherModal');
        });
      }

      const openPrefMenuBtn = document.getElementById('menuOpenPreferencesBtn');
      if (openPrefMenuBtn) {
        openPrefMenuBtn.addEventListener('click', () => {
          this.toggleProfilePopover(false);
          this.openModal('preferencesModal');
        });
      }

      const aboutMenuBtn = document.getElementById('menuAboutBtn');
      if (aboutMenuBtn) {
        aboutMenuBtn.addEventListener('click', () => {
          this.toggleProfilePopover(false);
          this.openModal('aboutModal');
        });
      }
    }

    // First-Time Welcome Modal Actions
    const welcomeCreateBtn = document.getElementById('welcomeCreateProfileBtn');
    if (welcomeCreateBtn) {
      welcomeCreateBtn.addEventListener('click', () => {
        this.closeModal('firstTimeProfileModal');
        this.openProfileFormModal('create');
      });
    }

    document.querySelectorAll('.btn-preset-pill').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const preset = e.currentTarget.dataset.preset;
        if (preset) {
          this.switchRole(preset);
          this.closeModal('firstTimeProfileModal');
          localStorage.setItem('retinax_profile_setup_done', 'true');
        }
      });
    });

    // Profile Setup / Edit Form & Collapsible Details
    const profileForm = document.getElementById('userProfileForm');
    if (profileForm) {
      profileForm.addEventListener('submit', (e) => this.handleProfileFormSubmit(e));
    }

    const formFullName = document.getElementById('formFullName');
    const formProfTitle = document.getElementById('formProfTitle');
    const formRoleSelect = document.getElementById('formRoleSelect');

    if (formFullName) {
      formFullName.addEventListener('input', () => this.updateProfileFormPreview());
    }
    if (formProfTitle) {
      formProfTitle.addEventListener('change', () => this.updateProfileFormPreview());
    }
    if (formRoleSelect) {
      formRoleSelect.addEventListener('change', () => {
        this.updateProfileFormRoleFields();
        this.updateProfileFormPreview();
      });
    }

    const toggleMoreBtn = document.getElementById('toggleMoreDetailsBtn');
    const moreSection = document.getElementById('moreDetailsSection');
    const toggleArrow = document.getElementById('toggleDetailsArrow');
    if (toggleMoreBtn && moreSection) {
      toggleMoreBtn.addEventListener('click', () => {
        const isHidden = moreSection.style.display === 'none';
        moreSection.style.display = isHidden ? 'block' : 'none';
        toggleMoreBtn.setAttribute('aria-expanded', isHidden ? 'true' : 'false');
        if (toggleArrow) toggleArrow.innerText = isHidden ? '▴' : '▾';
      });
    }

    // Role Switcher Cards in Modal
    document.querySelectorAll('.role-select-card').forEach(card => {
      card.addEventListener('click', (e) => {
        const roleId = e.currentTarget.dataset.role;
        if (roleId && this.presetRoles[roleId]) {
          this.switchRole(roleId);
          this.closeModal('roleSwitcherModal');
        }
      });
    });

    const customCreateCard = document.getElementById('roleOptionCustomCreate');
    if (customCreateCard) {
      customCreateCard.addEventListener('click', () => {
        this.closeModal('roleSwitcherModal');
        this.openProfileFormModal('create');
      });
    }

    const roleNoticeSwitchBtn = document.getElementById('roleNoticeSwitchBtn');
    if (roleNoticeSwitchBtn) {
      roleNoticeSwitchBtn.addEventListener('click', () => {
        this.switchRole('specialist');
      });
    }

    const profileModalEditBtn = document.getElementById('profileModalEditBtn');
    if (profileModalEditBtn) {
      profileModalEditBtn.addEventListener('click', () => {
        this.closeModal('demoProfileModal');
        this.openProfileFormModal('edit');
      });
    }

    const profileModalSwitchBtn = document.getElementById('profileModalSwitchBtn');
    if (profileModalSwitchBtn) {
      profileModalSwitchBtn.addEventListener('click', () => {
        this.closeModal('demoProfileModal');
        this.openModal('roleSwitcherModal');
      });
    }

    const btnEditReview = document.getElementById('btnEditSpecialistReview');
    if (btnEditReview) {
      btnEditReview.addEventListener('click', () => {
        const revCard = document.getElementById('reviewRecordedCard');
        const revForm = document.getElementById('specialistReviewForm');
        if (revCard) revCard.style.display = 'none';
        if (revForm) revForm.style.display = 'block';
      });
    }

    // Preferences form interactions
    const prefThemeSelect = document.getElementById('prefThemeSelect');
    if (prefThemeSelect) {
      prefThemeSelect.addEventListener('change', (e) => {
        this.setTheme(e.target.value);
      });
    }

    const prefLangSelect = document.getElementById('prefLanguageSelect');
    if (prefLangSelect) {
      prefLangSelect.addEventListener('change', (e) => {
        this.currentLang = e.target.value;
        this.showToast(`Language set to ${e.target.value === 'hi' ? 'हिन्दी (Hindi)' : 'English'}`);
      });
    }

    const prefReducedMotion = document.getElementById('prefReducedMotion');
    if (prefReducedMotion) {
      prefReducedMotion.addEventListener('change', (e) => {
        document.body.classList.toggle('reduced-motion', e.target.checked);
        this.showToast(e.target.checked ? 'Reduced motion enabled' : 'Reduced motion disabled');
      });
    }

    // Topbar Theme Toggle Button
    const themeBtn = document.getElementById('themeToggle');
    if (themeBtn) {
      themeBtn.addEventListener('click', () => this.toggleTheme());
    }

    // Hero Action Buttons
    const heroDemoBtn = document.getElementById('heroStartDemoBtn');
    if (heroDemoBtn) {
      heroDemoBtn.addEventListener('click', () => this.startGuidedDemo());
    }

    const heroPatientsBtn = document.getElementById('heroViewPatientsBtn');
    if (heroPatientsBtn) {
      heroPatientsBtn.addEventListener('click', () => this.navigateToScreen('screen-patients'));
    }

    // LEVEL 2: 6 Action Cards on Home
    this.setupHomeActionCards();

    // LEVEL 3: Today Section Stat Cards
    this.setupTodayCards();

    // Secondary Screen Triggers
    const fuOutreachBtn = document.getElementById('fuGoOutreachBtn');
    if (fuOutreachBtn) {
      fuOutreachBtn.addEventListener('click', () => this.navigateToScreen('screen-outreach'));
    }

    // Patient Directory Toolbar
    const searchInput = document.getElementById('patientSearchInput');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.searchQuery = e.target.value.trim().toLowerCase();
        this.renderPatientsList();
      });
    }

    const clearSearchBtn = document.getElementById('clearSearchBtn');
    if (clearSearchBtn) {
      clearSearchBtn.addEventListener('click', () => {
        if (searchInput) searchInput.value = '';
        this.searchQuery = '';
        this.renderPatientsList();
      });
    }

    // Filter Pills & More Filters Dropdown in Patients Screen
    const moreFiltersBtn = document.getElementById('moreFiltersBtn');
    const moreFiltersMenu = document.getElementById('moreFiltersMenu');

    if (moreFiltersBtn && moreFiltersMenu) {
      moreFiltersBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = moreFiltersMenu.classList.toggle('show');
        moreFiltersBtn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
      });

      document.addEventListener('click', () => {
        moreFiltersMenu.classList.remove('show');
        moreFiltersBtn.setAttribute('aria-expanded', 'false');
      });

      moreFiltersMenu.querySelectorAll('.more-filter-item').forEach(item => {
        item.addEventListener('click', (e) => {
          e.stopPropagation();
          const filter = e.currentTarget.dataset.filter;
          if (filter) {
            this.currentFilter = filter;
            this.syncFilterPills(filter);
            this.renderPatientsList();
            moreFiltersMenu.classList.remove('show');
            moreFiltersBtn.setAttribute('aria-expanded', 'false');
          }
        });
      });
    }

    document.querySelectorAll('.filter-pills-row > .filter-pill:not(.more-filters-btn)').forEach(pill => {
      pill.addEventListener('click', (e) => {
        const filter = e.currentTarget.dataset.filter;
        this.currentFilter = filter;
        this.syncFilterPills(filter);
        this.renderPatientsList();
      });
    });

    // View Mode Toggle (Cards / Table)
    const cardsViewBtn = document.getElementById('viewModeCardsBtn');
    const tableViewBtn = document.getElementById('viewModeTableBtn');

    if (cardsViewBtn && tableViewBtn) {
      cardsViewBtn.addEventListener('click', () => {
        cardsViewBtn.classList.add('active');
        tableViewBtn.classList.remove('active');
        this.viewMode = 'cards';
        document.getElementById('patientsCardGrid').style.display = 'grid';
        document.getElementById('patientsTableContainer').style.display = 'none';
      });

      tableViewBtn.addEventListener('click', () => {
        tableViewBtn.classList.add('active');
        cardsViewBtn.classList.remove('active');
        this.viewMode = 'table';
        document.getElementById('patientsCardGrid').style.display = 'none';
        document.getElementById('patientsTableContainer').style.display = 'block';
      });
    }

    // Detail Back Button
    const backBtn = document.getElementById('backToWorklistBtn');
    if (backBtn) {
      backBtn.addEventListener('click', () => this.navigateToScreen('screen-patients'));
    }

    // Patient Detail Sub-Tabs
    document.querySelectorAll('.detail-tab').forEach(tab => {
      tab.addEventListener('click', (e) => {
        const tabName = e.target.dataset.tab;
        this.switchDetailTab(tabName);
      });
    });

    // Patient Profile Modals / Actions
    const dirRegBtn = document.getElementById('dirRegisterPatientBtn');
    if (dirRegBtn) {
      dirRegBtn.addEventListener('click', () => this.openModal('registerModal'));
    }

    const passportBtn = document.getElementById('detailCarePassportBtn');
    if (passportBtn) {
      passportBtn.addEventListener('click', () => this.showCarePassport(this.currentPatientId));
    }

    const reminderBtn = document.getElementById('detailSendReminderBtn');
    if (reminderBtn) {
      reminderBtn.addEventListener('click', () => this.showBilingualReminderModal());
    }

    const contactBtn = document.getElementById('detailLogContactBtn');
    if (contactBtn) {
      contactBtn.addEventListener('click', () => this.openModal('contactAttemptModal'));
    }

    const detailUploadBtn = document.getElementById('detailUploadDocBtn');
    if (detailUploadBtn) {
      detailUploadBtn.addEventListener('click', () => this.openModal('uploadDocModal'));
    }

    const detailAddEventBtn = document.getElementById('detailAddTimelineEventBtn');
    if (detailAddEventBtn) {
      detailAddEventBtn.addEventListener('click', () => this.openModal('addEventModal'));
    }

    const detailAddContactAttemptBtn = document.getElementById('detailAddContactAttemptBtn');
    if (detailAddContactAttemptBtn) {
      detailAddContactAttemptBtn.addEventListener('click', () => this.openModal('contactAttemptModal'));
    }

    // Specialist Review Form Submit
    const specForm = document.getElementById('specialistReviewForm');
    if (specForm) {
      specForm.addEventListener('submit', (e) => this.handleSubmitSpecialistReview(e));
    }

    // Follow-Up Status Save & Close Loop
    const saveFuBtn = document.getElementById('saveFollowupStatusBtn');
    if (saveFuBtn) {
      saveFuBtn.addEventListener('click', () => this.handleUpdateFollowup(false));
    }

    const closeLoopBtn = document.getElementById('closeCareLoopBtn');
    if (closeLoopBtn) {
      closeLoopBtn.addEventListener('click', () => this.handleUpdateFollowup(true));
    }

    // Forms inside Modals
    const regForm = document.getElementById('registerPatientForm');
    if (regForm) {
      regForm.addEventListener('submit', (e) => this.handleRegisterPatient(e));
    }

    const uploadDocForm = document.getElementById('uploadDocForm');
    if (uploadDocForm) {
      uploadDocForm.addEventListener('submit', (e) => this.handleUploadDocument(e));
    }

    const addEventForm = document.getElementById('addEventForm');
    if (addEventForm) {
      addEventForm.addEventListener('submit', (e) => this.handleAddTimelineEvent(e));
    }

    const contactForm = document.getElementById('contactAttemptForm');
    if (contactForm) {
      contactForm.addEventListener('submit', (e) => this.handleLogContactAttempt(e));
    }

    // Modal Close buttons
    document.querySelectorAll('.modal-close').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const modalId = e.currentTarget.dataset.modal;
        if (modalId) this.closeModal(modalId);
      });
    });

    // Follow-up Command Center Tabs
    document.querySelectorAll('.followup-tab-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        document.querySelectorAll('.followup-tab-btn').forEach(b => b.classList.remove('active'));
        e.currentTarget.classList.add('active');
        const category = e.currentTarget.dataset.category;
        this.renderFollowupsWorklist(category);
      });
    });

    // Document Categories Filter
    document.querySelectorAll('.doc-filter-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        document.querySelectorAll('.doc-filter-btn').forEach(b => b.classList.remove('active'));
        e.currentTarget.classList.add('active');
        const docType = e.currentTarget.dataset.docType;
        this.renderDocumentsHub(docType);
      });
    });

    // Reconciliation Exceptions Modal
    const openReconBtn = document.getElementById('openReconciliationModalBtn');
    if (openReconBtn) {
      openReconBtn.addEventListener('click', () => this.showReconciliationModal());
    }

    const openDocUploadBtn = document.getElementById('openDocUploadModalBtn');
    if (openDocUploadBtn) {
      openDocUploadBtn.addEventListener('click', () => this.openModal('uploadDocModal'));
    }

    // Low-Connectivity Mode Switchers
    const connOnlineBtn = document.getElementById('connOnlineBtn');
    const connOfflineBtn = document.getElementById('connOfflineBtn');
    const syncQueueBtn = document.getElementById('syncOfflineQueueBtn');

    if (connOnlineBtn && connOfflineBtn) {
      connOnlineBtn.addEventListener('click', () => this.setConnectivityMode(false));
      connOfflineBtn.addEventListener('click', () => this.setConnectivityMode(true));
    }

    if (syncQueueBtn) {
      syncQueueBtn.addEventListener('click', () => this.syncOfflineQueue());
    }

    // Care Journeys Directory & Workspace Events
    const journeySearchInput = document.getElementById('journeySearchInput');
    if (journeySearchInput) {
      journeySearchInput.addEventListener('input', (e) => {
        this.journeySearchQuery = e.target.value.trim().toLowerCase();
        this.renderCareJourneysDirectory();
      });
    }

    const clearJourneySearchBtn = document.getElementById('clearJourneySearchBtn');
    if (clearJourneySearchBtn) {
      clearJourneySearchBtn.addEventListener('click', () => {
        if (journeySearchInput) journeySearchInput.value = '';
        this.journeySearchQuery = '';
        this.renderCareJourneysDirectory();
      });
    }

    const journeyMoreFiltersBtn = document.getElementById('journeyMoreFiltersBtn');
    const journeyMoreFiltersMenu = document.getElementById('journeyMoreFiltersMenu');

    if (journeyMoreFiltersBtn && journeyMoreFiltersMenu) {
      journeyMoreFiltersBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = journeyMoreFiltersMenu.classList.toggle('show');
        journeyMoreFiltersBtn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
      });

      document.addEventListener('click', () => {
        journeyMoreFiltersMenu.classList.remove('show');
        journeyMoreFiltersBtn.setAttribute('aria-expanded', 'false');
      });

      journeyMoreFiltersMenu.querySelectorAll('.more-filter-item').forEach(item => {
        item.addEventListener('click', (e) => {
          e.stopPropagation();
          const filter = e.currentTarget.dataset.journeyFilter;
          if (filter) {
            this.journeyFilter = filter;
            this.syncJourneyFilterPills(filter);
            this.renderCareJourneysDirectory();
            journeyMoreFiltersMenu.classList.remove('show');
            journeyMoreFiltersBtn.setAttribute('aria-expanded', 'false');
          }
        });
      });
    }

    document.querySelectorAll('[data-journey-filter]:not(.more-filter-item)').forEach(pill => {
      pill.addEventListener('click', (e) => {
        const filter = e.currentTarget.dataset.journeyFilter;
        this.journeyFilter = filter;
        this.syncJourneyFilterPills(filter);
        this.renderCareJourneysDirectory();
      });
    });

    const backToJourneysDirBtn = document.getElementById('backToJourneysDirBtn');
    if (backToJourneysDirBtn) {
      backToJourneysDirBtn.addEventListener('click', () => {
        this.closeCareJourneyWorkspace();
      });
    }

    const journeySelect = document.getElementById('journeyPatientSelect');
    if (journeySelect) {
      journeySelect.addEventListener('change', (e) => {
        this.openCareJourneyWorkspace(e.target.value);
      });
    }

    // Specialist Reviews Queue & Workspace Events
    const reviewSearchInput = document.getElementById('reviewSearchInput');
    if (reviewSearchInput) {
      reviewSearchInput.addEventListener('input', (e) => {
        this.reviewSearchQuery = e.target.value.trim().toLowerCase();
        this.renderSpecialistReviewQueue();
      });
    }

    const clearReviewSearchBtn = document.getElementById('clearReviewSearchBtn');
    if (clearReviewSearchBtn) {
      clearReviewSearchBtn.addEventListener('click', () => {
        if (reviewSearchInput) reviewSearchInput.value = '';
        this.reviewSearchQuery = '';
        this.renderSpecialistReviewQueue();
      });
    }

    const reviewMoreFiltersBtn = document.getElementById('reviewMoreFiltersBtn');
    const reviewMoreFiltersMenu = document.getElementById('reviewMoreFiltersMenu');

    if (reviewMoreFiltersBtn && reviewMoreFiltersMenu) {
      reviewMoreFiltersBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = reviewMoreFiltersMenu.classList.toggle('show');
        reviewMoreFiltersBtn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
      });

      document.addEventListener('click', () => {
        reviewMoreFiltersMenu.classList.remove('show');
        reviewMoreFiltersBtn.setAttribute('aria-expanded', 'false');
      });

      reviewMoreFiltersMenu.querySelectorAll('.more-filter-item').forEach(item => {
        item.addEventListener('click', (e) => {
          e.stopPropagation();
          const filter = e.currentTarget.dataset.reviewFilter;
          if (filter) {
            this.reviewFilter = filter;
            this.syncReviewFilterPills(filter);
            this.renderSpecialistReviewQueue();
            reviewMoreFiltersMenu.classList.remove('show');
            reviewMoreFiltersBtn.setAttribute('aria-expanded', 'false');
          }
        });
      });
    }

    document.querySelectorAll('[data-review-filter]:not(.more-filter-item)').forEach(pill => {
      pill.addEventListener('click', (e) => {
        const filter = e.currentTarget.dataset.reviewFilter;
        this.reviewFilter = filter;
        this.syncReviewFilterPills(filter);
        this.renderSpecialistReviewQueue();
      });
    });

    const backToReviewsQueueBtn = document.getElementById('backToReviewsQueueBtn');
    if (backToReviewsQueueBtn) {
      backToReviewsQueueBtn.addEventListener('click', () => {
        this.closeSpecialistReviewWorkspace();
      });
    }

    const reviewGoJourneyBtn = document.getElementById('reviewGoJourneyBtn');
    if (reviewGoJourneyBtn) {
      reviewGoJourneyBtn.addEventListener('click', () => {
        if (this.currentReviewPatientId) {
          const pid = this.currentReviewPatientId;
          this.navigateToScreen('screen-journeys');
          this.openCareJourneyWorkspace(pid);
        }
      });
    }

    const wsRoleNoticeSwitchBtn = document.getElementById('wsRoleNoticeSwitchBtn');
    if (wsRoleNoticeSwitchBtn) {
      wsRoleNoticeSwitchBtn.addEventListener('click', () => {
        this.switchRole('specialist');
        if (this.currentReviewPatientId) {
          this.openSpecialistReviewWorkspace(this.currentReviewPatientId);
        }
      });
    }

    const wsReturnQueueBtn = document.getElementById('wsReturnQueueBtn');
    if (wsReturnQueueBtn) {
      wsReturnQueueBtn.addEventListener('click', () => {
        this.closeSpecialistReviewWorkspace();
      });
    }

    const wsBtnEditReview = document.getElementById('wsBtnEditReview');
    if (wsBtnEditReview) {
      wsBtnEditReview.addEventListener('click', () => {
        const recCard = document.getElementById('wsReviewRecordedCard');
        const form = document.getElementById('wsSpecialistReviewForm');
        if (recCard) recCard.style.display = 'none';
        if (form) form.style.display = 'block';
      });
    }

    const wsSaveDraftReviewBtn = document.getElementById('wsSaveDraftReviewBtn');
    if (wsSaveDraftReviewBtn) {
      wsSaveDraftReviewBtn.addEventListener('click', () => {
        this.handleSaveDraftReview();
      });
    }

    const wsSpecialistReviewForm = document.getElementById('wsSpecialistReviewForm');
    if (wsSpecialistReviewForm) {
      wsSpecialistReviewForm.addEventListener('submit', (e) => {
        this.handleSubmitReviewWorkspace(e);
      });
    }

    // Guided Demo Stepper Nav
    document.querySelectorAll('.demo-step-pill').forEach(pill => {
      pill.addEventListener('click', (e) => {
        const step = parseInt(e.currentTarget.dataset.step, 10);
        this.goToDemoStep(step);
      });
    });

    const demoPrevBtn = document.getElementById('demoPrevStepBtn');
    const demoNextBtn = document.getElementById('demoNextStepBtn');
    if (demoPrevBtn) demoPrevBtn.addEventListener('click', () => this.goToDemoStep(this.currentDemoStep - 1));
    if (demoNextBtn) demoNextBtn.addEventListener('click', () => this.goToDemoStep(this.currentDemoStep + 1));

    // Reminder modal preview triggers
    const remindSelect = document.getElementById('remindTypeSelect');
    if (remindSelect) {
      remindSelect.addEventListener('change', () => this.updateReminderPreviewText());
    }

    const confirmSendRemBtn = document.getElementById('confirmSendReminderBtn');
    if (confirmSendRemBtn) {
      confirmSendRemBtn.addEventListener('click', () => this.handleSendSimulatedReminder());
    }

    const copyEnBtn = document.getElementById('copyEnReminderBtn');
    if (copyEnBtn) {
      copyEnBtn.addEventListener('click', () => {
        const text = document.getElementById('reminderTextEn').innerText;
        navigator.clipboard.writeText(text);
        copyEnBtn.innerText = 'Copied!';
        setTimeout(() => copyEnBtn.innerText = 'Copy', 1500);
      });
    }

    const copyHiBtn = document.getElementById('copyHiReminderBtn');
    if (copyHiBtn) {
      copyHiBtn.addEventListener('click', () => {
        const text = document.getElementById('reminderTextHi').innerText;
        navigator.clipboard.writeText(text);
        copyHiBtn.innerText = 'Copied!';
        setTimeout(() => copyHiBtn.innerText = 'Copy', 1500);
      });
    }
  }

  setupHomeActionCards() {
    const cardMap = [
      { id: 'cardGoPatients', target: 'screen-patients' },
      { id: 'cardGoJourneys', target: 'screen-journeys' },
      { id: 'cardGoFollowups', target: 'screen-followups' },
      { id: 'cardGoDocuments', target: 'screen-documents' },
      { id: 'cardGoReviews', target: 'screen-reviews' },
      { id: 'cardGoInsights', target: 'screen-analytics' }
    ];

    cardMap.forEach(item => {
      const el = document.getElementById(item.id);
      if (el) {
        el.addEventListener('click', () => {
          if (item.action) item.action();
          else this.navigateToScreen(item.target);
        });
      }
    });
  }

  setupTodayCards() {
    const map = [
      { id: 'todayCardReview', action: () => { this.reviewFilter = 'awaiting_review'; this.navigateToScreen('screen-reviews'); this.syncReviewFilterPills('awaiting_review'); } },
      { id: 'todayCardFollowup', action: () => { this.navigateToScreen('screen-followups'); this.renderFollowupsWorklist('due_today'); } },
      { id: 'todayCardContact', action: () => { this.navigateToScreen('screen-followups'); this.renderFollowupsWorklist('unable_to_contact'); } },
      { id: 'todayCardClosed', action: () => { this.navigateToScreen('screen-followups'); this.renderFollowupsWorklist('completed'); } }
    ];

    map.forEach(item => {
      const el = document.getElementById(item.id);
      if (el) {
        el.addEventListener('click', item.action);
      }
    });
  }

  /* =========================================================================
     DEMO USER & CLINICIAN PROFILE SYSTEM
     ========================================================================= */
  initProfile() {
    try {
      const saved = localStorage.getItem('retinax_user_profile');
      if (saved) {
        this.currentUserProfile = JSON.parse(saved);
        this.currentRole = this.currentUserProfile;
      } else {
        // Default to Care Coordinator preset
        this.currentUserProfile = { ...this.presetRoles.coordinator };
        this.currentRole = this.currentUserProfile;

        // If first-time user and not dismissed, show welcome setup modal
        const setupDone = localStorage.getItem('retinax_profile_setup_done') || window.location.search.includes('skip_welcome=1');
        if (!setupDone) {
          setTimeout(() => {
            this.openModal('firstTimeProfileModal');
          }, 350);
        }
      }
    } catch (e) {
      this.currentUserProfile = { ...this.presetRoles.coordinator };
      this.currentRole = this.currentUserProfile;
    }
  }

  generateInitials(name) {
    if (!name) return 'RX';
    const clean = name.replace(/^(Dr\.|Prof\.|Mr\.|Ms\.|Mrs\.)\s*/i, '').trim();
    const parts = clean.split(/\s+/).filter(Boolean);
    if (parts.length === 0) return 'RX';
    if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }

  toggleProfilePopover(forceState) {
    const popover = document.getElementById('profilePopoverMenu');
    const btn = document.getElementById('userProfileBtn');
    if (!popover || !btn) return;

    const shouldOpen = forceState !== undefined ? forceState : !popover.classList.contains('show');
    popover.classList.toggle('show', shouldOpen);
    btn.setAttribute('aria-expanded', shouldOpen ? 'true' : 'false');
  }

  openProfileFormModal(mode = 'create') {
    const modalTitle = document.getElementById('profileFormModalTitle');
    const titleSelect = document.getElementById('formProfTitle');
    const nameInput = document.getElementById('formFullName');
    const roleSelect = document.getElementById('formRoleSelect');
    const specialtyInput = document.getElementById('formSpecialty');
    const deptInput = document.getElementById('formDept');
    const facilityInput = document.getElementById('formFacility');
    const regInput = document.getElementById('formRegNumber');
    const emailInput = document.getElementById('formEmail');
    const phoneInput = document.getElementById('formPhone');
    const langSelect = document.getElementById('formLangPref');

    if (mode === 'edit' && this.currentUserProfile) {
      if (modalTitle) modalTitle.innerText = 'Edit Demo Profile';
      const prof = this.currentUserProfile;
      if (titleSelect) titleSelect.value = prof.title || 'Dr.';
      if (nameInput) nameInput.value = prof.fullName || prof.name.replace(/^(Dr\.|Prof\.|Mr\.|Ms\.|Mrs\.)\s*/i, '');
      if (roleSelect) roleSelect.value = prof.role || 'coordinator';
      if (specialtyInput) specialtyInput.value = prof.specialty || 'Ophthalmology';
      if (deptInput) deptInput.value = prof.dept || '';
      if (facilityInput) facilityInput.value = prof.facility || '';
      if (regInput) regInput.value = prof.regNumber || '';
      if (emailInput) emailInput.value = prof.email || '';
      if (phoneInput) phoneInput.value = prof.phone || '';
      if (langSelect) langSelect.value = prof.language || 'en';
    } else {
      if (modalTitle) modalTitle.innerText = 'Create Your Profile';
      if (titleSelect) titleSelect.value = 'Dr.';
      if (nameInput) nameInput.value = '';
      if (roleSelect) roleSelect.value = 'specialist';
      if (specialtyInput) specialtyInput.value = 'Ophthalmology';
      if (deptInput) deptInput.value = 'Department of Ophthalmology';
      if (facilityInput) facilityInput.value = 'District Eye Hospital';
      if (regInput) regInput.value = '';
      if (emailInput) emailInput.value = '';
      if (phoneInput) phoneInput.value = '';
      if (langSelect) langSelect.value = 'en';
    }

    this.updateProfileFormRoleFields();
    this.updateProfileFormPreview();
    this.openModal('profileFormModal');
  }

  updateProfileFormRoleFields() {
    const roleSelect = document.getElementById('formRoleSelect');
    const clinicianFields = document.getElementById('clinicianFieldsGroup');
    const lblDept = document.getElementById('lblFormDept');
    const lblFacility = document.getElementById('lblFormFacility');
    const role = roleSelect ? roleSelect.value : 'coordinator';

    if (clinicianFields) {
      clinicianFields.style.display = (role === 'specialist') ? 'block' : 'none';
    }

    if (lblDept) {
      lblDept.innerText = (role === 'admin') ? 'Department / Health Unit' : 'Department';
    }

    if (lblFacility) {
      lblFacility.innerText = (role === 'specialist') ? 'Facility / Hospital *' : ((role === 'admin') ? 'Organization / Health System *' : 'Facility / Clinic *');
    }
  }

  updateProfileFormPreview() {
    const titleSelect = document.getElementById('formProfTitle');
    const nameInput = document.getElementById('formFullName');
    const roleSelect = document.getElementById('formRoleSelect');
    const avatarPreview = document.getElementById('formAvatarPreview');
    const namePreview = document.getElementById('formAvatarNamePreview');
    const rolePreview = document.getElementById('formAvatarRolePreview');

    const title = titleSelect ? titleSelect.value : '';
    const rawName = nameInput ? nameInput.value.trim() : '';
    const role = roleSelect ? roleSelect.value : 'coordinator';

    const displayName = rawName ? `${title ? title + ' ' : ''}${rawName}` : 'Your Full Name';
    const initials = rawName ? this.generateInitials(rawName) : 'RX';
    const roleLabel = role === 'specialist' ? 'Ophthalmologist / Eye-Care Specialist' : (role === 'admin' ? 'Program Administrator' : 'Care Coordinator');

    if (avatarPreview) avatarPreview.innerText = initials;
    if (namePreview) namePreview.innerText = displayName;
    if (rolePreview) rolePreview.innerText = roleLabel;
  }

  handleProfileFormSubmit(e) {
    e.preventDefault();
    const title = document.getElementById('formProfTitle').value;
    const fullName = document.getElementById('formFullName').value.trim();
    const role = document.getElementById('formRoleSelect').value;
    const specialty = role === 'specialist' ? (document.getElementById('formSpecialty').value.trim() || 'Ophthalmology') : (role === 'admin' ? 'Health Informatics' : 'Care Coordination');
    const dept = document.getElementById('formDept').value.trim() || (role === 'specialist' ? 'Department of Ophthalmology' : 'Care Continuity');
    const facility = document.getElementById('formFacility').value.trim() || (role === 'specialist' ? 'District Eye Hospital' : 'Diabetic Care Centre');
    const regNumber = document.getElementById('formRegNumber').value.trim();
    const email = document.getElementById('formEmail').value.trim();
    const phone = document.getElementById('formPhone').value.trim();
    const language = document.getElementById('formLangPref').value;

    const displayName = `${title ? title + ' ' : ''}${fullName}`;
    const initials = this.generateInitials(fullName);
    const roleLabel = role === 'specialist' ? 'Ophthalmologist / Eye-Care Specialist' : (role === 'admin' ? 'Program Administrator' : 'Care Coordinator');

    const newProfile = {
      id: 'custom_' + Date.now(),
      name: displayName,
      title: title,
      fullName: fullName,
      role: role,
      roleLabel: roleLabel,
      specialty: specialty,
      dept: dept,
      facility: facility,
      regNumber: regNumber,
      email: email,
      phone: phone,
      language: language,
      avatar: initials,
      clinicalAuthoring: (role === 'specialist')
    };

    this.currentUserProfile = newProfile;
    this.currentRole = newProfile;
    localStorage.setItem('retinax_user_profile', JSON.stringify(newProfile));
    localStorage.setItem('retinax_profile_setup_done', 'true');

    this.updateRoleUI();
    this.closeModal('profileFormModal');
    this.closeModal('firstTimeProfileModal');
    this.showToast(`Profile active: ${newProfile.name} (${roleLabel})`);

    // Adapt open patient review workspace if visible
    if (this.currentPatientId && this.activeScreen === 'screen-patient-detail') {
      const patient = this.patients.find(p => p.id === this.currentPatientId);
      if (patient) this.renderDetailSpecialistWorkspace(patient);
    }
  }

  switchRole(roleId) {
    if (!this.presetRoles[roleId]) return;
    const preset = { ...this.presetRoles[roleId] };
    this.currentUserProfile = preset;
    this.currentRole = preset;
    localStorage.setItem('retinax_user_profile', JSON.stringify(preset));
    localStorage.setItem('retinax_profile_setup_done', 'true');

    this.updateRoleUI();
    this.showToast(`Demo role switched to ${preset.roleLabel} (${preset.name})`);

    // If a patient detail screen is open on specialist review tab, adapt UI
    if (this.currentPatientId && this.activeScreen === 'screen-patient-detail') {
      const patient = this.patients.find(p => p.id === this.currentPatientId);
      if (patient) this.renderDetailSpecialistWorkspace(patient);
    }
  }

  updateRoleUI() {
    const prof = this.currentUserProfile;
    
    // Topbar Profile Control
    this.setElText('topUserAvatar', prof.avatar);
    this.setElText('topUserName', prof.name);

    // Popover Menu Header
    this.setElText('popoverAvatar', prof.avatar);
    this.setElText('popoverName', prof.name);
    this.setElText('popoverRole', `${prof.roleLabel} • ${prof.facility}`);
    this.setElText('popoverRoleBadge', prof.roleLabel);

    // Role switcher active cards highlight
    document.querySelectorAll('.role-select-card').forEach(card => {
      card.classList.toggle('active-role', card.dataset.role === prof.role && !card.classList.contains('custom-create-card'));
    });

    // View Profile Modal Details
    this.setElText('profileViewAvatar', prof.avatar);
    this.setElText('profileViewFullName', prof.name);
    this.setElText('profileViewRoleBadge', prof.roleLabel);
    this.setElText('profileViewSpecialty', prof.specialty || 'General Care Coordination');
    this.setElText('profileViewDept', prof.dept || 'Care Continuity');
    this.setElText('profileViewFacility', prof.facility || 'District Health Facility');
    
    const regEl = document.getElementById('profileViewRegNum');
    if (regEl) {
      if (prof.regNumber) {
        regEl.innerHTML = `<strong>${prof.regNumber}</strong> <span class="text-muted font-size-11">(Self-entered demo info)</span>`;
      } else {
        regEl.innerHTML = `<span class="text-muted">Not Provided (Optional demo field)</span>`;
      }
    }
    
    this.setElText('profileViewLang', prof.language === 'hi' ? 'हिन्दी (Hindi)' : 'English');
  }

  showDemoProfileModal() {
    this.updateRoleUI();
    this.openModal('demoProfileModal');
  }

  showToast(message) {
    const toast = document.getElementById('appToast');
    if (!toast) return;

    toast.innerText = message;
    toast.classList.add('show');
    setTimeout(() => {
      toast.classList.remove('show');
    }, 2800);
  }

  /* =========================================================================
     NAVIGATION & SCREEN SWITCHING
     ========================================================================= */
  navigateToScreen(screenId) {
    this.activeScreen = screenId;
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active-screen'));
    
    const target = document.getElementById(screenId);
    if (target) {
      target.classList.add('active-screen');
    }

    // Sync primary top nav tabs (only 3 exist in topbar)
    document.querySelectorAll('.top-nav-tabs .nav-tab-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.target === screenId);
    });

    window.scrollTo({ top: 0, behavior: 'smooth' });

    // Refresh context depending on target screen
    if (screenId === 'screen-overview') {
      this.fetchAnalytics();
      this.fetchGapRadar();
    } else if (screenId === 'screen-patients') {
      this.renderPatientsList();
    } else if (screenId === 'screen-journeys') {
      if (this.currentJourneyPatientId) {
        this.openCareJourneyWorkspace(this.currentJourneyPatientId);
      } else {
        this.closeCareJourneyWorkspace();
      }
    } else if (screenId === 'screen-reviews') {
      if (this.currentReviewPatientId) {
        this.openSpecialistReviewWorkspace(this.currentReviewPatientId);
      } else {
        this.closeSpecialistReviewWorkspace();
      }
    } else if (screenId === 'screen-followups') {
      this.renderFollowupsWorklist('due_today');
    } else if (screenId === 'screen-documents') {
      this.renderDocumentsHub('all');
    } else if (screenId === 'screen-analytics') {
      this.fetchAnalytics();
    } else if (screenId === 'screen-outreach') {
      this.renderOutreachFieldTasks();
    }
  }

  syncFilterPills(filter) {
    document.querySelectorAll('.filter-pill').forEach(p => {
      p.classList.toggle('active', p.dataset.filter === filter);
    });
  }

  toggleTheme() {
    const isDark = document.body.classList.toggle('dark-mode');
    this.currentTheme = isDark ? 'dark' : 'light';
    const btn = document.getElementById('themeToggle');
    if (btn) btn.textContent = isDark ? '☾' : '☼';
    const prefSelect = document.getElementById('prefThemeSelect');
    if (prefSelect) prefSelect.value = this.currentTheme;
  }

  setTheme(theme) {
    this.currentTheme = theme;
    if (theme === 'dark') {
      document.body.classList.add('dark-mode');
      const btn = document.getElementById('themeToggle');
      if (btn) btn.textContent = '☾';
    } else {
      document.body.classList.remove('dark-mode');
      const btn = document.getElementById('themeToggle');
      if (btn) btn.textContent = '☼';
    }
  }

  initTheme() {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      this.setTheme('dark');
    }
  }

  openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.add('active');
  }

  closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove('active');
  }

  /* =========================================================================
     DATA FETCHING & API INTEGRATION
     ========================================================================= */
  async fetchPatients() {
    try {
      const res = await fetch('/api/patients');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      this.patients = data.patients || [];
      this.metrics = data.metrics || {};
      this.updateMetricsUI();
      this.renderPatientsList();
      this.renderCareJourneysDirectory();
      this.renderSpecialistReviewQueue();
    } catch (err) {
      console.error('Failed to fetch patients:', err);
    }
  }

  async fetchAnalytics() {
    try {
      const res = await fetch('/api/analytics');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      this.renderAnalyticsFunnel(data.funnel);
      this.renderBottlenecks(data.bottlenecks);
      this.renderTurnaround(data.turnaround);
      this.renderTeamWorkload(data.ownership);
    } catch (err) {
      console.error('Failed to fetch analytics:', err);
    }
  }

  async fetchGapRadar() {
    try {
      const res = await fetch('/api/gap-radar');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      this.renderFullGapRadar(data.gap_items);
    } catch (err) {
      console.error('Failed to fetch gap radar:', err);
    }
  }

  async resetDemoData() {
    if (!confirm('Reset synthetic demo dataset to initial baseline state?')) return;
    try {
      const res = await fetch('/api/patients/reset', { method: 'POST' });
      if (res.ok) {
        this.showToast('Synthetic demo dataset reset to baseline state.');
        await this.fetchPatients();
        await this.fetchAnalytics();
        await this.fetchGapRadar();
        this.navigateToScreen('screen-overview');
      }
    } catch (err) {
      alert('Failed to reset demo data: ' + err.message);
    }
  }

  /* =========================================================================
     METRICS & OVERVIEW RENDERING
     ========================================================================= */
  updateMetricsUI() {
    const m = this.metrics;
    const total = m.total_patients || (this.patients.length || 12);
    const completedCount = this.patients.filter(p => p.workflow_status && p.workflow_status.care_loop_completed).length;
    const awaitingReviewCount = this.patients.filter(p => !p.specialist_review.completed && (p.documents || []).some(d => d.doc_type === 'Retinal Screening Report')).length;
    const inReviewCount = Object.keys(this.reviewDrafts).length;
    const specialistCompletedCount = this.patients.filter(p => p.specialist_review && p.specialist_review.completed).length;
    const reconcileCount = this.patients.filter(p => p.workflow_status && p.workflow_status.screening_workflow === 'Completed' && !(p.documents || []).some(d => d.doc_type === 'Retinal Screening Report')).length;
    const unableContactCount = this.patients.filter(p => (p.followup && p.followup.status === 'Unable to Contact') || (p.workflow_status && p.workflow_status.overall_stage === 'Unable to Contact')).length;
    const pendingScreeningCount = this.patients.filter(p => p.workflow_status && p.workflow_status.screening_workflow === 'Not Started').length;
    const followupCount = this.patients.filter(p => p.followup && ['Pending', 'Scheduled'].includes(p.followup.status) && !p.workflow_status.care_loop_completed).length;

    // Home Action Card Stat Pills
    this.setElText('homeCardPatientsStat', `${total} patients`);
    this.setElText('homeCardFollowupsStat', `${followupCount} pending`);
    this.setElText('homeCardReviewsStat', `${awaitingReviewCount} awaiting review`);

    // Today Section 4 Numbers
    this.setElText('today-awaiting-review', awaitingReviewCount);
    this.setElText('today-followups', followupCount);
    this.setElText('today-uncontacted', unableContactCount);
    this.setElText('today-loop-closed', completedCount);

    // Patients Directory Filter Pill Counters
    const countNeeds = total - completedCount;
    this.setElText('count-all', total);
    this.setElText('count-needs-attention', countNeeds);
    this.setElText('count-awaiting-review', awaitingReviewCount);
    this.setElText('count-followup-pending', followupCount);
    this.setElText('count-unable-contact', unableContactCount);
    this.setElText('count-pending-screening', pendingScreeningCount);
    this.setElText('count-report-missing', reconcileCount);
    this.setElText('count-completed', completedCount);

    // Care Journeys Directory Filter Pill Counters
    this.setElText('count-journey-all', total);
    this.setElText('count-journey-needs-attention', countNeeds);
    this.setElText('count-journey-followup', followupCount);
    this.setElText('count-journey-completed', completedCount);
    this.setElText('count-journey-awaiting-review', awaitingReviewCount);
    this.setElText('count-journey-unable-contact', unableContactCount);
    this.setElText('count-journey-pending-screening', pendingScreeningCount);
    this.setElText('count-journey-report-missing', reconcileCount);

    // Specialist Reviews Queue Filter Pill Counters
    this.setElText('count-rev-awaiting', awaitingReviewCount);
    this.setElText('count-rev-in-review', inReviewCount);
    this.setElText('count-rev-completed', specialistCompletedCount);
    this.setElText('count-rev-all', total);
    this.setElText('count-rev-reconcile', reconcileCount);
  }

  setElText(id, text) {
    const el = document.getElementById(id);
    if (el) el.innerText = text;
  }

  /* =========================================================================
     PATIENTS DIRECTORY & CARDS LIST (SIMPLIFIED UX)
     ========================================================================= */
  getPatientStatusInfo(p) {
    const wf = p.workflow_status || {};
    const fu = p.followup || {};
    const hasReport = (p.documents || []).some(d => d.doc_type === 'Retinal Screening Report');
    const hasReview = p.specialist_review && p.specialist_review.completed;

    if (wf.care_loop_completed) {
      return {
        statusText: 'Care Loop Closed',
        dotClass: 'status-emerald',
        currentStep: 'Care Loop Closed',
        nextAction: 'Care cycle completed'
      };
    }

    if (fu.status === 'Unable to Contact' || wf.overall_stage === 'Unable to Contact') {
      return {
        statusText: 'Unable to Contact',
        dotClass: 'status-red',
        currentStep: 'Outreach & Contact',
        nextAction: 'Community outreach'
      };
    }

    if (hasReport && !hasReview) {
      return {
        statusText: 'Awaiting Specialist Review',
        dotClass: 'status-amber',
        currentStep: 'Specialist Review',
        nextAction: 'Coordinate specialist review'
      };
    }

    if (wf.screening_workflow === 'Completed' && !hasReport) {
      return {
        statusText: 'Record Reconciliation',
        dotClass: 'status-amber',
        currentStep: 'Record Reconciliation',
        nextAction: 'Reconcile screening report'
      };
    }

    if (hasReview && ['Pending', 'Scheduled'].includes(fu.status)) {
      const isHospital = (p.specialist_review.referral_status || '').includes('Hospital');
      return {
        statusText: 'Follow-Up Scheduled',
        dotClass: 'status-purple',
        currentStep: 'Follow-Up Coordination',
        nextAction: isHospital ? 'Coordinate hospital follow-up' : 'Coordinate routine follow-up'
      };
    }

    if (wf.screening_workflow === 'Scheduled') {
      return {
        statusText: 'Screening Scheduled',
        dotClass: 'status-blue',
        currentStep: 'Screening Appointment',
        nextAction: 'Confirm appointment'
      };
    }

    return {
      statusText: 'Screening Pending',
      dotClass: 'status-blue',
      currentStep: 'Screening Intake',
      nextAction: 'Schedule screening'
    };
  }

  syncFilterPills(activeFilter) {
    const morePill = document.getElementById('moreFiltersBtn');
    const moreLabel = document.getElementById('moreFiltersLabel');
    const moreItems = document.querySelectorAll('.more-filter-item');
    const primaryPills = document.querySelectorAll('.filter-pills-row > .filter-pill:not(.more-filters-btn)');

    const moreMap = {
      'awaiting_review': 'Awaiting Review',
      'unable_to_contact': 'Unable to Contact',
      'pending_screening': 'Screening Pending',
      'report_missing': 'Record Reconciliation'
    };

    if (moreMap[activeFilter]) {
      if (morePill) morePill.classList.add('active');
      if (moreLabel) moreLabel.innerText = moreMap[activeFilter];
      primaryPills.forEach(p => p.classList.remove('active'));
      moreItems.forEach(item => {
        item.classList.toggle('active', item.dataset.filter === activeFilter);
      });
    } else {
      if (morePill) morePill.classList.remove('active');
      if (moreLabel) moreLabel.innerText = 'More';
      primaryPills.forEach(p => {
        p.classList.toggle('active', p.dataset.filter === activeFilter);
      });
      moreItems.forEach(item => item.classList.remove('active'));
    }
  }

  renderPatientsList() {
    const cardGrid = document.getElementById('patientsCardGrid');
    const tableBody = document.getElementById('patientTableBody');
    if (!cardGrid || !tableBody) return;

    let list = [...this.patients];

    if (this.currentFilter === 'needs_attention') {
      list = list.filter(p => !p.workflow_status.care_loop_completed);
    } else if (this.currentFilter === 'awaiting_review') {
      list = list.filter(p => !p.specialist_review.completed && (p.documents || []).some(d => d.doc_type === 'Retinal Screening Report'));
    } else if (this.currentFilter === 'followup_pending') {
      list = list.filter(p => ['Pending', 'Scheduled'].includes(p.followup.status) && !p.workflow_status.care_loop_completed);
    } else if (this.currentFilter === 'unable_to_contact') {
      list = list.filter(p => p.followup.status === 'Unable to Contact' || p.workflow_status.overall_stage === 'Unable to Contact');
    } else if (this.currentFilter === 'pending_screening') {
      list = list.filter(p => p.workflow_status.screening_workflow === 'Not Started');
    } else if (this.currentFilter === 'report_missing') {
      list = list.filter(p => p.workflow_status.screening_workflow === 'Completed' && !(p.documents || []).some(d => d.doc_type === 'Retinal Screening Report'));
    } else if (this.currentFilter === 'completed') {
      list = list.filter(p => p.workflow_status.care_loop_completed);
    }

    if (this.searchQuery) {
      list = list.filter(p => {
        const s = `${p.id} ${p.name} ${p.facility} ${p.clinician} ${p.workflow_status.next_workflow_action}`.toLowerCase();
        return s.includes(this.searchQuery);
      });
    }

    if (list.length === 0) {
      cardGrid.innerHTML = `<div class="p-4 text-muted font-size-13">No patients match the selected filter criteria.</div>`;
      tableBody.innerHTML = `<tr><td colspan="9" class="p-4 text-center text-muted">No patients found.</td></tr>`;
      return;
    }

    // Render Clean, Simplified Directory Cards
    cardGrid.innerHTML = list.map(p => {
      const initials = p.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
      const statusInfo = this.getPatientStatusInfo(p);

      return `
        <div class="patient-card" onclick="app.openPatientDetail('${p.id}')">
          <div class="card-top-row">
            <div class="card-patient-meta">
              <div class="patient-avatar-box">${initials}</div>
              <div>
                <div class="patient-card-name">${p.name}</div>
                <div class="patient-card-id">${p.id}</div>
              </div>
            </div>
          </div>

          <div class="patient-status-indicator">
            <span class="status-dot ${statusInfo.dotClass}"></span>
            <span>${statusInfo.statusText}</span>
          </div>

          <div class="card-workflow-sections">
            <div class="card-step-box">
              <span class="card-step-label">Current Step</span>
              <span class="card-step-val">${statusInfo.currentStep}</span>
            </div>

            <div class="card-step-box">
              <span class="card-step-label">Next</span>
              <span class="card-step-val">${statusInfo.nextAction}</span>
            </div>
          </div>

          <div class="card-footer-cta">
            <span>Journey &rarr;</span>
          </div>
        </div>
      `;
    }).join('');

    // Render Table
    tableBody.innerHTML = list.map(p => {
      const stage = p.workflow_status.overall_stage;
      const compPct = p.completeness ? p.completeness.score_percentage : 70;
      const statusInfo = this.getPatientStatusInfo(p);

      return `
        <tr>
          <td>
            <strong>${p.name}</strong><br/>
            <span class="text-muted">${p.id} &bull; ${p.age}y ${p.sex}</span>
          </td>
          <td>
            ${p.facility}<br/>
            <span class="text-muted">${p.clinician}</span>
          </td>
          <td>
            <span class="patient-status-indicator">
              <span class="status-dot ${statusInfo.dotClass}"></span> ${statusInfo.statusText}
            </span>
          </td>
          <td>${p.specialist_review.completed ? '✓ ' + p.specialist_review.clinician_name : '<span class="text-amber">⏳ Pending</span>'}</td>
          <td><strong>${statusInfo.nextAction}</strong></td>
          <td>${p.workflow_status.assigned_to || 'Care Coordinator'}</td>
          <td>${p.workflow_status.due_date || 'Today'}</td>
          <td>${compPct}%</td>
          <td>
            <button class="btn-outline btn-sm" onclick="event.stopPropagation(); app.openPatientDetail('${p.id}')">Inspect &rarr;</button>
          </td>
        </tr>
      `;
    }).join('');
  }

  getStageBadgeClass(stage = '', loopCompleted = false) {
    if (loopCompleted) return 'badge-completed';
    if (stage.includes('Review')) return 'badge-review';
    if (stage.includes('Follow-Up')) return 'badge-followup';
    if (stage.includes('Unable') || stage.includes('Unreachable')) return 'badge-uncontacted';
    if (stage.includes('Screening')) return 'badge-screening';
    return 'badge-screening';
  }

  /* =========================================================================
     CARE JOURNEYS DIRECTORY & WORKSPACE
     ========================================================================= */
  getJourneyStepIndex(p) {
    const wf = p.workflow_status || {};
    const fu = p.followup || {};
    const hasReport = (p.documents || []).some(d => d.doc_type === 'Retinal Screening Report');
    const hasReview = p.specialist_review && p.specialist_review.completed;
    const loopDone = wf.care_loop_completed;

    if (loopDone) return 8;
    if (hasReview && fu.contact_attempts && fu.contact_attempts.length > 0) return 7;
    if (hasReview) return 6;
    if (hasReport) return 5;
    if (wf.screening_workflow === 'Completed') return 4;
    if (wf.screening_workflow === 'Scheduled') return 2;
    return 1;
  }

  getJourneyMiniStepperHtml(p) {
    const activeIdx = this.getJourneyStepIndex(p);
    const loopDone = p.workflow_status && p.workflow_status.care_loop_completed;
    const steps = [1, 2, 3, 4, 5, 6, 7, 8];
    
    return `
      <div class="journey-mini-stepper" title="Journey Progress: Step ${activeIdx} of 8">
        ${steps.map((num, i) => {
          const isDone = num < activeIdx || (num === 8 && loopDone);
          const isCurrent = num === activeIdx && !loopDone;
          const cls = isDone ? 'done' : (isCurrent ? 'current' : 'pending');
          const symbol = isDone ? '✓' : (isCurrent ? '●' : '○');
          const connector = i < 7 ? `<span class="mini-connector ${isDone ? 'done' : (isCurrent ? 'current' : '')}"></span>` : '';
          return `<span class="mini-step ${cls}">${symbol}</span>${connector}`;
        }).join('')}
      </div>
    `;
  }

  getJourneyWhyAttentionText(p) {
    const wf = p.workflow_status || {};
    const fu = p.followup || {};
    const hasReport = (p.documents || []).some(d => d.doc_type === 'Retinal Screening Report');
    const hasReview = p.specialist_review && p.specialist_review.completed;

    if (wf.care_loop_completed) {
      return `Care journey complete for the 2026 cycle. Patient attended clinician-directed follow-up and next routine recall is scheduled.`;
    }
    if (fu.status === 'Unable to Contact' || wf.overall_stage === 'Unable to Contact') {
      return `Patient unreachable after ${fu.contact_attempts ? fu.contact_attempts.length : 2} phone outreach attempts. Community ASHA visit required to prevent drop-out.`;
    }
    if (hasReport && !hasReview) {
      return `Retinal screening report uploaded and awaiting specialist ophthalmologist clinical evaluation and follow-up plan entry.`;
    }
    if (wf.screening_workflow === 'Completed' && !hasReport) {
      return `Mobile camp screening marked complete, but digital report record is pending reconciliation in Document Hub.`;
    }
    if (hasReview && ['Pending', 'Scheduled'].includes(fu.status)) {
      return `Specialist review completed. Coordinator follow-up coordination task is active (Target: ${fu.planned_date || 'Upcoming'}).`;
    }
    if (wf.screening_workflow === 'Scheduled') {
      return `Patient is scheduled for screening at ${p.facility}. Coordinator confirmation pending.`;
    }
    return `Patient intake registered. Retinal screening appointment slot pending booking.`;
  }

  syncJourneyFilterPills(activeFilter) {
    const morePill = document.getElementById('journeyMoreFiltersBtn');
    const moreLabel = document.getElementById('journeyMoreFiltersLabel');
    const moreItems = document.querySelectorAll('#journeyMoreFiltersMenu .more-filter-item');
    const primaryPills = document.querySelectorAll('#journeysDirectoryView .filter-pills-row > .filter-pill:not(.more-filters-btn)');

    const moreMap = {
      'awaiting_review': 'Awaiting Specialist Review',
      'unable_to_contact': 'Unable to Contact',
      'pending_screening': 'Screening Pending',
      'report_missing': 'Record Reconciliation'
    };

    if (moreMap[activeFilter]) {
      if (morePill) morePill.classList.add('active');
      if (moreLabel) moreLabel.innerText = moreMap[activeFilter];
      primaryPills.forEach(p => p.classList.remove('active'));
      moreItems.forEach(item => {
        item.classList.toggle('active', item.dataset.journeyFilter === activeFilter);
      });
    } else {
      if (morePill) morePill.classList.remove('active');
      if (moreLabel) moreLabel.innerText = 'More';
      primaryPills.forEach(p => {
        p.classList.toggle('active', p.dataset.journeyFilter === activeFilter);
      });
      moreItems.forEach(item => item.classList.remove('active'));
    }
  }

  renderCareJourneysDirectory() {
    const grid = document.getElementById('journeyCardsGrid');
    if (!grid) return;

    let list = [...this.patients];

    if (this.journeyFilter === 'needs_attention') {
      list = list.filter(p => !p.workflow_status.care_loop_completed);
    } else if (this.journeyFilter === 'awaiting_review') {
      list = list.filter(p => !p.specialist_review.completed && (p.documents || []).some(d => d.doc_type === 'Retinal Screening Report'));
    } else if (this.journeyFilter === 'followup_pending') {
      list = list.filter(p => ['Pending', 'Scheduled'].includes(p.followup.status) && !p.workflow_status.care_loop_completed);
    } else if (this.journeyFilter === 'unable_to_contact') {
      list = list.filter(p => p.followup.status === 'Unable to Contact' || p.workflow_status.overall_stage === 'Unable to Contact');
    } else if (this.journeyFilter === 'pending_screening') {
      list = list.filter(p => p.workflow_status.screening_workflow === 'Not Started');
    } else if (this.journeyFilter === 'report_missing') {
      list = list.filter(p => p.workflow_status.screening_workflow === 'Completed' && !(p.documents || []).some(d => d.doc_type === 'Retinal Screening Report'));
    } else if (this.journeyFilter === 'completed') {
      list = list.filter(p => p.workflow_status.care_loop_completed);
    }

    if (this.journeySearchQuery) {
      list = list.filter(p => {
        const s = `${p.id} ${p.name} ${p.facility} ${p.clinician} ${p.workflow_status.next_workflow_action}`.toLowerCase();
        return s.includes(this.journeySearchQuery);
      });
    }

    if (list.length === 0) {
      grid.innerHTML = `<div class="p-4 text-muted font-size-13">No patient journeys match the selected filter.</div>`;
      return;
    }

    grid.innerHTML = list.map(p => {
      const initials = p.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
      const statusInfo = this.getPatientStatusInfo(p);
      const miniStepper = this.getJourneyMiniStepperHtml(p);

      return `
        <div class="patient-card" onclick="app.openCareJourneyWorkspace('${p.id}')">
          <div class="card-top-row">
            <div class="card-patient-meta">
              <div class="patient-avatar-box">${initials}</div>
              <div>
                <div class="patient-card-name">${p.name}</div>
                <div class="patient-card-id">${p.id} &bull; ${p.age}y ${p.sex}</div>
              </div>
            </div>
          </div>

          <div class="patient-status-indicator">
            <span class="status-dot ${statusInfo.dotClass}"></span>
            <span>${statusInfo.statusText}</span>
          </div>

          ${miniStepper}

          <div class="card-workflow-sections">
            <div class="card-step-box">
              <span class="card-step-label">Current Step</span>
              <span class="card-step-val">${statusInfo.currentStep}</span>
            </div>
            <div class="card-step-box">
              <span class="card-step-label">Next Action</span>
              <span class="card-step-val">${statusInfo.nextAction}</span>
            </div>
          </div>

          <div class="card-footer-cta">
            <span>View Care Journey &rarr;</span>
          </div>
        </div>
      `;
    }).join('');
  }

  openCareJourneyWorkspace(patientId) {
    this.currentJourneyPatientId = patientId;
    const patient = this.patients.find(p => p.id === patientId);
    if (!patient) return;

    if (this.activeScreen !== 'screen-journeys') {
      this.navigateToScreen('screen-journeys');
    }

    const dirView = document.getElementById('journeysDirectoryView');
    const wsView = document.getElementById('journeyDetailWorkspaceView');
    if (dirView) dirView.style.display = 'none';
    if (wsView) wsView.style.display = 'block';

    // Populate patient switcher select in Care Journeys
    const select = document.getElementById('journeyPatientSelect');
    if (select) {
      select.innerHTML = this.patients.map(p => `
        <option value="${p.id}" ${p.id === patientId ? 'selected' : ''}>${p.name} (${p.id})</option>
      `).join('');
    }

    // Populate Hero Details
    const initials = patient.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
    this.setElText('twinAvatar', initials);
    this.setElText('twinPatientName', patient.name);
    this.setElText('twinPatientId', patient.id);
    this.setElText('twinPatientSub', `${patient.age} yrs • ${patient.sex} • ${patient.diabetes_profile ? patient.diabetes_profile.type : 'Type 2 DM'} • ${patient.facility}`);
    
    const statusPill = document.getElementById('twinStatusPill');
    if (statusPill) {
      const statusInfo = this.getPatientStatusInfo(patient);
      statusPill.innerText = statusInfo.statusText;
      statusPill.className = `stage-badge ${this.getStageBadgeClass(statusInfo.statusText, patient.workflow_status.care_loop_completed)}`;
    }

    const statusInfo = this.getPatientStatusInfo(patient);
    this.setElText('twinCurrentStepVal', statusInfo.currentStep);
    this.setElText('twinNextActionVal', statusInfo.nextAction);
    this.setElText('twinAssignedToVal', patient.workflow_status.assigned_to || 'Care Coordinator');

    // Render 8-Step Stepper Track
    const milestones = [
      { num: 1, title: 'Registered' },
      { num: 2, title: 'Scheduled' },
      { num: 3, title: 'Screened' },
      { num: 4, title: 'Report Filed' },
      { num: 5, title: 'Specialist Review' },
      { num: 6, title: 'Follow-Up Plan' },
      { num: 7, title: 'Engaged' },
      { num: 8, title: 'Loop Closed' }
    ];

    const activeIndex = this.getJourneyStepIndex(patient);
    const loopDone = patient.workflow_status.care_loop_completed;

    const track = document.getElementById('twinStepperTrack');
    if (track) {
      track.innerHTML = milestones.map((m, idx) => {
        const stepNum = m.num;
        let stateClass = '';
        if (stepNum < activeIndex || (stepNum === 8 && loopDone)) stateClass = 'completed';
        else if (stepNum === activeIndex) stateClass = 'in-progress active-selected';
        else stateClass = 'pending';

        return `
          <div class="step-node ${stateClass}" onclick="app.inspectJourneyNode('${patient.id}', ${idx})" data-node-idx="${idx}" style="cursor: pointer;">
            <div class="step-connector"></div>
            <div class="step-circle">${stepNum < activeIndex || (stepNum === 8 && loopDone) ? '✓' : stepNum}</div>
            <div class="step-label">${m.title}</div>
          </div>
        `;
      }).join('');
    }

    // Why This Journey Needs Attention text
    this.setElText('journeyWhyAttentionText', this.getJourneyWhyAttentionText(patient));

    // Inspect the current active node
    this.inspectJourneyNode(patient.id, activeIndex - 1);
  }

  closeCareJourneyWorkspace() {
    this.currentJourneyPatientId = null;
    const dirView = document.getElementById('journeysDirectoryView');
    const wsView = document.getElementById('journeyDetailWorkspaceView');
    if (dirView) dirView.style.display = 'block';
    if (wsView) wsView.style.display = 'none';
    this.renderCareJourneysDirectory();
  }

  inspectJourneyNode(patientId, nodeIndex) {
    const patient = this.patients.find(p => p.id === patientId);
    if (!patient) return;

    this.selectedJourneyNodeIndex = nodeIndex;

    // Highlight selected node in the stepper
    document.querySelectorAll('#twinStepperTrack .step-node').forEach((node, idx) => {
      node.classList.toggle('active-selected', idx === nodeIndex);
    });

    const milestones = [
      { num: 1, title: 'Patient Registration & Intake', desc: `Patient enrolled on ${patient.registration_date}. Demographics recorded.`, actor: 'Care Coordinator', due: 'Completed', source: 'Outpatient Clinic' },
      { num: 2, title: 'Screening Schedule Confirmed', desc: `Retinal screening appointment slot booked for ${patient.facility}.`, actor: 'Care Coordinator', due: 'Completed', source: 'Appointment Desk' },
      { num: 3, title: 'Fundus Scans Acquired', desc: `Digital fundus photography completed per screening protocol.`, actor: 'Ophthalmic Technician', due: 'Completed', source: 'Mobile Eye Camp' },
      { num: 4, title: 'Report Filed & Indexed', desc: `Retinal screening report uploaded into Document Hub.`, actor: 'Care Coordinator', due: 'Completed', source: 'Document Hub' },
      { num: 5, title: 'Specialist Ophthalmologist Review', desc: patient.specialist_review.completed ? `Review recorded by ${patient.specialist_review.clinician_name}. Assessment: ${patient.specialist_review.clinical_assessment}` : 'Uploaded fundus report awaiting specialist clinical evaluation.', actor: patient.specialist_review.clinician_name || 'Department of Ophthalmology', due: 'Today', source: 'Specialist Review Portal' },
      { num: 6, title: 'Clinician Follow-Up Directive', desc: patient.specialist_review.completed ? `Operational task generated per clinician directive: ${patient.specialist_review.followup_instructions}` : 'Pending clinician directives.', actor: 'Care Coordinator', due: patient.followup.planned_date || 'Upcoming', source: 'Clinician Instruction' },
      { num: 7, title: 'Patient Engagement & Outreach', desc: `Bilingual reminders and outreach logged to confirm appointment attendance.`, actor: 'Outreach Coordinator / ASHA', due: 'Active', source: 'Outreach Module' },
      { num: 8, title: 'Care Loop Closed', desc: patient.workflow_status.care_loop_completed ? 'Patient attended follow-up. Care cycle completed for 2026.' : 'Care loop closes once clinician-directed follow-up is documented.', actor: 'Care Coordinator', due: 'Target: 2026', source: 'Continuity Engine' }
    ];

    const current = milestones[nodeIndex] || milestones[0];

    this.setElText('inspectStepBadge', `Step ${current.num} of 8`);
    this.setElText('inspectTitle', current.title);
    this.setElText('inspectDesc', current.desc);
    this.setElText('inspectActor', current.actor);
    this.setElText('inspectDue', current.due);
    this.setElText('inspectSource', current.source);

    const actContainer = document.getElementById('inspectActionButtons');
    if (actContainer) {
      if (current.num === 5) {
        actContainer.innerHTML = `<button class="btn-primary btn-sm" onclick="app.openSpecialistReviewWorkspace('${patient.id}')">🩺 Open Specialist Review &rarr;</button>`;
      } else if (current.num === 7) {
        actContainer.innerHTML = `<button class="btn-primary btn-sm" onclick="app.showBilingualReminderModal('${patient.id}')">💬 Send Reminder</button>`;
      } else if (current.num === 6 || current.num === 8) {
        actContainer.innerHTML = `<button class="btn-primary btn-sm" onclick="app.openPatientDetail('${patient.id}', 'followup')">🎯 Manage Follow-Up &rarr;</button>`;
      } else {
        actContainer.innerHTML = `<button class="btn-outline btn-sm" onclick="app.openPatientDetail('${patient.id}')">🔍 Open Patient Record &rarr;</button>`;
      }
    }
  }

  /* =========================================================================
     SPECIALIST REVIEWS QUEUE & CLINICIAN WORKSPACE
     ========================================================================= */
  getSpecialistReviewStatusInfo(p) {
    const hasReport = (p.documents || []).some(d => d.doc_type === 'Retinal Screening Report');
    const hasReview = p.specialist_review && p.specialist_review.completed;
    const isDraft = !!this.reviewDrafts[p.id];
    const reportDoc = (p.documents || []).find(d => d.doc_type === 'Retinal Screening Report');

    if (hasReview) {
      return {
        statusText: 'Completed',
        dotClass: 'status-emerald',
        badgeClass: 'badge-completed',
        screeningDate: (reportDoc && reportDoc.upload_date) || p.registration_date,
        reportSource: (reportDoc && reportDoc.source) || 'Mobile Screening Camp',
        assignedTo: p.specialist_review.clinician_name || 'Dr. Suresh Chandran',
        dueDate: 'Completed',
        btnText: 'View Review →',
        notes: `Assessment recorded: ${p.specialist_review.clinical_assessment ? p.specialist_review.clinical_assessment.substring(0, 60) + '...' : 'Completed'}`
      };
    }

    if (isDraft) {
      return {
        statusText: 'In Review (Draft Saved)',
        dotClass: 'status-purple',
        badgeClass: 'badge-followup',
        screeningDate: (reportDoc && reportDoc.upload_date) || p.registration_date,
        reportSource: (reportDoc && reportDoc.source) || 'Mobile Screening Camp',
        assignedTo: this.currentUserProfile.name,
        dueDate: 'In Progress',
        btnText: 'Resume Review →',
        notes: 'Clinician draft saved locally. Awaiting submission.'
      };
    }

    if (hasReport) {
      return {
        statusText: 'Awaiting Review',
        dotClass: 'status-amber',
        badgeClass: 'badge-review',
        screeningDate: (reportDoc && reportDoc.upload_date) || p.registration_date,
        reportSource: (reportDoc && reportDoc.source) || 'Mobile Eye Camp',
        assignedTo: 'Department of Ophthalmology',
        dueDate: 'Today',
        btnText: 'Open Review →',
        notes: 'Fundus images available in Document Hub. Clinical evaluation pending.'
      };
    }

    if (p.workflow_status.screening_workflow === 'Completed') {
      return {
        statusText: 'Record Reconciliation Required',
        dotClass: 'status-amber',
        badgeClass: 'badge-review',
        screeningDate: p.registration_date,
        reportSource: 'External Record Pending',
        assignedTo: 'Care Coordinator',
        dueDate: 'Pending Record',
        btnText: 'Open Workspace →',
        notes: 'Screening done at camp. Document reconciliation required before review.'
      };
    }

    return {
      statusText: 'Screening Pending',
      dotClass: 'status-blue',
      badgeClass: 'badge-screening',
      screeningDate: 'Pending',
      reportSource: 'Screening Not Completed',
      assignedTo: 'Care Coordinator',
      dueDate: 'Pending',
      btnText: 'Open Workspace →',
      notes: 'Patient not yet screened.'
    };
  }

  syncReviewFilterPills(activeFilter) {
    const morePill = document.getElementById('reviewMoreFiltersBtn');
    const moreLabel = document.getElementById('reviewMoreFiltersLabel');
    const moreItems = document.querySelectorAll('#reviewMoreFiltersMenu .more-filter-item');
    const primaryPills = document.querySelectorAll('#reviewsQueueView .filter-pills-row > .filter-pill:not(.more-filters-btn)');

    const moreMap = {
      'reconciliation': 'Record Reconciliation Required'
    };

    if (moreMap[activeFilter]) {
      if (morePill) morePill.classList.add('active');
      if (moreLabel) moreLabel.innerText = moreMap[activeFilter];
      primaryPills.forEach(p => p.classList.remove('active'));
      moreItems.forEach(item => {
        item.classList.toggle('active', item.dataset.reviewFilter === activeFilter);
      });
    } else {
      if (morePill) morePill.classList.remove('active');
      if (moreLabel) moreLabel.innerText = 'More';
      primaryPills.forEach(p => {
        p.classList.toggle('active', p.dataset.reviewFilter === activeFilter);
      });
      moreItems.forEach(item => item.classList.remove('active'));
    }
  }

  renderSpecialistReviewQueue() {
    const grid = document.getElementById('reviewsQueueGrid');
    if (!grid) return;

    let list = [...this.patients];

    if (this.reviewFilter === 'awaiting_review') {
      list = list.filter(p => !p.specialist_review.completed && (p.documents || []).some(d => d.doc_type === 'Retinal Screening Report') && !this.reviewDrafts[p.id]);
    } else if (this.reviewFilter === 'in_review') {
      list = list.filter(p => !!this.reviewDrafts[p.id]);
    } else if (this.reviewFilter === 'completed') {
      list = list.filter(p => p.specialist_review && p.specialist_review.completed);
    } else if (this.reviewFilter === 'reconciliation') {
      list = list.filter(p => p.workflow_status.screening_workflow === 'Completed' && !(p.documents || []).some(d => d.doc_type === 'Retinal Screening Report'));
    }

    if (this.reviewSearchQuery) {
      list = list.filter(p => {
        const s = `${p.id} ${p.name} ${p.facility} ${p.clinician}`.toLowerCase();
        return s.includes(this.reviewSearchQuery);
      });
    }

    if (list.length === 0) {
      grid.innerHTML = `<div class="p-4 text-muted font-size-13">No review records match the selected queue filter.</div>`;
      return;
    }

    grid.innerHTML = list.map(p => {
      const initials = p.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
      const info = this.getSpecialistReviewStatusInfo(p);

      return `
        <div class="patient-card" onclick="app.openSpecialistReviewWorkspace('${p.id}')">
          <div class="card-top-row">
            <div class="card-patient-meta">
              <div class="patient-avatar-box">${initials}</div>
              <div>
                <div class="patient-card-name">${p.name}</div>
                <div class="patient-card-id">${p.id} &bull; ${p.age}y ${p.sex}</div>
              </div>
            </div>
          </div>

          <div class="patient-status-indicator">
            <span class="status-dot ${info.dotClass}"></span>
            <span>${info.statusText}</span>
          </div>

          <div class="queue-card-meta">
            <div class="queue-meta-col">
              <span class="queue-meta-lbl">Acquired</span>
              <span class="queue-meta-val">${info.screeningDate}</span>
            </div>
            <div class="queue-meta-col">
              <span class="queue-meta-lbl">Source</span>
              <span class="queue-meta-val">${info.reportSource}</span>
            </div>
            <div class="queue-meta-col">
              <span class="queue-meta-lbl">Assigned</span>
              <span class="queue-meta-val">${info.assignedTo}</span>
            </div>
            <div class="queue-meta-col">
              <span class="queue-meta-lbl">Due</span>
              <span class="queue-meta-val">${info.dueDate}</span>
            </div>
          </div>

          <div class="font-size-11 text-muted mt-2" style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
            ${info.notes}
          </div>

          <div class="card-footer-cta mt-2">
            <span>${info.btnText}</span>
          </div>
        </div>
      `;
    }).join('');
  }

  openSpecialistReviewWorkspace(patientId) {
    this.currentReviewPatientId = patientId;
    const patient = this.patients.find(p => p.id === patientId);
    if (!patient) return;

    if (this.activeScreen !== 'screen-reviews') {
      this.navigateToScreen('screen-reviews');
    }

    const queueView = document.getElementById('reviewsQueueView');
    const wsView = document.getElementById('reviewWorkspaceView');
    if (queueView) queueView.style.display = 'none';
    if (wsView) wsView.style.display = 'block';

    // Populate patient bar
    const initials = patient.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
    this.setElText('revWsAvatar', initials);
    this.setElText('revWsPatientName', patient.name);
    this.setElText('revWsPatientId', patient.id);
    this.setElText('revWsDemographics', `${patient.age} yrs • ${patient.sex} • ${patient.diabetes_profile ? patient.diabetes_profile.type : 'Type 2 DM'} • ${patient.facility}`);

    const statusBadge = document.getElementById('revWsStatusBadge');
    if (statusBadge) {
      const rev = patient.specialist_review;
      if (rev && rev.completed) {
        statusBadge.innerText = 'Completed';
        statusBadge.className = 'stage-badge badge-completed';
      } else if (this.reviewDrafts[patient.id]) {
        statusBadge.innerText = 'In Review (Draft Saved)';
        statusBadge.className = 'stage-badge badge-followup';
      } else {
        statusBadge.innerText = 'Awaiting Review';
        statusBadge.className = 'stage-badge badge-review';
      }
    }

    // Populate Left Column (Source Records & Clinical Context)
    const reportDoc = (patient.documents || []).find(d => d.doc_type === 'Retinal Screening Report');
    this.setElText('wsReviewDocTitle', reportDoc ? reportDoc.title : 'Retinal_Report_' + patient.id + '.pdf');
    this.setElText('wsSheetDate', `Acquired: ${(reportDoc && reportDoc.upload_date) || patient.registration_date} • Mobile Eye Camp`);
    this.setElText('wsContextHbA1c', (patient.diabetes_profile && patient.diabetes_profile.hba1c) ? `${patient.diabetes_profile.hba1c}%` : '8.2%');
    this.setElText('wsContextDuration', (patient.diabetes_profile && patient.diabetes_profile.duration) ? patient.diabetes_profile.duration : '7 years');

    // Role checking & active clinician chip
    const isSpecialist = this.currentUserProfile.clinicalAuthoring;
    const roleBanner = document.getElementById('wsRoleNoticeBanner');
    if (roleBanner) {
      roleBanner.style.display = isSpecialist ? 'none' : 'flex';
    }

    // Active clinician profile chip
    this.setElText('wsClinicianProfileName', this.currentUserProfile.name);
    this.setElText('wsClinicianProfileSpecialty', this.currentUserProfile.specialty || 'Ophthalmology');
    this.setElText('wsClinicianProfileFacility', this.currentUserProfile.facility || 'District Eye Hospital');

    // Check form inputs readOnly/disabled state
    const assessmentInput = document.getElementById('wsReviewAssessment');
    const referralInput = document.getElementById('wsReviewReferral');
    const dateInput = document.getElementById('wsReviewFollowupDate');
    const instructionsInput = document.getElementById('wsReviewInstructions');
    const notesInput = document.getElementById('wsReviewNotes');
    const submitBtn = document.getElementById('wsSubmitReviewBtn');
    const draftBtn = document.getElementById('wsSaveDraftReviewBtn');

    if (assessmentInput) assessmentInput.readOnly = !isSpecialist;
    if (referralInput) referralInput.disabled = !isSpecialist;
    if (dateInput) dateInput.disabled = !isSpecialist;
    if (instructionsInput) instructionsInput.readOnly = !isSpecialist;
    if (notesInput) notesInput.readOnly = !isSpecialist;

    if (submitBtn) {
      submitBtn.disabled = !isSpecialist;
      submitBtn.innerText = isSpecialist ? '✓ Submit Review' : 'Restricted to Specialist Role';
    }
    if (draftBtn) {
      draftBtn.disabled = !isSpecialist;
    }

    // Check if review has already been completed
    const recCard = document.getElementById('wsReviewRecordedCard');
    const reviewForm = document.getElementById('wsSpecialistReviewForm');
    const successBanner = document.getElementById('wsReviewSuccessBanner');
    if (successBanner) successBanner.style.display = 'none';

    const rev = patient.specialist_review;
    if (rev && rev.completed) {
      if (recCard) recCard.style.display = 'block';
      if (reviewForm) reviewForm.style.display = 'none';

      this.setElText('wsRevCardRecordedTime', rev.review_timestamp ? `Recorded: ${rev.review_timestamp}` : 'Recorded');
      this.setElText('wsRevCardClinicianName', rev.clinician_name || 'Attending Ophthalmologist');
      this.setElText('wsRevCardSpecialty', rev.clinician_specialty || 'Ophthalmology');
      this.setElText('wsRevCardFacility', rev.clinician_facility || 'District Eye Hospital');
      this.setElText('wsRevCardAssessment', rev.clinical_assessment || '');
      this.setElText('wsRevCardDisposition', rev.referral_status || 'Hospital Follow-Up (6 Months)');
      this.setElText('wsRevCardDueDate', patient.followup && patient.followup.planned_date ? `Due: ${patient.followup.planned_date}` : 'Per Clinician Plan');
      this.setElText('wsRevCardInstructions', rev.followup_instructions || 'Routine care monitoring.');
      this.setElText('wsProvClinicianLabel', rev.clinician_name || 'Evaluating Clinician');

      const regBox = document.getElementById('wsRevCardRegBox');
      const regNumEl = document.getElementById('wsRevCardRegNum');
      if (regBox && regNumEl) {
        if (rev.registration_number) {
          regBox.style.display = 'block';
          regNumEl.innerText = rev.registration_number;
        } else {
          regBox.style.display = 'none';
        }
      }

      // Prepopulate form values for potential revisions
      if (assessmentInput) assessmentInput.value = rev.clinical_assessment || '';
      if (referralInput) referralInput.value = rev.referral_status || 'Hospital Follow-Up (6 Months)';
      if (instructionsInput) instructionsInput.value = rev.followup_instructions || '';
      if (dateInput && patient.followup && patient.followup.planned_date) {
        dateInput.value = patient.followup.planned_date;
      }
    } else {
      if (recCard) recCard.style.display = 'none';
      if (reviewForm) reviewForm.style.display = 'block';

      const draft = this.reviewDrafts[patient.id];
      if (draft) {
        if (assessmentInput) assessmentInput.value = draft.assessment || '';
        if (referralInput) referralInput.value = draft.referral || 'Hospital Follow-Up (6 Months)';
        if (instructionsInput) instructionsInput.value = draft.instructions || '';
        if (dateInput) dateInput.value = draft.followupDate || '2027-04-01';
        if (notesInput) notesInput.value = draft.notes || '';
      } else {
        if (assessmentInput) assessmentInput.value = '';
        if (referralInput) referralInput.value = 'Hospital Follow-Up (6 Months)';
        if (instructionsInput) instructionsInput.value = '';
        if (dateInput) dateInput.value = '2027-04-01';
        if (notesInput) notesInput.value = '';
      }
    }
  }

  closeSpecialistReviewWorkspace() {
    this.currentReviewPatientId = null;
    const queueView = document.getElementById('reviewsQueueView');
    const wsView = document.getElementById('reviewWorkspaceView');
    if (queueView) queueView.style.display = 'block';
    if (wsView) wsView.style.display = 'none';
    this.renderSpecialistReviewQueue();
  }

  handleSaveDraftReview() {
    if (!this.currentReviewPatientId) return;
    const patientId = this.currentReviewPatientId;
    const assessment = document.getElementById('wsReviewAssessment').value.trim();
    const referral = document.getElementById('wsReviewReferral').value;
    const instructions = document.getElementById('wsReviewInstructions').value.trim();
    const followupDate = document.getElementById('wsReviewFollowupDate').value;
    const notes = document.getElementById('wsReviewNotes').value.trim();

    this.reviewDrafts[patientId] = {
      assessment,
      referral,
      instructions,
      followupDate,
      notes,
      savedAt: new Date().toISOString()
    };

    this.updateMetricsUI();
    this.showToast(`Draft review saved for patient ${patientId}. Marked as In Review.`);
    this.openSpecialistReviewWorkspace(patientId);
  }

  async handleSubmitReviewWorkspace(e) {
    e.preventDefault();
    if (!this.currentReviewPatientId) return;
    const patientId = this.currentReviewPatientId;

    if (!this.currentUserProfile.clinicalAuthoring) {
      alert('Only the Ophthalmologist / Specialist role can submit clinical assessments. Switch to Specialist Demo Role to proceed.');
      return;
    }

    const assessment = document.getElementById('wsReviewAssessment').value.trim();
    const referral = document.getElementById('wsReviewReferral').value;
    const followupDate = document.getElementById('wsReviewFollowupDate').value;
    const instructions = document.getElementById('wsReviewInstructions').value.trim();
    const notes = document.getElementById('wsReviewNotes').value.trim();

    const payload = {
      clinician_name: this.currentUserProfile.name,
      clinician_title: this.currentUserProfile.title || 'Dr.',
      clinician_specialty: this.currentUserProfile.specialty || 'Ophthalmology',
      clinician_facility: this.currentUserProfile.facility || 'District Eye Hospital',
      registration_number: this.currentUserProfile.regNumber || '',
      clinical_assessment: assessment,
      referral_status: referral,
      next_followup_date: followupDate,
      followup_instructions: instructions,
      notes: notes || 'Clinical assessment entered manually by qualified healthcare professional.'
    };

    try {
      const res = await fetch(`/api/patients/${patientId}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || 'Review save failed');
      }

      delete this.reviewDrafts[patientId];
      this.showToast(`Specialist review recorded! Operational follow-up task created.`);
      
      await this.fetchPatients();
      await this.fetchGapRadar();

      // Show success banner
      const successBanner = document.getElementById('wsReviewSuccessBanner');
      if (successBanner) {
        successBanner.style.display = 'block';
      }

      this.openSpecialistReviewWorkspace(patientId);
    } catch (err) {
      alert('Error submitting specialist review: ' + err.message);
    }
  }

  renderFullGapRadar(gapItems = []) {
    const grid = document.getElementById('fullGapRadarGrid');
    const badge = document.getElementById('gapCountBadge');
    if (!grid) return;

    if (badge) badge.innerText = `${gapItems.length} patients requiring workflow attention`;

    if (!gapItems.length) {
      grid.innerHTML = `<div class="p-4 text-muted">All active patient care loops are operating without delay.</div>`;
      return;
    }

    grid.innerHTML = gapItems.map(item => `
      <div class="bottleneck-card">
        <div class="d-flex justify-content-between align-items-center mb-1">
          <strong>${item.patient_name} (${item.patient_id})</strong>
          <span class="stage-badge ${item.urgency === 'High' ? 'badge-uncontacted' : 'badge-review'}">${item.urgency} Priority</span>
        </div>
        <div class="font-size-12 text-primary font-weight-bold mb-1">${item.gap_type}</div>
        <div class="font-size-12 text-muted mb-2">${item.description}</div>
        <div class="d-flex justify-content-between align-items-center">
          <span class="font-size-11 text-muted">Owner: <strong>${item.assigned_owner}</strong></span>
          <button class="btn-primary btn-sm" onclick="app.openPatientDetail('${item.patient_id}')">Resolve Gap &rarr;</button>
        </div>
      </div>
    `).join('');
  }

  /* =========================================================================
     FOLLOW-UPS PAGE
     ========================================================================= */
  async renderFollowupsWorklist(category = 'due_today') {
    const container = document.getElementById('followupCardsContainer');
    if (!container) return;

    try {
      const res = await fetch('/api/followups');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      this.setElText('count-fu-today', data.counts.due_today || 0);
      this.setElText('count-fu-upcoming', data.counts.upcoming || 0);
      this.setElText('count-fu-uncontacted', data.counts.unable_to_contact || 0);
      this.setElText('count-fu-completed', data.counts.completed || 0);

      const items = data[category] || [];
      if (!items.length) {
        container.innerHTML = `<div class="p-4 text-muted">No follow-up cases found in this category.</div>`;
        return;
      }

      container.innerHTML = items.map(p => `
        <div class="followup-card">
          <div>
            <div class="followup-card-header">
              <div>
                <strong>${p.name}</strong> <span class="text-muted">(${p.id})</span><br/>
                <span class="text-muted font-size-12">${p.age}y ${p.sex} &bull; ${p.facility}</span>
              </div>
              <span class="stage-badge ${p.status === 'Unable to Contact' ? 'badge-uncontacted' : (p.status === 'Completed' ? 'badge-completed' : 'badge-followup')}">${p.status}</span>
            </div>

            <div class="card-details-grid">
              <div class="card-detail-item">
                <span class="card-detail-label">Planned Date</span>
                <span class="card-detail-val">${p.planned_date}</span>
              </div>
              <div class="card-detail-item">
                <span class="card-detail-label">Disposition</span>
                <span class="card-detail-val">${p.referral_status}</span>
              </div>
            </div>

            <div class="font-size-12 text-muted mt-2">
              <strong>Notes:</strong> ${p.notes || 'Routine follow-up coordination.'}
            </div>
          </div>

          <div class="followup-actions-row">
            <button class="btn-primary btn-sm flex-1" onclick="app.openPatientDetail('${p.id}', 'followup')">Manage Follow-Up</button>
            <button class="btn-outline btn-sm" onclick="app.showBilingualReminderModal('${p.id}')">💬 Reminder</button>
          </div>
        </div>
      `).join('');
    } catch (err) {
      container.innerHTML = `<div class="p-4 text-danger">Failed to load follow-ups: ${err.message}</div>`;
    }
  }

  /* =========================================================================
     DOCUMENTS HUB & RECONCILIATION
     ========================================================================= */
  renderDocumentsHub(filterDocType = 'all') {
    const grid = document.getElementById('documentCardsGrid');
    if (!grid) return;

    const docs = [];
    this.patients.forEach(p => {
      (p.documents || []).forEach(d => {
        docs.push({ ...d, patient_id: p.id, patient_name: p.name, facility: p.facility });
      });
    });

    this.allDocuments = docs;
    let filtered = docs;
    if (filterDocType !== 'all') {
      filtered = docs.filter(d => d.doc_type === filterDocType);
    }

    if (!filtered.length) {
      grid.innerHTML = `<div class="p-4 text-muted">No documents found matching category '${filterDocType}'.</div>`;
      return;
    }

    grid.innerHTML = filtered.map(d => `
      <div class="home-action-card" style="cursor: default; min-height: 140px;">
        <div class="d-flex justify-content-between align-items-start mb-2">
          <div>
            <h3 class="card-title" style="font-size: 15px;">${d.title}</h3>
            <span class="font-size-12 text-muted">Patient: <strong>${d.patient_name}</strong> (${d.patient_id})</span>
          </div>
          <span class="doc-badge">${d.doc_type}</span>
        </div>
        <div class="d-flex justify-content-between align-items-center mt-2">
          <span class="stage-badge ${d.review_status.includes('Reviewed') ? 'badge-completed' : 'badge-review'}">${d.review_status}</span>
          <button class="btn-outline btn-sm" onclick="app.openPatientDetail('${d.patient_id}', 'documents')">View &rarr;</button>
        </div>
      </div>
    `).join('');
  }

  async showReconciliationModal() {
    try {
      const res = await fetch('/api/reconciliation');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();

      const container = document.getElementById('reconciliationExceptionsList');
      if (container) {
        if (!data.exceptions.length) {
          container.innerHTML = `<div class="p-3 text-emerald font-weight-bold">✓ Zero reconciliation exceptions. All mobile camp reports are linked.</div>`;
        } else {
          container.innerHTML = data.exceptions.map(ex => `
            <div class="bottleneck-card mb-2">
              <div class="d-flex justify-content-between align-items-center mb-1">
                <strong>${ex.patient_name} (${ex.patient_id})</strong>
                <span class="stage-badge badge-pending-screening">Record Pending</span>
              </div>
              <div class="font-size-12 text-muted mb-2">${ex.exception_reason}</div>
              <button class="btn-primary btn-sm" onclick="app.resolveReconciliationException('${ex.patient_id}')">
                ✓ Reconcile & Attach Report
              </button>
            </div>
          `).join('');
        }
      }
      this.openModal('reconciliationModal');
    } catch (err) {
      alert('Failed to load reconciliation items: ' + err.message);
    }
  }

  async resolveReconciliationException(patientId) {
    try {
      const res = await fetch(`/api/reconciliation/${patientId}/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: `Reconciled Fundus Screening Report - ${patientId}`,
          source: 'Reconciled Mobile Camp EMR'
        })
      });
      if (res.ok) {
        this.showToast(`Record for ${patientId} successfully reconciled! Report attached.`);
        this.closeModal('reconciliationModal');
        await this.fetchPatients();
        await this.fetchGapRadar();
        this.renderDocumentsHub('all');
      }
    } catch (err) {
      alert('Error reconciling record: ' + err.message);
    }
  }

  /* =========================================================================
     CONTINUITY INSIGHTS (ANALYTICS)
     ========================================================================= */
  renderAnalyticsFunnel(funnel = []) {
    const container = document.getElementById('funnelContainer');
    if (!container) return;

    container.innerHTML = funnel.map(step => `
      <div class="funnel-stage-row">
        <div class="funnel-meta-row">
          <span>${step.stage}</span>
          <span><strong>${step.count}</strong> (${step.pct}%)</span>
        </div>
        <div class="funnel-bar-bg">
          <div class="funnel-bar-fill" style="width: ${step.pct}%"></div>
        </div>
      </div>
    `).join('');
  }

  renderBottlenecks(bottlenecks = []) {
    const container = document.getElementById('bottlenecksList');
    if (!container) return;

    container.innerHTML = bottlenecks.map(b => `
      <div class="bottleneck-card">
        <div class="d-flex justify-content-between align-items-center mb-1">
          <strong>${b.category}</strong>
          <span class="stage-badge ${b.status === 'Critical' ? 'badge-uncontacted' : 'badge-review'}">${b.count} cases</span>
        </div>
        <div class="font-size-12 text-muted mb-2">${b.impact}</div>
        <div class="d-flex justify-content-between font-size-11 text-muted">
          <span>Owner: <strong>${b.primary_owner}</strong></span>
          <span>Avg Delay: <strong>${b.median_days_waiting}d</strong></span>
        </div>
      </div>
    `).join('');
  }

  renderTurnaround(turnaround = {}) {
    const grid = document.getElementById('turnaroundGrid');
    if (!grid) return;

    grid.innerHTML = `
      <div class="turnaround-kpi-box">
        <div class="turnaround-kpi-val">${turnaround.avg_days_registration_to_screening || '5.4'}d</div>
        <div class="turnaround-kpi-lbl">Registration to Screening</div>
      </div>
      <div class="turnaround-kpi-box">
        <div class="turnaround-kpi-val">${turnaround.avg_days_screening_to_report || '1.8'}d</div>
        <div class="turnaround-kpi-lbl">Screening to Report</div>
      </div>
      <div class="turnaround-kpi-box">
        <div class="turnaround-kpi-val">${turnaround.avg_days_report_to_specialist_review || '3.2'}d</div>
        <div class="turnaround-kpi-lbl">Report to MD Review</div>
      </div>
      <div class="turnaround-kpi-box">
        <div class="turnaround-kpi-val">${turnaround.care_loop_resolution_rate_pct || '78'}%</div>
        <div class="turnaround-kpi-lbl">Loop Completion Rate</div>
      </div>
    `;
  }

  renderTeamWorkload(ownership = {}) {
    const list = document.getElementById('teamWorkloadList');
    if (!list) return;

    list.innerHTML = Object.entries(ownership).map(([role, count]) => `
      <div class="workload-item">
        <span>${role}</span>
        <span class="stage-badge badge-screening">${count} tasks</span>
      </div>
    `).join('');
  }

  /* =========================================================================
     FIELD OUTREACH MODE
     ========================================================================= */
  setConnectivityMode(isOffline) {
    this.isOfflineMode = isOffline;
    const onlineBtn = document.getElementById('connOnlineBtn');
    const offlineBtn = document.getElementById('connOfflineBtn');
    const banner = document.getElementById('outreachFieldBanner');
    const title = document.getElementById('bannerStatusTitle');
    const desc = document.getElementById('bannerStatusDesc');
    const syncBtn = document.getElementById('syncOfflineQueueBtn');

    if (isOffline) {
      offlineBtn.classList.add('active-conn');
      onlineBtn.classList.remove('active-conn');
      banner.style.background = 'var(--red-subtle)';
      title.innerText = 'Offline Mode Active';
      desc.innerText = 'Visit logs stored locally in queue.';
      if (syncBtn) syncBtn.disabled = this.offlineQueue.length === 0;
    } else {
      onlineBtn.classList.add('active-conn');
      offlineBtn.classList.remove('active-conn');
      banner.style.background = 'var(--primary-subtle)';
      title.innerText = 'Network Connected';
      desc.innerText = 'Field visit logs sync automatically with central server.';
      if (syncBtn) syncBtn.disabled = this.offlineQueue.length === 0;
    }
  }

  renderOutreachFieldTasks() {
    const grid = document.getElementById('fieldTasksGrid');
    if (!grid) return;

    const fieldList = this.patients.filter(p => p.followup.status === 'Unable to Contact' || p.followup.status === 'Pending').slice(0, 6);

    grid.innerHTML = fieldList.map(p => `
      <div class="home-action-card" style="cursor: default;">
        <div>
          <div class="d-flex justify-content-between align-items-start mb-2">
            <div>
              <strong>${p.name}</strong> <span class="text-muted">(${p.id})</span><br/>
              <span class="text-muted font-size-12">Contact: ${p.contact}</span>
            </div>
            <span class="stage-badge ${p.followup.status === 'Unable to Contact' ? 'badge-uncontacted' : 'badge-followup'}">${p.followup.status}</span>
          </div>
          <div class="font-size-12 text-muted mb-3">
            <strong>Next Action:</strong> ${p.workflow_status.next_workflow_action}
          </div>
        </div>

        <div class="d-flex gap-2">
          <button class="btn-primary btn-sm flex-1" onclick="app.quickLogFieldContact('${p.id}')">Log Field Visit</button>
          <button class="btn-outline btn-sm" onclick="app.showBilingualReminderModal('${p.id}')">SMS</button>
        </div>
      </div>
    `).join('');
  }

  quickLogFieldContact(patientId) {
    if (this.isOfflineMode) {
      this.offlineQueue.push({ patientId, timestamp: new Date().toISOString() });
      document.getElementById('offlineQueueCount').innerText = this.offlineQueue.length;
      document.getElementById('syncOfflineQueueBtn').disabled = false;
      this.showToast(`[OFFLINE SAVED] Field visit logged locally for ${patientId}.`);
    } else {
      this.openPatientDetail(patientId, 'followup');
    }
  }

  syncOfflineQueue() {
    if (!this.offlineQueue.length) return;
    this.showToast(`Synchronized ${this.offlineQueue.length} offline field logs with central database.`);
    this.offlineQueue = [];
    document.getElementById('offlineQueueCount').innerText = '0';
    document.getElementById('syncOfflineQueueBtn').disabled = true;
  }

  /* =========================================================================
     PATIENT PROFILE & DETAIL VIEW (PROGRESSIVE DISCLOSURE)
     ========================================================================= */
  async openPatientDetail(patientId, targetTab = 'overview') {
    this.currentPatientId = patientId;
    const patient = this.patients.find(p => p.id === patientId);
    if (!patient) return;

    this.navigateToScreen('screen-patient-detail');

    const initials = patient.name.split(' ').map(n => n[0]).join('').substring(0, 2);
    document.getElementById('detailAvatar').innerText = initials;
    document.getElementById('detailPatientName').innerText = patient.name;
    document.getElementById('detailPatientId').innerText = patient.id;
    
    const stageBadge = document.getElementById('detailStageBadge');
    stageBadge.innerText = patient.workflow_status.overall_stage;
    stageBadge.className = `stage-badge ${this.getStageBadgeClass(patient.workflow_status.overall_stage, patient.workflow_status.care_loop_completed)}`;

    document.getElementById('detailDemographics').innerText = `${patient.age} yrs • ${patient.sex} • ${patient.facility} • ${patient.contact}`;

    // Current Step, Next Action, Owner
    document.getElementById('detailCurrentStep').innerText = patient.workflow_status.overall_stage;
    document.getElementById('detailNextAction').innerText = patient.workflow_status.next_workflow_action;
    document.getElementById('detailAssignedTo').innerText = patient.workflow_status.assigned_to || 'Care Coordinator';

    // Embedded Stepper
    this.renderDetailStepper(patient);

    // Tab Contents
    this.renderDetailSummary(patient);
    this.renderDetailSpecialistWorkspace(patient);
    this.renderDetailDocuments(patient);
    this.renderDetailFollowup(patient);
    this.renderDetailTimeline(patient);

    this.switchDetailTab(targetTab);
  }

  switchDetailTab(tabName) {
    document.querySelectorAll('.detail-tab').forEach(t => {
      t.classList.toggle('active', t.dataset.tab === tabName);
    });

    document.querySelectorAll('.detail-tab-content').forEach(c => {
      c.classList.toggle('active-tab', c.id === `tab-${tabName}`);
    });
  }

  renderDetailStepper(patient) {
    const container = document.getElementById('patientDetailStepperBox');
    if (!container) return;

    const milestones = [
      { num: 1, title: 'Registered' },
      { num: 2, title: 'Screening' },
      { num: 3, title: 'Report' },
      { num: 4, title: 'Specialist Review' },
      { num: 5, title: 'Follow-Up' },
      { num: 6, title: 'Loop Closed' }
    ];

    container.innerHTML = `
      <div class="stepper-track-wrap">
        <div class="stepper-track" style="min-width: 600px;">
          ${milestones.map(m => {
            const isDone = patient.workflow_status.care_loop_completed || m.num <= 3;
            const isCurrent = !patient.workflow_status.care_loop_completed && m.num === 4;
            let cls = isDone ? 'completed' : (isCurrent ? 'in-progress' : 'pending');
            return `
              <div class="step-node ${cls}">
                <div class="step-connector"></div>
                <div class="step-circle">${isDone ? '✓' : (isCurrent ? '●' : m.num)}</div>
                <div class="step-label">${m.title}</div>
              </div>
            `;
          }).join('')}
        </div>
      </div>
    `;
  }

  renderDetailSummary(patient) {
    const comp = patient.completeness || { score_percentage: 80, missing_items: [], checks: {} };
    document.getElementById('summaryScoreNum').innerText = `${comp.score_percentage}%`;

    const checklistContainer = document.getElementById('summaryChecklistItems');
    if (checklistContainer) {
      const checkEntries = [
        { label: 'Primary contact telephone documented', ok: comp.checks ? comp.checks.contact_number : true },
        { label: 'Baseline diabetes duration recorded', ok: comp.checks ? comp.checks.baseline_diabetes_duration : true },
        { label: 'Baseline HbA1c lab result documented', ok: comp.checks ? comp.checks.baseline_hba1c : true },
        { label: 'Retinal screening report uploaded', ok: comp.checks ? comp.checks.screening_report_uploaded : true },
        { label: 'Specialist ophthalmologist review recorded', ok: comp.checks ? comp.checks.specialist_review_recorded : false },
        { label: 'Follow-up appointment scheduled', ok: comp.checks ? comp.checks.followup_plan_defined : true }
      ];

      checklistContainer.innerHTML = checkEntries.map(entry => `
        <div class="checklist-item ${entry.ok ? 'item-done' : 'item-missing'}" style="padding: 8px 12px; font-size: 12.5px; display: flex; justify-content: space-between; border-bottom: 1px solid var(--line);">
          <span>${entry.label}</span>
          <span class="font-weight-bold ${entry.ok ? 'text-emerald' : 'text-red'}">${entry.ok ? '✓ Complete' : '⚠️ Missing'}</span>
        </div>
      `).join('');
    }
  }

  renderDetailSpecialistWorkspace(patient) {
    const reportDoc = patient.documents.find(d => d.doc_type === 'Retinal Screening Report');
    const docTitle = document.getElementById('reviewDocTitle');
    if (docTitle) docTitle.innerText = reportDoc ? reportDoc.title : 'No Report Uploaded';

    const recordedCard = document.getElementById('reviewRecordedCard');
    const reviewForm = document.getElementById('specialistReviewForm');
    const roleNotice = document.getElementById('specialistRoleNotice');
    const submitBtn = document.getElementById('submitReviewBtn');
    const isSpecialist = this.currentUserProfile.clinicalAuthoring;
    const rev = patient.specialist_review;

    // Role banner handling
    if (roleNotice) {
      roleNotice.style.display = isSpecialist ? 'none' : 'flex';
    }

    // Input fields state based on active demo profile
    const clinicianInput = document.getElementById('reviewClinicianName');
    const assessmentInput = document.getElementById('reviewAssessment');
    const referralInput = document.getElementById('reviewReferral');
    const dateInput = document.getElementById('reviewFollowupDate');
    const instructionsInput = document.getElementById('reviewInstructions');

    if (clinicianInput) clinicianInput.readOnly = !isSpecialist;
    if (assessmentInput) assessmentInput.readOnly = !isSpecialist;
    if (referralInput) referralInput.disabled = !isSpecialist;
    if (dateInput) dateInput.disabled = !isSpecialist;
    if (instructionsInput) instructionsInput.readOnly = !isSpecialist;

    if (submitBtn) {
      submitBtn.disabled = !isSpecialist;
      submitBtn.innerText = isSpecialist ? '✓ Submit Review & Generate Task' : 'Restricted to Specialist Role';
    }

    // Check if review has already been completed
    if (rev && rev.completed) {
      if (recordedCard) recordedCard.style.display = 'block';
      if (reviewForm) reviewForm.style.display = 'none';

      // Populate recorded review display
      this.setElText('revCardRecordedTime', rev.review_timestamp ? `Recorded: ${rev.review_timestamp}` : 'Recorded');
      this.setElText('revCardClinicianName', rev.clinician_name || 'Attending Ophthalmologist');
      this.setElText('revCardSpecialty', rev.clinician_specialty || 'Ophthalmology');
      this.setElText('revCardFacility', rev.clinician_facility || 'District Eye Hospital');
      this.setElText('revCardAssessment', rev.clinical_assessment || '');
      this.setElText('revCardDisposition', rev.referral_status || 'Hospital Follow-Up (6 Months)');
      this.setElText('revCardDueDate', patient.followup && patient.followup.planned_date ? `Due: ${patient.followup.planned_date}` : 'Per Clinician Plan');
      this.setElText('revCardInstructions', rev.followup_instructions || 'Routine care monitoring.');
      this.setElText('provClinicianLabel', rev.clinician_name || 'Evaluating Clinician');

      const regBox = document.getElementById('revCardRegBox');
      const regNumEl = document.getElementById('revCardRegNum');
      if (regBox && regNumEl) {
        if (rev.registration_number) {
          regBox.style.display = 'block';
          regNumEl.innerText = rev.registration_number;
        } else {
          regBox.style.display = 'none';
        }
      }

      // Prepopulate form values for potential revisions
      if (clinicianInput) clinicianInput.value = rev.clinician_name || '';
      if (assessmentInput) assessmentInput.value = rev.clinical_assessment || '';
      if (instructionsInput) instructionsInput.value = rev.followup_instructions || '';
      if (referralInput) referralInput.value = rev.referral_status || 'Hospital Follow-Up (6 Months)';
      if (dateInput && patient.followup && patient.followup.planned_date) {
        dateInput.value = patient.followup.planned_date;
      }
    } else {
      if (recordedCard) recordedCard.style.display = 'none';
      if (reviewForm) reviewForm.style.display = 'block';

      if (clinicianInput) clinicianInput.value = isSpecialist ? this.currentUserProfile.name : 'Dr. Suresh Chandran, MS (Ophthalmology)';
      if (assessmentInput) assessmentInput.value = '';
      if (instructionsInput) instructionsInput.value = '';
      if (referralInput) referralInput.value = 'Hospital Follow-Up (6 Months)';
    }
  }

  async handleSubmitSpecialistReview(e) {
    e.preventDefault();
    if (!this.currentPatientId) return;

    if (!this.currentUserProfile.clinicalAuthoring) {
      alert('Only the Ophthalmologist / Specialist role can submit clinical assessments. Switch to Specialist Demo Role to proceed.');
      return;
    }

    const clinicianName = document.getElementById('reviewClinicianName').value.trim() || this.currentUserProfile.name;
    const assessment = document.getElementById('reviewAssessment').value.trim();
    const referral = document.getElementById('reviewReferral').value;
    const followupDate = document.getElementById('reviewFollowupDate').value;
    const instructions = document.getElementById('reviewInstructions').value.trim();

    const payload = {
      clinician_name: clinicianName,
      clinician_title: this.currentUserProfile.title || 'Dr.',
      clinician_specialty: this.currentUserProfile.specialty || 'Ophthalmology',
      clinician_facility: this.currentUserProfile.facility || 'District Eye Hospital',
      registration_number: this.currentUserProfile.regNumber || '',
      clinical_assessment: assessment,
      referral_status: referral,
      next_followup_date: followupDate,
      followup_instructions: instructions,
      notes: 'Clinical assessment entered manually by qualified healthcare professional.'
    };

    try {
      const res = await fetch(`/api/patients/${this.currentPatientId}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || 'Save failed');
      }

      this.showToast(`Specialist review saved for ${clinicianName}! Coordinator follow-up task created.`);
      await this.fetchPatients();
      await this.fetchGapRadar();
      this.openPatientDetail(this.currentPatientId, 'review');
    } catch (err) {
      alert('Error saving specialist review: ' + err.message);
    }
  }

  renderDetailDocuments(patient) {
    const container = document.getElementById('detailDocumentsGrid');
    if (!container) return;

    if (!patient.documents || !patient.documents.length) {
      container.innerHTML = `<div class="p-3 text-muted">No documents uploaded. Click '+ Attach Document' above.</div>`;
      return;
    }

    container.innerHTML = patient.documents.map(d => `
      <div class="home-action-card mb-2" style="cursor: default; min-height: 120px;">
        <div class="d-flex justify-content-between align-items-start">
          <div>
            <strong>${d.title}</strong><br/>
            <span class="font-size-12 text-muted">Date: ${d.upload_date} &bull; Source: ${d.source}</span>
          </div>
          <span class="stage-badge ${d.review_status.includes('Reviewed') ? 'badge-completed' : 'badge-review'}">${d.review_status}</span>
        </div>
      </div>
    `).join('');
  }

  renderDetailFollowup(patient) {
    const fu = patient.followup || {};
    document.getElementById('detailFollowupStatusSelect').value = fu.status || 'Pending';
    document.getElementById('detailFollowupTargetDate').value = fu.planned_date || '';
    document.getElementById('detailFollowupStaff').value = fu.responsible_staff || 'Care Coordinator';
    document.getElementById('detailFollowupNotes').value = fu.notes || '';

    const list = document.getElementById('detailContactAttemptsList');
    if (list) {
      if (!fu.contact_attempts || !fu.contact_attempts.length) {
        list.innerHTML = `<div class="p-2 text-muted font-size-12">No contact attempts logged yet. Click '+ Log Contact' above.</div>`;
      } else {
        list.innerHTML = fu.contact_attempts.map(c => `
          <div class="bottleneck-card mb-2">
            <div class="d-flex justify-content-between font-weight-bold font-size-12">
              <span>${c.method} &bull; ${c.date}</span>
              <span class="text-primary">${c.staff}</span>
            </div>
            <div class="font-size-12 mt-1">${c.result}</div>
          </div>
        `).join('');
      }
    }
  }

  async handleUpdateFollowup(closeLoop = false) {
    if (!this.currentPatientId) return;

    const payload = {
      status: closeLoop ? 'Completed' : document.getElementById('detailFollowupStatusSelect').value,
      planned_date: document.getElementById('detailFollowupTargetDate').value,
      responsible_staff: document.getElementById('detailFollowupStaff').value,
      notes: document.getElementById('detailFollowupNotes').value,
      close_care_loop: closeLoop
    };

    try {
      const res = await fetch(`/api/patients/${this.currentPatientId}/followup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        this.showToast(closeLoop ? 'Care loop marked as COMPLETED for 2026 cycle!' : 'Follow-up status updated.');
        await this.fetchPatients();
        await this.fetchGapRadar();
        this.openPatientDetail(this.currentPatientId, 'followup');
      }
    } catch (err) {
      alert('Error updating follow-up: ' + err.message);
    }
  }

  renderDetailTimeline(patient) {
    const trail = document.getElementById('detailTimelineTrail');
    if (!trail) return;

    if (!patient.timeline || !patient.timeline.length) {
      trail.innerHTML = `<div class="p-3 text-muted">No activity events recorded.</div>`;
      return;
    }

    trail.innerHTML = patient.timeline.slice().reverse().map(evt => `
      <div class="bottleneck-card mb-2">
        <div class="d-flex justify-content-between align-items-center mb-1">
          <strong>${evt.stage}</strong>
          <span class="text-muted font-size-11">${evt.timestamp}</span>
        </div>
        <div class="font-size-12 text-muted mb-1">${evt.note || ''}</div>
        <div class="font-size-11 text-muted">
          <span>Actor: <strong>${evt.actor}</strong> &bull; Source: <strong>${evt.source}</strong></span>
        </div>
      </div>
    `).join('');
  }

  /* =========================================================================
     MODAL DIALOG OPERATIONS & CREATION
     ========================================================================= */
  async handleRegisterPatient(e) {
    e.preventDefault();
    const payload = {
      name: document.getElementById('regName').value.trim(),
      age: parseInt(document.getElementById('regAge').value, 10),
      sex: document.getElementById('regSex').value,
      contact: document.getElementById('regContact').value.trim(),
      facility: document.getElementById('regFacility').value.trim(),
      diabetes_type: document.getElementById('regType').value,
      duration: document.getElementById('regDuration').value.trim(),
      hba1c: document.getElementById('regHbA1c').value.trim(),
      registered_by: this.currentRole.name
    };

    try {
      const res = await fetch('/api/patients', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const data = await res.json();
        this.showToast(`Patient ${payload.name} registered with ID ${data.patient.id}!`);
        this.closeModal('registerModal');
        document.getElementById('registerPatientForm').reset();
        await this.fetchPatients();
        await this.fetchAnalytics();
        this.openPatientDetail(data.patient.id);
      }
    } catch (err) {
      alert('Error registering patient: ' + err.message);
    }
  }

  async handleUploadDocument(e) {
    e.preventDefault();
    if (!this.currentPatientId) return;

    const title = document.getElementById('docTitle').value.trim();
    const docType = document.getElementById('docType').value;
    const source = document.getElementById('docSource').value.trim();

    try {
      const res = await fetch(`/api/patients/${this.currentPatientId}/documents`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, doc_type: docType, source })
      });
      if (res.ok) {
        this.showToast('Document attached successfully!');
        this.closeModal('uploadDocModal');
        document.getElementById('uploadDocForm').reset();
        await this.fetchPatients();
        this.openPatientDetail(this.currentPatientId, 'documents');
      }
    } catch (err) {
      alert('Error uploading document: ' + err.message);
    }
  }

  async handleAddTimelineEvent(e) {
    e.preventDefault();
    if (!this.currentPatientId) return;

    const payload = {
      stage: document.getElementById('eventStage').value.trim(),
      actor: this.currentRole.name,
      source: 'Coordination Desk',
      note: document.getElementById('eventNote').value.trim()
    };

    try {
      const res = await fetch(`/api/patients/${this.currentPatientId}/timeline`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        this.closeModal('addEventModal');
        document.getElementById('addEventForm').reset();
        await this.fetchPatients();
        this.openPatientDetail(this.currentPatientId, 'activity');
      }
    } catch (err) {
      alert('Error saving event: ' + err.message);
    }
  }

  async handleLogContactAttempt(e) {
    e.preventDefault();
    if (!this.currentPatientId) return;

    const attempt = {
      method: document.getElementById('contactMethod').value,
      staff: document.getElementById('contactStaff').value.trim() || this.currentRole.name,
      result: document.getElementById('contactOutcome').value,
      notes: document.getElementById('contactNotes').value.trim()
    };

    try {
      const res = await fetch(`/api/patients/${this.currentPatientId}/followup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ contact_attempt: attempt })
      });
      if (res.ok) {
        this.showToast('Contact attempt logged.');
        this.closeModal('contactAttemptModal');
        document.getElementById('contactAttemptForm').reset();
        await this.fetchPatients();
        this.openPatientDetail(this.currentPatientId, 'followup');
      }
    } catch (err) {
      alert('Error logging contact attempt: ' + err.message);
    }
  }

  /* =========================================================================
     CARE PASSPORT MODAL
     ========================================================================= */
  showCarePassport(patientId) {
    const p = this.patients.find(pt => pt.id === (patientId || this.currentPatientId));
    if (!p) return;

    const passportBody = document.getElementById('passportBody');
    if (!passportBody) return;

    passportBody.innerHTML = `
      <div style="background: #0f172a; color: #fff; padding: 20px; border-radius: var(--radius-lg);">
        <div style="display: flex; justify-content: space-between; border-bottom: 1px solid #334155; padding-bottom: 10px; margin-bottom: 12px;">
          <div>
            <h2 style="font-size: 18px; font-weight: 800;">${p.name}</h2>
            <div style="font-size: 11px; opacity: 0.8;">ID: ${p.id} &bull; ${p.age}y ${p.sex} &bull; ${p.diabetes_profile.type}</div>
          </div>
          <div style="background: #fff; color: #000; padding: 4px 8px; border-radius: var(--radius-sm); font-size: 9px; font-weight: 800; text-align: center;">
            DEMO QR<br/>${p.id}
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 12px;">
          <div><strong>Screening:</strong> ${p.workflow_status.screening_workflow === 'Completed' ? '✓ Completed' : 'Pending'}</div>
          <div><strong>Specialist Review:</strong> ${p.specialist_review.completed ? '✓ Recorded' : 'Pending'}</div>
          <div><strong>Next Checkup:</strong> ${p.followup.planned_date || 'Per Specialist Plan'}</div>
          <div><strong>Facility:</strong> ${p.facility}</div>
        </div>
      </div>
    `;

    this.openModal('carePassportModal');
  }

  /* =========================================================================
     BILINGUAL REMINDERS
     ========================================================================= */
  showBilingualReminderModal(patientId) {
    if (patientId) this.currentPatientId = patientId;
    this.updateReminderPreviewText();
    this.openModal('bilingualReminderModal');
  }

  updateReminderPreviewText() {
    const p = this.patients.find(pt => pt.id === this.currentPatientId) || this.patients[0] || {};
    const name = p.name || 'Patient';
    const dateStr = (p.followup && p.followup.planned_date) || 'your scheduled date';
    const facility = p.facility || 'your local clinic';
    const remType = document.getElementById('remindTypeSelect').value;

    let enText = `Dear ${name}, this is a reminder from your care team at ${facility} regarding your diabetic eye follow-up on ${dateStr}.`;
    let hiText = `प्रिय ${name}, ${facility} में आपकी देखभाल टीम द्वारा आपकी डायबिटिक नेत्र अनुवर्ती जांच (${dateStr}) के संबंध में यह अनुस्मारक है।`;

    document.getElementById('reminderTextEn').innerText = enText;
    document.getElementById('reminderTextHi').innerText = hiText;
  }

  async handleSendSimulatedReminder() {
    if (!this.currentPatientId) return;
    const remType = document.getElementById('remindTypeSelect').value;
    const textEn = document.getElementById('reminderTextEn').innerText;
    const textHi = document.getElementById('reminderTextHi').innerText;

    try {
      const res = await fetch(`/api/patients/${this.currentPatientId}/reminders`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: remType, text: textEn, text_hi: textHi, language: 'en' })
      });
      if (res.ok) {
        this.showToast('Simulated reminder generated and logged to timeline.');
        this.closeModal('bilingualReminderModal');
        await this.fetchPatients();
        this.openPatientDetail(this.currentPatientId, 'activity');
      }
    } catch (err) {
      alert('Error sending reminder: ' + err.message);
    }
  }

  /* =========================================================================
     GUIDED DEMO STORY (MOHAMMAD FAROOQ RX-1003)
     ========================================================================= */
  startGuidedDemo() {
    this.navigateToScreen('screen-demo-story');
    this.goToDemoStep(1);
  }

  goToDemoStep(stepNum) {
    if (stepNum < 1 || stepNum > 6) return;
    this.currentDemoStep = stepNum;

    document.querySelectorAll('.demo-step-pill').forEach(pill => {
      const pStep = parseInt(pill.dataset.step, 10);
      pill.classList.toggle('active', pStep === stepNum);
    });

    document.getElementById('demoStepIndicator').innerText = `Step ${stepNum} of 6`;
    document.getElementById('demoPrevStepBtn').disabled = stepNum === 1;
    document.getElementById('demoNextStepBtn').innerText = stepNum === 6 ? '✓ Finish' : 'Next Step →';

    const content = document.getElementById('demoStepContent');
    if (!content) return;

    if (stepNum === 1) {
      content.innerHTML = `
        <span class="stage-badge badge-review">STEP 1: IDENTIFY WORKFLOW GAP</span>
        <h3 class="mt-2 mb-2">Unreviewed Screening Report Flagged</h3>
        <p class="font-size-14 text-muted mb-3">
          Mohammad Farooq attended a diabetic eye screening camp. His retinal scans were uploaded 4 days ago, but specialist review is pending.
        </p>
        <button class="btn-primary" onclick="app.openPatientDetail('RX-1003', 'documents')">Inspect Uploaded Report &rarr;</button>
      `;
    } else if (stepNum === 2) {
      content.innerHTML = `
        <span class="stage-badge badge-screening">STEP 2: DOCUMENT REVIEW</span>
        <h3 class="mt-2 mb-2">Ophthalmologist Inspects Fundus Scans</h3>
        <p class="font-size-14 text-muted mb-3">
          The attending ophthalmologist opens Farooq's record in the Specialist Review workspace.
        </p>
        <button class="btn-primary" onclick="app.openPatientDetail('RX-1003', 'review')">Open Review Workspace &rarr;</button>
      `;
    } else if (stepNum === 3) {
      content.innerHTML = `
        <span class="stage-badge badge-review">STEP 3: CLINICIAN INPUT</span>
        <h3 class="mt-2 mb-2">Human-in-the-Loop Clinical Assessment</h3>
        <p class="font-size-14 text-muted mb-3">
          Dr. Suresh Chandran enters his manual clinical findings and management directives.
        </p>
        <button class="btn-primary" onclick="app.executeDemoReviewSubmit()">Submit Review & Generate Task</button>
      `;
    } else if (stepNum === 4) {
      content.innerHTML = `
        <span class="stage-badge badge-followup">STEP 4: OPERATIONAL TASK</span>
        <h3 class="mt-2 mb-2">Task Created from Clinician Directive</h3>
        <p class="font-size-14 text-muted mb-3">
          RetinaX Care converts Dr. Chandran's clinical instruction into a structured follow-up action for the care coordinator.
        </p>
        <button class="btn-primary" onclick="app.openPatientDetail('RX-1003', 'followup')">View Follow-Up Plan &rarr;</button>
      `;
    } else if (stepNum === 5) {
      content.innerHTML = `
        <span class="stage-badge badge-followup">STEP 5: PATIENT ENGAGEMENT</span>
        <h3 class="mt-2 mb-2">Bilingual Reminder Sent</h3>
        <p class="font-size-14 text-muted mb-3">
          The care coordinator triggers a simulated bilingual notification to confirm Farooq's 6-month eye clinic appointment.
        </p>
        <button class="btn-primary" onclick="app.showBilingualReminderModal('RX-1003')">Open Reminder &rarr;</button>
      `;
    } else if (stepNum === 6) {
      content.innerHTML = `
        <span class="stage-badge badge-completed">STEP 6: CARE LOOP CLOSED</span>
        <h3 class="mt-2 mb-2">Follow-Up Completed</h3>
        <p class="font-size-14 text-muted mb-3">
          Farooq attends his scheduled 6-month evaluation. The coordinator closes the care loop for the 2026 cycle.
        </p>
        <button class="btn-success" onclick="app.executeDemoLoopClosure()">Mark Care Loop Completed</button>
      `;
    }
  }

  async executeDemoReviewSubmit() {
    try {
      const res = await fetch('/api/patients/RX-1003/review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          clinician_name: 'Dr. Suresh Chandran, MS (Ophthalmology)',
          clinician_title: 'Dr.',
          clinician_specialty: 'Ophthalmology',
          clinician_facility: 'District Eye Hospital',
          registration_number: 'MCI-2016-849201',
          clinical_assessment: 'Manual clinical assessment: Bilateral microvascular changes observed. No high-risk proliferative features on visual inspection.',
          followup_instructions: 'Repeat dilated fundus examination at eye clinic in 6 months. Maintain strict glycemic control.',
          referral_status: 'Hospital Follow-Up (6 Months)',
          next_followup_date: '2027-04-01',
          notes: 'Clinical assessment entered manually by qualified healthcare professional.'
        })
      });
      if (res.ok) {
        this.showToast('Specialist review submitted for Mohammad Farooq! Advancing to Step 4.');
        await this.fetchPatients();
        await this.fetchGapRadar();
        this.goToDemoStep(4);
      }
    } catch (err) {
      alert('Demo error: ' + err.message);
    }
  }

  async executeDemoLoopClosure() {
    try {
      const res = await fetch('/api/patients/RX-1003/followup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          status: 'Completed',
          responsible_staff: 'Care Coordinator',
          notes: 'Patient attended 6-month evaluation. Care loop closed for 2026 cycle.',
          close_care_loop: true
        })
      });
      if (res.ok) {
        this.showToast('Care loop for Mohammad Farooq successfully closed!');
        await this.fetchPatients();
        await this.fetchAnalytics();
        this.openPatientDetail('RX-1003', 'overview');
      }
    } catch (err) {
      alert('Demo error: ' + err.message);
    }
  }
}

let app;
document.addEventListener('DOMContentLoaded', () => {
  app = new RetinaXCareApp();
});
