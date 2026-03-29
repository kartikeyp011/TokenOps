const BASE_URL = 'http://localhost:8000/api';
const PROXY_URL = 'http://localhost:8000/v1/chat/completions';

// Fallback Mock Data for UI/UX demonstration
const mockMode = false;

const generateTimeLabels = (count) => {
    const labels = [];
    const now = new Date();
    for (let i = count; i >= 0; i--) {
        const d = new Date(now.getTime() - i * 60000 * 5); // every 5 minutes
        labels.push(`${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`);
    }
    return labels;
};

const mockData = {
    '/dashboard': {
        totalCost: 18450.75,
        totalSavings: 4240.20,
        savedLive: 4240.20,
        chartData: [110, 190, 240, 180, 410, 350, 520, 610, 580, 480, 510, 590],
        chartLabels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    },
    '/usage': {
        models: [
            { name: 'GPT-4o', usage: '55%', cost: 12400 },
            { name: 'Claude-3.5-Sonnet', usage: '25%', cost: 3800 },
            { name: 'GPT-3.5-Turbo', usage: '15%', cost: 1540 },
            { name: 'Gemini-1.5-Pro', usage: '5%', cost: 710 }
        ],
        teams: [
            { name: 'Engineering', usage: '65%', cost: 11992 },
            { name: 'Product', usage: '20%', cost: 3690 },
            { name: 'Marketing', usage: '10%', cost: 1845 },
            { name: 'Sales', usage: '5%', cost: 923 }
        ],
        realtimeUsage: {
            labels: generateTimeLabels(15),
            datasets: [
                { label: 'GPT-4o', data: Array.from({length: 16}, () => Math.floor(Math.random() * 500 + 100)) },
                { label: 'Claude-3.5', data: Array.from({length: 16}, () => Math.floor(Math.random() * 300 + 50)) },
            ]
        }
    },
    '/logs': [
        { id: 'req_8902', prompt: 'Analyze 500MB product database for pricing anomalies...', decision: 'Blocked', reason: 'Context window quota exceeded (Team: Sales)', timestamp: 'Just now' },
        { id: 'req_8901', prompt: 'Summarize candidate interview transcripts...', decision: 'Approved', reason: 'HR Default Policy', timestamp: '1 min ago' },
        { id: 'req_8900', prompt: 'Write a python script to parse JSON logs...', decision: 'Cached', reason: 'Exact match (99.8%) - Semantic Cache Hit', timestamp: '2 mins ago' },
        { id: 'req_8899', prompt: 'Generate French translation for homepage...', decision: 'Approved', reason: 'Marketing Localization Budget', timestamp: '5 mins ago' },
        { id: 'req_8898', prompt: 'Analyze 10GB customer dataset and predict churn...', decision: 'Blocked', reason: 'Hard cost limit reached ($20 req limit)', timestamp: '10 mins ago' },
        { id: 'req_8897', prompt: 'Draft Q3 board meeting talking points...', decision: 'Approved', reason: 'Executive Tier Plan', timestamp: '15 mins ago' },
        { id: 'req_8896', prompt: 'Debug Kubernetes pod crash logs...', decision: 'Approved', reason: 'Engineering Default Plan', timestamp: '17 mins ago' },
        { id: 'req_8895', prompt: 'Debug Kubernetes pod crash logs...', decision: 'Cached', reason: 'Semantic match (95.1%) - Cache Hit', timestamp: '19 mins ago' },
    ],
    '/alerts': [
        { type: 'spike', severity: 'High', message: 'Critical Spend Anomaly: Sales team cost spiked by 400% in the last 15 minutes due to automated batch processing. Fallback rules initiated.', time: 'Just now' },
        { type: 'anomaly', severity: 'Medium', message: 'Pattern Anomaly: Unusually high latency detected from Anthropic Claude-3 Opus endpoint. Auto-failed over to GPT-4o momentarily.', time: '35 mins ago' },
        { type: 'budget', severity: 'High', message: 'Budget Breach: Product Research department reached 95% of their $5,000 monthly allowance.', time: '2 hours ago' },
        { type: 'anomaly', severity: 'Low', message: 'System Notification: Cache hit ratio dropped below 15% for the last hour. Optimization rules might need adjustment.', time: '4 hours ago' }
    ],
    '/policies': [
        { id: 1, name: 'Eng Strict Quota', team: 'Engineering', budget: '$12,000/mo', activeRules: 6, status: 'Active' },
        { id: 2, name: 'Marketing Capped', team: 'Marketing', budget: '$2,000/mo', activeRules: 2, status: 'Active' },
        { id: 3, name: 'Product Research', team: 'Product', budget: '$5,000/mo', activeRules: 4, status: 'Warning' },
        { id: 4, name: 'Sales Auto-block', team: 'Sales', budget: '$500/mo', activeRules: 3, status: 'Active' },
        { id: 5, name: 'Global Rate Limits', team: 'Global (All)', budget: 'N/A', activeRules: 1, status: 'Active' },
        { id: 6, name: 'Semantic Caching Layer', team: 'Global (Cache)', budget: 'N/A', activeRules: 2, status: 'Active' }
    ]
};

async function fetchFromAPI(endpoint, options = {}) {
    if (mockMode) {
        return new Promise((resolve) => {
            setTimeout(() => {
                resolve(mockData[endpoint] || []);
            }, 500); // Simulate network latency
        });
    }

    const apiKey = localStorage.getItem('tokentamer_api_key') || '';
    
    const fetchOptions = {
        ...options,
        headers: {
            'X-API-Key': apiKey,
            'Content-Type': 'application/json',
            ...(options.headers || {})
        }
    };

    try {
        const response = await fetch(`${BASE_URL}${endpoint}`, fetchOptions);
        if (response.status === 401 || response.status === 403) {
            window.location.href = 'login.html';
            throw new Error('Unauthorized');
        }
        if (!response.ok) throw new Error('Network response was not ok');
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        // Return safe defaults if backend fails
        if (endpoint.startsWith('/dashboard')) return { total_cost_today_usd: 0, cost_saved_today_usd: 0, requests_last_hour: [], provider_breakdown: {} };
        if (endpoint.startsWith('/usage')) return { daily_usage: [], model_breakdown: [] };
        if (endpoint.startsWith('/logs')) return { logs: [], total: 0, page: 1, total_pages: 1 };
        if (endpoint.startsWith('/alerts')) return { alerts: [], active_count: 0 };
        if (endpoint.startsWith('/policies')) return { policies: [], total: 0 };
        return {};
    }
}

async function postToAPI(endpoint, body) {
    return fetchFromAPI(endpoint, {
        method: 'POST',
        body: JSON.stringify(body)
    });
}

async function putToAPI(endpoint, body) {
    return fetchFromAPI(endpoint, {
        method: 'PUT',
        body: JSON.stringify(body)
    });
}

async function postProxy(body) {
    const apiKey = localStorage.getItem('tokentamer_api_key') || '';
    const response = await fetch(PROXY_URL, {
        method: 'POST',
        headers: {
            'X-API-Key': apiKey,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(body)
    });
    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || 'Proxy request failed');
    }
    return await response.json();
}
