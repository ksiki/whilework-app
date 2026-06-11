/**
 * list.js
 * Управление списком вакансий: фильтрация, кастомная сортировка,
 * сохранение состояния (localStorage) и бесконечная прокрутка.
 */

class SearchFilter {
    constructor(config) {
        this.input = document.getElementById(config.inputId);
        this.dropdown = document.getElementById(config.dropdownId);
        this.pillsContainer = document.getElementById(config.pillsId);
        this.dropdownTemplate = document.getElementById('dropdown-item-template');
        this.pillTemplate = document.getElementById('pill-tag-template');
        
        this.getItems = config.getItems;
        this.getValue = config.getValue;
        this.getName = config.getName;
        this.onChange = config.onChange;

        this.selectedItems = new Map();

        if (this.input && this.dropdown && this.pillsContainer) {
            this.init();
        }
    }

    init() {
        document.addEventListener('click', (e) => {
            if (!this.input.contains(e.target) && !this.dropdown.contains(e.target)) {
                this.closeDropdown();
            }
        });

        this.input.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase().trim();
            const available = this.getItems().filter(item => 
                this.getName(item).toLowerCase().includes(query) && !this.selectedItems.has(this.getValue(item))
            );
            this.renderDropdown(available);
        });

        this.input.addEventListener('focus', () => {
            if (this.input.value.trim() === '') {
                const available = this.getItems().filter(item => !this.selectedItems.has(this.getValue(item)));
                this.renderDropdown(available);
            }
        });
    }

    renderDropdown(items) {
        this.dropdown.innerHTML = '';
        if (items.length === 0 || this.input.value.trim() === '') {
            this.closeDropdown();
            return;
        }

        items.forEach(item => {
            const val = this.getValue(item);
            const name = this.getName(item);
            const clone = this.dropdownTemplate.content.cloneNode(true);
            const li = clone.querySelector('.dropdown-item');
            
            li.textContent = name;
            li.addEventListener('click', () => {
                this.addPill(val, name);
                this.input.value = '';
                this.closeDropdown();
            });

            this.dropdown.appendChild(clone);
        });

        this.dropdown.classList.add('active');
    }

    addPill(val, name, triggerSave = true) {
        if (this.selectedItems.has(val)) return;
        this.selectedItems.set(val, name);

        const clone = this.pillTemplate.content.cloneNode(true);
        const pill = clone.querySelector('.pill-tag');
        pill.querySelector('.pill-tag__text').textContent = name;

        pill.addEventListener('click', () => {
            this.selectedItems.delete(val);
            pill.remove();
            if (this.onChange) this.onChange();
        });

        this.pillsContainer.appendChild(clone);
        if (triggerSave && this.onChange) this.onChange();
    }

    closeDropdown() {
        this.dropdown.classList.remove('active');
    }

    clear() {
        this.selectedItems.clear();
        this.pillsContainer.innerHTML = '';
    }
}

class CustomSort {
    constructor(onChange) {
        this.dropdown = document.getElementById('custom-sort-dropdown');
        this.header = document.getElementById('custom-sort-header');
        this.valueSpan = document.getElementById('custom-sort-value');
        this.items = document.querySelectorAll('.custom-sort__item');
        this.onChange = onChange;

        if (this.dropdown && this.header) {
            this.init();
        }
    }

    init() {
        this.header.addEventListener('click', (e) => {
            e.stopPropagation();
            this.dropdown.classList.toggle('active');
        });

        document.addEventListener('click', (e) => {
            if (!this.dropdown.contains(e.target)) {
                this.dropdown.classList.remove('active');
            }
        });

        this.items.forEach(item => {
            item.addEventListener('click', () => this.update(item));
        });
    }

    update(item, triggerSave = true) {
        this.items.forEach(i => i.classList.remove('active'));
        item.classList.add('active');

        const newValue = item.dataset.value;
        const newI18n = item.dataset.i18n;
        
        this.valueSpan.dataset.value = newValue;
        if (newI18n) this.valueSpan.dataset.i18n = newI18n;
        this.valueSpan.textContent = item.textContent;

        this.dropdown.classList.remove('active');
        if (triggerSave && this.onChange) this.onChange();
    }
    
    setValue(value) {
         const item = document.querySelector(`.custom-sort__item[data-value="${value}"]`);
         if (item) this.update(item, false);
    }
}

class FilterManager {
    constructor(skillsDb, geoDb, onFilterChange) {
        this.db = { skills: skillsDb, geo: geoDb };
        this.onFilterChange = onFilterChange;
        this.currentGeoCategory = 'regions';
        
        this.initFilters();
        this.initListeners();
    }

