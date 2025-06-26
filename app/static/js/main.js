class ModularDropdown {
    constructor(triggerId, dropdownId) {
        this.trigger = document.getElementById(triggerId);
        this.dropdown = document.getElementById(dropdownId);
        this.arrow = this.trigger.querySelector('.dropdown-icon');
        this.init();
    }

    init() {
        this.dropdown.classList.add('dropdown-animate');
        this.trigger.addEventListener('click', () => this.toggle());
        document.addEventListener('click', (e) => this.handleClickOutside(e));
    }

    toggle() {
        this.dropdown.classList.toggle('show');
        if (this.arrow) {
            this.arrow.style.transform = this.dropdown.classList.contains('show') 
                ? 'rotate(180deg)' 
                : 'rotate(0deg)';
        }
    }

    handleClickOutside(event) {
        if (!this.trigger.contains(event.target) && !this.dropdown.contains(event.target)) {
            this.dropdown.classList.remove('show');
            if (this.arrow) {
                this.arrow.style.transform = 'rotate(0deg)';
            }
        }
    }
}

class TableCollapse {
    constructor(tableId, cardId) {
        this.table = document.getElementById(tableId);
        this.card = document.getElementById(cardId);
        this.isCollapsed = localStorage.getItem('tableCollapsed') === 'true';
        this.init();
    }

    init() {
        const button = this.card.querySelector('.collapse-toggle');
        button.addEventListener('click', () => this.toggle());
        
        // INITIAL STATE
        if (this.isCollapsed) {
            this.table.classList.add('collapsed');
            button.querySelector('.material-symbols-rounded').textContent = 'expand_more';
        }
    }

    toggle() {
        this.isCollapsed = !this.isCollapsed;
        localStorage.setItem('tableCollapsed', this.isCollapsed);
        
        const button = this.card.querySelector('.collapse-toggle');
        const icon = button.querySelector('.material-symbols-rounded');
        
        if (this.isCollapsed) {
            this.table.classList.add('collapsed');
            icon.textContent = 'expand_more';
        } else {
            this.table.classList.remove('collapsed');
            icon.textContent = 'expand_less';
        }
    }
}

class SidebarManager {
    constructor() {
        this.sidebarContainer = document.querySelector('.sidebar-container');
        this.sidebarToggle = document.querySelector('.sidebar-toggle');
        this.mobileMenuBtn = document.getElementById('mobileMenuBtn');
        this.mobileCloseBtn = document.getElementById('mobileCloseBtn');
        this.isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
        this.isMobileOpen = false;
        this.body = document.body;
        this.init();
    }

    init() {
        this.setupInitialState();
        this.setupEventListeners();
    }

    setupInitialState() {
        if (window.innerWidth > 600 && this.isCollapsed) {
            this.sidebarContainer.classList.add('collapsed');
            this.body.classList.add('sidebar-collapsed');
        }
    }

    setupEventListeners() {
        // Desktop toggle
        if (this.sidebarToggle) {
            this.sidebarToggle.addEventListener('click', () => this.toggleDesktop());
        }

        // Mobile menu button
        if (this.mobileMenuBtn) {
            this.mobileMenuBtn.addEventListener('click', () => this.toggleMobile());
        }

        // Mobile close button
        if (this.mobileCloseBtn) {
            this.mobileCloseBtn.addEventListener('click', () => this.closeMobile());
        }

        // Close on overlay click (mobile only)
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 600 && this.isMobileOpen) {
                if (!this.sidebarContainer.contains(e.target) && 
                    !this.mobileMenuBtn.contains(e.target)) {
                    this.closeMobile();
                }
            }
        });

        // Handle window resize
        window.addEventListener('resize', () => {
            if (window.innerWidth > 600) {
                // Desktop mode
                this.closeMobile();
                if (this.isCollapsed) {
                    this.sidebarContainer.classList.add('collapsed');
                    this.body.classList.add('sidebar-collapsed');
                }
            } else {
                // Mobile mode
                this.sidebarContainer.classList.remove('collapsed');
                this.body.classList.remove('sidebar-collapsed');
            }
        });
    }

    toggleDesktop() {
        if (window.innerWidth > 600) {
            this.isCollapsed = !this.isCollapsed;
            localStorage.setItem('sidebarCollapsed', this.isCollapsed);
            
            this.sidebarContainer.classList.toggle('collapsed');
            this.body.classList.toggle('sidebar-collapsed');
        }
    }

    openMobile() {
        if (window.innerWidth <= 600) {
            this.isMobileOpen = true;
            this.sidebarContainer.classList.add('mobile-visible');
            this.body.style.overflow = 'hidden'; // Prevent background scrolling
        }
    }

    closeMobile() {
        if (window.innerWidth <= 600) {
            this.isMobileOpen = false;
            this.sidebarContainer.classList.remove('mobile-visible');
            this.body.style.overflow = ''; // Restore scrolling
        }
    }

    toggleMobile() {
        if (window.innerWidth <= 600) {
            if (this.isMobileOpen) {
                this.closeMobile();
            } else {
                this.openMobile();
            }
        }
    }

    toggle() {
        if (window.innerWidth <= 600) {
            this.toggleMobile();
        } else {
            this.toggleDesktop();
        }
    }
}

// Page Loader Handler
document.addEventListener('DOMContentLoaded', function() {
    const pageLoader = document.querySelector('.page-loader');
    if (pageLoader) {
        // Hide loader when page is loaded
        pageLoader.style.display = 'none';
        
        // Handle browser back/forward navigation
        window.addEventListener('pageshow', function(event) {
            if (event.persisted) {
                // Page was restored from back/forward cache
                pageLoader.style.display = 'none';
            }
        });
    }

    new SidebarManager();
});

// Initialize Materialize select elements
var elems = document.querySelectorAll('select');
M.FormSelect.init(elems, {
    dropdownOptions: {
        coverTrigger: false,
        constrainWidth: false
    }
});

