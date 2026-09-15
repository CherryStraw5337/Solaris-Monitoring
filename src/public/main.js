'use strict';

const READINGS_LIMIT = 500;
const CELL_TIMELINE_LIMIT = 100;
const MODAL_READINGS_LIMIT = 10;

const TAB_TITLES = {
    overview: 'Vista general del sistema',
    cells: 'Celdas fotovoltaicas',
    analytics: 'Análisis de eficiencia',
    alerts: 'Lecturas anómalas',
    service: 'Estado del servicio',
    project: 'Proyecto y equipo',
};

const PERIOD_LABELS = { 1: 'Últimas 24 h', 7: 'Últimos 7 días', 30: 'Últimos 30 días' };

const NAV_BASE = 'nav-btn w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl font-medium text-sm transition-all';
const NAV_IDLE = `${NAV_BASE} text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent`;
const NAV_ACTIVE = `${NAV_BASE} bg-amber-500/10 text-amber-400 border border-amber-500/30`;

const STATUS_META = {
    ok: { label: 'Óptima', dot: 'bg-emerald-400', text: 'text-emerald-400', card: 'border-emerald-500/40 bg-emerald-500/10 hover:border-emerald-500' },
    warning: { label: 'Con anomalías', dot: 'bg-amber-400', text: 'text-amber-400', card: 'border-amber-500/50 bg-amber-500/10 hover:border-amber-500' },
    critical: { label: 'Última lectura anómala', dot: 'bg-red-400', text: 'text-red-400', card: 'border-red-500/60 bg-red-500/10 hover:border-red-500 cell-pulse' },
    nodata: { label: 'Sin datos en el período', dot: 'bg-slate-500', text: 'text-slate-400', card: 'border-slate-700 bg-slate-800/40 hover:border-slate-500' },
    inactive: { label: 'Inactiva', dot: 'bg-slate-600', text: 'text-slate-500', card: 'border-slate-800 bg-slate-900/60 opacity-70 hover:border-slate-600' },
};

const CAUSE_META = {
    overvoltage: { label: 'Sobrevoltaje', severity: 'Crítica', badge: 'bg-red-500/10 text-red-400 border-red-500/30', icon: 'fa-circle-exclamation text-red-400' },
    low_efficiency: { label: 'Baja eficiencia', severity: 'Advertencia', badge: 'bg-amber-500/10 text-amber-400 border-amber-500/30', icon: 'fa-triangle-exclamation text-amber-400' },
    unknown: { label: 'Anomalía registrada', severity: 'Advertencia', badge: 'bg-amber-500/10 text-amber-400 border-amber-500/30', icon: 'fa-triangle-exclamation text-amber-400' },
};

const state = {
    tab: 'overview',
    days: 7,
    pollMs: 30000,
    live: true,
    timerId: null,
    loading: false,
    health: null,
    cells: [],
    summaries: new Map(),
    readings: [],
    selectedCellId: null,
    timeline: [],
    alertFilter: 'all',
    lastUpdated: null,
};

const charts = { timeline: null, efficiency: null, voltageRange: null, anomalyCause: null };

// ---------- utilidades ----------

function escapeHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function $(id) {
    return document.getElementById(id);
}

function fmt(value, digits = 2) {
    return Number.isFinite(value) ? value.toFixed(digits) : '—';
}

function formatDate(iso) {
    return new Date(iso).toLocaleString('es-MX', { dateStyle: 'short', timeStyle: 'medium' });
}

function formatShortTime(iso) {
    return new Date(iso).toLocaleString('es-MX', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
}

function timeAgo(iso) {
    const seconds = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 1000));
    if (seconds < 60) return 'hace unos segundos';
    const minutes = Math.round(seconds / 60);
    if (minutes < 60) return `hace ${minutes} min`;
    const hours = Math.round(minutes / 60);
    if (hours < 24) return `hace ${hours} h`;
    return `hace ${Math.round(hours / 24)} d`;
}

async function getJson(path, { allowNotFound = false } = {}) {
    const response = await fetch(path, { headers: { Accept: 'application/json' } });
    if (allowNotFound && response.status === 404) return null;
    if (!response.ok) throw new Error(`${path} respondió ${response.status}`);
    return response.json();
}

function cellById(cellId) {
    return state.cells.find((cell) => cell.id === cellId);
}

function latestReadingOf(cellId) {
    // La API devuelve las lecturas de la más reciente a la más antigua.
    return state.readings.find((reading) => reading.cell_id === cellId);
}

function anomalyCauses(reading, cell) {
    if (!reading.is_anomaly) return [];
    const causes = [];
    if (cell && reading.voltage_measured > cell.max_safe_voltage) causes.push('overvoltage');
    if (cell && reading.efficiency_percentage < cell.efficiency_threshold) causes.push('low_efficiency');
    return causes.length ? causes : ['unknown'];
}

function cellStatus(cell) {
    if (!cell.is_active) return 'inactive';
    const summary = state.summaries.get(cell.id);
    if (!summary) return 'nodata';
    const latest = latestReadingOf(cell.id);
    if (latest && latest.is_anomaly) return 'critical';
    return summary.anomaly_count > 0 ? 'warning' : 'ok';
}

// ---------- carga de datos ----------

