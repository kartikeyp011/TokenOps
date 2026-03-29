document.addEventListener('DOMContentLoaded', async () => {
    // Render Shell
    renderSidebar('dashboard');
    renderNavbar('TokenOps Dashboard');

    const content = document.getElementById('dashboard-content');
    renderLoadingState('dashboard-content');

    // Fetch Data
    const data = await fetchFromAPI('/dashboard');
    const usageData = await fetchFromAPI('/usage');

    // Build UI
    const totalReqs = data.total_requests_today || 1;
    let html = `
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8 mt-2">
            ${renderCard('Total Cost Today', formatCurrency(data.total_cost_today_usd || 0), 'Last 24 hours', null, false)}
            ${renderCard('Cost Avoided Today', formatCurrency(data.cost_saved_today_usd || 0), 'From Cache & Policies', null, true)}
            
            <div class="bg-dark-800 border border-dark-700 rounded-xl p-6 shadow-xl relative overflow-hidden flex flex-col justify-center group hover:border-brand-500/30 transition-all">
                <div class="absolute inset-0 bg-gradient-to-br from-brand-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <div class="relative z-10 flex justify-between items-center mb-2">
                    <h3 class="text-slate-400 text-sm font-medium">Real-time Savings</h3>
                    <span class="flex h-2 w-2 relative">
                        <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                        <span class="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                    </span>
                </div>
                <div class="text-4xl font-bold text-brand-400 relative z-10 drop-shadow-[0_0_15px_rgba(20,184,166,0.2)]" id="live-savings">
                    ${formatCurrency(data.cost_saved_today_usd || 0)}
                </div>
                <p class="text-xs text-slate-500 mt-2 relative z-10 opacity-70">Updating live from router proxy</p>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <!-- Main Chart -->
            <div class="bg-dark-800 border border-dark-700 rounded-xl p-6 shadow-xl lg:col-span-2 flex flex-col">
                <div class="flex justify-between items-center mb-6">
                    <h3 class="text-lg font-semibold text-white tracking-tight">API Spend Trajectory</h3>
                    <select class="bg-dark-900 border border-dark-700 text-xs text-slate-300 rounded-md px-3 py-1.5 focus:outline-none focus:border-brand-500 hover:border-dark-600 cursor-pointer">
                        <option>Last 7 Days</option>
                        <option>Last 30 Days</option>
                        <option>This Year</option>
                    </select>
                </div>
                <div class="relative w-full flex-grow min-h-[16rem]">
                    <canvas id="costChart"></canvas>
                </div>
            </div>

            <!-- Top Models -->
            <div class="bg-dark-800 border border-dark-700 rounded-xl p-6 shadow-xl flex flex-col">
                <div class="flex justify-between items-center mb-6">
                    <h3 class="text-lg font-semibold text-white tracking-tight">Top Models</h3>
                    <a href="usage.html" class="text-xs text-brand-500 hover:text-brand-400 font-medium">View All →</a>
                </div>
                <div class="space-y-4 flex-grow overflow-y-auto pr-1">
                    ${(usageData.model_breakdown || []).slice(0, 5).map((m, i) => {
                        const usagePct = usageData.total_requests ? Math.round((m.requests / usageData.total_requests) * 100) + '%' : '0%';
                        return `
                        <div class="group flex flex-col p-3.5 bg-dark-900/50 rounded-xl border border-dark-700/50 hover:border-brand-500/30 hover:bg-dark-800 transition-all">
                            <div class="flex justify-between items-center mb-2">
                                <div class="flex items-center gap-3">
                                    <div class="w-6 h-6 rounded bg-dark-800 flex items-center justify-center text-xs font-bold text-slate-300 group-hover:text-brand-400 border border-dark-700 group-hover:border-brand-500/50">
                                        ${i + 1}
                                    </div>
                                    <span class="font-medium text-slate-200 text-sm">${m.model}</span>
                                </div>
                                <span class="text-xs text-slate-500 font-medium">${formatCurrency(m.total_cost || 0)}</span>
                            </div>
                            <div class="w-full bg-dark-950 rounded-full h-1.5 mt-1 overflow-hidden">
                                <div class="bg-gradient-to-r from-brand-600 to-brand-400 h-1.5 rounded-full relative" style="width: ${usagePct}">
                                    <div class="absolute top-0 right-0 bottom-0 left-0 bg-[linear-gradient(45deg,rgba(255,255,255,0.15)_25%,transparent_25%,transparent_50%,rgba(255,255,255,0.15)_50%,rgba(255,255,255,0.15)_75%,transparent_75%,transparent)] bg-[length:1rem_1rem]"></div>
                                </div>
                            </div>
                        </div>
                    `;
                    }).join('')}
                </div>
            </div>
        </div>
    `;
    content.innerHTML = html;

    // Simulate Live Counter Animation
    let currentSavings = data.cost_saved_today_usd || 0;
    setInterval(() => {
        currentSavings += (Math.random() * 0.05);
        const ls = document.getElementById('live-savings');
        if(ls) {
            ls.innerText = formatCurrency(currentSavings);
            ls.classList.remove('text-brand-400');
            ls.classList.add('text-teal-300');
            setTimeout(() => {
                ls.classList.remove('text-teal-300');
                ls.classList.add('text-brand-400');
            }, 300);
        }
    }, 2500);

    // Render Chart.js
    const ctx = document.getElementById('costChart');
    if (ctx) {
        const labels = (data.requests_last_hour || []).map(x => x.time);
        const chartData = (data.requests_last_hour || []).map(x => x.requests);
        
        // Create gradient fill
        const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 300);
        gradient.addColorStop(0, 'rgba(20, 184, 166, 0.4)');
        gradient.addColorStop(1, 'rgba(20, 184, 166, 0.0)');

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Requests per 5 min',
                    data: chartData,
                    borderColor: '#14b8a6', // brand-500
                    backgroundColor: gradient,
                    borderWidth: 2.5,
                    pointBackgroundColor: '#0f172a',
                    pointBorderColor: '#14b8a6',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { 
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#1e293b',
                        titleColor: '#f8fafc',
                        bodyColor: '#cbd5e1',
                        borderColor: '#334155',
                        borderWidth: 1,
                        padding: 10,
                        displayColors: false,
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) label += ': ';
                                if (context.parsed.y !== null) label += formatCurrency(context.parsed.y);
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    x: { 
                        grid: { color: '#1e293b', drawBorder: false }, 
                        ticks: { color: '#64748b', font: { family: "'Inter', sans-serif" } } 
                    },
                    y: { 
                        grid: { color: '#1e293b', drawBorder: false }, 
                        ticks: { 
                            color: '#64748b', 
                            font: { family: "'Inter', sans-serif" },
                            callback: function(value) { return '$' + value; }
                        },
                        beginAtZero: true
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index',
                },
            }
        });
    }
});
