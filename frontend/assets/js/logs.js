document.addEventListener('DOMContentLoaded', async () => {
    renderSidebar('logs');
    renderNavbar('Token Traffic Logs');

    const content = document.getElementById('logs-content');
    renderLoadingState('logs-content');

    const response = await fetchFromAPI('/logs');
    const logs = response.logs || [];

    let html = `
        <div class="bg-dark-800 border border-dark-700 rounded-xl shadow-xl overflow-hidden mt-2 flex flex-col h-[calc(100vh-140px)]">
            <div class="p-5 border-b border-dark-700 bg-dark-900/40 backdrop-blur-sm flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div class="flex items-center gap-3">
                    <div class="p-2 bg-dark-800 rounded-lg border border-dark-700 shadow-sm text-brand-500">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16"></path></svg>
                    </div>
                    <div>
                        <h3 class="text-lg font-semibold text-white tracking-tight">Recent Decisions</h3>
                        <p class="text-xs text-slate-500">Live feed from TokenOps edge proxy</p>
                    </div>
                </div>
                
                <div class="flex gap-2 w-full sm:w-auto">
                    <div class="relative w-full sm:w-64">
                        <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <svg class="h-4 w-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                        </div>
                        <input type="text" placeholder="Search prompts, IDs..." class="block w-full pl-10 pr-3 py-2 border border-dark-700 rounded-lg leading-5 bg-dark-900/80 text-slate-300 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-brand-500 focus:border-brand-500 sm:text-sm transition-colors">
                    </div>
                    <button class="bg-dark-800 hover:bg-dark-700 text-slate-300 border border-dark-700 p-2 rounded-lg transition-colors" title="Filter list">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"></path></svg>
                    </button>
                </div>
            </div>
            
            <div class="overflow-x-auto flex-grow relative">
                <table class="data-table w-full">
                    <thead class="sticky top-0 bg-dark-900 z-10">
                        <tr>
                            <th class="w-20 hidden md:table-cell">Req ID</th>
                            <th>Prompt Snapshot</th>
                            <th class="w-28 text-center">Decision</th>
                            <th>Policy Triggered</th>
                            <th class="w-32 text-right">Time</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${logs.map(log => `
                            <tr class="group cursor-pointer">
                                <td class="hidden md:table-cell font-mono text-[11px] text-slate-500 truncate max-w-[80px]">${log.id}</td>
                                <td>
                                    <div class="font-mono text-xs text-slate-300 truncate max-w-xs md:max-w-md lg:max-w-xl group-hover:text-white transition-colors">"${log.prompt_preview || log.model_used}"</div>
                                </td>
                                <td class="text-center">
                                    <span class="badge ${getBadgeClass(log.status)} w-full inline-block">${log.status}</span>
                                </td>
                                <td>
                                    <div class="flex items-center text-sm text-slate-400">
                                        <svg class="w-3.5 h-3.5 mr-1.5 opacity-70" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                                        ${log.routing_reason || log.error_message || 'N/A'}
                                    </div>
                                </td>
                                <td class="text-right text-slate-500 text-[11px] font-medium whitespace-nowrap">${formatTimestamp(log.timestamp)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
            
            <div class="p-3 border-t border-dark-700 bg-dark-900/50 flex justify-between items-center text-xs text-slate-500">
                <span>Showing ${logs.length} of ${response.total || 0} requests</span>
                <div class="flex space-x-1">
                    <button class="px-2 py-1 rounded border border-dark-700 hover:bg-dark-800 disabled:opacity-50" disabled>Prev</button>
                    <button class="px-2 py-1 rounded border border-dark-700 bg-dark-800 text-slate-300">1</button>
                    <button class="px-2 py-1 rounded border border-dark-700 hover:bg-dark-800 disabled:opacity-50" disabled>Next</button>
                </div>
            </div>
        </div>
    `;
    content.innerHTML = html;
});
