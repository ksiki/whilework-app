/**
 * detail.js
 * Инкапсулирует логику страницы профиля: переключение вкладок,
 * модальные окна настроек и управление черным списком.
 */

class ProfileTabs {
    constructor() {
        this.navBtns = document.querySelectorAll('.profile-nav__btn');
        this.sections = document.querySelectorAll('.profile-section');
        
        if (this.navBtns.length) {
            this.init();
        }
    }

    init() {
        this.navBtns.forEach(btn => {
            btn.addEventListener('click', () => this.switchTab(btn));
        });
    }

    switchTab(activeBtn) {
        this.navBtns.forEach(b => b.classList.remove('active'));
        this.sections.forEach(s => s.classList.remove('active'));

        activeBtn.classList.add('active');
        
        const targetId = activeBtn.getAttribute('data-target');
        const targetSection = document.getElementById(targetId);
        
        if (targetSection) {
            targetSection.classList.add('active');
        }
    }
}


class BlacklistManager {
    constructor() {
        this.btns = document.querySelectorAll('.blacklist-item .btn-icon');
        
        if (this.btns.length) {
            this.init();
        }
    }

    init() {
        this.btns.forEach(btn => {
            btn.addEventListener('click', (e) => this.remove(e));
        });
    }

    async remove(e) {
        const item = e.target.closest('.blacklist-item');
        if (!item) return;
        
        const companyId = item.dataset.companyid;

        try {
            const response = await window.App.api.post('/api/user/blacklist/companies/', {
                company_id: companyId,
                delete: true
            });

            if (response.ok) {
                item.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                item.style.opacity = '0';
                item.style.transform = 'scale(0.9)';
                
                setTimeout(() => item.remove(), 300);
            }
        } catch (error) {
            console.error('Blacklist API error:', error);
        }
    }
}

class NotificationManager {
    constructor() {
        this.notificationsList = document.querySelector('.notifications-list');
        
        if (this.notificationsList) {
            this.init();
        }
    }

    init() {
        this.notificationsList.addEventListener('click', (e) => {
            const item = e.target.closest('.notification-item.unread');
            if (item) {
                this.markAsRead(item);
            }
        });
    }

    async markAsRead(item) {
        const notifId = item.dataset.id;
        if (!notifId) return;

        try {
            const response = await window.App.api.post('/api/user/notification/read/', {
                notification_id: notifId
            });

            if (response.ok) {
                item.classList.remove('unread');
            } else {
                console.error('Failed to mark notification as read');
            }
        } catch (error) {
            console.error('Notification API error:', error);
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('.profile-layout')) {
        new ProfileTabs();
        new BlacklistManager();
        new NotificationManager();

        document.getElementById('btn-open-password')?.addEventListener('click', () => {
            window.App.modal.open('tpl-change-password');
        });

        document.getElementById('btn-open-delete')?.addEventListener('click', () => {
            window.App.modal.open('tpl-delete-account', (clone) => {
                clone.querySelector('#btn-cancel-modal').onclick = () => window.App.modal.close();
            });
        });
        
        document.querySelectorAll('.btn-close-job').forEach(btn => {
            btn.addEventListener('click', () => {
                window.App.modal.open('tpl-close-job', (clone) => {
                    clone.querySelector('#btn-cancel-modal').onclick = () => window.App.modal.close();
                });
            });
        });
    }
});