/**
 * index.js
 * Управление главной страницей: логика базы знаний (FAQ) с поиском и фильтрацией,
 * а также модальное окно службы поддержки.
 */

class FaqManager {
    constructor() {
        this.layout = document.querySelector('.faq-layout');
        if (!this.layout) return;

        this.items = document.querySelectorAll('.faq-item');
        this.navBtns = document.querySelectorAll('.faq-nav__btn');
        this.searchInput = document.getElementById('faq-search');
        this.emptyState = document.getElementById('faq-empty-state');

        this.init();
    }

    init() {
        this.items.forEach(item => {
            const header = item.querySelector('.faq-item__header');
            header?.addEventListener('click', () => item.classList.toggle('active'));
        });

        this.navBtns.forEach(btn => {
            btn.addEventListener('click', () => this.filterByCategory(btn));
        });

        this.searchInput?.addEventListener('input', (e) => this.handleSearch(e));
    }

    filterByCategory(activeBtn) {
        this.navBtns.forEach(b => b.classList.remove('active'));
        activeBtn.classList.add('active');

        if (this.searchInput) {
            this.searchInput.value = '';
        }

        const category = activeBtn.dataset.category;

        this.items.forEach(item => {
            item.classList.remove('active');
            item.style.display = (category === 'all' || item.dataset.category === category) ? 'block' : 'none';
        });

        this.checkEmptyState();
    }

    handleSearch(e) {
        const searchTerm = e.target.value.toLowerCase().trim();

        if (searchTerm.length > 0) {
            this.navBtns.forEach(b => b.classList.remove('active'));
            const btnAll = document.querySelector('.faq-nav__btn[data-category="all"]');
            btnAll?.classList.add('active');
        }

        this.items.forEach(item => {
            const titleText = item.querySelector('.faq-item__title')?.textContent.toLowerCase() || '';
            const bodyText = item.querySelector('.faq-item__content')?.textContent.toLowerCase() || '';

            if (titleText.includes(searchTerm) || bodyText.includes(searchTerm)) {
                item.style.display = 'block';
                if (searchTerm.length > 2) {
                    item.classList.add('active');
                } else {
                    item.classList.remove('active');
                }
            } else {
                item.style.display = 'none';
                item.classList.remove('active');
            }
        });

        this.checkEmptyState();
    }

    checkEmptyState() {
        if (!this.emptyState) return;
        
        const hasVisible = Array.from(this.items).some(item => item.style.display !== 'none');
        this.emptyState.style.display = hasVisible ? 'none' : 'block';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new FaqManager();

    const btnSupport = document.getElementById('btn-open-support');
    
    if (btnSupport) {
        btnSupport.addEventListener('click', (e) => {
            e.preventDefault();
            const isAuth = btnSupport.dataset.isAuth;

            if (isAuth !== 'true') {
                window.App.modal.open('tpl-auth-required', (clone) => {
                    clone.querySelector('.btn--outline').onclick = () => window.App.modal.close();
                });
                return;
            }

            window.App.modal.open('tpl-support', (clone) => {
                const btnSend = clone.querySelector('#btn-send-support');
                const topicInput = clone.querySelector('#support-topic');
                const msgInput = clone.querySelector('#support-message');

                btnSend.onclick = async () => {
                    const topic = topicInput.value.trim();
                    const msg = msgInput.value.trim();
                    
                    if (!topic || !msg) return; 

                    await window.App.api.post('/api/navbar/create/support-message/', {
                        title: topic,
                        message: msg
                    });

                    btnSend.innerHTML = '<span style="font-family: var(--font-code); font-weight: 700;">> system.send() ... OK</span>';
                    btnSend.style.backgroundColor = '#10B981';
                    btnSend.style.borderColor = '#10B981';
                    
                    setTimeout(() => {
                        window.App.modal.close();
                    }, 1500);
                };
            });
        });
    }
});