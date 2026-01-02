let currentFile = null;
let currentFolder = null;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    loadFiles();
    setupFileUpload();
});

// File Upload Setup
function setupFileUpload() {
    const fileInput = document.getElementById('fileInput');
    const uploadArea = document.querySelector('.upload-area');
    
    fileInput.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            const file = e.target.files[0];
            showFileInfo(file);
        }
    });
    
    // Drag and drop
    uploadArea.addEventListener('dragover', function(e) {
        e.preventDefault();
        uploadArea.style.background = '#f0f2ff';
    });
    
    uploadArea.addEventListener('dragleave', function(e) {
        e.preventDefault();
        uploadArea.style.background = '#f8f9ff';
    });
    
    uploadArea.addEventListener('drop', function(e) {
        e.preventDefault();
        uploadArea.style.background = '#f8f9ff';
        
        if (e.dataTransfer.files.length > 0) {
            const file = e.dataTransfer.files[0];
            if (file.name.endsWith('.csv')) {
                fileInput.files = e.dataTransfer.files;
                showFileInfo(file);
            } else {
                showStatus('Please upload a CSV file', 'error');
            }
        }
    });
}

function showFileInfo(file) {
    document.getElementById('fileName').textContent = file.name;
    document.getElementById('fileInfo').style.display = 'flex';
    document.querySelector('.upload-area').style.display = 'none';
}

function cancelUpload() {
    document.getElementById('fileInput').value = '';
    document.getElementById('fileInfo').style.display = 'none';
    document.querySelector('.upload-area').style.display = 'block';
    document.getElementById('uploadStatus').style.display = 'none';
}

async function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    if (!fileInput.files.length) {
        showStatus('Please select a file first', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    
    showStatus('Uploading and processing file...', 'info');
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showStatus('File processed successfully!', 'success');
            cancelUpload();
            setTimeout(() => {
                loadFiles();
            }, 1000);
        } else {
            showStatus('Error: ' + (data.error || 'Processing failed'), 'error');
        }
    } catch (error) {
        showStatus('Error: ' + error.message, 'error');
    }
}

function showStatus(message, type) {
    const statusDiv = document.getElementById('uploadStatus');
    statusDiv.textContent = message;
    statusDiv.className = 'status-message ' + type;
    statusDiv.style.display = 'block';
}


// Load Files
async function loadFiles() {
    try {
        const response = await fetch('/api/files');
        const data = await response.json();
        
        renderFileList('years', data.years);
        renderFileList('notice_years', data.notice_years);
    } catch (error) {
        console.error('Error loading files:', error);
        document.getElementById('yearsFileList').innerHTML = '<div class="loading">Error loading files</div>';
        document.getElementById('notice_yearsFileList').innerHTML = '<div class="loading">Error loading files</div>';
    }
}

function renderFileList(folder, files) {
    const container = document.getElementById(folder + 'FileList');
    
    if (files.length === 0) {
        container.innerHTML = '<div class="loading">No files available</div>';
        return;
    }
    
    container.innerHTML = files.map(file => `
        <div class="file-item">
            <div class="file-item-info">
                <div class="file-item-name">${file.name}</div>
                <div class="file-item-size">${formatFileSize(file.size)}</div>
            </div>
            <div class="file-item-actions">
                <button class="btn btn-primary" onclick="viewFile('${folder}', '${file.name}')">View</button>
                <button class="btn btn-success" onclick="downloadFile('${folder}', '${file.name}')">Download</button>
            </div>
        </div>
    `).join('');
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Tabs
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(tabName + 'Tab').classList.add('active');
    event.target.classList.add('active');
}

// View File
async function viewFile(folder, filename) {
    currentFile = filename;
    currentFolder = folder;
    
    try {
        const response = await fetch(`/api/view/${folder}/${filename}`);
        const data = await response.json();
        
        if (response.ok) {
            document.getElementById('viewerTitle').textContent = filename;
            document.getElementById('fileStats').textContent = `${data.count} countries`;
            
            // Format and display JSON
            const jsonViewer = document.getElementById('jsonViewer');
            jsonViewer.innerHTML = '<pre>' + JSON.stringify(data.data, null, 2) + '</pre>';
            
            document.getElementById('viewerModal').style.display = 'block';
        } else {
            alert('Error: ' + (data.error || 'Could not load file'));
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// Download File
function downloadFile(folder, filename) {
    window.location.href = `/api/download/${folder}/${filename}`;
}

function downloadCurrentFile() {
    if (currentFile && currentFolder) {
        downloadFile(currentFolder, currentFile);
    }
}

// Copy to Clipboard
async function copyToClipboard() {
    const jsonViewer = document.getElementById('jsonViewer');
    const text = jsonViewer.querySelector('pre').textContent;
    
    try {
        await navigator.clipboard.writeText(text);
        alert('JSON copied to clipboard!');
    } catch (error) {
        alert('Failed to copy: ' + error.message);
    }
}

// Close Viewer
function closeViewer() {
    document.getElementById('viewerModal').style.display = 'none';
    currentFile = null;
    currentFolder = null;
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('viewerModal');
    if (event.target === modal) {
        closeViewer();
    }
}

