/**
 * detail.js
 * Управление страницей деталей вакансии. Инкапсулирует работу с модальными окнами,
 * API запросами и действиями пользователя (контакты, шаринг, жалобы, блеклист).
 */
class JobDetailController {
    constructor() {
        this.modal = window.App.modal;
        this.bindActions();
        this.markAsViewed();
    }

    markAsViewed() {
        const container = document.querySelector('.job-detail__main');
        if (!container || !container.dataset.id) return;

        const vacancyId = container.dataset.id;
        window.App.api.post('/api/user/add-viewed-vacancy/', { vacancy: vacancyId })
            .catch(() => {});
    }

    bindActions() {
        document.getElementById('btn-show-contacts')?.addEventListener('click', (e) => this.handleContacts(e.currentTarget));
        document.getElementById('btn-share')?.addEventListener('click', (e) => this.handleShare(e.currentTarget));
        document.getElementById('btn-report')?.addEventListener('click', (e) => this.handleReport(e.currentTarget));
        document.getElementById('btn-blacklist')?.addEventListener('click', (e) => this.handleBlacklist(e.currentTarget));
        document.querySelector('.back-link')?.addEventListener('click', (e) => this.handleBack(e));
    }

    handleContacts(btn) {
        const { isAuth, tg, email, discord, jobId } = btn.dataset;

        if (isAuth !== 'true') {
            window.App.modal.open('tpl-auth-required', (clone) => {
                clone.querySelector('.btn--outline').onclick = () => window.App.modal.close();
            });
            return;
        }

        this.modal.open('tpl-contacts', (clone) => {
            const container = clone.querySelector('.contacts-container');

            if (!tg && !email && !discord) {
                const noContacts = document.createElement('p');
                noContacts.style.cssText = 'color: var(--text-secondary); text-align: center;';
                noContacts.setAttribute('data-i18n', 'modal.no_contacts_specified');
                noContacts.textContent = 'Контакты не указаны';
                container.appendChild(noContacts);
            } else {
                if (tg) {
                    const cleanTg = tg.replace('@', '');
                    const btnTg = document.createElement('a');
                    btnTg.href = `https://t.me/${cleanTg}`;
                    btnTg.target = '_blank';
                    btnTg.className = 'btn btn--solid';
                    btnTg.style.cssText = 'text-align: center; text-decoration: none;';
                    btnTg.setAttribute('data-i18n', 'modal.write_in_telegram');
                    btnTg.textContent = 'Написать в Telegram';
                    container.appendChild(btnTg);
                }
                
                if (email) {
                    const btnEmail = document.createElement('a');
                    btnEmail.href = `mailto:${email}`;
                    btnEmail.className = 'btn btn--outline';
                    btnEmail.style.cssText = 'text-align: center; text-decoration: none; font-family: var(--font-code);';
                    btnEmail.textContent = email;
                    container.appendChild(btnEmail);
                }

                if (discord) {
                    const btnDiscord = document.createElement('div');
                    btnDiscord.className = 'btn btn--outline';
                    btnDiscord.style.cssText = 'text-align: center; font-family: var(--font-code); display: flex; justify-content: center; gap: 8px; user-select: all; cursor: text;';

                    const labelSpan = document.createElement('span');
                    labelSpan.setAttribute('data-i18n', 'modal.discord');
                    labelSpan.textContent = 'Discord:';

                    const valueSpan = document.createElement('span');
                    valueSpan.textContent = discord;

                    btnDiscord.appendChild(labelSpan);
                    btnDiscord.appendChild(valueSpan);

                    container.appendChild(btnDiscord);
                }
            }
        });

        if (jobId) {
            window.App.api.post('/api/vacancy/show-contacts/', { vacancy: jobId })
                .catch(console.error);
        }
    }

    handleShare(btn) {
        navigator.clipboard.writeText(window.location.href).then(() => {
            const originalContent = btn.innerHTML;

            btn.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg> <span style="color: #10B981;" data-i18n="detail.copy">Скопировано!</span>`;

            if (window.App && window.App.i18n) {
                window.App.i18n.translateDOM(btn);
            }

            setTimeout(() => { 
                btn.innerHTML = originalContent; 
            }, 2000);
        });
    }

    handleReport(btn) {
        const { isAuth, id } = btn.dataset;

        if (isAuth !== 'true') {
            window.App.modal.open('tpl-auth-required', (clone) => {
                clone.querySelector('.btn--outline').onclick = () => window.App.modal.close();
            });
            return;
        }

        this.modal.open('tpl-report', (clone) => {
            const submitBtn = clone.querySelector('#submit-report');
            const selectReason = clone.querySelector('#report-reason');
            const textareaDetails = clone.querySelector('#report-text');

            // Убираем подсветку ошибки при выборе причины
            selectReason.addEventListener('change', () => {
                selectReason.classList.remove('has-error');
            });

            submitBtn.onclick = () => {
                const reason = selectReason.value;
                const details = textareaDetails.value.trim();

                // Валидация: причина обязательна
                if (!reason) {
                    selectReason.classList.add('has-error');
                    return;
                }

                // Отправляем payload (ключи совпадают с Pydantic схемой ComplaintRequest)
                window.App.api.post('/api/vacancy/complaint/', { 
                    vacancy: id, 
                    reason: reason,
                    details: details
                })
                .then(() => {
                    this.modal.open('tpl-report-success');
                    setTimeout(() => this.modal.close(), 2500);
                })
                .catch(error => {
                    console.error('Report submission failed:', error);
                });
            };
        });
    }

    handleBlacklist(btn) {
        const { isAuth, id, companyName } = btn.dataset;
        const name = companyName || 'этой компании';

        if (isAuth !== 'true') {
            window.App.modal.open('tpl-auth-required', (clone) => {
                clone.querySelector('.btn--outline').onclick = () => window.App.modal.close();
            });
            return;
        }

        if (!id || id.trim() === '' || id === 'None') {
            this.modal.open('tpl-action-impossible', (clone) => {
                clone.querySelector('#close-impossible-modal').onclick = () => this.modal.close();
            });
            return;
        }

        this.modal.open('tpl-blacklist', (clone) => {
            clone.querySelector('.blacklist-company-name').textContent = name;
            clone.querySelector('#cancel-blacklist').onclick = () => this.modal.close();

            clone.querySelector('#confirm-blacklist').onclick = () => {
                window.App.api.post('/api/user/blacklist/companies/', { company_id: id, delete: false })
                    .catch(console.error);
                
                this.modal.open('tpl-blacklist-success');
                setTimeout(() => this.modal.close(), 2500);
            };
        });
    }

    handleBack(e) {
        e.preventDefault();
        if (window.history.length > 1) {
            window.history.back();
        } else {
            window.location.href = e.currentTarget.getAttribute('href');
        }
    }
}

class ScrollAnimationManager {
    constructor() {
        this.initSimilarJobsObserver();
    }

    initSimilarJobsObserver() {
        const grid = document.querySelector('.similar-jobs-grid');
        if (!grid) return;

        const observer = new IntersectionObserver((entries, obs) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('is-animated');
                    
                    obs.unobserve(entry.target); 
                }
            });
        }, {
            root: null,
            rootMargin: '0px',
            threshold: 0.15 
        });

        observer.observe(grid);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new JobDetailController();
    new ScrollAnimationManager();
});