async function refresh(manual = false) {
    if (state.loading) return;
    state.loading = true;
    $('refresh-icon').classList.add('animate-spin');

    try {
        const [health, cells, readings] = await Promise.all([
            getJson('/health'),
            getJson('/api/v1/cells'),
            getJson(`/api/v1/readings?limit=${READINGS_LIMIT}`),
        ]);

        const summaries = await Promise.all(
            cells.map((cell) => getJson(`/api/v1/readings/cell/${cell.id}/summary?days=${state.days}`, { allowNotFound: true })),
        );

        state.health = health;
        state.cells = cells;
        state.readings = readings;
        state.summaries = new Map(cells.map((cell, index) => [cell.id, summaries[index]]).filter(([, summary]) => summary));

        if (!cellById(state.selectedCellId)) {
            const withData = cells.find((cell) => state.summaries.has(cell.id));
            state.selectedCellId = (withData || cells[0] || {}).id ?? null;
        }
        state.timeline = await loadTimeline(state.selectedCellId);

        state.lastUpdated = new Date();
        setApiStatus(health.status === 'ok' ? 'online' : 'degraded');
        $('error-banner').classList.add('hidden');
        render();
        if (manual) showToast('Datos actualizados', 'success');
    } catch (error) {
        setApiStatus('offline');
        // fetch lanza TypeError cuando no hay respuesta (servidor caído o sin red).
        const detail = error instanceof TypeError ? 'La API no responde.' : error.message;
        $('error-banner-text').textContent = `${detail} Se muestran los últimos datos cargados.`;
        $('error-banner').classList.remove('hidden');
        if (manual) showToast('No se pudo conectar con la API', 'error');
    } finally {
        state.loading = false;
        $('refresh-icon').classList.remove('animate-spin');
    }
}

async function loadTimeline(cellId) {
    if (cellId === null) return [];
    const rows = await getJson(`/api/v1/readings/cell/${cellId}?limit=${CELL_TIMELINE_LIMIT}`, { allowNotFound: true });
    return (rows || []).slice().reverse();
}

async function selectCell(cellId) {
    state.selectedCellId = cellId;
    try {
        state.timeline = await loadTimeline(cellId);
    } catch (error) {
        state.timeline = [];
        showToast('No se pudieron cargar las lecturas de la celda', 'error');
    }
    renderTimelineChart();
}

// ---------- render ----------

function render() {
    const periodLabel = PERIOD_LABELS[state.days];
    document.querySelectorAll('.period-label').forEach((el) => { el.textContent = periodLabel; });
    $('last-updated-text').textContent = state.lastUpdated ? state.lastUpdated.toLocaleTimeString('es-MX') : '—';

    renderKpis();
    renderCellSelect();
    renderTimelineChart();
    renderEfficiencyChart();
    renderCellStatusList();
    renderQuickEvents();
    renderCellGrid();
    renderAnalytics();
    renderAlerts();
    renderService();
}

function renderKpis() {
    const activeCells = state.cells.filter((cell) => cell.is_active).length;
    const summaries = [...state.summaries.values()];
    const readingCount = summaries.reduce((sum, s) => sum + s.reading_count, 0);
    const anomalyCount = summaries.reduce((sum, s) => sum + s.anomaly_count, 0);
    const weightedEfficiency = readingCount
        ? summaries.reduce((sum, s) => sum + s.avg_efficiency * s.reading_count, 0) / readingCount
        : NaN;

    $('kpi-active-cells').textContent = state.cells.length ? activeCells : '0';
    $('kpi-total-cells').textContent = `/ ${state.cells.length}`;
    const inactive = state.cells.length - activeCells;
    $('kpi-active-cells-note').textContent = inactive ? `${inactive} inactiva(s)` : 'Todas operando';

    $('kpi-avg-efficiency').textContent = fmt(weightedEfficiency, 1);
    $('kpi-reading-count').textContent = readingCount.toLocaleString('es-MX');
    $('kpi-anomaly-count').textContent = anomalyCount.toLocaleString('es-MX');
    $('kpi-anomaly-rate').textContent = readingCount ? `${fmt((anomalyCount / readingCount) * 100, 1)} %` : '';

    const latest = state.readings[0];
    if (latest) {
        const cell = cellById(latest.cell_id);
        $('kpi-last-voltage').textContent = fmt(latest.voltage_measured);
        $('kpi-last-reading-note').textContent = `${cell ? cell.name : `Celda ${latest.cell_id}`} · ${timeAgo(latest.timestamp)}`;
    } else {
        $('kpi-last-voltage').textContent = '—';
        $('kpi-last-reading-note').textContent = 'Sin lecturas todavía';
    }

    const recentAnomalies = state.readings.filter((r) => r.is_anomaly).length;
    $('cell-count-badge').textContent = state.cells.length;
    $('alert-count-badge').textContent = recentAnomalies;
    $('mobile-cell-count').textContent = state.cells.length;
    $('mobile-alert-count').textContent = recentAnomalies > 99 ? '99+' : recentAnomalies;
    $('mobile-alert-count').classList.toggle('hidden', recentAnomalies === 0);
    $('no-cells-notice').classList.toggle('hidden', state.cells.length > 0);
}

