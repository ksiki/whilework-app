/**
 * header.js
 * Управление интерактивными элементами шапки сайта:
 * анимация печатного текста слогана и логика всплывающих уведомлений (Toast).
 */

class SloganAnimator {
    constructor(elementId, phrases, highlights) {
        this.el = document.getElementById(elementId);
        this.phrases = phrases;
        this.highlights = highlights;
        this.phraseIndex = 0;
        this.charIndex = 0;
        this.isDeleting = false;

        if (this.el) {
            setTimeout(() => this.type(), 1000);
        }
    }

    format(text) {
        let html = text.replace(/</g, '&lt;').replace(/>/g, '&gt;');
        
        this.highlights.forEach(word => {
            const escaped = word.replace(/</g, '&lt;').replace(/>/g, '&gt;');
            html = html.split(escaped).join(`<span class="slogan-highlight">${escaped}</span>`);
        });
        
        return html;
    }

    type() {
        const currentPhrase = this.phrases[this.phraseIndex];
        
        this.charIndex += this.isDeleting ? -1 : 1;
        this.el.innerHTML = this.format(currentPhrase.substring(0, this.charIndex));

        let typeSpeed = this.isDeleting ? 30 : 80;

        if (!this.isDeleting && this.charIndex === currentPhrase.length) {
            typeSpeed = 30000;
            this.isDeleting = true;
        } else if (this.isDeleting && this.charIndex === 0) {
            this.isDeleting = false;
            this.phraseIndex = (this.phraseIndex + 1) % this.phrases.length;
            typeSpeed = 500;
        }

        setTimeout(() => this.type(), typeSpeed);
    }
}

class ToastManager {
    constructor(toastId, triggerSelector, duration = 3000) {
        this.toast = document.getElementById(toastId);
        this.triggers = document.querySelectorAll(triggerSelector);
        this.duration = duration;
        this.timeout = null;

        if (this.toast && this.triggers.length > 0) {
            this.init();
        }
    }

    init() {
        this.triggers.forEach(trigger => {
            trigger.addEventListener('click', (e) => this.show(e));
        });
    }

    show(e) {
        e.preventDefault();
        this.toast.classList.add('show');
        
        clearTimeout(this.timeout);
        this.timeout = setTimeout(() => {
            this.toast.classList.remove('show');
        }, this.duration);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const PHRASES = [
        "while money < infinity: find_job()",
        "from while_work.search import job",
        "const future = build_it()",
        "git commit -m \"new job\"",
        "wallet.balance = 999999"
    ];
    
    const HIGHLIGHTS = [
        'while ', 'find_job()', 'import', 'from', 'const', 'build_it()', 'git'
    ];

    new SloganAnimator('slogan-text', PHRASES, HIGHLIGHTS);
    new ToastManager('toast-coming-soon', '.toast-trigger, [data-i18n="post_job"]');
});