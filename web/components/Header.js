// Unified Header Component with Logo and Back Button
class Header {
  constructor(options = {}) {
    this.showBack = options.showBack !== false; // Default true
    this.showLogo = options.showLogo !== false; // Default true
    this.backUrl = options.backUrl || 'home.html';
    this.logoUrl = options.logoUrl || 'home.html';
    this.title = options.title || '';
    this.showLogout = options.showLogout !== false; // Default true
  }

  render() {
    let html = '<div class="unified-header">';
    
    // Left side: Back button and Logo
    html += '<div class="header-left">';
    if (this.showBack) {
      html += `<a href="#" class="header-back-btn" onclick="Header.goBack('${this.backUrl}'); return false;">← Back</a>`;
    }
    if (this.showLogo) {
      html += `<a href="${this.logoUrl}" class="header-logo-link"><img src="assets/mmu logo.png" alt="MMU Logo" class="header-logo"></a>`;
    }
    html += '</div>';
    
    // Center: Title (if provided)
    if (this.title) {
      html += `<div class="header-center"><h1>${this.title}</h1></div>`;
    }
    
    // Right side: Logout button
    if (this.showLogout) {
      html += '<div class="header-right">';
      html += '<button class="header-logout-btn" onclick="Header.logout()">Logout</button>';
      html += '</div>';
    }
    
    html += '</div>';
    return html;
  }

  static goBack(targetUrl) {
    // Check if we can go back in history
    if (window.history.length > 1 && document.referrer && !document.referrer.includes('login.html')) {
      // Try to go back, but limit to home.html
      const currentUrl = window.location.pathname;
      if (currentUrl.includes('home.html')) {
        // Already at home, don't go back
        return;
      }
      window.history.back();
    } else {
      // No history or coming from login, go to home
      window.location.href = targetUrl;
    }
  }

  static logout() {
    localStorage.removeItem('user_id');
    localStorage.removeItem('user_type');
    window.location.href = 'login.html';
  }
}

// CSS for unified header
const headerCSS = `
.unified-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
  position: sticky;
  top: 0;
  z-index: 1000;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.header-back-btn {
  padding: 8px 16px;
  background: #6b7280;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  text-decoration: none;
  display: inline-block;
  font-size: 14px;
  font-weight: 500;
  transition: background 0.2s;
}

.header-back-btn:hover {
  background: #4b5563;
}

.header-logo-link {
  display: inline-block;
  height: 40px;
}

.header-logo {
  height: 100%;
  width: auto;
  object-fit: contain;
}

.header-center {
  flex: 1;
  text-align: center;
}

.header-center h1 {
  font-size: 20px;
  color: #111827;
  font-weight: 700;
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
}

.header-logout-btn {
  padding: 8px 16px;
  background: #dc2626;
  color: white;
  border: 2px solid #991b1b;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s;
}

.header-logout-btn:hover {
  background: #b91c1c;
  border-color: #7f1d1d;
}

@media (max-width: 768px) {
  .unified-header {
    padding: 10px 15px;
  }
  
  .header-logo-link {
    height: 30px;
  }
  
  .header-center h1 {
    font-size: 16px;
  }
  
  .header-back-btn,
  .header-logout-btn {
    padding: 6px 12px;
    font-size: 12px;
  }
}
`;

// Inject CSS if not already injected
if (!document.getElementById('header-component-css')) {
  const style = document.createElement('style');
  style.id = 'header-component-css';
  style.textContent = headerCSS;
  document.head.appendChild(style);
}

