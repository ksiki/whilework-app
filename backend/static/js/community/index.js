/**
 * index.js (Community & Ideas Page)
 * Управление хабом комьюнити: копирование контактов, 
 * система лайков (апвоутов) в ленте и отправка новых идей.
 */

class CommunityClipboard {
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

class ChangelogFeed {
    constructor() {
        this.scrollContainer = document.querySelector('.code-window__scroll');
        if (!this.scrollContainer) return;

        this.currentPage = 1;
        this.isLoading = false;
        this.hasMore = true;

        this.init();
    }

    async init() {
        await this.loadLogs(this.currentPage, false);

        this.setupIntersectionObserver();
    }

    setupIntersectionObserver() {
        this.sentinel = document.createElement('div');
        this.sentinel.className = 'changelog-sentinel';
        this.sentinel.style.height = '1px'; 
        this.scrollContainer.appendChild(this.sentinel);

        this.observer = new IntersectionObserver((entries) => {
            const entry = entries[0];
            if (entry.isIntersecting && !this.isLoading && this.hasMore) {
                this.currentPage += 1;
                this.loadLogs(this.currentPage, true);
            }
        }, {
            root: this.scrollContainer,
            rootMargin: '50px',
            threshold: 0.1
        });

        this.observer.observe(this.sentinel);
    }

    async loadLogs(page, append = true) {
        this.isLoading = true;
        try {
            const response = await window.App.api.get(
                '/api/community/production_logs/',
                { page: page }
            );

            if (!response.ok) throw new Error('Failed to fetch production logs');

            const html = await response.text();

            if (!html.trim()) {
                this.hasMore = false;
                if (this.observer && this.sentinel) {
                    this.observer.unobserve(this.sentinel);
                    this.sentinel.remove();
                }
                if (!append) {
                    this.scrollContainer.innerHTML = '<div class="log-entry style="opacity: 0.5;">> No production logs found.</div>';
                }
            } else {
                if (append) {
                    this.sentinel.insertAdjacentHTML('beforebegin', html);
                } else {
                    this.scrollContainer.innerHTML = '';
                    this.scrollContainer.insertAdjacentHTML('beforeend', html);
                }
            }
        } catch (error) {
            console.error('Changelog loading error:', error);
            if (append) this.currentPage -= 1;
        } finally {
            this.isLoading = false;
        }
    }
}

class IdeasFeed {
    constructor() {
        this.feedContainer = document.getElementById('ideas-feed-list');
        this.filters = document.querySelectorAll('.feed-filters .filter');
        
        this.currentPage = 1;
        this.isLoading = false;
        this.hasMore = true;
        this.currentSort = 'popular';

        if (this.feedContainer) {
            this.init();
        }
    }

    async init() {
        this.feedContainer.addEventListener('click', (e) => {
            const upvoteBtn = e.target.closest('.idea-upvote');
            if (upvoteBtn) this.toggleUpvote(upvoteBtn);
        });

        this.filters.forEach(filter => {
            filter.addEventListener('click', (e) => this.handleFilterClick(e));
        });

        await this.loadPage(this.currentPage, this.currentSort, false);

        this.setupIntersectionObserver();
    }

    setupIntersectionObserver() {
        this.sentinel = document.createElement('div');
        this.sentinel.className = 'feed-sentinel';
        this.sentinel.style.height = '20px';
        this.feedContainer.insertAdjacentElement('afterend', this.sentinel);

        this.observer = new IntersectionObserver((entries) => {
            const entry = entries[0];
            if (entry.isIntersecting && !this.isLoading && this.hasMore) {
                this.currentPage += 1;
                this.loadPage(this.currentPage, this.currentSort, true);
            }
        }, {
            root: null,
            rootMargin: '150px',
            threshold: 0.1
        });

        this.observer.observe(this.sentinel);
    }

    async loadPage(page, sort, append = false) {
        this.isLoading = true;
        try {
            const response = await window.App.api.get(
                '/api/community/suggests/', 
                { page: page, sort: sort }, 
                false, 
                { 'X-Requested-With': 'XMLHttpRequest' }
            );
            
            if (!response.ok) throw new Error('Failed to fetch suggests');
            
            const html = await response.text();

            if (!html.trim()) {
                this.hasMore = false;
                if (!append) {
                    this.feedContainer.innerHTML = '<p class="text-center py-4" style="opacity: 0.6;">Идей пока нет. Предложите первую!</p>';
                }
            } else {
                if (append) {
                    this.feedContainer.insertAdjacentHTML('beforeend', html);
                } else {
                    this.feedContainer.innerHTML = html;
                }
                
                if (window.App && window.App.i18n) {
                    window.App.i18n.translateDOM(this.feedContainer);
                }
            }
        } catch (error) {
            console.error('Load page error:', error);
            if (append) this.currentPage -= 1;
        } finally {
            this.isLoading = false;
        }
    }

    async handleFilterClick(e) {
        const target = e.target;
        if (target.classList.contains('active')) return;

        this.filters.forEach(f => f.classList.remove('active'));
        target.classList.add('active');

        this.currentSort = target.dataset.code;
        this.currentPage = 1;
        this.hasMore = true;

        await this.loadPage(this.currentPage, this.currentSort, false);
    }

