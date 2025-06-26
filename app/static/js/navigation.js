// Navigation and Loading State Management
document.addEventListener('DOMContentLoaded', function() {
    const pageLoader = document.getElementById('pageLoader');
    
    // Hide loader initially
    if (pageLoader) {
        pageLoader.style.display = 'none';
    }

    // Handle all navigation events
    window.addEventListener('beforeunload', function() {
        // Don't show loader for page refreshes
        if (performance.navigation.type !== 1) {
            sessionStorage.setItem('isNavigating', 'true');
        }
    });

    window.addEventListener('pageshow', function(event) {
        // Remove loading state
        sessionStorage.removeItem('isNavigating');
        if (pageLoader) {
            pageLoader.style.display = 'none';
        }
        document.body.style.overflow = 'auto';
    });

    window.addEventListener('load', function() {
        // Remove loading state
        sessionStorage.removeItem('isNavigating');
        if (pageLoader) {
            pageLoader.style.display = 'none';
        }
        document.body.style.overflow = 'auto';
    });

    // Handle back/forward navigation
    window.addEventListener('popstate', function() {
        // Remove loading state immediately for back/forward navigation
        sessionStorage.removeItem('isNavigating');
        if (pageLoader) {
            pageLoader.style.display = 'none';
        }
        document.body.style.overflow = 'auto';
    });

    // Check if we're coming back from navigation
    if (sessionStorage.getItem('isNavigating')) {
        if (pageLoader) {
            pageLoader.style.display = 'none';
        }
        sessionStorage.removeItem('isNavigating');
    }
});
