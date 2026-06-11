/**
 * banner.js
 * Управление приветственным баннером: закрытие с сохранением состояния
 * и функция копирования ссылки на платформу с учетом локализации.
 */

class WelcomeBanner {
    constructor() {
        this.banner = document.getElementById('top-welcome-banner');
        this.closeBtn = document.getElementById('btn-close-welcome');
        this.shareBtn = document.getElementById('btn-share-platform');
        this.storageKey = 'whileWorkWelcomeClosed';

        if (this.banner) {
            this.init();
        }
    }

    init() {
        if (localStorage.getItem(this.storageKey) === 'true') {
            this.banner.style.display = 'none';
            return;
        }

        this.closeBtn?.addEventListener('click', () => this.close());
        this.shareBtn?.addEventListener('click', () => this.share());
    }

    close() {
        this.banner.classList.add('closed');
        localStorage.setItem(this.storageKey, 'true');
        
        setTimeout(() => {
            this.banner.style.display = 'none';
        }, 500);
    }

    share() {
        const siteUrl = window.location.origin;
        
        navigator.clipboard.writeText(siteUrl).then(() => {
            const originalHtml = this.shareBtn.innerHTML;
            
            const lang = window.App?.i18n?.lang || 'ru';
            const successText = lang === 'ru' ? 'Ссылка скопирована!' : 'Link copied!';
            
            this.shareBtn.innerHTML = `
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="20 6 9 17 4 12"></polyline>
                </svg> 
                <span>${successText}</span>
            `;
            this.shareBtn.style.background = '#10B981';
            this.shareBtn.style.color = '#FFFFFF';
            
            setTimeout(() => {
                this.shareBtn.innerHTML = originalHtml;
                this.shareBtn.style.background = '';
                this.shareBtn.style.color = '';
            }, 3000);
        }).catch(err => {
            console.error('Copy link error:', err);
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new WelcomeBanner();
});