function renderCellSelect() {
    const select = $('cell-select');
    select.innerHTML = state.cells.length
        ? state.cells.map((cell) => `<option value="${cell.id}">${escapeHtml(cell.name)}</option>`).join('')
        : '<option value="">Sin celdas</option>';
    if (state.selectedCellId !== null) select.value = String(state.selectedCellId);
}

const GRID_COLOR = 'rgba(255, 255, 255, 0.05)';
const TICK_COLOR = '#64748b';

function chartsAvailable() {
    return typeof window.Chart !== 'undefined';
}

// Mismo corte que el breakpoint md de Tailwind usado en index.html.
function isMobile() {
    return window.matchMedia('(max-width: 767px)').matches;
}

function renderTimelineChart() {
    if (!chartsAvailable()) return;
    const cell = cellById(state.selectedCellId);
    const rows = state.timeline;
    $('timeline-empty').classList.toggle('hidden', rows.length > 0);

    const labels = rows.map((r) => formatShortTime(r.timestamp));
    const pointColors = rows.map((r) => (r.is_anomaly ? '#ef4444' : '#f59e0b'));
    const threshold = rows.map(() => (cell ? cell.efficiency_threshold : null));

    if (!charts.timeline) {
        const compact = isMobile();
        charts.timeline = new Chart($('timelineChart'), {
            type: 'line',
            data: {
                labels,
                datasets: [
                    { label: 'Voltaje (V)', data: [], borderColor: '#f59e0b', backgroundColor: 'rgba(245, 158, 11, 0.1)', borderWidth: 2, fill: true, tension: 0.3, yAxisID: 'y', pointRadius: 3 },
                    { label: 'Eficiencia (%)', data: [], borderColor: '#06b6d4', backgroundColor: 'transparent', borderWidth: 2, tension: 0.3, yAxisID: 'y1', pointRadius: 0 },
                    { label: 'Umbral (%)', data: [], borderColor: '#94a3b8', borderDash: [6, 6], borderWidth: 1, pointRadius: 0, yAxisID: 'y1' },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { color: GRID_COLOR }, ticks: { color: TICK_COLOR, font: { size: compact ? 9 : 10 }, maxTicksLimit: compact ? 4 : 8, maxRotation: 0 } },
                    y: { position: 'left', grid: { color: GRID_COLOR }, ticks: { color: '#f59e0b', font: { size: compact ? 9 : 10 } }, title: { display: !compact, text: 'V', color: '#f59e0b' } },
                    y1: { position: 'right', grid: { drawOnChartArea: false }, ticks: { color: '#06b6d4', font: { size: compact ? 9 : 10 } }, title: { display: !compact, text: '%', color: '#06b6d4' } },
                },
            },
        });
    }

    const chart = charts.timeline;
    chart.data.labels = labels;
    chart.data.datasets[0].data = rows.map((r) => r.voltage_measured);
    chart.data.datasets[0].pointBackgroundColor = pointColors;
    chart.data.datasets[0].pointBorderColor = pointColors;
    chart.data.datasets[0].pointRadius = rows.map((r) => (r.is_anomaly ? 5 : 2));
    chart.data.datasets[1].data = rows.map((r) => r.efficiency_percentage);
    chart.data.datasets[2].data = threshold;
    chart.update();
}

function renderEfficiencyChart() {
    if (!chartsAvailable()) return;
    const cells = state.cells;
    const values = cells.map((cell) => state.summaries.get(cell.id)?.avg_efficiency ?? null);
    const colors = cells.map((cell, i) => {
        if (values[i] === null) return '#475569';
        return values[i] < cell.efficiency_threshold ? '#f59e0b' : '#10b981';
    });

    if (!charts.efficiency) {
        charts.efficiency = new Chart($('efficiencyBarChart'), {
            type: 'bar',
            data: { labels: [], datasets: [{ data: [], backgroundColor: [], borderRadius: 4 }] },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false }, tooltip: { callbacks: { label: (ctx) => `${fmt(ctx.parsed.y, 1)} %` } } },
                scales: {
                    x: { grid: { display: false }, ticks: { color: TICK_COLOR, font: { size: 10 } } },
                    y: { beginAtZero: true, suggestedMax: 100, grid: { color: GRID_COLOR }, ticks: { color: TICK_COLOR, font: { size: 10 } } },
                },
            },
        });
    }

    charts.efficiency.data.labels = cells.map((cell) => cell.name);
    charts.efficiency.data.datasets[0].data = values;
    charts.efficiency.data.datasets[0].backgroundColor = colors;
    charts.efficiency.update();
}

function renderCellStatusList() {
    const container = $('cell-status-list');
    if (!state.cells.length) {
        container.innerHTML = '<p class="text-sm text-slate-500">Sin celdas registradas.</p>';
        return;
    }
    container.innerHTML = state.cells.map((cell) => {
        const status = STATUS_META[cellStatus(cell)];
        const summary = state.summaries.get(cell.id);
        return `
            <button type="button" onclick="openCellModal(${cell.id})" class="text-left bg-slate-950/60 rounded-xl p-4 border border-slate-800 hover:border-slate-600 flex items-center justify-between gap-3 transition-all">
                <div class="min-w-0">
                    <div class="flex items-center gap-2">
                        <span class="w-2.5 h-2.5 rounded-full ${status.dot}"></span>
                        <span class="font-semibold text-sm text-white truncate">${escapeHtml(cell.name)}</span>
                    </div>
                    <p class="text-xs text-slate-400 mt-1 truncate">${escapeHtml(cell.location)}</p>
                </div>
                <div class="text-right shrink-0">
                    <span class="text-sm font-bold ${status.text}">${summary ? `${fmt(summary.avg_efficiency, 1)} %` : '—'}</span>
                    <p class="text-[11px] text-slate-400">${summary ? `${summary.reading_count} lecturas` : 'Sin datos'}</p>
                </div>
            </button>`;
    }).join('');
}

