function renderSidebar(activeMenu = 'dashboard') {
    const sidebarHTML = `
        <aside class="w-64 bg-dark-900 border-r border-dark-700 h-screen fixed top-0 left-0 hidden md:flex flex-col z-20">
            <div class="h-16 border-b border-dark-700 flex items-center px-6">
                <div class="flex items-center gap-3">
                    <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-blue-600 flex items-center justify-center shadow-lg shadow-brand-500/30">
                        <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                    </div>
                    <span class="text-xl font-bold text-white tracking-tight">TokenOps</span>
                </div>
            </div>
            
            <nav class="flex-1 overflow-y-auto py-6">
                <div class="px-4 mb-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">Main Menu</div>
                <ul class="space-y-1.5 px-3">
                    ${renderNavItem('dashboard', 'Dashboard', 'dashboard.html', activeMenu, `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"></path>`)}
                    ${renderNavItem('usage', 'Usage', 'usage.html', activeMenu, `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>`)}
                    ${renderNavItem('logs', 'Logs', 'logs.html', activeMenu, `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16"></path>`)}
                    ${renderNavItem('alerts', 'Alerts', 'alerts.html', activeMenu, `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"></path>`)}
                    ${renderNavItem('policies', 'Policies', 'policies.html', activeMenu, `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path>`)}
                </ul>
            </nav>
            
            <div class="px-4 py-6 border-t border-dark-700">
                <div class="bg-dark-800 rounded-xl p-4 border border-dark-700">
                    <p class="text-xs text-slate-400 font-medium mb-2">Monthly Budget</p>
                    <div class="w-full bg-dark-900 rounded-full h-1.5 mb-2">
                        <div class="bg-brand-500 h-1.5 rounded-full" style="width: 65%"></div>
                    </div>
                    <p class="text-xs text-slate-300"><span class="font-bold text-white">$12,450</span> / $20,000</p>
                </div>
            </div>
        </aside>
    `;
    const container = document.getElementById('sidebar-container');
    if (container) container.innerHTML = sidebarHTML;
}

function renderNavItem(id, label, href, activeMenu, iconPath) {
    const isActive = id === activeMenu;
    const baseClasses = "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 font-medium text-sm w-full";
    const activeClasses = isActive 
        ? "bg-brand-500/10 text-brand-400 shadow-[inset_2px_0_0_0_#14b8a6]" 
        : "text-slate-400 hover:bg-dark-800 hover:text-slate-200";
    
    return `
        <li>
            <a href="${href}" class="${baseClasses} ${activeClasses}">
                <svg class="w-5 h-5 ${isActive ? 'text-brand-400' : 'text-slate-500'}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    ${iconPath}
                </svg>
                ${label}
            </a>
        </li>
    `;
}
