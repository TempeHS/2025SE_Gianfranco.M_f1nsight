class ThemeSwitcher {
    constructor() {
        // Cache DOM queries and theme
        this.root = document.documentElement;
        this.currentTheme = localStorage.getItem('theme') || 'default';
        this.toggle = null;
        this.switcher = null;
        this.initialized = false;

        // Bind methods to preserve context
        this.handleThemeChange = this.handleThemeChange.bind(this);
        this.handleClickOutside = this.handleClickOutside.bind(this);
        
        // Initialize immediately if document is already loaded
        if (document.readyState === 'complete') {
            this.init();
        } else {
            // Otherwise wait for DOMContentLoaded
            document.addEventListener('DOMContentLoaded', () => this.init());
        }
    }

    init() {
        if (this.initialized) return;
        
        // Apply theme immediately
        this.applyTheme(this.currentTheme);
        
        // Create UI with requestAnimationFrame for better performance
        requestAnimationFrame(() => {
            this.createThemeSwitcher();
            this.addEventListeners();
        });

        this.initialized = true;
    }

    createThemeSwitcher() {
        // Create elements individually for better performance
        const container = document.createElement('div');
        container.className = 'theme-switcher-container';
        
        const toggle = document.createElement('div');
        toggle.className = 'theme-toggle';
        toggle.id = 'themeToggle';
        
        const icon = document.createElement('i');
        icon.className = 'material-symbols-rounded';
        icon.textContent = 'palette';
        
        toggle.appendChild(icon);
        container.appendChild(toggle);
        
        const switcher = document.createElement('div');
        switcher.className = 'theme-switcher';
        switcher.id = 'themeSwitcher';
        switcher.style.display = 'none';
        
        const themes = [
            { id: 'default', name: 'Default' },
            { id: 'ferrari', name: 'Ferrari' },
            { id: 'mclaren', name: 'McLaren' }
        ];
        
        switcher.innerHTML = `
            <div class="theme-title">Select Theme</div>
            <div class="theme-options">
                ${themes.map(theme => `
                    <div class="theme-option ${this.currentTheme === theme.id ? 'active' : ''}" data-theme="${theme.id}">
                        <span class="theme-option-color ${theme.id}"></span>
                        <span>${theme.name}</span>
                    </div>
                `).join('')}
            </div>
        `;
        
        container.appendChild(switcher);
        document.body.appendChild(container);

        this.toggle = toggle;
        this.switcher = switcher;
    }

    addEventListeners() {
        // Use passive event listeners for better performance
        this.toggle.addEventListener('click', () => {
            const isVisible = this.switcher.style.display === 'block';
            this.switcher.style.display = isVisible ? 'none' : 'block';
        }, { passive: true });

        // Event delegation for theme options
        this.switcher.addEventListener('click', this.handleThemeChange, { passive: true });

        // Optimize click outside detection
        document.addEventListener('click', this.handleClickOutside, { passive: true });
    }

    handleThemeChange(e) {
        const option = e.target.closest('.theme-option');
        if (!option) return;

        const theme = option.dataset.theme;
        this.applyTheme(theme);

        // Update UI
        this.switcher.querySelectorAll('.theme-option').forEach(opt => {
            opt.classList.toggle('active', opt === option);
        });

        this.switcher.style.display = 'none';
    }

    handleClickOutside(e) {
        if (!this.toggle.contains(e.target) && !this.switcher.contains(e.target)) {
            this.switcher.style.display = 'none';
        }
    }

    applyTheme(theme) {
        // Use requestAnimationFrame for smoother theme transitions
        requestAnimationFrame(() => {
            this.currentTheme = theme;
            this.root.setAttribute('data-theme', theme);
            localStorage.setItem('theme', theme);
        });
    }
}

// Initialize theme switcher only when needed
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => new ThemeSwitcher());
} else {
    new ThemeSwitcher();
}