    initFilters() {
        this.skillsFilter = new SearchFilter({
            inputId: 'skills-search-input',
            dropdownId: 'skills-dropdown-list',
            pillsId: 'skills-selected-pills',
            getItems: () => this.db.skills,
            getValue: item => item.slug,
            getName: item => item.name,
            onChange: () => this.saveAndTrigger()
        });

        this.geoFilter = new SearchFilter({
            inputId: 'geo-search-input',
            dropdownId: 'geo-dropdown-list',
            pillsId: 'geo-selected-pills',
            getItems: () => this.db.geo[this.currentGeoCategory] || [],
            getValue: item => item,
            getName: item => item,
            onChange: () => this.saveAndTrigger()
        });

        this.sortControl = new CustomSort(() => this.saveAndTrigger());
    }

    initListeners() {
        const geoRadios = document.querySelectorAll('input[name="geo_category"]');
        geoRadios.forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.currentGeoCategory = e.target.value;
                document.getElementById('geo-search-input').value = '';
                this.geoFilter.clear();
                this.saveAndTrigger();
            });
        });

        const boundSave = () => this.saveAndTrigger();
        document.querySelector('.sidebar-filters')?.addEventListener('change', boundSave);
        document.querySelector('.search-filters')?.addEventListener('change', boundSave);
        document.getElementById('main-search-input')?.addEventListener('input', boundSave);

        const expInput = document.getElementById('experience-from-input');
        if (expInput) {
            expInput.addEventListener('input', (e) => {
                e.target.value = e.target.value.replace(/[^0-9]/g, '');
                boundSave();
            });
        }

        const salaryMinInput = document.getElementById('salary-min-input');
        if (salaryMinInput) {
            salaryMinInput.addEventListener('input', (e) => {
                e.target.value = e.target.value.replace(/[^0-9]/g, '');
                boundSave();
            });
        }
    }

    getValues(name) {
        return Array.from(document.querySelectorAll(`input[name="${name}"]:checked`)).map(el => el.value);
    }

    getRadio(name, defaultVal) {
        return document.querySelector(`input[name="${name}"]:checked`)?.value || defaultVal;
    }

    getState() {
        const mainSearch = document.getElementById('main-search-input');
        const sortVal = document.getElementById('custom-sort-value');
        const expInput = document.getElementById('experience-from-input');
        const salaryMinInput = document.getElementById('salary-min-input');

        return {
            search: {
                query: mainSearch ? mainSearch.value.trim() : '',
                fields: this.getValues('search_in')
            },
            sort: sortVal?.dataset.value || 'date',
            experience_from: expInput?.value || '',
            salary_min: salaryMinInput?.value ? parseInt(salaryMinInput.value, 10) : null,
            sources: { mode: this.getRadio('source_mode', 'choose'), items: this.getValues('sources') },
            work_type: { logic: this.getRadio('work_type_logic', 'and'), mode: this.getRadio('work_type_mode', 'choose'), items: this.getValues('work_type') },
            work_format: { logic: this.getRadio('work_format_logic', 'and'), mode: this.getRadio('work_format_mode', 'choose'), items: this.getValues('work_format') },
            grade: { logic: this.getRadio('grade_logic', 'and'), mode: this.getRadio('grade_mode', 'choose'), items: this.getValues('grade') },
            skills: { logic: this.getRadio('skills_logic', 'and'), mode: this.getRadio('skills_mode', 'choose'), items: Array.from(this.skillsFilter.selectedItems.keys()) },
            geo: { category: this.getRadio('geo_category', 'regions'), mode: this.getRadio('geo_mode', 'choose'), items: Array.from(this.geoFilter.selectedItems.keys()) }
        };
    }

    saveAndTrigger() {
        localStorage.setItem('whilework_filters', JSON.stringify(this.getState()));
        if (this.onFilterChange) this.onFilterChange();
    }

    load() {
        const saved = localStorage.getItem('whilework_filters');
        if (!saved) return false;

        try {
            const state = JSON.parse(saved);

            const setRadio = (name, value) => {
                const el = document.querySelector(`input[name="${name}"][value="${value}"]`);
                if (el) el.checked = true;
            };

            const setChecks = (name, values) => {
                document.querySelectorAll(`input[name="${name}"]`).forEach(el => {
                    el.checked = values.includes(el.value);
                });
            };

            if (state.search) {
                const main = document.getElementById('main-search-input');
                if (main) main.value = state.search.query;
                setChecks('search_in', state.search.fields);
            }

            if (state.sort) this.sortControl.setValue(state.sort);
            
            const exp = document.getElementById('experience-from-input');
            if (state.experience_from && exp) exp.value = state.experience_from;

            const salaryMin = document.getElementById('salary-min-input');
            if (state.salary_min && salaryMin) salaryMin.value = state.salary_min;

            if (state.sources) { setRadio('source_mode', state.sources.mode); setChecks('sources', state.sources.items); }
            if (state.work_type) { setRadio('work_type_logic', state.work_type.logic); setRadio('work_type_mode', state.work_type.mode); setChecks('work_type', state.work_type.items); }
            if (state.work_format) { setRadio('work_format_logic', state.work_format.logic); setRadio('work_format_mode', state.work_format.mode); setChecks('work_format', state.work_format.items); }
            if (state.grade) { setRadio('grade_logic', state.grade.logic); setRadio('grade_mode', state.grade.mode); setChecks('grade', state.grade.items); }

            if (state.skills) {
                setRadio('skills_logic', state.skills.logic);
                setRadio('skills_mode', state.skills.mode);
                state.skills.items.forEach(slug => {
                    const skill = this.db.skills.find(s => s.slug === slug);
                    this.skillsFilter.addPill(slug, skill ? skill.name : slug, false);
                });
            }

            if (state.geo) {
                setRadio('geo_category', state.geo.category);
                setRadio('geo_mode', state.geo.mode);
                this.currentGeoCategory = state.geo.category;
                state.geo.items.forEach(item => this.geoFilter.addPill(item, item, false));
            }
            
            return true;
        } catch (e) {
            console.error("Filter load error:", e);
            return false;
        }
    }
}

