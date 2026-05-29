// Configuration file for the app
// Update SERVER_URL with your Linux server's IP address on the VPN

export const CONFIG = {
  // Replace with your server's IP address
  // Example: 'http://192.168.1.100:5000'
  SERVER_URL: 'http://YOUR_SERVER_IP:5000',
  
  // API endpoints
  API: {
    BOOKS: '/api/books',
    HEALTH: '/api/health',
  },
};

export default CONFIG;