function anomalyRows() {
    return state.readings
        .filter((reading) => reading.is_anomaly)
        .map((reading) => {
            const cell = cellById(reading.cell_id);
            return { reading, cell, causes: anomalyCauses(reading, cell) };
        });
}

function renderQuickEvents() {
    const rows = anomalyRows().slice(0, 8);
    $('quick-events-list').innerHTML = rows.length
        ? rows.map(({ reading, cell, causes }) => {
            const meta = CAUSE_META[causes[0]];
            return `
                <div class="flex items-start gap-2.5 p-2 rounded-lg bg-slate-950/40 border border-slate-800/60 text-xs">
                    <i class="fa-solid ${meta.icon} mt-0.5"></i>
                    <div class="flex-1 min-w-0">
                        <p class="font-medium text-slate-200 truncate">${escapeHtml(cell ? cell.name : `Celda ${reading.cell_id}`)}</p>
                        <p class="text-[11px] text-slate-400">${causes.map((c) => CAUSE_META[c].label).join(' · ')} · ${fmt(reading.voltage_measured)} V</p>
                        <p class="text-[10px] text-slate-500 font-mono">${escapeHtml(timeAgo(reading.timestamp))}</p>
                    </div>
                </div>`;
        }).join('')
        : '<p class="text-xs text-slate-500">Sin anomalías en las últimas lecturas.</p>';
}

function renderCellGrid() {
    const container = $('cell-grid');
    if (!state.cells.length) {
        container.innerHTML = '<p class="text-sm text-slate-500 col-span-full">Sin celdas registradas.</p>';
        return;
    }
    container.innerHTML = state.cells.map((cell) => {
        const statusKey = cellStatus(cell);
        const status = STATUS_META[statusKey];
        const latest = latestReadingOf(cell.id);
        const summary = state.summaries.get(cell.id);
        return `
            <button type="button" onclick="openCellModal(${cell.id})" class="active-touch text-left border rounded-xl p-2.5 md:p-4 transition-all duration-200 flex flex-col gap-2 md:gap-3 min-w-0 ${status.card}">
                <div class="min-w-0 w-full">
                    <p class="font-bold text-xs md:text-sm text-white truncate">${escapeHtml(cell.name)}</p>
                    <p class="text-[9px] md:text-[10px] font-semibold uppercase tracking-wide truncate ${status.text}">${status.label}</p>
                    <p class="text-[10px] md:text-[11px] text-slate-400 mt-1 truncate"><i class="fa-solid fa-location-dot mr-1"></i>${escapeHtml(cell.location)}</p>
                </div>
                <div>
                    <span class="text-base md:text-2xl font-bold tracking-tight text-white">${latest ? fmt(latest.voltage_measured) : '—'} <small class="text-[10px] md:text-xs font-normal text-slate-400">V</small></span>
                    <p class="text-[10px] md:text-[11px] text-slate-400 truncate">${latest ? `${fmt(latest.efficiency_percentage, 1)} % · ${escapeHtml(timeAgo(latest.timestamp))}` : 'Sin lecturas recientes'}</p>
                </div>
                <div class="w-full flex items-center justify-between gap-1 text-[9px] md:text-[11px] text-slate-400 pt-1.5 md:pt-2 border-t border-slate-800/60">
                    <span class="truncate">Nom. ${fmt(cell.rated_voltage)} V</span>
                    <span class="whitespace-nowrap">${summary ? `${summary.anomaly_count} anom.` : '—'}</span>
                </div>
            </button>`;
    }).join('');
}

