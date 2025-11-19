// Mock Telegram WebApp API for local development
(function() {
    // Only mock if not in Telegram environment
    if (window.Telegram && window.Telegram.WebApp) {
        console.log('Running in real Telegram environment');
        return;
    }

    console.log('Initializing Telegram Mock for local development');

    // Mock user data - customize this for testing
    const mockUser = {
        id: 123456789,
        first_name: 'Test',
        last_name: 'User',
        username: 'testuser',
        language_code: 'ru',
        is_premium: false,
        allows_write_to_pm: true
    };

    // Generate mock initData string (simplified version)
    function generateMockInitData() {
        const authDate = Math.floor(Date.now() / 1000);
        const userData = btoa(JSON.stringify(mockUser));
        return `user=${encodeURIComponent(userData)}&auth_date=${authDate}&hash=mock_hash_for_local_dev`;
    }

    // Create mock BackButton
    const MockBackButton = {
        isVisible: false,
        onClick(callback) {
            this.callback = callback;
        },
        offClick(callback) {
            if (this.callback === callback) {
                this.callback = null;
            }
        },
        show() {
            this.isVisible = true;
            this._render();
        },
        hide() {
            this.isVisible = false;
            this._remove();
        },
        _render() {
            if (document.getElementById('tg-mock-back-button')) return;
            
            const button = document.createElement('button');
            button.id = 'tg-mock-back-button';
            button.textContent = '← Back';
            button.style.cssText = `
                position: fixed;
                top: 10px;
                left: 10px;
                z-index: 10000;
                padding: 8px 16px;
                background: #007AFF;
                color: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-size: 14px;
                font-weight: 500;
            `;
            button.onclick = () => {
                if (this.callback) this.callback();
            };
            document.body.appendChild(button);
        },
        _remove() {
            const button = document.getElementById('tg-mock-back-button');
            if (button) button.remove();
        }
    };

    // Create mock MainButton
    const MockMainButton = {
        text: 'CONTINUE',
        color: '#007AFF',
        textColor: '#FFFFFF',
        isVisible: false,
        isActive: true,
        isProgressVisible: false,
        setText(text) {
            this.text = text;
            this._update();
        },
        onClick(callback) {
            this.callback = callback;
        },
        offClick(callback) {
            if (this.callback === callback) {
                this.callback = null;
            }
        },
        show() {
            this.isVisible = true;
            this._render();
        },
        hide() {
            this.isVisible = false;
            this._remove();
        },
        enable() {
            this.isActive = true;
            this._update();
        },
        disable() {
            this.isActive = false;
            this._update();
        },
        showProgress(leaveActive = false) {
            this.isProgressVisible = true;
            if (!leaveActive) this.isActive = false;
            this._update();
        },
        hideProgress() {
            this.isProgressVisible = false;
            this._update();
        },
        setParams(params) {
            if (params.text !== undefined) this.text = params.text;
            if (params.color !== undefined) this.color = params.color;
            if (params.text_color !== undefined) this.textColor = params.text_color;
            if (params.is_active !== undefined) this.isActive = params.is_active;
            if (params.is_visible !== undefined) {
                if (params.is_visible) this.show();
                else this.hide();
            }
            this._update();
        },
        _render() {
            if (document.getElementById('tg-mock-main-button')) return;
            
            const button = document.createElement('button');
            button.id = 'tg-mock-main-button';
            button.textContent = this.text;
            button.style.cssText = `
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                z-index: 10000;
                padding: 16px;
                background: ${this.color};
                color: ${this.textColor};
                border: none;
                cursor: pointer;
                font-size: 16px;
                font-weight: 600;
            `;
            button.onclick = () => {
                if (this.callback && this.isActive) this.callback();
            };
            document.body.appendChild(button);
            this._update();
        },
        _update() {
            const button = document.getElementById('tg-mock-main-button');
            if (!button) return;
            
            button.textContent = this.isProgressVisible ? 'Loading...' : this.text;
            button.style.background = this.color;
            button.style.color = this.textColor;
            button.style.opacity = this.isActive ? '1' : '0.5';
            button.style.cursor = this.isActive ? 'pointer' : 'not-allowed';
        },
        _remove() {
            const button = document.getElementById('tg-mock-main-button');
            if (button) button.remove();
        }
    };

    // Create mock HapticFeedback
    const MockHapticFeedback = {
        impactOccurred(style) {
            console.log(`[Mock] Haptic feedback: ${style}`);
        },
        notificationOccurred(type) {
            console.log(`[Mock] Notification haptic: ${type}`);
        },
        selectionChanged() {
            console.log('[Mock] Selection haptic');
        }
    };

    // Create mock WebApp object
    window.Telegram = {
        WebApp: {
            initData: generateMockInitData(),
            initDataUnsafe: {
                user: mockUser,
                auth_date: Math.floor(Date.now() / 1000),
                hash: 'mock_hash_for_local_dev'
            },
            version: '6.7',
            platform: 'web',
            colorScheme: 'dark',
            themeParams: {
                bg_color: '#000000',
                text_color: '#ffffff',
                hint_color: '#aaaaaa',
                link_color: '#007AFF',
                button_color: '#007AFF',
                button_text_color: '#ffffff',
                secondary_bg_color: '#1c1c1c'
            },
            isExpanded: false,
            viewportHeight: window.innerHeight,
            viewportStableHeight: window.innerHeight,
            headerColor: '#000000',
            backgroundColor: '#000000',
            BackButton: MockBackButton,
            MainButton: MockMainButton,
            HapticFeedback: MockHapticFeedback,
            
            // Methods
            ready() {
                console.log('[Mock] Telegram WebApp ready');
            },
            expand() {
                this.isExpanded = true;
                console.log('[Mock] Expanding app');
            },
            close() {
                console.log('[Mock] Closing app');
                alert('В реальном Telegram приложение закрылось бы');
            },
            setHeaderColor(color) {
                this.headerColor = color;
                console.log(`[Mock] Header color set to: ${color}`);
                document.body.style.setProperty('--tg-header-color', color);
            },
            setBackgroundColor(color) {
                this.backgroundColor = color;
                console.log(`[Mock] Background color set to: ${color}`);
            },
            enableClosingConfirmation() {
                console.log('[Mock] Closing confirmation enabled');
            },
            disableClosingConfirmation() {
                console.log('[Mock] Closing confirmation disabled');
            },
            showPopup(params, callback) {
                const message = params.message || '';
                const title = params.title || 'Telegram';
                alert(`${title}\n\n${message}`);
                if (callback) callback();
            },
            showAlert(message, callback) {
                alert(message);
                if (callback) callback();
            },
            showConfirm(message, callback) {
                const result = confirm(message);
                if (callback) callback(result);
            },
            openLink(url, options = {}) {
                console.log(`[Mock] Opening link: ${url}`);
                if (options.try_instant_view) {
                    console.log('[Mock] Using instant view');
                }
                window.open(url, '_blank');
            },
            openTelegramLink(url) {
                console.log(`[Mock] Opening Telegram link: ${url}`);
                alert(`В реальном Telegram открылась бы ссылка: ${url}`);
            },
            sendData(data) {
                console.log('[Mock] Sending data to bot:', data);
                alert(`Данные отправлены боту: ${data}`);
            }
        }
    };

    // Add visual indicator that mock is active
    const indicator = document.createElement('div');
    indicator.textContent = '🔧 Mock Mode';
    indicator.style.cssText = `
        position: fixed;
        top: 10px;
        right: 10px;
        z-index: 10000;
        padding: 4px 8px;
        background: rgba(255, 152, 0, 0.9);
        color: white;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 600;
        pointer-events: none;
    `;
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            document.body.appendChild(indicator);
        });
    } else {
        document.body.appendChild(indicator);
    }

    console.log('Telegram Mock initialized with user:', mockUser);
    console.log('%cТелеграм мок активен!', 'color: orange; font-size: 14px; font-weight: bold');
    console.log('Для смены пользователя используйте: window.TelegramMock.setUser({id: 999, first_name: "Имя", ...})');
    
    // Expose API for testing
    window.TelegramMock = {
        currentUser: mockUser,
        setUser(newUser) {
            Object.assign(mockUser, newUser);
            this.currentUser = mockUser;
            window.Telegram.WebApp.initDataUnsafe.user = mockUser;
            window.Telegram.WebApp.initData = generateMockInitData();
            console.log('Mock user updated:', mockUser);
            
            // Clear session storage to trigger re-authentication
            sessionStorage.removeItem('tg_authenticated');
            sessionStorage.removeItem('telegram_id');
            
            // Optionally reload
            if (confirm('Пользователь изменен. Перезагрузить страницу?')) {
                window.location.reload();
            }
        },
        getInitData() {
            return window.Telegram.WebApp.initData;
        },
        reloadAuth() {
            sessionStorage.removeItem('tg_authenticated');
            sessionStorage.removeItem('telegram_id');
            window.location.reload();
        }
    };
})();
