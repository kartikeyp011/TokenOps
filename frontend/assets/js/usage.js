document.addEventListener('DOMContentLoaded', async () => {
    renderSidebar('usage');
    renderNavbar('Usage Analytics');

    const content = document.getElementById('usage-content');
    renderLoadingState('usage-content');

    const usageData = await fetchFromAPI('/usage');

    let html = `
        <!-- Real-time Request Flow Graph -->
        <div class="bg-dark-800 border border-dark-700 rounded-xl shadow-xl overflow-hidden flex flex-col mt-2 mb-8">
            <div class="p-6 border-b border-dark-700 bg-dark-900/40 backdrop-blur-sm flex justify-between items-center">
                <div>
                    <h3 class="text-lg font-semibold text-white tracking-tight flex items-center gap-2">
                        <span class="flex h-2.5 w-2.5 relative mr-1">
                            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-500 opacity-75"></span>
                            <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-brand-500"></span>
                        </span>
                        Live Traffic & Token Velocity
                    </h3>
                    <p class="text-xs text-slate-500 mt-1">Real-time requests flowing through TokenOps edge proxies</p>
                </div>
                <div class="flex space-x-2">
                    <span class="px-3 py-1 bg-brand-500/10 text-brand-400 border border-brand-500/20 rounded-md text-xs font-medium">GPT-4o</span>
                    <span class="px-3 py-1 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-md text-xs font-medium">Claude-3.5</span>
                </div>
            </div>
            <div class="p-6 relative w-full min-h-[20rem]">
                <canvas id="usageChart"></canvas>
            </div>
        </div>

        <div class="grid grid-cols-1 xl:grid-cols-2 gap-8">
            <!-- Model Usage Box -->
            <div class="bg-dark-800 border border-dark-700 rounded-xl shadow-xl overflow-hidden flex flex-col">
                <div class="p-6 border-b border-dark-700 bg-dark-900/40 backdrop-blur-sm flex justify-between items-center">
                    <h3 class="text-lg font-semibold text-white tracking-tight flex items-center gap-2">
                        <svg class="w-5 h-5 text-brand-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
                        Model Usage Breakdown
                    </h3>
                </div>
                <div class="p-0 overflow-x-auto flex-grow">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>AI Model</th>
                                <th>Request Volume Share</th>
                                <th>Est. Cost</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${(usageData.model_breakdown || []).map(m => {
                                const usagePct = usageData.total_requests ? Math.round((m.requests / usageData.total_requests) * 100) + '%' : '0%';
                                return `
                                <tr>
                                    <td class="font-medium text-slate-200">${m.model}</td>
                                    <td class="min-w-[12rem]">
                                        <div class="flex items-center space-x-3">
                                            <div class="flex-grow bg-dark-900 rounded-full h-2 shadow-inner">
                                                <div class="bg-gradient-to-r ${m.model.includes('Claude') ? 'from-blue-600 to-blue-400' : 'from-brand-600 to-brand-400'} h-2 rounded-full relative" style="width: ${usagePct}"></div>
                                            </div>
                                            <span class="text-xs text-slate-400 w-8 text-right font-medium">${usagePct}</span>
                                        </div>
                                    </td>
                                    <td class="font-semibold tracking-wide ${m.model.includes('Claude') ? 'text-blue-400' : 'text-brand-400'}">${formatCurrency(m.total_cost || 0)}</td>
                                </tr>
                            `;
                            }).join('')}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Team Usage Box -->
            <div class="bg-dark-800 border border-dark-700 rounded-xl shadow-xl overflow-hidden flex flex-col">
                <div class="p-6 border-b border-dark-700 bg-dark-900/40 backdrop-blur-sm flex justify-between items-center">
                    <h3 class="text-lg font-semibold text-white tracking-tight flex items-center gap-2">
                        <svg class="w-5 h-5 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"></path></svg>
                        Daily Usage Summary
                    </h3>
                </div>
                <div class="p-0 overflow-x-auto flex-grow">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Requests</th>
                                <th>Est. Cost</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${(usageData.daily_usage || []).map((t, i) => {
        const gradients = ['from-indigo-600 to-indigo-400', 'from-amber-600 to-amber-400', 'from-emerald-600 to-emerald-400', 'from-rose-600 to-rose-400'];
        const maxReqs = Math.max(...(usageData.daily_usage || []).map(d => d.requests), 1);
        const dailyUsagePct = Math.round((t.requests / maxReqs) * 100) + '%';
        return `
                                <tr>
                                    <td class="font-medium text-slate-200">
                                        <div class="flex items-center gap-2">
                                            <div class="w-2.5 h-2.5 rounded-full ${gradients[i % gradients.length].split(' ')[1].replace('to-', 'bg-')}"></div>
                                            ${t.date}
                                        </div>
                                    </td>
                                    <td class="min-w-[12rem]">
                                        <div class="flex items-center space-x-3">
                                            <div class="flex-grow bg-dark-900 rounded-full h-2 shadow-inner">
                                                <div class="bg-gradient-to-r ${gradients[i % gradients.length]} h-2 rounded-full" style="width: ${dailyUsagePct}"></div>
                                            </div>
                                            <span class="text-xs text-slate-400 w-8 text-right font-medium">${t.requests}</span>
                                        </div>
                                    </td>
                                    <td class="text-slate-300 font-semibold tracking-wide">${formatCurrency(t.cost)}</td>
                                </tr>
                            `}).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
    content.innerHTML = html;

    // Render Realtime Chart.js Graph
    const ctx = document.getElementById('usageChart');
    if (ctx && usageData.daily_usage) {

        let labels = usageData.daily_usage.map(d => d.date);
        let chartData = usageData.daily_usage.map(d => d.requests);
        let chartData2 = usageData.daily_usage.map(d => Math.round(d.cost * 100)); // Just an alternative metric

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Total Requests',
                        data: chartData,
                        borderColor: '#14b8a6', // brand-500
                        backgroundColor: 'rgba(20, 184, 166, 0.1)',
                        borderWidth: 2,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: 'Cost (Cents)',
                        data: chartData2,
                        borderColor: '#3b82f6', // blue-500
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        fill: true,
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: '#1e293b',
                        titleColor: '#f8fafc',
                        bodyColor: '#cbd5e1',
                        borderColor: '#334155',
                        borderWidth: 1,
                        padding: 10
                    }
                },
                scales: {
                    x: {
                        grid: { display: false, drawBorder: false },
                        ticks: { color: '#64748b', font: { family: "'Inter', sans-serif", size: 10 }, maxRotation: 0 }
                    },
                    y: {
                        grid: { color: '#1e293b', drawBorder: false },
                        ticks: { color: '#64748b', font: { family: "'Inter', sans-serif" } },
                        beginAtZero: true
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });
    }
});