function renderAnalytics() {
    const cells = state.cells;
    const summaries = cells.map((cell) => state.summaries.get(cell.id) || null);

    $('summary-table-body').innerHTML = cells.length
        ? cells.map((cell, i) => {
            const s = summaries[i];
            const effClass = s && s.avg_efficiency < cell.efficiency_threshold ? 'text-amber-400' : 'text-emerald-400';
            return `
                <tr class="hover:bg-slate-800/30">
                    <td class="py-3 px-3 font-semibold text-white">${escapeHtml(cell.name)}</td>
                    <td class="py-3 px-3 text-right text-slate-300">${s ? s.reading_count : 0}</td>
                    <td class="py-3 px-3 text-right font-mono text-slate-300">${s ? fmt(s.min_voltage) : '—'}</td>
                    <td class="py-3 px-3 text-right font-mono text-slate-300">${s ? fmt(s.avg_voltage) : '—'}</td>
                    <td class="py-3 px-3 text-right font-mono text-slate-300">${s ? fmt(s.max_voltage) : '—'}</td>
                    <td class="py-3 px-3 text-right font-mono text-slate-400">${fmt(cell.rated_voltage)}</td>
                    <td class="py-3 px-3 text-right font-mono ${s ? effClass : 'text-slate-500'}">${s ? `${fmt(s.avg_efficiency, 1)} %` : '—'}</td>
                    <td class="py-3 px-3 text-right font-mono text-slate-400">${fmt(cell.efficiency_threshold, 0)} %</td>
                    <td class="py-3 px-3 text-right ${s && s.anomaly_count ? 'text-amber-400 font-semibold' : 'text-slate-400'}">${s ? s.anomaly_count : 0}</td>
                </tr>`;
        }).join('')
        : '<tr><td colspan="9" class="py-6 text-center text-slate-500">Sin celdas registradas.</td></tr>';

    $('summary-cards').innerHTML = cells.length
        ? cells.map((cell, i) => {
            const s = summaries[i];
            const effClass = s && s.avg_efficiency < cell.efficiency_threshold ? 'text-amber-400' : 'text-emerald-400';
            return `
                <div class="p-3 rounded-xl bg-slate-950/70 border border-slate-800/80">
                    <div class="flex items-center justify-between gap-2">
                        <span class="text-xs font-semibold text-white truncate">${escapeHtml(cell.name)}</span>
                        <span class="text-sm font-bold whitespace-nowrap ${s ? effClass : 'text-slate-500'}">${s ? `${fmt(s.avg_efficiency, 1)} %` : 'Sin datos'}</span>
                    </div>
                    <div class="grid grid-cols-3 gap-2 mt-2 text-[10px] text-slate-400">
                        <span>Mín <strong class="block text-slate-200 font-mono">${s ? fmt(s.min_voltage) : '—'} V</strong></span>
                        <span>Prom <strong class="block text-slate-200 font-mono">${s ? fmt(s.avg_voltage) : '—'} V</strong></span>
                        <span>Máx <strong class="block text-slate-200 font-mono">${s ? fmt(s.max_voltage) : '—'} V</strong></span>
                    </div>
                    <p class="mt-2 text-[10px] text-slate-500">
                        ${s ? s.reading_count : 0} lecturas · nominal ${fmt(cell.rated_voltage)} V · umbral ${fmt(cell.efficiency_threshold, 0)} %
                        · <span class="${s && s.anomaly_count ? 'text-amber-400 font-semibold' : ''}">${s ? s.anomaly_count : 0} anomalías</span>
                    </p>
                </div>`;
        }).join('')
        : '<p class="py-4 text-center text-xs text-slate-500">Sin celdas registradas.</p>';

    if (!chartsAvailable()) return;

    if (!charts.voltageRange) {
        charts.voltageRange = new Chart($('voltageRangeChart'), {
            type: 'bar',
            data: {
                labels: [],
                datasets: [
                    { label: 'Mínimo', data: [], backgroundColor: '#0e7490', borderRadius: 4 },
                    { label: 'Promedio', data: [], backgroundColor: '#f59e0b', borderRadius: 4 },
                    { label: 'Máximo', data: [], backgroundColor: '#ef4444', borderRadius: 4 },
                    { label: 'Nominal', data: [], type: 'line', borderColor: '#e2e8f0', borderDash: [6, 6], borderWidth: 1.5, pointRadius: 3, pointBackgroundColor: '#e2e8f0' },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { labels: { color: '#cbd5e1', boxWidth: 12, font: { size: 11 } } } },
                scales: {
                    x: { grid: { display: false }, ticks: { color: TICK_COLOR } },
                    y: { beginAtZero: true, grid: { color: GRID_COLOR }, ticks: { color: TICK_COLOR }, title: { display: true, text: 'V', color: TICK_COLOR } },
                },
            },
        });
    }
    charts.voltageRange.data.labels = cells.map((cell) => cell.name);
    charts.voltageRange.data.datasets[0].data = summaries.map((s) => (s ? s.min_voltage : null));
    charts.voltageRange.data.datasets[1].data = summaries.map((s) => (s ? s.avg_voltage : null));
    charts.voltageRange.data.datasets[2].data = summaries.map((s) => (s ? s.max_voltage : null));
    charts.voltageRange.data.datasets[3].data = cells.map((cell) => cell.rated_voltage);
    charts.voltageRange.update();

    const counts = { overvoltage: 0, low_efficiency: 0, unknown: 0 };
    anomalyRows().forEach(({ causes }) => causes.forEach((cause) => { counts[cause] += 1; }));
    const total = counts.overvoltage + counts.low_efficiency + counts.unknown;
    $('anomaly-cause-empty').classList.toggle('hidden', total > 0);

    if (!charts.anomalyCause) {
        charts.anomalyCause = new Chart($('anomalyCauseChart'), {
            type: 'doughnut',
            data: {
                labels: ['Sobrevoltaje', 'Baja eficiencia', 'Sin causa identificada'],
                datasets: [{ data: [], backgroundColor: ['#ef4444', '#f59e0b', '#64748b'], borderColor: '#0f172a', borderWidth: 2 }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '62%',
                plugins: { legend: { position: 'bottom', labels: { color: '#cbd5e1', boxWidth: 12, font: { size: 11 } } } },
            },
        });
    }
    charts.anomalyCause.data.datasets[0].data = total ? [counts.overvoltage, counts.low_efficiency, counts.unknown] : [];
    charts.anomalyCause.update();
}

function renderAlerts() {
    document.querySelectorAll('.alert-filter').forEach((btn) => {
        const active = btn.dataset.alertFilter === state.alertFilter;
        btn.className = `alert-filter flex-1 md:flex-none whitespace-nowrap px-1.5 md:px-2.5 py-1.5 md:py-1 rounded font-medium transition-all ${active ? 'bg-amber-500 text-slate-950' : 'text-slate-400 hover:text-slate-200'}`;
    });

    const rows = anomalyRows().filter(({ causes }) => state.alertFilter === 'all' || causes.includes(state.alertFilter));

    $('alerts-feed').innerHTML = rows.length
        ? rows.map(({ reading, cell, causes }) => {
            const primary = CAUSE_META[causes[0]];
            return `
                <div class="p-3 rounded-xl bg-slate-950/70 border border-slate-800/80 flex items-start gap-2.5">
                    <i class="fa-solid ${primary.icon} mt-0.5"></i>
                    <div class="flex-1 min-w-0">
                        <div class="flex items-baseline justify-between gap-2">
                            <span class="text-xs font-bold text-slate-200 truncate">${escapeHtml(cell ? cell.name : `Celda ${reading.cell_id}`)}</span>
                            <span class="text-[10px] text-slate-500 font-mono whitespace-nowrap">${escapeHtml(timeAgo(reading.timestamp))}</span>
                        </div>
                        <p class="text-[11px] text-slate-400 mt-0.5">${causes.map((c) => CAUSE_META[c].label).join(' · ')}</p>
                        <div class="flex items-center gap-2 mt-1.5">
                            <span class="px-1.5 py-0.5 rounded-full text-[9px] font-semibold border ${primary.badge}">${primary.severity.toUpperCase()}</span>
                            <span class="text-[11px] font-mono text-amber-400">${fmt(reading.voltage_measured)} V</span>
                            <span class="text-[11px] font-mono text-slate-400">${fmt(reading.efficiency_percentage, 1)} %</span>
                        </div>
                    </div>
                </div>`;
        }).join('')
        : `<p class="py-4 text-center text-xs text-slate-500">Sin anomalías en las últimas ${READINGS_LIMIT} lecturas.</p>`;
    $('alerts-table-body').innerHTML = rows.length
        ? rows.map(({ reading, cell, causes }) => {
            const primary = CAUSE_META[causes[0]];
            return `
                <tr class="hover:bg-slate-800/30">
                    <td class="py-3 px-4"><span class="px-2 py-0.5 rounded-full text-[10px] font-semibold border ${primary.badge}">${primary.severity.toUpperCase()}</span></td>
                    <td class="py-3 px-4 font-semibold text-white">${escapeHtml(cell ? cell.name : `Celda ${reading.cell_id}`)}</td>
                    <td class="py-3 px-4 text-slate-300">${causes.map((c) => CAUSE_META[c].label).join(' · ')}</td>
                    <td class="py-3 px-4 text-right font-mono text-amber-400">${fmt(reading.voltage_measured)} V</td>
                    <td class="py-3 px-4 text-right font-mono text-slate-300">${fmt(reading.efficiency_percentage, 1)} %</td>
                    <td class="py-3 px-4 text-slate-400 font-mono whitespace-nowrap">${escapeHtml(formatDate(reading.timestamp))}</td>
                </tr>`;
        }).join('')
        : `<tr><td colspan="6" class="py-6 text-center text-slate-500">Sin anomalías en las últimas ${READINGS_LIMIT} lecturas.</td></tr>`;
}

function renderService() {
    const health = state.health;
    if (!health) return;
    const ok = health.status === 'ok';
    $('service-status').innerHTML = `<span class="${ok ? 'text-emerald-400' : 'text-amber-400'}">${ok ? 'Operativo' : 'Degradado'}</span>`;
    $('service-commit').textContent = health.commit ? String(health.commit).slice(0, 12) : '—';
    $('service-branch').textContent = health.branch || '—';
    $('service-update-date').textContent = health.update_date || '—';
    $('service-message').textContent = health.message || '';
    $('json-debugger').textContent = JSON.stringify(health, null, 2);
}

function setApiStatus(status) {
    const badge = $('api-status-badge');
    const styles = {
        online: ['text-emerald-400 bg-emerald-500/10 border-emerald-500/20', 'bg-emerald-400 animate-ping', 'En línea'],
        degraded: ['text-amber-400 bg-amber-500/10 border-amber-500/20', 'bg-amber-400', 'Degradado'],
        offline: ['text-red-400 bg-red-500/10 border-red-500/20', 'bg-red-400', 'Sin conexión'],
    };
    const [classes, dot, label] = styles[status];
    badge.className = `flex items-center gap-1.5 text-xs font-medium px-2 py-0.5 rounded-full border ${classes}`;
    badge.innerHTML = `<span class="w-1.5 h-1.5 rounded-full ${dot}"></span> ${label}`;
    $('mobile-status-dot').className = `w-1.5 h-1.5 rounded-full ${dot.replace(' animate-ping', ' animate-pulse')}`;
    $('mobile-status-text').textContent = status === 'online' && state.lastUpdated
        ? `${label} · ${state.lastUpdated.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' })}`
        : label;
}

// ---------- detalle de celda ----------

async function openCellModal(cellId) {
    const cell = cellById(cellId);
    if (!cell) return;
    const statusKey = cellStatus(cell);
    const status = STATUS_META[statusKey];
    const summary = state.summaries.get(cell.id);

    $('modal-cell-badge').textContent = `#${cell.id}`;
    $('modal-cell-title').textContent = cell.name;
    $('modal-cell-subtitle').textContent = `${cell.location} · ${status.label}`;
    $('modal-cell-body').innerHTML = `
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
            ${statBox('V nominal', `${fmt(cell.rated_voltage)} V`, 'text-white')}
            ${statBox('V máx. seguro', `${fmt(cell.max_safe_voltage)} V`, 'text-red-400')}
            ${statBox('Umbral eficiencia', `${fmt(cell.efficiency_threshold, 0)} %`, 'text-cyan-400')}
            ${statBox('Estado', cell.is_active ? 'Activa' : 'Inactiva', cell.is_active ? 'text-emerald-400' : 'text-slate-400')}
        </div>
        <h4 class="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">${PERIOD_LABELS[state.days]}</h4>
        ${summary ? `
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
                ${statBox('Lecturas', summary.reading_count, 'text-white')}
                ${statBox('Eficiencia prom.', `${fmt(summary.avg_efficiency, 1)} %`, summary.avg_efficiency < cell.efficiency_threshold ? 'text-amber-400' : 'text-emerald-400')}
                ${statBox('V mín / máx', `${fmt(summary.min_voltage)} / ${fmt(summary.max_voltage)}`, 'text-amber-400')}
                ${statBox('Anomalías', summary.anomaly_count, summary.anomaly_count ? 'text-amber-400' : 'text-white')}
            </div>
            <div class="space-y-2 mb-5">
                <div class="flex justify-between text-xs text-slate-300">
                    <span>Eficiencia promedio frente al 100 % nominal</span>
                    <strong>${fmt(summary.avg_efficiency, 1)} %</strong>
                </div>
                <div class="w-full bg-slate-950 h-2 rounded-full overflow-hidden border border-slate-800">
                    <div class="${summary.avg_efficiency < cell.efficiency_threshold ? 'bg-amber-500' : 'bg-emerald-500'} h-full" style="width: ${Math.min(100, Math.max(0, summary.avg_efficiency)).toFixed(1)}%"></div>
                </div>
            </div>` : '<p class="text-sm text-slate-500 mb-5">Sin lecturas en el período.</p>'}
        <h4 class="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Últimas lecturas</h4>
        <div id="modal-readings" class="text-xs text-slate-500">Cargando…</div>`;

    const modal = $('cell-modal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');

    try {
        const rows = await getJson(`/api/v1/readings/cell/${cell.id}?limit=${MODAL_READINGS_LIMIT}`, { allowNotFound: true });
        // En móvil la fecha sin segundos deja espacio para la columna de estado.
        const formatWhen = isMobile() ? formatShortTime : formatDate;
        $('modal-readings').innerHTML = rows && rows.length
            ? `<div class="overflow-x-auto"><table class="w-full text-left text-[11px] md:text-xs">
                <thead><tr class="text-slate-400 border-b border-slate-800"><th class="py-2 pr-2 md:pr-3">Fecha</th><th class="py-2 pr-2 md:pr-3 text-right">Voltaje</th><th class="py-2 pr-2 md:pr-3 text-right">Efic.</th><th class="py-2">Estado</th></tr></thead>
                <tbody class="divide-y divide-slate-800/60">${rows.map((r) => `
                    <tr><td class="py-2 pr-2 md:pr-3 font-mono text-slate-400 whitespace-nowrap">${escapeHtml(formatWhen(r.timestamp))}</td>
                        <td class="py-2 pr-3 text-right font-mono text-slate-200">${fmt(r.voltage_measured)} V</td>
                        <td class="py-2 pr-3 text-right font-mono text-slate-200">${fmt(r.efficiency_percentage, 1)} %</td>
                        <td class="py-2 ${r.is_anomaly ? 'text-red-400' : 'text-emerald-400'}">${r.is_anomaly ? anomalyCauses(r, cell).map((c) => CAUSE_META[c].label).join(' · ') : 'Normal'}</td></tr>`).join('')}
                </tbody></table></div>`
            : 'Sin lecturas registradas.';
    } catch (error) {
        $('modal-readings').textContent = 'No se pudieron cargar las lecturas.';
    }
}

function statBox(label, value, valueClass) {
    return `
        <div class="p-3 bg-slate-950/70 rounded-xl border border-slate-800">
            <span class="text-[10px] text-slate-400 uppercase font-semibold">${escapeHtml(label)}</span>
            <p class="text-base font-bold mt-0.5 ${valueClass}">${escapeHtml(value)}</p>
        </div>`;
}

function closeCellModal() {
    const modal = $('cell-modal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
}

// ---------- controles ----------

function switchTab(tabId) {
    const changed = state.tab !== tabId;
    state.tab = tabId;
    document.querySelectorAll('.tab-content').forEach((el) => el.classList.add('hidden'));
    $(`tab-${tabId}`).classList.remove('hidden');
    document.querySelectorAll('.nav-btn').forEach((btn) => {
        btn.className = btn.dataset.tab === tabId ? NAV_ACTIVE : NAV_IDLE;
    });
    document.querySelectorAll('.nav-btn, .mobile-nav-btn').forEach((btn) => {
        btn.setAttribute('aria-current', btn.dataset.tab === tabId ? 'page' : 'false');
    });
    $('page-title').textContent = TAB_TITLES[tabId];
    closeMobileSheet();
    if (changed) document.querySelector('main').scrollTop = 0;
    // Chart.js no mide bien un canvas creado dentro de una pestaña oculta.
    requestAnimationFrame(() => Object.values(charts).forEach((chart) => chart && chart.resize()));
}

function openMobileSheet() {
    const sheet = $('mobile-sheet');
    sheet.classList.remove('hidden');
    sheet.classList.add('flex');
}

function closeMobileSheet() {
    const sheet = $('mobile-sheet');
    sheet.classList.add('hidden');
    sheet.classList.remove('flex');
}

const STREAM_BTN_BASE = 'active-touch flex items-center justify-center gap-2 w-9 h-9 md:w-auto md:h-auto md:px-3 md:py-1.5 rounded-lg text-xs font-semibold border transition-all';

function toggleStreaming() {
    state.live = !state.live;
    const btn = $('toggle-stream-btn');
    if (state.live) {
        btn.className = `${STREAM_BTN_BASE} bg-emerald-500/10 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20`;
        $('stream-btn-icon').className = 'fa-solid fa-pause';
        $('stream-btn-text').textContent = 'En vivo';
        refresh();
        showToast('Actualización automática reanudada', 'success');
    } else {
        btn.className = `${STREAM_BTN_BASE} bg-amber-500/10 border-amber-500/30 text-amber-400 hover:bg-amber-500/20`;
        $('stream-btn-icon').className = 'fa-solid fa-play';
        $('stream-btn-text').textContent = 'Pausado';
        showToast('Actualización automática pausada', 'info');
    }
}

function startPolling() {
    clearInterval(state.timerId);
    state.timerId = setInterval(() => {
        if (state.live && !document.hidden) refresh();
    }, state.pollMs);
    $('polling-rate-text').textContent = state.pollMs >= 60000 ? `${state.pollMs / 60000} min` : `${state.pollMs / 1000} s`;
}

function exportReadingsCsv() {
    if (!state.readings.length) {
        showToast('No hay lecturas para exportar', 'info');
        return;
    }
    const quote = (value) => `"${String(value).replace(/"/g, '""')}"`;
    const header = 'id,celda,voltaje_v,eficiencia_pct,anomalia,timestamp_utc';
    const lines = state.readings.map((r) => {
        const cell = cellById(r.cell_id);
        return [r.id, quote(cell ? cell.name : r.cell_id), r.voltage_measured, r.efficiency_percentage, r.is_anomaly, r.timestamp].join(',');
    });
    const blob = new Blob([`${header}\n${lines.join('\n')}\n`], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `lecturas_solaris_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    showToast(`${state.readings.length} lecturas exportadas`, 'success');
}

function showToast(message, type = 'info') {
    const styles = {
        success: ['bg-emerald-900/90 border-emerald-500 text-emerald-200', 'fa-circle-check'],
        error: ['bg-red-900/90 border-red-500 text-red-200', 'fa-circle-xmark'],
        info: ['bg-slate-800/90 border-slate-700 text-slate-200', 'fa-circle-info'],
    };
    const [classes, icon] = styles[type] || styles.info;
    const toast = document.createElement('div');
    toast.className = `px-4 py-2.5 rounded-xl border shadow-xl text-xs font-medium backdrop-blur flex items-center gap-2 ${classes}`;
    toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${escapeHtml(message)}</span>`;
    $('toast-container').appendChild(toast);
    setTimeout(() => toast.remove(), 3500);
}

// ---------- arranque ----------

document.addEventListener('DOMContentLoaded', () => {
    $('api-origin-text').textContent = window.location.origin;

    // Barra lateral (escritorio), barra inferior y panel de opciones (móvil).
    document.querySelectorAll('button[data-tab]').forEach((btn) => btn.addEventListener('click', () => switchTab(btn.dataset.tab)));
    document.querySelectorAll('.alert-filter').forEach((btn) => btn.addEventListener('click', () => {
        state.alertFilter = btn.dataset.alertFilter;
        renderAlerts();
    }));

    // Hay un selector de período en el encabezado (escritorio) y otro en el panel (móvil).
    document.querySelectorAll('.period-select').forEach((select) => select.addEventListener('change', (event) => {
        state.days = Number(event.target.value);
        document.querySelectorAll('.period-select').forEach((other) => { other.value = event.target.value; });
        refresh();
    }));
    $('cell-select').addEventListener('change', (event) => selectCell(Number(event.target.value)));
    $('polling-select').addEventListener('change', (event) => {
        state.pollMs = Number(event.target.value);
        startPolling();
        showToast('Frecuencia de actualización guardada', 'success');
    });
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            closeCellModal();
            closeMobileSheet();
        }
    });

    if (!chartsAvailable()) showToast('No se pudo cargar Chart.js: las gráficas no estarán disponibles', 'error');

    switchTab('overview');
    refresh();
    startPolling();
});
