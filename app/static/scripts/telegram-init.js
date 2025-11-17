// Telegram Mini App initialization
(function() {
    // Check if running inside Telegram
    if (window.Telegram && window.Telegram.WebApp) {
        const tg = window.Telegram.WebApp;
        
        // Expand the app to full height
        tg.expand();
        
        // Set header color
        tg.setHeaderColor('#000000');
        
        // Ready the app
        tg.ready();
        
        // Send initData to server for authentication
        const initData = tg.initData;
        
        // Check if we already tried to authenticate in this session
        const isAuthenticated = sessionStorage.getItem('tg_authenticated');
        
        if (initData && !isAuthenticated) {
            fetch('/api/init', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    initData: initData
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log('Telegram user authenticated:', data.user);
                    
                    // Display user telegram_id
                    const userIdElement = document.getElementById('user-id');
                    if (userIdElement) {
                        userIdElement.textContent = data.user.telegram_id;
                    }
                    
                    // Mark as authenticated in sessionStorage
                    sessionStorage.setItem('tg_authenticated', 'true');
                    sessionStorage.setItem('telegram_id', data.user.telegram_id);
                    
                    // Reload page to show user's projects
                    if (window.location.pathname === '/') {
                        window.location.reload();
                    }
                } else {
                    console.error('Authentication failed:', data.error);
                    tg.showAlert('Authentication failed: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Error authenticating:', error);
            });
        } else if (isAuthenticated) {
            console.log('Already authenticated in this session');
            
            // Display saved telegram_id
            const savedTelegramId = sessionStorage.getItem('telegram_id');
            const userIdElement = document.getElementById('user-id');
            if (userIdElement && savedTelegramId) {
                userIdElement.textContent = savedTelegramId;
            }
        } else {
            console.warn('No initData available - not running in Telegram Mini App context');
        }
        
        // Setup back button for project pages
        const currentPath = window.location.pathname;
        
        // Show back button on project detail or new project pages
        if (currentPath.startsWith('/project/') && currentPath !== '/project/new' || currentPath === '/project/new') {
            tg.BackButton.show();
            tg.BackButton.onClick(function() {
                window.location.href = '/';
            });
        } else {
            // Hide back button on home page
            tg.BackButton.hide();
        }
        
    } else {
        console.warn('Not running inside Telegram Mini App');
    }
})();
