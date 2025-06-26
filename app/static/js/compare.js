// Cache DOM elements
const customSelects = document.querySelectorAll('.custom-select');

// Initialize custom selects
customSelects.forEach((select, index) => {
    const header = select.querySelector('.select-header');
    const selectedText = header.querySelector('.selected-driver');
    const options = select.querySelector('.select-options');
    const searchInput = select.querySelector('.driver-search');
    const hiddenInput = select.querySelector('input[type="hidden"]');
    
    // Handle click outside to close dropdown
    document.addEventListener('click', (e) => {
        if (!select.contains(e.target)) {
            select.classList.remove('open');
        }
    });

    // Toggle dropdown
    header.addEventListener('click', (e) => {
        e.stopPropagation();
        const wasOpen = select.classList.contains('open');
        
        // Close all other selects
        customSelects.forEach(s => s.classList.remove('open'));
        
        if (!wasOpen) {
            select.classList.add('open');
            searchInput.focus();
        }
    });

    // Handle search
    searchInput.addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase();
        const allOptions = options.querySelectorAll('.select-option');
        
        allOptions.forEach(option => {
            const text = option.textContent.toLowerCase();
            option.style.display = text.includes(searchTerm) ? '' : 'none';
        });
    });

    // Handle option selection
    options.addEventListener('click', (e) => {
        const option = e.target.closest('.select-option');
        if (!option) return;

        const value = option.dataset.value;
        const text = option.textContent.trim();

        // Update selected text and hidden input
        selectedText.textContent = text;
        hiddenInput.value = value;

        // Update selected state
        options.querySelectorAll('.select-option').forEach(opt => {
            opt.classList.remove('selected');
        });
        option.classList.add('selected');

        // Close dropdown
        select.classList.remove('open');

        // Clear search
        searchInput.value = '';
        options.querySelectorAll('.select-option').forEach(opt => {
            opt.style.display = '';
        });

        // Trigger change event for chart update
        const event = new CustomEvent('driverSelected', {
            detail: {
                driver: value,
                selector: index + 1
            }
        });
        document.dispatchEvent(event);
    });
});

// Listen for driver selection changes and update chart
document.addEventListener('driverSelected', (e) => {
    const { driver, selector } = e.detail;
    const driver1 = document.getElementById('driver1').value;
    const driver2 = document.getElementById('driver2').value;

    if (driver1 && driver2) {
        updateChart(driver1, driver2);
    }
});

// Update base.html to include our new CSS
