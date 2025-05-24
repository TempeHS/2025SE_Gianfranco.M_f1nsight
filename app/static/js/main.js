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
        this.isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
        this.body = document.body;
        this.init();
    }

    init() {
        this.setupInitialState();
        this.setupEventListeners();
    }

    setupInitialState() {
        if (this.isCollapsed) {
            this.sidebarContainer.classList.add('collapsed');
            this.body.classList.add('sidebar-collapsed');
        }
    }

    setupEventListeners() {
        this.sidebarToggle.addEventListener('click', () => this.toggle());

        // MOBILE HANDLING
        if (window.innerWidth <= 600) {
            document.addEventListener('click', (e) => {
                if (!this.sidebarContainer.contains(e.target)) {
                    this.sidebarContainer.classList.remove('mobile-visible');
                }
            });
        }
    }

    toggle() {
        this.isCollapsed = !this.isCollapsed;
        localStorage.setItem('sidebarCollapsed', this.isCollapsed);
        
        this.sidebarContainer.classList.toggle('collapsed');
        this.body.classList.toggle('sidebar-collapsed');

        if (window.innerWidth <= 600) {
            this.sidebarContainer.classList.toggle('mobile-visible');
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
    new SidebarManager();
});
