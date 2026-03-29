function renderNavbar(title = 'Dashboard') {
    const navbarHTML = `
        <header class="bg-dark-900/80 backdrop-blur-md border-b border-dark-700 sticky top-0 z-10 flex items-center justify-between px-8 py-4">
            <div class="flex items-center">
                <h1 class="text-xl font-semibold text-white tracking-tight">${title}</h1>
            </div>
            <div class="flex items-center space-x-6">
                <!-- Status Indicator -->
                <div class="hidden sm:flex items-center space-x-2 text-sm bg-dark-800 px-3 py-1.5 rounded-full border border-dark-700">
                    <span class="flex h-2.5 w-2.5 relative">
                      <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-500 opacity-75"></span>
                      <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-brand-500"></span>
                    </span>
                    <span class="text-slate-300 font-medium text-xs">System Online</span>
                </div>
                
                <!-- Notification Bell -->
                <button class="text-slate-400 hover:text-white transition-colors relative">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"></path></svg>
                    <span class="absolute top-0 right-0 block h-2 w-2 rounded-full bg-red-500 ring-2 ring-dark-900"></span>
                </button>

                <!-- User Profile -->
                <div class="h-9 w-9 rounded-full bg-gradient-to-tr from-brand-500 to-blue-600 flex items-center justify-center text-white font-bold cursor-pointer shadow-lg shadow-brand-500/20 ring-2 ring-dark-700 hover:ring-brand-500 transition-all">
                    A
                </div>
            </div>
        </header>
    `;
    const container = document.getElementById('navbar-container');
    if (container) container.innerHTML = navbarHTML;
}
