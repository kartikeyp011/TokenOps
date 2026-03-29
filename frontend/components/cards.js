function renderCard(title, value, subtitle, trend = null, trendUp = true) {
    const trendConfig = trend !== null ? {
        class: trendUp ? 'text-teal-400' : 'text-red-400',
        bg: trendUp ? 'bg-teal-400/10' : 'bg-red-400/10',
        icon: trendUp ? '↑' : '↓',
        text: trendUp ? `+${trend}%` : `-${trend}%`
    } : null;
    
    return `
        <div class="bg-dark-800 border border-dark-700 rounded-xl p-6 shadow-xl hover:shadow-brand-500/5 hover:border-dark-600 transition-all duration-300 relative overflow-hidden group">
            <div class="absolute inset-0 bg-gradient-to-br from-brand-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            
            <div class="flex justify-between items-start mb-4 relative z-10">
                <h3 class="text-slate-400 text-sm font-medium tracking-wide">${title}</h3>
                ${trendConfig ? `
                    <div class="flex items-center px-2 py-0.5 rounded-md ${trendConfig.bg} ${trendConfig.class} text-xs font-semibold">
                        <span>${trendConfig.icon}</span>
                        <span class="ml-1">${trendConfig.text}</span>
                    </div>
                ` : ''}
            </div>
            
            <div class="relative z-10">
                <span class="text-3xl font-bold text-white tracking-tight">${value}</span>
            </div>
            
            ${subtitle ? `
                <div class="mt-3 flex items-center text-xs text-slate-500 relative z-10">
                    <svg class="w-3.5 h-3.5 mr-1 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                    ${subtitle}
                </div>
            ` : ''}
        </div>
    `;
}
