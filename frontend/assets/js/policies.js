document.addEventListener('DOMContentLoaded', async () => {
    renderSidebar('policies');
    renderNavbar('Governance Hub');

    const content = document.getElementById('policies-content');
    renderLoadingState('policies-content');

    const data = await fetchFromAPI('/policies');
    const policies = data.policies || [];

    window.editPolicy = async function(name, currentValue) {
        const newValue = prompt(`Enter new value for ${name}:`, currentValue);
        if (newValue !== null && newValue !== currentValue) {
            try {
                await putToAPI('/policies/' + name, { value: newValue });
                window.location.reload();
            } catch (e) {
                alert('Failed to update policy');
            }
        }
    };

    let html = `
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 px-2 mt-2 gap-4">
            <div>
                <h2 class="text-xl font-bold text-white tracking-tight">Active Policies</h2>
                <p class="text-sm text-slate-400 mt-1">Manage rules, routing, and access controls.</p>
            </div>
            <button class="bg-brand-600 hover:bg-brand-500 text-white font-medium py-2.5 px-5 rounded-lg shadow-lg shadow-brand-500/20 transition-all flex items-center group">
                <svg class="w-5 h-5 mr-2 group-hover:rotate-90 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
                Create Policy
            </button>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            ${policies.map(p => `
                <div class="bg-dark-800 border ${p.name.includes('budget') ? 'border-amber-500/50' : 'border-dark-700'} rounded-xl p-6 shadow-xl hover:-translate-y-1 hover:shadow-2xl hover:border-brand-500/40 transition-all duration-300 flex flex-col relative overflow-hidden group">
                    <!-- Decorator gradient -->
                    <div class="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
                    
                    <div class="flex justify-between items-start mb-5 relative z-10">
                        <div class="flex items-center gap-3">
                            <div class="w-10 h-10 rounded-lg bg-dark-900 border border-dark-700 flex items-center justify-center text-brand-500 shadow-inner">
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>
                            </div>
                            <div>
                                <h4 class="text-white font-bold text-lg leading-tight tracking-tight hover:text-brand-400 pb-1 cursor-pointer transition-colors">${p.name}</h4>
                            </div>
                        </div>
                    </div>
                    
                    <div class="space-y-4 flex-grow relative z-10">
                        <p class="text-sm text-slate-400 mb-2">${p.description}</p>
                        <div class="bg-dark-900/50 rounded-lg p-3 border border-dark-700/50">
                            <div class="flex justify-between items-center text-sm mb-2">
                                <span class="text-slate-400 flex items-center gap-1.5"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg> Current Value</span>
                                <span class="text-white font-mono bg-dark-950 px-2 py-1 border border-dark-700 rounded">${p.value}</span>
                            </div>
                            <div class="flex justify-between items-center text-sm mt-3 pt-2 border-t border-dark-700/50">
                                <span class="text-slate-400 text-xs">Updated</span>
                                <span class="text-slate-300 text-xs">${formatTimestamp(p.last_updated)}</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="mt-6 pt-5 border-t border-dark-700/50 flex space-x-3 relative z-10 items-center justify-end">
                        <div class="flex space-x-2">
                            <button onclick="editPolicy('${p.name}', '${p.value}')" class="bg-dark-700 hover:bg-dark-600 text-white p-2 rounded-lg transition-colors border border-dark-600" title="Edit Policy">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path></svg>
                            </button>
                        </div>
                    </div>
                </div>
            `).join('')}
            
            <!-- Add New Placeholder -->
            <div class="bg-dark-900 border-2 border-dashed border-dark-700 rounded-xl p-6 flex flex-col items-center justify-center text-slate-500 hover:text-brand-500 hover:border-brand-500/50 hover:bg-brand-500/5 transition-all cursor-pointer group min-h-[280px]">
                <div class="w-16 h-16 rounded-full bg-dark-800 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform shadow-inner">
                    <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path></svg>
                </div>
                <h4 class="font-medium text-lg">Add Custom Policy</h4>
                <p class="text-sm mt-1 opacity-70">Define cost alerts or blocks</p>
            </div>
        </div>
    `;
    content.innerHTML = html;
});
