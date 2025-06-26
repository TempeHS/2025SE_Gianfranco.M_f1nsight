/**
 * F1nsight Notifications System
 * This script handles desktop notifications for the application
 */

// Store notification permission state
let notificationPermission = 'default';

// Check if browser supports notifications
const supportsNotifications = 'Notification' in window;

// Function to update UI based on permission state
function updateNotificationUI(permission) {
    const notificationCheckbox = document.querySelector('input[type="checkbox"].filled-in');
    if (!notificationCheckbox) return;
    
    const span = notificationCheckbox.nextElementSibling;
    
    if (!supportsNotifications) {
        notificationCheckbox.checked = false;
        notificationCheckbox.disabled = true;
        if (span) span.textContent = 'desktop notifications (not supported)';
        return;
    }
    
    switch(permission) {
        case 'granted':
            notificationCheckbox.checked = true;
            notificationCheckbox.disabled = false;
            if (span) span.textContent = 'enable desktop notifications';
            break;
        case 'denied':
            notificationCheckbox.checked = false;
            notificationCheckbox.disabled = true;
            if (span) {
                span.textContent = 'desktop notifications (blocked by browser)';
                span.title = 'To enable notifications, you need to change permission settings in your browser';
            }
            break;
        default: // 'default' state
            notificationCheckbox.checked = false;
            notificationCheckbox.disabled = false;
            if (span) span.textContent = 'enable desktop notifications';
            break;
    }
}

// Function to request notification permission
function requestNotificationPermission() {
    if (!supportsNotifications) {
        console.log('This browser does not support desktop notifications');
        return Promise.resolve(false);
    }

    // If permission already granted, just return
    if (Notification.permission === 'granted') {
        notificationPermission = 'granted';
        updateNotificationUI('granted');
        return Promise.resolve(true);
    }

    // If permission denied, don't ask again
    if (Notification.permission === 'denied') {
        notificationPermission = 'denied';
        updateNotificationUI('denied');
        return Promise.resolve(false);
    }

    // Request permission
    return Notification.requestPermission()
        .then(permission => {
            notificationPermission = permission;
            updateNotificationUI(permission);
            return permission === 'granted';
        })
        .catch(error => {
            console.error('Error requesting notification permission:', error);
            return false;
        });
}

// Function to send a notification
function sendNotification(title, options = {}) {
    if (!supportsNotifications || notificationPermission !== 'granted') {
        console.log('Notifications not available or permission not granted');
        return null;
    }

    // Set default icon if not provided
    if (!options.icon) {
        options.icon = '/static/images/F1_logo.png';
    }

    // Set default options
    const notificationOptions = {
        body: options.body || '',
        icon: options.icon,
        badge: options.badge || '/static/images/F1_logo.png',
        tag: options.tag || 'f1nsight-notification',
        silent: options.silent || false,
        requireInteraction: options.requireInteraction || false
    };

    try {
        const notification = new Notification(title, notificationOptions);
        
        // Add click handler if provided
        if (options.onClick) {
            notification.onclick = options.onClick;
        } else {
            // Default click behavior: focus the window
            notification.onclick = function() {
                window.focus();
                notification.close();
            };
        }

        return notification;
    } catch (error) {
        console.error('Error creating notification:', error);
        return null;
    }
}

// Handle notification preference checkbox
document.addEventListener('DOMContentLoaded', function() {
    const notificationCheckbox = document.querySelector('input[type="checkbox"].filled-in');
    
    if (notificationCheckbox) {
        // Set initial state based on current permission
        if (supportsNotifications) {
            // Initialize UI based on current permission
            updateNotificationUI(Notification.permission);
        } else {
            updateNotificationUI('not-supported');
        }
        
        // Add change event listener
        notificationCheckbox.addEventListener('change', function(e) {
            if (this.checked) {
                requestNotificationPermission().then(granted => {
                    if (granted) {
                        // Show a test notification
                        setTimeout(() => {
                            sendNotification('Notifications Enabled', {
                                body: 'You will now receive notifications from F1nsight',
                                requireInteraction: false
                            });
                        }, 500);
                    } else {
                        // If permission was denied, update UI
                        updateNotificationUI(Notification.permission);
                    }
                });
            }
        });
    }
});

// Expose functions to global scope
window.f1NotificationSystem = {
    requestPermission: requestNotificationPermission,
    sendNotification: sendNotification,
    checkSupport: () => supportsNotifications,
    getPermissionStatus: () => notificationPermission,
    updateUI: () => updateNotificationUI(Notification.permission)
};