    async toggleUpvote(btn) {
        const isAuth = this.feedContainer.dataset.isAuth;
        if (!isAuth || isAuth.toLowerCase() !== 'true') {
            if (window.App && window.App.modal) {
                window.App.modal.open('tpl-auth-required', (clone) => {
                    const closeBtn = clone.querySelector('.btn--outline');
                    if (closeBtn) closeBtn.onclick = () => window.App.modal.close();
                });
            }
            return;
        }

        const suggestId = btn.dataset.id;
        const countSpan = btn.querySelector('.upvote-count');
        let currentCount = parseInt(countSpan.textContent, 10);
        const isActive = btn.classList.contains('active');

        if (isActive) {
            btn.classList.remove('active');
            countSpan.textContent = currentCount - 1;
        } else {
            btn.classList.add('active');
            countSpan.textContent = currentCount + 1;
        }

        try {
            const response = await window.App.api.post(
                `/api/community/suggest/${suggestId}/like/`, 
                {}, 
                true, 
                { 'X-Requested-With': 'XMLHttpRequest' }
            );
            
            const data = await response.json();
            if (!response.ok || !data.success) throw new Error(data.message || 'API Error');
        } catch (error) {
            console.error('Like error:', error);
            if (isActive) {
                btn.classList.add('active');
                countSpan.textContent = currentCount;
            } else {
                btn.classList.remove('active');
                countSpan.textContent = currentCount;
            }
        }
    }
}

class IdeasForm {
    constructor() {
        this.form = document.getElementById('community-ideas-form');
        this.btnSubmit = document.getElementById('btn-submit-idea');
        this.tplSuccess = document.getElementById('tpl-idea-success');
        
        if (this.form && this.btnSubmit && this.tplSuccess) {
            this.init();
        }
    }

    init() {
        this.form.addEventListener('input', (e) => this.handleInput(e));
        this.btnSubmit.addEventListener('click', (e) => this.handleSubmit(e));
    }

    handleInput(e) {
        if (e.target.classList.contains('form-input')) {
            e.target.classList.remove('input-error');
        }
    }

    clearAllErrors() {
        this.form.querySelectorAll('.form-input').forEach(i => i.classList.remove('input-error'));
        this.form.querySelectorAll('.error-msg').forEach(el => el.classList.remove('visible'));
        const sysErr = document.getElementById('form-system-error');
        if (sysErr) sysErr.style.display = 'none';
    }

    setFieldError(fieldName, errorText) {
        const input = this.form.querySelector(`[name="${fieldName}"]`);
        const errorNode = document.getElementById(`error-${fieldName}`);
        
        if (input) input.classList.add('input-error');
        if (errorNode) {
            errorNode.textContent = errorText;
            errorNode.classList.add('visible');
        }
    }

    validate(payload) {
        let isValid = true;
        if (!payload.title) {
            this.setFieldError('title', 'Заголовок не может быть пустым');
            isValid = false;
        }
        if (!payload.description || payload.description.length < 10) {
            this.setFieldError('description', 'Опишите идею подробнее (минимум 10 символов)');
            isValid = false;
        }
        return isValid;
    }

    async handleSubmit(e) {
        e.preventDefault();
        this.clearAllErrors();

        const isAuth = this.form.dataset.isAuth;
        if (!isAuth || isAuth.toLowerCase() !== 'true') {
            if (window.App && window.App.modal) {
                window.App.modal.open('tpl-auth-required', (clone) => {
                    const closeBtn = clone.querySelector('.btn--outline');
                    if (closeBtn) closeBtn.onclick = () => window.App.modal.close();
                });
            }
            return;
        }

        const payload = {
            title: this.form.querySelector('[name="title"]').value.trim(),
            description: this.form.querySelector('[name="description"]').value.trim()
        };

        if (!this.validate(payload)) return;

        const originalBtnText = this.btnSubmit.textContent;
        this.btnSubmit.disabled = true;
        this.btnSubmit.innerHTML = `<svg class="spinner" viewBox="0 0 50 50" style="width: 20px; height: 20px; animation: rotate 2s linear infinite; margin: 0 auto;"><circle cx="25" cy="25" r="20" fill="none" stroke="currentColor" stroke-width="4" stroke-dasharray="1, 200" stroke-dashoffset="0" stroke-linecap="round" style="animation: dash 1.5s ease-in-out infinite;"></circle></svg>`;

        try {
            const response = await window.App.api.post(
                '/api/community/suggest/create/',
                payload,
                true,
                { 'X-Requested-With': 'XMLHttpRequest' }
            );

            const data = await response.json();
            if (!response.ok || !data.success) throw new Error(data.message || 'ServerError');

            this.form.style.opacity = '0';
            this.form.style.transform = 'scale(0.95)';
            this.form.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';

            setTimeout(() => {
                const successNode = this.tplSuccess.content.cloneNode(true);
                const parent = this.form.parentElement;
                
                this.form.remove(); 
                parent.appendChild(successNode); 

                if (window.App && window.App.i18n) {
                    window.App.i18n.translateDOM(parent);
                }
            }, 300);

        } catch (error) {
            this.btnSubmit.disabled = false;
            this.btnSubmit.textContent = originalBtnText;
            
            console.error('Submit error:', error);
            const sysErrNode = document.getElementById('form-system-error');
            sysErrNode.textContent = 'Системная ошибка. Попробуйте позже.';
            sysErrNode.style.display = 'block';
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('.comm-layout')) {
        new CommunityClipboard();
        new IdeasFeed();
        new IdeasForm();
        new ChangelogFeed();
    }
});