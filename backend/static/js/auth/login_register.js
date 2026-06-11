/**
 * login_register.js
 * Управление авторизацией и регистрацией: переключение видов,
 * анимации терминала, работа с OTP-кодами и API-запросы.
 */

class AuthApi {
    static extractError(errorData) {
        if (!errorData) return 'Неизвестная ошибка сервера';
        if (typeof errorData === 'string') return errorData;
        if (Array.isArray(errorData)) return this.extractError(errorData[0]);
        if (typeof errorData === 'object') {
            const values = Object.values(errorData);
            return values.length > 0 ? this.extractError(values[0]) : JSON.stringify(errorData);
        }
        return String(errorData);
    }

    static async post(url, payload) {
        try {
            const response = await window.App.api.post(url, payload, true, {
                'X-Requested-With': 'XMLHttpRequest'
            });
            
            const data = await response.json().catch(() => ({}));
            
            if (!response.ok) {
                const rawError = data.error || data.detail || data.message || data;
                throw { 
                    message: this.extractError(rawError), 
                    i18n: data.i18n
                };
            }
            return { success: true, data };
        } catch (error) {
            return { 
                success: false, 
                error: error.message || 'Ошибка соединения', 
                i18n: error.i18n 
            };
        }
    }
}

class UIManager {
    static toggleLoading(btn, isLoading, originalText = '') {
        if (!btn) return;
        if (isLoading) {
            btn.disabled = true;
            btn.innerHTML = `<svg class="spinner" viewBox="0 0 50 50" style="width: 20px; height: 20px; animation: rotate 2s linear infinite; margin: 0 auto;"><circle cx="25" cy="25" r="20" fill="none" stroke="currentColor" stroke-width="4" stroke-dasharray="1, 200" stroke-dashoffset="0" stroke-linecap="round" style="animation: dash 1.5s ease-in-out infinite;"></circle></svg>`;
        } else {
            btn.disabled = false;
            btn.textContent = originalText;
            // Восстанавливаем перевод кнопки, если у нее есть data-i18n
            if (window.App?.i18n?.translateDOM) window.App.i18n.translateDOM(btn.parentElement);
        }
    }
}

class TerminalController {
    constructor() {
        this.title = document.querySelector('.presentation-title');
        this.desc = document.querySelector('.presentation-desc');
        this.body = document.querySelector('.terminal-body');
    }

    updateStatus(statusHTML) {
        const termStatus = document.getElementById('term-status');
        if (termStatus) termStatus.innerHTML = statusHTML;
    }

    setMode(mode) {
        if (mode === 'login') {
            if (this.title) this.title.innerHTML = 'while(unauthorized) {<br>&nbsp;&nbsp;login();<br>}';
            if (this.desc) {
                this.desc.setAttribute('data-i18n', 'auth.login_desc');
                this.desc.textContent = 'Войдите в систему, чтобы продолжить поиск и отслеживание вакансий.';
            }
            if (this.body) {
                this.body.innerHTML = `
                    <div class="term-line"><span class="term-prompt">~/$</span> ./auth_session.sh</div>
                    <div class="term-line text-secondary">> Checking token... <span class="text-danger">NOT FOUND</span></div>
                    <div class="term-line text-secondary">> Requesting manual login... <span class="term-ok">OK</span></div>
                    <div class="term-line typing-anim" id="term-status">Awaiting credentials<span class="cursor">_</span></div>
                `;
            }
        } else {
            if (this.title) this.title.innerHTML = 'while(unregistered) {<br>&nbsp;&nbsp;signup();<br>}';
            if (this.desc) {
                this.desc.setAttribute('data-i18n', 'auth.register_desc');
                this.desc.textContent = 'Получи доступ к скрытым вакансиям, создай свой черный список и управляй откликами.';
            }
            if (this.body) {
                this.body.innerHTML = `
                    <div class="term-line"><span class="term-prompt">~/$</span> ./init_user.sh</div>
                    <div class="term-line text-secondary">> System check... <span class="term-ok">OK</span></div>
                    <div class="term-line text-secondary">> Establishing secure connection... <span class="term-ok">OK</span></div>
                    <div class="term-line typing-anim" id="term-status">Awaiting credentials<span class="cursor">_</span></div>
                `;
            }
        }
        
        if (window.App?.i18n?.translateDOM) {
            window.App.i18n.translateDOM(document.querySelector('.auth-presentation'));
        }
    }
}

