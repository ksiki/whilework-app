class AnalyticsManager {
    constructor() {
        this.charts = {};
        this.isLoading = false;
        
        // Премиальная палитра (от основного фиолетового к акцентным)
        this.colors = ['#7C3AED', '#60A5FA', '#34D399', '#F472B6', '#A78BFA'];
        
        this.isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        this.textColor = this.isDark ? '#94A3B8' : '#6B7280';
        this.gridColor = this.isDark ? '#334155' : '#E5E7EB';
        
        this.init();
    }

    init() {
        this.baseOptions = {
            chart: {
                fontFamily: 'Inter, sans-serif',
                background: 'transparent',
                toolbar: { show: false },
                animations: {
                    enabled: true,
                    easing: 'easeinout',
                    speed: 800,
                    dynamicAnimation: { enabled: true, speed: 350 }
                }
            },
            theme: { mode: this.isDark ? 'dark' : 'light' },
            dataLabels: { enabled: false },
            tooltip: { 
                theme: this.isDark ? 'dark' : 'light',
                y: { formatter: (val) => `${val}` } 
            },
            grid: {
                borderColor: this.gridColor,
                strokeDashArray: 3,
                xaxis: { lines: { show: true } },
                yaxis: { lines: { show: false } },
                padding: { top: 0, right: 0, bottom: 0, left: 10 }
            }
        };
    }

    setLoadingState(isLoading) {
        this.isLoading = isLoading;
        document.querySelectorAll('.analytics-card').forEach(card => {
            isLoading ? card.classList.add('is-loading') : card.classList.remove('is-loading');
        });
    }

    async fetchData(filters = {}) {
        if (this.isLoading) return;
        this.setLoadingState(true);

        try {
            await new Promise(resolve => setTimeout(resolve, 1200));

            const response = await window.App.api.get('/api/analytics/calculate/', { 
                filters: JSON.stringify(filters) 
            });
            
            if (response.ok) {
                const data = await response.json();

                this.renderAll(data);
            } else {
                console.error("Ошибка ответа API аналитики. Статус:", response.status);
            }
        } catch (error) {
            console.error("Ошибка сети или парсинга при загрузке аналитики:", error);
        } finally {
            this.setLoadingState(false);
        }
    }

    renderAll(data) {
        this.renderSkillsChart(data.top_skills);
        this.renderFormatsChart(data.work_formats);
        this.renderExperienceChart(data.experience_funnel);
        this.renderGradesChart(data.grades_distribution);
        this.renderDaysChart(data.vacancies_per_day);
    }

    // 1. Топ навыков (Horizontal Bar с градиентом)
    renderSkillsChart(data) {
        if (!data || !data.length) return;
        const options = {
            ...this.baseOptions,
            series: [{ name: 'Vacancies', data: data.map(i => i.count) }],
            chart: { ...this.baseOptions.chart, type: 'bar', height: 240 },
            colors: [this.colors[0]],
            fill: {
                type: 'gradient',
                gradient: {
                    shade: this.isDark ? 'dark' : 'light',
                    type: 'horizontal',
                    shadeIntensity: 0.5,
                    gradientToColors: [this.colors[1]], 
                    inverseColors: false,
                    opacityFrom: 1,
                    opacityTo: 0.8,
                    stops: [0, 100]
                }
            },
            plotOptions: {
                bar: { 
                    horizontal: true, 
                    borderRadius: 4, 
                    borderRadiusApplication: 'end',
                    barHeight: '60%'
                }
            },
            grid: {
                borderColor: this.gridColor,
                strokeDashArray: 3,
                xaxis: { lines: { show: false } },
                yaxis: { lines: { show: false } },
                padding: { top: -15, right: 15, bottom: -10, left: 0 } 
            },
            xaxis: { 
                categories: data.map(i => i.skill), 
                labels: { show: false },
                axisBorder: { show: false },
                axisTicks: { show: false }
            },
            yaxis: { 
                labels: { 
                    maxWidth: 80,
                    style: { colors: this.textColor, fontWeight: 500 },
                    formatter: function(val) {
                        return val.length > 10 ? val.substring(0, 10) + '...' : val;
                    }
                } 
            }
        };
        this.mountOrUpdateChart('chart-top-skills', options);
    }

    // 2. Форматы работы (Donut с пустым центром)
    renderFormatsChart(data) {
        if (!data || Object.keys(data).length === 0) return;

        const seriesData = Object.keys(data).map(key => ({
            name: key,
            data: [data[key]]
        }));

        const options = {
            ...this.baseOptions,
            series: seriesData,
            chart: {
                ...this.baseOptions.chart,
                type: 'bar',
                height: 100, // Делаем график компактным по высоте
                stacked: true,
                stackType: '100%'
            },
            colors: [this.colors[0], this.colors[1], this.colors[2]],
            fill: {
                type: 'gradient',
                gradient: {
                    shade: this.isDark ? 'dark' : 'light',
                    type: 'vertical',
                    shadeIntensity: 0.3,
                    opacityFrom: 1,
                    opacityTo: 0.85,
                    stops: [0, 100]
                }
            },
            plotOptions: {
                bar: {
                    horizontal: true,
                    borderRadius: 4, // Скругление краев полосы
                }
            },
            grid: { show: false, padding: { top: -20, bottom: -10, left: 0, right: 0 } },
            // Скрываем оси, оставляем только красивую полоску
            xaxis: {
                categories: ['Форматы'],
                labels: { show: false },
                axisBorder: { show: false },
                axisTicks: { show: false }
            },
            yaxis: { show: false },
            legend: { position: 'bottom', labels: { colors: this.textColor } },
            tooltip: {
                theme: this.isDark ? 'dark' : 'light',
                y: { formatter: (val) => val }
            }
        };
        this.mountOrUpdateChart('chart-work-formats', options);
    }

    // 3. Требуемый опыт (Vertical Bar с вертикальным градиентом)
    renderExperienceChart(data) {
        if (!data) return;
        const options = {
            ...this.baseOptions,
            series: [{ name: 'Vacancies', data: Object.values(data) }],
            chart: { ...this.baseOptions.chart, type: 'bar', height: 240 },
            colors: [this.colors[1]],
            fill: {
                type: 'gradient',
                gradient: {
                    shade: 'light',
                    type: 'vertical',
                    shadeIntensity: 0.5,
                    gradientToColors: [this.colors[2]], 
                    opacityFrom: 1,
                    opacityTo: 0.8,
                    stops: [0, 100]
                }
            },
            plotOptions: {
                bar: { 
                    borderRadius: 6, 
                    borderRadiusApplication: 'end',
                    columnWidth: '45%' 
                }
            },
            // НОВОЕ: Убираем отступы сверху и снизу
            grid: {
                borderColor: this.gridColor,
                strokeDashArray: 3,
                xaxis: { lines: { show: false } },
                yaxis: { lines: { show: false } },
                padding: { top: -10, right: 0, bottom: -15, left: 10 }
            },
            xaxis: { 
                categories: Object.keys(data), 
                labels: { 
                    style: { colors: this.textColor },
                    offsetY: -5
                },
                axisBorder: { show: false },
                axisTicks: { show: false }
            },
            yaxis: { 
                show: false 
            }
        };
        this.mountOrUpdateChart('chart-experience-funnel', options);
    }

    // 4. Грейды (Radial Bar - починили проценты)
    renderGradesChart(data) {
        if (!data || Object.keys(data).length === 0) return;

        const options = {
            ...this.baseOptions,
            series: Object.values(data),
            labels: Object.keys(data),
            chart: { 
                ...this.baseOptions.chart, 
                type: 'polarArea', 
                height: 320 
            },
            colors: [this.colors[0], this.colors[1], this.colors[2], this.colors[3], '#F59E0B', '#10B981'], 
            stroke: {
                colors: [this.isDark ? '#1E293B' : '#FFFFFF'],
                width: 1
            },
            fill: {
                type: 'gradient',
                gradient: {
                    shade: this.isDark ? 'dark' : 'light',
                    shadeIntensity: 0.4,
                    opacityFrom: 0.9,
                    opacityTo: 0.7,
                    stops: [0, 100]
                }
            },
            plotOptions: {
                polarArea: {
                    rings: { 
                        strokeWidth: 1, 
                        strokeColor: this.gridColor 
                    },
                    spokes: { 
                        strokeWidth: 0 
                    }
                }
            },
            yaxis: {
                show: false
            },
            legend: { 
                show: true, 
                position: 'bottom', 
                labels: { colors: this.textColor },
                markers: { radius: 12 } 
            },
            tooltip: {
                enabled: true,
                theme: this.isDark ? 'dark' : 'light',
                y: {
                    formatter: function(val) {
                        return val;
                    }
                }
            }
        };
        this.mountOrUpdateChart('chart-grades-distribution', options);
    }

    // 5. Динамика вакансий (Тот самый красивый Area chart)
    renderDaysChart(data) {
        if (!data || !data.length) return;
        const options = {
            ...this.baseOptions,
            series: [{ name: 'Vacancies', data: data.map(i => i.count) }],
            chart: { ...this.baseOptions.chart, type: 'area', height: 220 },
            colors: [this.colors[0]],
            fill: {
                type: 'gradient',
                gradient: {
                    shadeIntensity: 1,
                    opacityFrom: 0.6,
                    opacityTo: 0.05,
                    stops: [0, 90, 100]
                }
            },
            stroke: { curve: 'smooth', width: 3 },
            grid: {
                borderColor: this.gridColor,
                strokeDashArray: 3,
                xaxis: { lines: { show: false } },
                yaxis: { lines: { show: true } },
                padding: { bottom: 0 }
            },
            xaxis: {
                categories: data.map(i => i.day),
                labels: { show: false },
                axisBorder: { show: false },
                axisTicks: { show: false },
                tooltip: { enabled: false }
            },
            yaxis: { labels: { style: { colors: this.textColor } } },
            tooltip: {
                theme: this.isDark ? 'dark' : 'light',
                x: { 
                    show: true
                },
                y: {
                    formatter: (val) => `${val}`
                }
            }
        };
        this.mountOrUpdateChart('chart-vacancies-day', options);
    }

    mountOrUpdateChart(containerId, options) {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (this.charts[containerId]) {
        this.charts[containerId].updateOptions(options);
    } else {
        this.charts[containerId] = new ApexCharts(container, options);
        this.charts[containerId].render().then(() => {
            const observer = new ResizeObserver((entries) => {
                for (let entry of entries) {
                    if (entry.contentRect.width > 0) {
                        window.dispatchEvent(new Event('resize'));
                        observer.disconnect();
                    }
                }
            });
            
            observer.observe(container);
        });
    }
}
}

document.addEventListener('DOMContentLoaded', () => {
    window.AnalyticsSidebar = new AnalyticsManager();
});