const API_BASE = 'http://127.0.0.1:8000';

let currentTab = 'chatbot';
let selectedFiles = {
    chatbot: null,
    submission: null,
    notification: null
};

// Check if user is logged in and is a teacher
if (!localStorage.getItem('user_id')) {
    window.location.href = 'login.html';
}

const userType = localStorage.getItem('user_type');
if (userType !== 'teacher') {
    alert('Access denied. Teacher access required.');
    window.location.href = 'home.html';
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    setupFileUploads();
    loadPDFLists();
});

function switchTab(tabName) {
    currentTab = tabName;
    
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');
    
    // Load PDF list for current tab
    loadPDFList(tabName);
}

function setupFileUploads() {
    const types = ['chatbot', 'submission', 'notification'];
    
    types.forEach(type => {
        const uploadArea = document.getElementById(`${type}-upload-area`);
        const fileInput = document.getElementById(`${type}-file-input`);
        const fileNameDisplay = document.getElementById(`${type}-file-name`);
        
        // Click to browse
        uploadArea.addEventListener('click', () => fileInput.click());
        
        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFileSelect(files[0], type);
            }
        });
        
        // File input change
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFileSelect(e.target.files[0], type);
            }
        });
    });
}

function handleFileSelect(file, type) {
    if (!file.name.endsWith('.pdf')) {
        showMessage('Please select a PDF file', 'error');
        return;
    }
    
    selectedFiles[type] = file;
    const fileNameDisplay = document.getElementById(`${type}-file-name`);
    fileNameDisplay.textContent = `Selected: ${file.name} (${formatFileSize(file.size)})`;
    
    // Auto upload
    uploadPDF(file, type);
}

async function uploadPDF(file, type) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('pdf_type', type);
    
    // Get user_id from localStorage
    const userId = localStorage.getItem('user_id');
    if (userId) {
        formData.append('user_id', userId);
    }
    
    try {
        showMessage(`Uploading ${file.name}...`, 'success');
        
        const response = await fetch(`${API_BASE}/api/teacher/upload-pdf`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `HTTP ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            showMessage(`Successfully uploaded ${result.file_name}`, 'success');
            // Clear file selection
            selectedFiles[type] = null;
            document.getElementById(`${type}-file-name`).textContent = '';
            document.getElementById(`${type}-file-input`).value = '';
            // Reload PDF list
            loadPDFList(type);
        } else {
            throw new Error(result.error || 'Upload failed');
        }
        
    } catch (error) {
        showMessage(`Upload error: ${error.message}`, 'error');
        console.error('Upload error:', error);
    }
}

async function loadPDFLists() {
    loadPDFList('chatbot');
    loadPDFList('submission');
    loadPDFList('notification');
}

async function loadPDFList(type) {
    const listBody = document.getElementById(`${type}-pdf-list`);
    listBody.innerHTML = '<tr><td colspan="4" class="empty-state">Loading...</td></tr>';
    
    try {
        const response = await fetch(`${API_BASE}/api/teacher/list-pdfs?pdf_type=${type}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success && result.files && result.files.length > 0) {
            listBody.innerHTML = result.files.map(pdf => `
                <tr>
                    <td>${pdf.file_name}</td>
                    <td>${formatFileSize(pdf.file_size)}</td>
                    <td>${formatDate(pdf.upload_time)}</td>
                    <td>
                        <button class="delete-btn" onclick="deletePDF('${pdf.file_name}', '${type}')">Delete</button>
                    </td>
                </tr>
            `).join('');
        } else {
            listBody.innerHTML = '<tr><td colspan="4" class="empty-state">No PDF files uploaded yet</td></tr>';
        }
        
    } catch (error) {
        listBody.innerHTML = `<tr><td colspan="4" class="empty-state">Error loading PDFs: ${error.message}</td></tr>`;
        console.error('Load PDF list error:', error);
    }
}

async function deletePDF(filename, type) {
    if (!confirm(`Are you sure you want to delete "${filename}"?`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/teacher/delete-pdf?filename=${encodeURIComponent(filename)}&pdf_type=${type}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `HTTP ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            showMessage(`Successfully deleted ${result.file_name}`, 'success');
            loadPDFList(type);
        } else {
            throw new Error(result.error || 'Delete failed');
        }
        
    } catch (error) {
        showMessage(`Delete error: ${error.message}`, 'error');
        console.error('Delete error:', error);
    }
}

function showMessage(message, type) {
    const messageEl = document.getElementById('message');
    messageEl.textContent = message;
    messageEl.className = `message ${type}`;
    
    // Auto hide after 5 seconds
    setTimeout(() => {
        messageEl.className = 'message';
    }, 5000);
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    try {
        const date = new Date(dateString);
        return date.toLocaleString();
    } catch (e) {
        return dateString;
    }
}

function logout() {
    localStorage.removeItem('user_id');
    localStorage.removeItem('user_type');
    window.location.href = 'login.html';
}

