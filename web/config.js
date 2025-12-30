// API Configuration - automatically detects environment
(function() {
  // Detect if running locally or on cloud
  const hostname = window.location.hostname;
  const protocol = window.location.protocol;
  
  // If localhost or 127.0.0.1, use local API
  // Otherwise, use same origin (cloud deployment)
  let API_BASE;
  if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '') {
    API_BASE = 'http://127.0.0.1:8000';
  } else {
    // Use same origin for cloud deployment
    API_BASE = `${protocol}//${hostname}${window.location.port ? ':' + window.location.port : ''}`;
  }
  
  // Make API_BASE available globally
  window.API_BASE = API_BASE;
  
  console.log('API Base URL:', API_BASE);
})();

