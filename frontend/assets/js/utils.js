// Utility functions for TokenOps
const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 2
    }).format(value);
};

const formatNumber = (value) => {
    return new Intl.NumberFormat('en-US').format(value);
};

const getBadgeClass = (status) => {
    switch(status.toLowerCase()) {
        case 'approved':
        case 'active':
            return 'badge-success';
        case 'blocked':
        case 'critical':
        case 'high':
            return 'badge-danger';
        case 'warning':
        case 'medium':
            return 'badge-warning';
        case 'cached':
        case 'neutral':
        case 'low':
            return 'badge-neutral';
        default:
            return 'badge-neutral';
    }
};

const renderLoadingState = (containerId) => {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = `
        <div class="animate-pulse flex flex-col space-y-4">
            <div class="h-32 bg-dark-800 rounded-xl border border-dark-700 w-full"></div>
            <div class="h-64 bg-dark-800 rounded-xl border border-dark-700 w-full"></div>
        </div>
    `;
};

const formatTimestamp = (isoString) => {
    if (!isoString) return 'N/A';
    const date = new Date(isoString);
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) return `Just now`;
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} mins ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
    
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
};
