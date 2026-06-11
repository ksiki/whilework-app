/**
 * index.js (Cooperation Page)
 * Управление страницей сотрудничества: конфигуратор рекламных форматов,
 * взаимодействие с буфером обмена и отправка формы предложений.
 */

class CooperationConfigurator {
    constructor() {
        this.pills = document.querySelectorAll('.config-pill');
        this.output = document.getElementById('config-code-output');
        
        this.data = {
            'social': {
                className: 'SocialMediaPromo',
                platform: 'YT / TT / IG / Threads',
                format: { ru: 'Пост / Шортс', en: 'Post / Shorts' },
                target: { ru: 'Подписчики каналов', en: 'Channel subscribers' }
            },
            'banner': {
                className: 'MainPageBanner',
                platform: 'whilework',
                format: { ru: 'Баннер (Hero Section)', en: 'Banner (Hero Section)' },
                target: { ru: 'Все посетители сайта', en: 'All website visitors' }
            }
        };

        if (this.pills.length && this.output) {
            this.init();
        }
    }

    init() {
        this.update('social');

        this.pills.forEach(pill => {
            pill.addEventListener('click', () => {
                this.pills.forEach(p => p.classList.remove('active'));
                pill.classList.add('active');
                this.update(pill.dataset.type);
            });
        });

        document.addEventListener('app:languageChanged', () => {
            const activePill = document.querySelector('.config-pill.active');
            if (activePill) this.update(activePill.dataset.type);
        });
    }

    getLang() {
        return window.App?.i18n?.lang || 'ru';
    }

    update(type) {
        const data = this.data[type];
        if (!data) return;

        const lang = this.getLang();

        this.output.style.opacity = '0.3';
        this.output.style.transform = 'translateY(4px)';
        this.output.style.transition = 'all 0.2s ease';
        
        setTimeout(() => {
            this.output.innerHTML = `<span class="token-keyword">class</span> <span class="token-class">${data.className}</span>:\n    platform = <span class="token-string">"${data.platform}"</span>\n    format = <span class="token-string">"${data.format[lang]}"</span>\n    target = <span class="token-string">"${data.target[lang]}"</span>\n    status = <span class="token-builtin">ready_to_launch</span>`;
            
            this.output.style.opacity = '1';
            this.output.style.transform = 'translateY(0)';
        }, 200);
    }
}

class CooperationClipboard {
    constructor() {
        this.btn = document.getElementById('btn-copy-email');
        this.email = 'partner@while.work';
        
        if (this.btn) {
            this.init();
        }
    }

    init() {
        this.btn.addEventListener('click', (e) => this.copy(e));
    }

    copy(e) {
        e.preventDefault();
        
        navigator.clipboard.writeText(this.email).then(() => {
            const originalText = this.btn.textContent;
            
            this.btn.innerHTML = '<span style="font-family: var(--font-code);">> system.copy("SUCCESS")</span>';
            this.btn.style.backgroundColor = '#10B981'; 
            this.btn.style.borderColor = '#10B981';
            this.btn.style.color = '#FFFFFF';
            
            setTimeout(() => {
                this.btn.textContent = originalText;
                this.btn.style.backgroundColor = '';
                this.btn.style.borderColor = '';
                this.btn.style.color = '';
            }, 2000);
        }).catch(err => console.error('Clipboard error:', err));
    }
}

class CooperationForm {
    constructor() {
        this.form = document.getElementById('partnership-form');
        this.btnSubmit = document.getElementById('btn-submit-coop');
        this.tplSuccess = document.getElementById('tpl-coop-success');
        
        if (this.form && this.btnSubmit && this.tplSuccess) {
            this.init();
        }
    }

    init() {
        this.form.addEventListener('input', (e) => this.handleInput(e));
        this.btnSubmit.addEventListener('click', (e) => this.handleSubmit(e));
    }

    isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    handleInput(e) {
        if (e.target.classList.contains('form-input')) {
            e.target.classList.remove('input-error');
            
            if (e.target.type === 'email' && e.target.value.trim() !== '') {
                if (!this.isValidEmail(e.target.value.trim())) {
                    e.target.classList.add('input-error');
                }
            }
        }
    }

