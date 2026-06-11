/**
 * base.js
 * Ядро приложения WhileWork. Отвечает за глобальные настройки: локализацию и тему.
 */

const AppConfig = {
    KEYS: {
        THEME: 'whilework_theme',
        LANG: 'whilework_language'
    },
    DEFAULTS: {
        THEME: 'dark',
        LANG: 'ru'
    }
};

class ThemeManager {
    constructor() {
        this.htmlElement = document.documentElement;
        this.toggleBtn = document.getElementById('theme-toggle');
        this.theme = localStorage.getItem(AppConfig.KEYS.THEME) || AppConfig.DEFAULTS.THEME;
        
        this.init();
    }

    init() {
        this.applyTheme(this.theme);
        if (this.toggleBtn) {
            this.toggleBtn.addEventListener('click', () => this.toggle());
        }
    }

    toggle() {
        const newTheme = this.theme === 'light' ? 'dark' : 'light';
        this.applyTheme(newTheme);
    }

    applyTheme(theme) {
        this.theme = theme;
        this.htmlElement.setAttribute('data-theme', theme);
        localStorage.setItem(AppConfig.KEYS.THEME, theme);
        this.updateIcon();
    }

    updateIcon() {
        if (!this.toggleBtn) return;
        const iconSvg = this.toggleBtn.querySelector('.theme-icon');
        if (!iconSvg) return;

        iconSvg.innerHTML = this.theme === 'dark' 
            ? `<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>`
            : `<circle cx="12" cy="12" r="5"></circle>
               <line x1="12" y1="1" x2="12" y2="3"></line>
               <line x1="12" y1="21" x2="12" y2="23"></line>
               <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
               <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
               <line x1="1" y1="12" x2="3" y2="12"></line>
               <line x1="21" y1="12" x2="23" y2="12"></line>
               <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
               <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>`;
    }
}

class I18nManager {
    constructor() {
        const cookieLang = document.cookie.split('; ').find(row => row.startsWith('django_language='))?.split('=')[1];

        this.lang = localStorage.getItem(AppConfig.KEYS.LANG) || AppConfig.DEFAULTS.LANG;
        this.translations = {};
        this.toggleBtn = document.getElementById('lang-toggle');
        
        this.init();
    }

    async init() {
        try {
            const response = await fetch('/static/assets/i18n.json');
            if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
            
            this.translations = await response.json();
            
            this.applyLanguage(this.lang);
            this.bindEvents();
        } catch (error) {
            console.error('I18n Manager: Failed to load translations', error);
        }
    }

    getTranslation(path) {
        if (!this.translations[this.lang]) return undefined;
        return path.split('.').reduce((obj, key) => (obj && obj[key] !== undefined) ? obj[key] : undefined, this.translations[this.lang]);
    }

    applyLanguage(lang) {
        this.lang = lang;
        localStorage.setItem(AppConfig.KEYS.LANG, lang);
        document.cookie = `django_language=${lang}; path=/; max-age=31536000; SameSite=Lax`;
        document.documentElement.lang = lang;

        if (this.toggleBtn) {
            const btnText = this.getTranslation('common.lang_btn');
            if (btnText) this.toggleBtn.textContent = btnText;
        }

        this.translateDOM();

        document.dispatchEvent(new CustomEvent('app:languageChanged', { 
            detail: { lang: this.lang, i18n: this } 
        }));
    }

    translateDOM(context = document) {
        context.querySelectorAll('[data-i18n]').forEach(el => {
            const translation = this.getTranslation(el.dataset.i18n);
            if (!translation) return;

            if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                el.placeholder = translation;
            } else {
                el.textContent = translation;
            }
        });
    }

    bindEvents() {
        if (!this.toggleBtn) return;
        this.toggleBtn.addEventListener('click', () => {
            const newLang = this.lang === 'ru' ? 'en' : 'ru';
            this.applyLanguage(newLang);
        });
    }
}

class ModalManager {
    constructor() {
        this.overlay = document.getElementById('interactive-modal');
        this.body = document.getElementById('modal-body');
        this.closeBtn = document.getElementById('modal-close');
        
        if (this.overlay && this.body) {
            this.bindEvents();
        }
    }

    bindEvents() {
        this.closeBtn?.addEventListener('click', () => this.close());
        this.overlay.addEventListener('click', (e) => {
            if (e.target === this.overlay) this.close();
        });
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.overlay.classList.contains('is-open')) this.close();
        });
    }

    close() {
        this.overlay.classList.remove('is-open');
        setTimeout(() => { this.body.innerHTML = ''; }, 300);
    }

    open(templateId, setupCallback = null) {
        const template = document.getElementById(templateId);
        if (!template) return;

        this.body.innerHTML = '';
        const clone = template.content.cloneNode(true);

        if (setupCallback) {
            setupCallback(clone);
        }

        this.body.appendChild(clone);
        this.overlay.classList.add('is-open');

        if (window.App?.i18n?.translateDOM) {
            window.App.i18n.translateDOM(this.body);
        }
    }
}

class ApiService {
    getCsrfToken() {
        const match = document.cookie.match(/(^|;)\s*csrftoken=([^;]+)/);
        return match ? decodeURIComponent(match[2]) : '';
    }

    /**
     * Универсальный метод для POST-запросов
     * @param {string} url - URL эндпоинта
     * @param {object} data - Тело запроса (будет преобразовано в JSON)
     * @param {boolean} withCsrf - Добавлять ли X-CSRFToken (по умолчанию true)
     */
    async post(url, data = {}, withCsrf = true, extraHeaders = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...extraHeaders
        };

        if (withCsrf) {
            headers['X-CSRFToken'] = this.getCsrfToken();
        }

        return await fetch(url, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(data)
        });
    }

    /**
     * Универсальный метод для GET-запросов
     * @param {string} url - URL эндпоинта
     * @param {object} params - Query-параметры (например: { id: 5, search: 'text' })
     * @param {boolean} withCsrf - Добавлять ли X-CSRFToken (по умолчанию false)
     */
    async get(url, params = {}, withCsrf = false, extraHeaders = {}) {
        const headers = {
            'Content-Type': 'application/json',
            ...extraHeaders
        };

        if (withCsrf) {
            headers['X-CSRFToken'] = this.getCsrfToken();
        }

        let finalUrl = url;
        if (Object.keys(params).length > 0) {
            const queryString = new URLSearchParams(params).toString();
            finalUrl = `${url}?${queryString}`;
        }

        return await fetch(finalUrl, {
            method: 'GET',
            headers: headers
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.App = window.App || {};
    window.App.theme = new ThemeManager();
    window.App.i18n = new I18nManager();
    window.App.api = new ApiService();
    window.App.modal = new ModalManager();
});