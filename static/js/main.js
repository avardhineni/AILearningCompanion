// Main JavaScript for AI Tutor Document Processor

document.addEventListener('DOMContentLoaded', function() {
    // Initialize upload form handling
    initializeUploadForm();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize file input styling
    initializeFileInput();
});

function initializeUploadForm() {
    const uploadForm = document.getElementById('uploadForm');
    const uploadBtn = document.getElementById('uploadBtn');
    const uploadProgress = document.getElementById('uploadProgress');
    const fileInput = document.getElementById('file');
    
    if (!uploadForm) return;
    
    uploadForm.addEventListener('submit', function(e) {
        // Validate file selection
        if (!fileInput.files[0]) {
            e.preventDefault();
            showAlert('Please select a file to upload.', 'warning');
            return;
        }
        
        // Validate file type
        const file = fileInput.files[0];
        if (!file.name.toLowerCase().endsWith('.docx')) {
            e.preventDefault();
            showAlert('Please select a valid Word document (.docx file).', 'danger');
            return;
        }
        
        // Validate file size (16MB limit)
        const maxSize = 16 * 1024 * 1024; // 16MB in bytes
        if (file.size > maxSize) {
            e.preventDefault();
            showAlert('File size too large. Please select a file smaller than 16MB.', 'danger');
            return;
        }
        
        // Show loading state
        showUploadProgress();
    });
}

function showUploadProgress() {
    const uploadBtn = document.getElementById('uploadBtn');
    const uploadProgress = document.getElementById('uploadProgress');
    
    if (uploadBtn) {
        uploadBtn.disabled = true;
        uploadBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
        uploadBtn.classList.add('uploading');
    }
    
    if (uploadProgress) {
        uploadProgress.style.display = 'block';
        const progressBar = uploadProgress.querySelector('.progress-bar');
        if (progressBar) {
            progressBar.style.width = '100%';
        }
    }
}

function initializeTooltips() {
    // Initialize Bootstrap tooltips if any exist
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

function initializeFileInput() {
    const fileInput = document.getElementById('file');
    if (!fileInput) return;
    
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            // Update UI to show selected file
            const fileName = file.name;
            const fileSize = formatFileSize(file.size);
            
            // Create or update file info display
            let fileInfo = document.getElementById('fileInfo');
            if (!fileInfo) {
                fileInfo = document.createElement('div');
                fileInfo.id = 'fileInfo';
                fileInfo.className = 'mt-2 p-2 bg-secondary bg-opacity-10 rounded';
                fileInput.parentNode.appendChild(fileInfo);
            }
            
            fileInfo.innerHTML = `
                <small class="text-muted">
                    <i data-feather="file" class="me-1"></i>
                    <strong>${fileName}</strong> (${fileSize})
                </small>
            `;
            
            // Re-initialize feather icons
            feather.replace();
        }
    });
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function showAlert(message, type = 'info') {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        <i data-feather="${getAlertIcon(type)}" class="me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Find container or create one
    let container = document.querySelector('.container');
    if (!container) {
        container = document.body;
    }
    
    // Insert alert at the top
    container.insertBefore(alertDiv, container.firstChild);
    
    // Re-initialize feather icons
    feather.replace();
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv && alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

function getAlertIcon(type) {
    const icons = {
        'success': 'check-circle',
        'danger': 'alert-circle',
        'warning': 'alert-triangle',
        'info': 'info'
    };
    return icons[type] || 'info';
}

// Utility function for content toggling (used in view_document.html)
function toggleContent(pageId) {
    const fullContent = document.getElementById(`full-content-${pageId}`);
    if (!fullContent) return;
    
    const isHidden = fullContent.style.display === 'none' || fullContent.style.display === '';
    fullContent.style.display = isHidden ? 'block' : 'none';
    
    // Update button text and icon
    const toggleBtn = event && event.target ? event.target.closest('button') : null;
    if (toggleBtn) {
        const icon = toggleBtn.querySelector('i[data-feather]');
        const text = toggleBtn.childNodes[toggleBtn.childNodes.length - 1];
        
        if (icon && text) {
            if (isHidden) {
                icon.setAttribute('data-feather', 'chevron-up');
                text.textContent = ' Show Less';
            } else {
                icon.setAttribute('data-feather', 'chevron-down');
                text.textContent = ' Show More';
            }
            
            // Re-initialize feather icons
            feather.replace();
        }
    }
}

// Handle page navigation with keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Only handle shortcuts on document view pages
    if (!window.location.pathname.includes('/document/')) return;
    
    // Left arrow or 'p' for previous page
    if ((e.key === 'ArrowLeft' || e.key === 'p') && !e.ctrlKey && !e.metaKey) {
        const prevBtn = document.querySelector('a:contains("Previous")');
        if (prevBtn) {
            prevBtn.click();
            e.preventDefault();
        }
    }
    
    // Right arrow or 'n' for next page
    if ((e.key === 'ArrowRight' || e.key === 'n') && !e.ctrlKey && !e.metaKey) {
        const nextBtn = document.querySelector('a:contains("Next")');
        if (nextBtn) {
            nextBtn.click();
            e.preventDefault();
        }
    }
    
    // Escape key to go back to all pages view
    if (e.key === 'Escape') {
        const allPagesBtn = document.querySelector('a:contains("All Pages")');
        if (allPagesBtn) {
            allPagesBtn.click();
            e.preventDefault();
        }
    }
});

// Add smooth scrolling for anchor links
document.addEventListener('click', function(e) {
    if (e.target.matches('a[href^="#"]')) {
        e.preventDefault();
        const target = document.querySelector(e.target.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth'
            });
        }
    }
});

// Handle form confirmations
document.addEventListener('submit', function(e) {
    const form = e.target;
    
    // Handle delete confirmations
    if (form.action && form.action.includes('/delete/')) {
        if (!confirm('Are you sure you want to delete this document? This action cannot be undone.')) {
            e.preventDefault();
        }
    }
});

// Add loading states to buttons
document.addEventListener('click', function(e) {
    const btn = e.target.closest('button, .btn');
    if (btn && btn.type === 'submit' && !btn.disabled) {
        // Add loading state
        const originalText = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
        
        // Reset after 30 seconds as fallback
        setTimeout(() => {
            btn.disabled = false;
            btn.innerHTML = originalText;
            feather.replace();
        }, 30000);
    }
});
