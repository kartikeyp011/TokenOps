document.addEventListener('DOMContentLoaded', async () => {
    renderSidebar('alerts');
    renderNavbar('System Alerts');

    const content = document.getElementById('alerts-content');
    renderLoadingState('alerts-content');

    const data = await fetchFromAPI('/alerts');
    const alerts = data.alerts || [];

    // Define resolve function globally
    window.resolveAlert = async function(id, btn) {
        btn.disabled = true;
        btn.innerHTML = 'Resolving...';
        try {
            await postToAPI('/alerts/' + id + '/resolve', {});
            const alertDiv = btn.closest('.bg-dark-800');
            alertDiv.style.opacity = '0.5';
            setTimeout(() => alertDiv.remove(), 300);
        } catch (e) {
            console.error('Failed to resolve alert', e);
            btn.disabled = false;
            btn.innerHTML = 'Dismiss';
        }
    };

    let html = `
        <div class="max-w-4xl mx-auto mt-4 px-2">
            <div class="flex justify-between items-end mb-6">
                <div>
                    <h2 class="text-xl font-bold text-white tracking-tight">Active Incidents</h2>
                    <p class="text-sm text-slate-400 mt-1">Requires your attention or review.</p>
                </div>
                <button class="text-sm text-slate-400 hover:text-white transition-colors flex items-center">
                    <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
                    Mark All Read
                </button>
            </div>
            
            <div class="space-y-4">
                ${alerts.map(a => {
                    const isHigh = a.severity === 'critical' || a.severity === 'High';
                    const isMedium = a.severity === 'warning' || a.severity === 'Medium';
                    const borderClass = isHigh ? 'border-red-500/40' : (isMedium ? 'border-amber-500/40' : 'border-blue-500/40');
                    const bgHover = isHigh ? 'hover:bg-red-500/5' : (isMedium ? 'hover:bg-amber-500/5' : 'hover:bg-blue-500/5');
                    const iconBg = isHigh ? 'bg-red-500/10 text-red-400' : (isMedium ? 'bg-amber-500/10 text-amber-400' : 'bg-blue-500/10 text-blue-400');
                    const isSpike = a.alert_type === 'cost_spike' || a.alert_type === 'surge';
                    const iconSvg = isSpike 
                        ? `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path>`
                        : ((a.alert_type === 'anomaly' || a.alert_type === 'high_error_rate') ? `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path>` 
                        : `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>`);
                    
                    return `
                    <div class="bg-dark-800 border ${borderClass} rounded-xl p-5 shadow-lg flex items-start space-x-4 transition-all ${bgHover} relative overflow-hidden group">
                        ${isHigh ? '<div class="absolute left-0 top-0 bottom-0 w-1 bg-red-500"></div>' : ''}
                        
                        <div class="p-3 rounded-xl mt-1 ${iconBg} shadow-inner">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">${iconSvg}</svg>
                        </div>
                        <div class="flex-grow pl-1">
                            <div class="flex justify-between items-start">
                                <h4 class="text-white font-semibold text-lg hover:text-brand-400 transition-colors cursor-pointer">
                                    ${(a.alert_type || a.type || 'Alert').replace(/_/g, ' ').toUpperCase()}
                                </h4>
                                <span class="badge ${getBadgeClass(a.severity)} text-[10px] uppercase tracking-wider px-2 py-0.5">${a.severity}</span>
                            </div>
                            <p class="text-slate-300 mt-1 text-sm leading-relaxed">${a.message}</p>
                            <div class="flex items-center justify-between mt-4">
                                <span class="text-xs text-slate-500 font-medium flex items-center">
                                    <svg class="w-3.5 h-3.5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                                    ${formatTimestamp(a.timestamp)}
                                </span>
                                <div class="opacity-0 group-hover:opacity-100 transition-opacity flex space-x-2">
                                    <button onclick="resolveAlert(${a.id}, this)" class="text-xs px-3 py-1.5 rounded-lg bg-dark-900 border border-dark-700 text-slate-300 hover:text-white hover:bg-dark-700 transition-colors">Dismiss</button>
                                </div>
                            </div>
                        </div>
                    </div>
                `}).join('')}
            </div>
        </div>
    `;
    content.innerHTML = html;
});