class OtpController {
    constructor() {
        this.inputs = document.querySelectorAll('.otp-digit');
        if (this.inputs.length) this.init();
    }

    init() {
        this.inputs.forEach((input, index) => {
            input.addEventListener('input', () => {
                input.value = input.value.replace(/[^0-9]/g, '');
                if (input.value !== '' && index < this.inputs.length - 1) {
                    this.inputs[index + 1].focus();
                }
            });
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Backspace' && input.value === '' && index > 0) {
                    this.inputs[index - 1].focus();
                }
            });
            input.addEventListener('focus', () => input.select());
        });
    }

    getCode() {
        return Array.from(this.inputs).map(i => i.value).join('');
    }

    clear() {
        this.inputs.forEach(i => i.value = '');
        if (this.inputs.length > 0) this.inputs[0].focus();
    }
}

class AuthController {
    constructor() {
        this.views = {
            register: document.getElementById('register-view'),
            login: document.getElementById('login-view'),
            step1: document.getElementById('auth-step-1'),
            step2: document.getElementById('auth-step-2')
        };

        this.elements = {
            loginEmail: document.getElementById('login-email'),
            loginPass: document.getElementById('login-password'),
            loginError: document.getElementById('login-error'),
            
            regEmail: document.getElementById('reg-email'),
            regPass: document.getElementById('reg-password'),
            regPassConfirm: document.getElementById('reg-password-confirm'),
            passError: document.getElementById('password-error'),
            otpError: document.getElementById('otp-error'),
            displayEmail: document.getElementById('display-email')
        };

        this.terminal = new TerminalController();
        this.otp = new OtpController();

        this.bindEvents();
    }

    bindEvents() {
        document.getElementById('switch-to-login')?.addEventListener('click', (e) => this.switchView(e, 'login'));
        document.getElementById('switch-to-register')?.addEventListener('click', (e) => this.switchView(e, 'register'));
        
        document.getElementById('btn-login-submit')?.addEventListener('click', (e) => this.handleLogin(e));
        document.getElementById('btn-next-step')?.addEventListener('click', (e) => this.handleRegisterStep1(e));
        document.getElementById('btn-back-step')?.addEventListener('click', (e) => this.handleRegisterBack(e));
        document.getElementById('btn-verify')?.addEventListener('click', (e) => this.handleVerify(e));
    }

    // Мгновенный перевод и защита от пустых полей
    translateError(el, i18nKey, defaultText) {
        if (!el) return;
        
        if (i18nKey && window.App?.i18n) {
            const fullKey = `messages.${i18nKey}`;
            el.setAttribute('data-i18n', fullKey);
            const translation = window.App.i18n.getTranslation(fullKey);
            el.textContent = translation || defaultText;
        } else {
            el.removeAttribute('data-i18n');
            el.textContent = defaultText;
        }
        
        el.style.display = 'block';
    }

    switchView(e, target) {
        e.preventDefault();
        this.views.login.style.display = ''; 
        this.views.register.style.display = '';

        if (target === 'login') {
            this.views.register.classList.remove('active');
            this.views.login.classList.add('active');
            this.terminal.setMode('login');
        } else {
            this.views.login.classList.remove('active');
            this.views.register.classList.add('active');
            
            if (this.views.step1 && this.views.step2) {
                this.views.step2.classList.remove('active');
                this.views.step1.classList.add('active');
            }
            this.terminal.setMode('register');
        }
    }