class VacancyList {
    constructor(filterManager) {
        this.container = document.getElementById('jobs-list-container');
        this.sentinel = document.getElementById('loading-sentinel');
        this.filterManager = filterManager;
        
        this.page = 1;
        this.isLoading = false;
        this.hasMore = true;
        this.debounceTimer = null;

        if (this.container && this.sentinel) {
            this.initObserver();
        }
    }

    async fetch(page, isAppend = false) {
        if (this.isLoading || (!this.hasMore && isAppend)) return;
        this.isLoading = true;

        if (isAppend) {
            this.sentinel.style.visibility = 'visible';
        } else {
            this.container.style.opacity = '0.5';
        }

        try {
            const params = {
                page: page,
                filters: JSON.stringify(this.filterManager.getState())
            };

            const response = await window.App.api.get('/', params, false, {
                'X-Requested-With': 'XMLHttpRequest'
            });

            if (!response.ok) throw new Error('Server error');
            const html = await response.text();

            if (html.trim() === '') {
                this.hasMore = false;
                document.getElementById('no-more-jobs').style.display = 'block'; 
            } else {
                this.page = page;
                this.hasMore = true;
                document.getElementById('no-more-jobs').style.display = 'none'; 
            }

            if (isAppend) {
                this.container.insertAdjacentHTML('beforeend', html);
            } else {
                this.container.innerHTML = html;
            }

            if (html.trim() === '') {
                this.hasMore = false;
            } else {
                this.page = page;
                this.hasMore = true;
            }
            
            if (window.App?.i18n?.translateDOM) {
                window.App.i18n.translateDOM(this.container);
            }

        } catch (e) {
            console.error('Fetch error:', e);
        } finally {
            this.isLoading = false;
            this.sentinel.style.visibility = 'hidden';
            this.container.style.opacity = '1';
        }
    }

    triggerReload() {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => {
            this.hasMore = true;
            this.fetch(1, false);
        }, 300);
    }

    initObserver() {
        const observer = new IntersectionObserver((entries) => {
            if (entries[0].isIntersecting) {
                this.fetch(this.page + 1, true);
            }
        }, { rootMargin: '100px' });

        observer.observe(this.sentinel);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const skillsEl = document.getElementById('skills-data');
    const geoEl = document.getElementById('geo-data');
    
    if (!skillsEl || !geoEl) return;

    const skillsDb = JSON.parse(skillsEl.textContent);
    const geoDb = JSON.parse(geoEl.textContent);

    let vacancyList;
    
    const filterManager = new FilterManager(skillsDb, geoDb, () => {
        if (vacancyList) vacancyList.triggerReload();
    });

    vacancyList = new VacancyList(filterManager);
    
    const hasSavedFilters = filterManager.load();

    if (hasSavedFilters) {
        vacancyList.triggerReload();
    }

    document.body.addEventListener('mousedown', (e) => {
        const link = e.target.closest('.job-card__link');
        if (!link) return;

        const card = link.closest('.job-card');
        if (card && !card.classList.contains('viewed')) {
            card.classList.add('viewed');

            const headerRight = card.querySelector('.job-card__header-right');
            if (headerRight && !headerRight.querySelector('.viewed-status')) {
                const statusSpan = document.createElement('span');
                statusSpan.className = 'viewed-status code-text';
                statusSpan.textContent = '// read';
                
                headerRight.prepend(statusSpan);
            }
        }
    });
});