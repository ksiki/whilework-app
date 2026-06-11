/**
 * 404.js
 * Управление страницей ошибки 404: обработка кнопки "Сообщить о баге",
 * отправка реального отчета на сервер и вывод Toast-уведомления.
 */

class ErrorReporter {
    constructor() {
        this.btn = document.getElementById('btn-error-report');
        this.toastTemplate = document.getElementById('tpl-error-toast');

        if (this.btn && this.toastTemplate) {
            this.init();
        }
    }

    init() {
        this.btn.addEventListener('click', () => this.report());
    }

    async report() {
        const originalHTML = this.btn.innerHTML;
        
        this.btn.disabled = true;
        this.btn.innerHTML = '<span style="font-family: var(--font-code);">> sending_log...</span>';

        try {
            const response = await window.App.api.post('/api/system/report-404/', {
                url: window.location.href
            }, true, {
                'X-Requested-With': 'XMLHttpRequest'
            });

            if (!response.ok) throw new Error('Server error');

            this.showToast();
        } catch (error) {
            console.error('Report error:', error);
            this.showToast(); 
        } finally {
            this.btn.disabled = false;
            this.btn.innerHTML = originalHTML;
        }
    }

    showToast() {
        const existing = document.getElementById('toast-coming-soon');
        if (existing) existing.remove();

        const clone = this.toastTemplate.content.cloneNode(true);
        const toastEl = clone.querySelector('.toast');
        
        toastEl.style.opacity = '0';
        toastEl.style.transform = 'translateY(20px)';
        toastEl.style.transition = 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)';

        if (window.App?.i18n?.translateDOM) {
            window.App.i18n.translateDOM(clone);
        }

        document.body.appendChild(clone);

        requestAnimationFrame(() => {
            const activeToast = document.getElementById('toast-coming-soon');
            if (activeToast) {
                activeToast.style.opacity = '1';
                activeToast.style.transform = 'translateY(0)';
            }
        });

        setTimeout(() => {
            const activeToast = document.getElementById('toast-coming-soon');
            if (activeToast) {
                activeToast.style.opacity = '0';
                activeToast.style.transform = 'translateY(10px)';
                
                setTimeout(() => activeToast.remove(), 300); 
            }
        }, 3500);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new ErrorReporter();
});