    clearAllErrors() {
        this.form.querySelectorAll('.form-input').forEach(i => i.classList.remove('input-error'));
        this.form.querySelectorAll('.error-msg').forEach(el => el.classList.remove('visible'));
        const sysErr = document.getElementById('form-system-error');
        if (sysErr) sysErr.style.display = 'none';
    }

    setFieldError(fieldName, i18nKey) {
        const input = this.form.querySelector(`[name="${fieldName}"]`);
        const errorNode = document.getElementById(`error-${fieldName}`);
        
        if (input) input.classList.add('input-error');
        if (errorNode) {
            errorNode.setAttribute('data-i18n', i18nKey);
            errorNode.textContent = window.App?.i18n?.getTranslation(i18nKey) || 'Ошибка валидации';
            errorNode.classList.add('visible');
        }
    }

    parseBackendValidation(detail) {
        detail.forEach(err => {
            const fieldName = err.loc[err.loc.length - 1];
            const errType = err.type;

            let i18nKey = `cooperation.error_invalid`;

            if (errType === 'missing') i18nKey = 'cooperation.error_required';
            else if (errType === 'string_too_short') i18nKey = 'cooperation.error_min_length';
            else if (errType.includes('email')) i18nKey = 'cooperation.error_invalid_email';

            this.setFieldError(fieldName, i18nKey);
        });
    }

    async handleSubmit(e) {
        e.preventDefault();
        this.clearAllErrors();

        const payload = {
            name: this.form.querySelector('[name="name"]').value.trim(),
            email: this.form.querySelector('[name="email"]').value.trim(),
            message: this.form.querySelector('[name="message"]').value.trim()
        };

        const originalBtnText = this.btnSubmit.textContent;
        this.btnSubmit.disabled = true;
        this.btnSubmit.innerHTML = `<svg class="spinner" viewBox="0 0 50 50" style="width: 20px; height: 20px; animation: rotate 2s linear infinite; margin: 0 auto;"><circle cx="25" cy="25" r="20" fill="none" stroke="currentColor" stroke-width="4" stroke-dasharray="1, 200" stroke-dashoffset="0" stroke-linecap="round" style="animation: dash 1.5s ease-in-out infinite;"></circle></svg>`;

        try {
            const response = await window.App.api.post(
                '/api/cooperation/create/message/',
                payload,
                true,
                { 'X-Requested-With': 'XMLHttpRequest' }
            );

            const data = await response.json();

            if (response.status === 422) {
                this.parseBackendValidation(data.detail);
                throw new Error('ValidationFailed');
            }

            if (!response.ok) throw new Error('ServerError');

            this.form.style.opacity = '0';
            this.form.style.transform = 'scale(0.95)';
            this.form.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';

            setTimeout(() => {
                const successNode = this.tplSuccess.content.cloneNode(true);
                const parent = this.form.parentElement;
                
                const descNode = successNode.querySelector('.success-desc');
                if (descNode && data.i18n) {
                    descNode.setAttribute('data-i18n', data.i18n);
                    descNode.textContent = window.App?.i18n?.getTranslation(data.i18n) || descNode.textContent;
                }

                this.form.remove(); 
                parent.appendChild(successNode); 
            }, 300);

        } catch (error) {
            this.btnSubmit.disabled = false;
            this.btnSubmit.textContent = originalBtnText;
            
            if (error.message !== 'ValidationFailed') {
                console.error('Submit error:', error);
                const sysErrNode = document.getElementById('form-system-error');
                sysErrNode.setAttribute('data-i18n', 'cooperation.error_system');
                sysErrNode.textContent = window.App?.i18n?.getTranslation('cooperation.error_system') || 'Системная ошибка. Попробуйте позже.';
                sysErrNode.style.display = 'block';
            }
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('.coop-layout')) {
        new CooperationConfigurator();
        new CooperationClipboard();
        new CooperationForm();
    }
});