    async handleLogin(e) {
        const btn = e.currentTarget;
        const email = this.elements.loginEmail.value.trim();
        const password = this.elements.loginPass.value;

        if (!email || !password) {
            this.translateError(this.elements.loginError, 'fill_all_fields', 'Заполните все поля');
            return;
        }

        this.elements.loginError.style.display = 'none';
        UIManager.toggleLoading(btn, true);
        this.terminal.updateStatus(`> Authenticating user... <span class="cursor">_</span>`);

        const result = await AuthApi.post('/api/user/login/', { email, password });

        if (result.success) {
            this.terminal.updateStatus(`> Authenticating user... <span class="term-ok">SUCCESS</span><br><br><span class="typing-anim">Redirecting...</span>`);
            setTimeout(() => window.location.href = '/user/profile/', 800);
        } else {
            this.terminal.updateStatus(`> Authenticating user... <span class="text-danger">FAILED</span><br><br><span class="typing-anim">Awaiting credentials<span class="cursor">_</span></span>`);
            this.translateError(this.elements.loginError, result.i18n, result.error);
            UIManager.toggleLoading(btn, false, 'Войти');
        }
    }

    async handleRegisterStep1(e) {
        const btn = e.currentTarget;
        const email = this.elements.regEmail.value.trim();
        const password = this.elements.regPass.value;
        const passwordConfirm = this.elements.regPassConfirm.value;

        if (!email || !password) {
            this.translateError(this.elements.passError, 'fill_all_fields', 'Заполните все поля');
            return;
        }

        if (password !== passwordConfirm) {
            this.elements.regPassConfirm.classList.add('input-error');
            this.translateError(this.elements.passError, 'error_password_match', 'Пароли не совпадают');
            this.terminal.updateStatus(`<span class="text-danger">> Error: Passwords do not match</span><br><br>Awaiting credentials<span class="cursor">_</span>`);
            return;
        }

        this.elements.regPassConfirm.classList.remove('input-error');
        this.elements.passError.style.display = 'none';
        
        UIManager.toggleLoading(btn, true);
        this.terminal.updateStatus(`> Creating user record... <span class="cursor">_</span>`);

        const result = await AuthApi.post('/api/user/register/', { email, password });

        if (result.success) {
            if (this.elements.displayEmail) this.elements.displayEmail.textContent = email;
            
            this.views.step1.classList.remove('active');
            this.views.step2.style.display = ''; 
            this.views.step2.classList.add('active');

            this.terminal.updateStatus(`> Creating user record... <span class="term-ok">OK</span><br>> Sending OTP to ${email}... <span class="term-ok">OK</span><br><br><span class="typing-anim">Awaiting verification<span class="cursor">_</span></span>`);
        } else {
            this.translateError(this.elements.passError, result.i18n, result.error);
            this.terminal.updateStatus(`> Creating user record... <span class="text-danger">FAILED</span><br><br>Awaiting credentials<span class="cursor">_</span>`);
            UIManager.toggleLoading(btn, false, 'Продолжить');
        }
    }

    handleRegisterBack(e) {
        e.preventDefault();
        this.views.step2.classList.remove('active');
        this.views.step1.classList.add('active');
        this.terminal.updateStatus(`Awaiting credentials<span class="cursor">_</span>`);
        this.otp.clear();
    }

    async handleVerify(e) {
        const btn = e.currentTarget;
        const email = this.elements.regEmail.value.trim();
        const otpCode = this.otp.getCode();

        if (otpCode.length < 4) {
            this.translateError(this.elements.otpError, 'enter_code', 'Введите код');
            return;
        }

        this.elements.otpError.style.display = 'none';
        UIManager.toggleLoading(btn, true);
        this.terminal.updateStatus(`> Verifying OTP token... <span class="cursor">_</span>`);

        const result = await AuthApi.post('/api/user/verify/', { email, code: otpCode });

        if (result.success) {
            this.terminal.updateStatus(`> Verifying OTP token... <span class="term-ok">VALID</span><br>> Initializing session... <span class="term-ok">OK</span><br><br><span class="typing-anim">Redirecting...</span>`);
            setTimeout(() => window.location.href = '/user/profile/', 800);
        } else {
            this.terminal.updateStatus(`> Verifying OTP token... <span class="text-danger">INVALID</span><br><br><span class="typing-anim">Awaiting verification<span class="cursor">_</span></span>`);
            this.translateError(this.elements.otpError, result.i18n, result.error);
            
            this.otp.clear();
            UIManager.toggleLoading(btn, false, 'Завершить регистрацию');
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('.auth-layout')) {
        new AuthController();
    }
});