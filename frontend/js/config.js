// Check if the browser is currently looking at localhost
const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';

// Automatically set the correct backend URL based on where the UI is running
const API_BASE_URL = isLocalhost
    ? 'http://localhost:8000'
    : 'https://home-expense-tracker-api.onrender.com';

console.log(`[Config] UI running on ${window.location.hostname}. API set to: ${API_BASE_URL}`);