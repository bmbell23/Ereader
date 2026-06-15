// GreatReads JavaScript Application

// Global configuration
// Get the base path from the window variable set in base.html (handles reverse proxy)
const BASE_PATH = window.APP_BASE_PATH || '';
const API_BASE = `${BASE_PATH}/api`;

// Utility functions
function showToast(message, type = 'info') {
    // Create toast element
    const toastHtml = `
        <div class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    // Add to toast container (create if doesn't exist)
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '1055';
        document.body.appendChild(toastContainer);
    }
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    // Show toast
    const toastElement = toastContainer.lastElementChild;
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
    
    // Remove from DOM after hiding
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

function formatDate(dateString) {
    if (!dateString) return 'Not set';
    // Parse as local date to avoid timezone conversion issues
    // Date strings from API are in YYYY-MM-DD format
    const [year, month, day] = dateString.split('-').map(Number);
    const date = new Date(year, month - 1, day); // month is 0-indexed
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatRating(rating) {
    if (!rating) return '';

    rating = parseFloat(rating);

    // Convert from 1-10 scale to 1-5 scale if needed
    if (rating > 5) {
        rating = rating / 2;
    }

    // Clamp rating to 1-5 range
    rating = Math.max(1, Math.min(5, rating));

    let html = '';
    for (let i = 1; i <= 5; i++) {
        if (rating >= i) {
            // Full star
            html += '<i class="fas fa-star text-warning"></i>';
        } else if (rating >= i - 0.5) {
            // Half star
            html += '<i class="fas fa-star-half-alt text-warning"></i>';
        } else {
            // Empty star
            html += '<i class="far fa-star text-muted"></i>';
        }
    }
    return html;
}

// Emoji Rating Component
function getEmojiForType(type) {
    const emojis = {
        'star': '⭐',
        'blood': '🩸',
        'pepper': '🌶️'
    };
    return emojis[type] || '⭐';
}

function initEmojiRating(container) {
    const ratingType = container.dataset.ratingType;
    const emojiType = container.dataset.emoji || 'star';
    const hiddenInput = container.querySelector('input[type="hidden"]');
    const display = container.querySelector('.emoji-rating-display');
    const emoji = getEmojiForType(emojiType);

    // Create 5 emoji items
    display.innerHTML = '';
    for (let i = 1; i <= 5; i++) {
        const item = document.createElement('span');
        item.className = 'emoji-rating-item empty';
        item.textContent = emoji;
        item.dataset.value = i;

        // Click to set rating
        item.addEventListener('click', (e) => {
            e.stopPropagation();
            const value = parseInt(item.dataset.value);
            setEmojiRating(container, value);
        });

        // Hover preview
        item.addEventListener('mouseenter', () => {
            previewEmojiRating(container, i);
        });

        display.appendChild(item);
    }

    // Reset preview on mouse leave
    display.addEventListener('mouseleave', () => {
        const currentValue = parseInt(hiddenInput.value) || 0;
        updateEmojiDisplay(container, currentValue);
    });

    // Set initial value
    const initialValue = parseInt(hiddenInput.value) || 0;
    updateEmojiDisplay(container, initialValue);
}

function setEmojiRating(container, value) {
    const hiddenInput = container.querySelector('input[type="hidden"]');
    const currentValue = parseInt(hiddenInput.value) || 0;

    // If clicking the same value, clear the rating
    if (currentValue === value) {
        hiddenInput.value = '0';
        updateEmojiDisplay(container, 0);
    } else {
        hiddenInput.value = value.toString();
        updateEmojiDisplay(container, value);
    }
}

function previewEmojiRating(container, value) {
    updateEmojiDisplay(container, value);
}

function updateEmojiDisplay(container, value) {
    const items = container.querySelectorAll('.emoji-rating-item');
    items.forEach((item, index) => {
        if (index < value) {
            item.classList.remove('empty');
            item.classList.add('filled');
        } else {
            item.classList.remove('filled');
            item.classList.add('empty');
        }
    });
}

// Initialize all emoji ratings on page
function initAllEmojiRatings() {
    document.querySelectorAll('.emoji-rating').forEach(container => {
        initEmojiRating(container);
    });
}

function getStatusBadge(reading) {
    if (reading.is_finished) {
        return `<span class="status-badge status-finished">Finished</span>`;
    } else if (reading.is_started) {
        return `<span class="status-badge status-in-progress">In Progress</span>`;
    } else {
        return `<span class="status-badge status-not-started">Not Started</span>`;
    }
}

function getStatusClass(reading) {
    if (reading.is_finished) {
        return 'finished';
    } else if (reading.is_started) {
        return 'in-progress';
    } else {
        return 'not-started';
    }
}

// API helper functions
async function apiCall(endpoint, options = {}) {
    try {
        const response = await axios({
            url: `${API_BASE}${endpoint}`,
            ...options
        });
        return response.data;
    } catch (error) {
        console.error('API call failed:', error);
        
        if (error.response) {
            // Server responded with error status
            const message = error.response.data?.detail || error.response.data?.message || 'Server error';
            showToast(message, 'danger');
        } else if (error.request) {
            // Request made but no response
            showToast('Network error - please check your connection', 'danger');
        } else {
            // Something else happened
            showToast('An unexpected error occurred', 'danger');
        }
        
        throw error;
    }
}

// Reading management functions
async function updateReading(readingId, data) {
    return await apiCall(`/readings/${readingId}`, {
        method: 'PUT',
        data: data
    });
}

async function finishReading(readingId) {
    return await apiCall(`/readings/${readingId}/finish`, {
        method: 'POST'
    });
}

async function pauseReading(readingId) {
    return await apiCall(`/readings/${readingId}/pause`, {
        method: 'POST'
    });
}

async function unpauseReading(readingId) {
    return await apiCall(`/readings/${readingId}/unpause`, {
        method: 'POST'
    });
}

async function startReading(readingId, startDate = null) {
    return await apiCall(`/readings/${readingId}/start`, {
        method: 'POST',
        params: startDate ? { start_date: startDate } : {}
    });
}

async function reorderReadings(readingId, newPosition) {
    return await apiCall('/readings/reorder', {
        method: 'POST',
        params: {
            reading_id: readingId,
            new_position: newPosition
        }
    });
}

async function recalculateChains() {
    return await apiCall('/chains/recalculate', {
        method: 'POST'
    });
}

// Modal management
function showEditModal(reading) {
    const modal = document.getElementById('editReadingModal');
    if (!modal) {
        console.error('Edit modal not found');
        return;
    }

    // Populate form fields
    document.getElementById('editReadingId').value = reading.id;
    document.getElementById('editBookTitle').textContent = reading.book.title;
    document.getElementById('editAuthor').textContent = reading.book.author;
    document.getElementById('editMedia').value = reading.media || '';
    document.getElementById('editDateStarted').value = reading.date_started || '';
    document.getElementById('editDateFinished').value = reading.date_finished_actual || '';

    // Show/hide progress section for In Progress books
    const progressSection = document.getElementById('progressSection');
    if (progressSection) {
        if (reading.is_started && !reading.is_finished) {
            progressSection.style.display = 'block';

            // Populate progress fields with current calculated values
            const currentPercentField = document.getElementById('editCurrentPercent');
            const currentPageField = document.getElementById('editCurrentPage');
            const totalPagesSpan = document.getElementById('totalPages');

            const currentPercent = reading.current_progress_percent || 0;
            const currentPage = reading.current_progress_page || 0;
            const totalPages = reading.book?.page_count || 0;

            if (currentPercentField) {
                currentPercentField.value = currentPercent.toFixed(1);
                currentPercentField.dataset.totalPages = totalPages;
                currentPercentField.dataset.originalValue = currentPercent.toFixed(1); // Track original value
            }

            if (currentPageField) {
                currentPageField.value = currentPage;
                currentPageField.max = totalPages;
                currentPageField.dataset.totalPages = totalPages;
            }

            if (totalPagesSpan) {
                totalPagesSpan.textContent = `/ ${totalPages}`;
            }

            // Add event listeners to sync percentage and page
            if (currentPercentField && currentPageField && totalPages > 0) {
                currentPercentField.addEventListener('input', function() {
                    const percent = parseFloat(this.value) || 0;
                    const page = Math.round((percent / 100) * totalPages);
                    currentPageField.value = page;
                });

                currentPageField.addEventListener('input', function() {
                    const page = parseInt(this.value) || 0;
                    const percent = (page / totalPages) * 100;
                    currentPercentField.value = percent.toFixed(1);
                });
            }
        } else {
            progressSection.style.display = 'none';
        }
    }

    // Show/hide buttons based on reading status
    // (These buttons only exist on TBR page, not journal page)
    const startBtn = document.getElementById('startReadingBtn');
    const startManualBtn = document.getElementById('startReadingManualBtn');
    const pauseBtn = document.getElementById('pauseReadingBtn');
    const unpauseBtn = document.getElementById('unpauseReadingBtn');
    const finishBtn = document.getElementById('finishReadingBtn');

    if (startBtn && finishBtn) {
        if (!reading.date_started) {
            // Not started yet - show Start buttons
            startBtn.style.display = 'inline-block';
            if (startManualBtn) startManualBtn.style.display = 'inline-block';
            if (pauseBtn) pauseBtn.style.display = 'none';
            if (unpauseBtn) unpauseBtn.style.display = 'none';
            finishBtn.style.display = 'none';
        } else if (reading.status === 'paused') {
            // Paused - show Unpause and Finish buttons
            startBtn.style.display = 'none';
            if (startManualBtn) startManualBtn.style.display = 'none';
            if (pauseBtn) pauseBtn.style.display = 'none';
            if (unpauseBtn) unpauseBtn.style.display = 'inline-block';
            finishBtn.style.display = 'inline-block';
        } else {
            // In progress - show Pause and Finish buttons
            startBtn.style.display = 'none';
            if (startManualBtn) startManualBtn.style.display = 'none';
            if (pauseBtn) pauseBtn.style.display = 'inline-block';
            if (unpauseBtn) unpauseBtn.style.display = 'none';
            finishBtn.style.display = 'inline-block';
        }
    }

    // Set book cover image
    const coverImg = document.getElementById('editBookCoverImg');
    const fallbackIcon = document.querySelector('#editBookCover .book-cover-fallback');

    coverImg.src = `${window.APP_BASE_PATH}/static/covers/${reading.book.id}.jpg`;
    coverImg.style.display = 'block';
    fallbackIcon.style.display = 'none';

    // Handle image load error
    coverImg.onerror = function() {
        this.style.display = 'none';
        fallbackIcon.style.display = 'block';
    };
    
    // Initialize emoji ratings first
    initAllEmojiRatings();

    // Populate ratings (convert from 1-10 to 1-5 scale if needed, then clamp to whole numbers)
    const ratings = ['horror', 'spice', 'world_building', 'writing', 'characters', 'readability', 'enjoyment'];
    ratings.forEach(rating => {
        const field = document.getElementById(`editRating${rating.charAt(0).toUpperCase() + rating.slice(1).replace('_', '')}`);
        if (field) {
            let value = reading[`rating_${rating}`];
            // Convert and clamp value to 1-5 range if it exists
            if (value !== null && value !== undefined && value !== '') {
                value = parseFloat(value);
                // If value is > 5, it's on the old 1-10 scale, so convert it
                if (value > 5) {
                    value = value / 2;
                }
                // Round to nearest whole number and clamp to 1-5 range
                value = Math.round(value);
                value = Math.max(0, Math.min(5, value));
            } else {
                value = 0;
            }
            field.value = value;

            // Update the emoji display
            const container = field.closest('.emoji-rating');
            if (container) {
                updateEmojiDisplay(container, value);
            }
        }
    });

    // Show modal
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

// Form submission handlers
async function saveReadingChanges() {
    const form = document.getElementById('editReadingForm');
    const formData = new FormData(form);
    const readingId = formData.get('reading_id');
    
    // Build update data
    const updateData = {};

    // Basic fields
    if (formData.get('media')) updateData.media = formData.get('media');

    // Handle date_started - allow clearing by explicitly setting to null
    const dateStarted = formData.get('date_started');
    if (dateStarted !== null) {
        updateData.date_started = dateStarted || null;
    }

    // Handle date_finished_actual - allow clearing by explicitly setting to null
    const dateFinished = formData.get('date_finished_actual');
    if (dateFinished !== null) {
        updateData.date_finished_actual = dateFinished || null;
    }

    // Progress tracking will be handled separately via the progress API if changed

    // Ratings (whole numbers 0-5, where 0 means no rating)
    const ratings = ['horror', 'spice', 'world_building', 'writing', 'characters', 'readability', 'enjoyment'];
    ratings.forEach(rating => {
        const value = formData.get(`rating_${rating}`);
        if (value !== null && value !== undefined && value !== '') {
            let numValue = parseInt(value);
            // Clamp to 0-5 range (0 = no rating)
            numValue = Math.max(0, Math.min(5, numValue));
            // Only include in update if > 0
            if (numValue > 0) {
                updateData[`rating_${rating}`] = numValue;
            } else {
                // Explicitly set to null to clear the rating
                updateData[`rating_${rating}`] = null;
            }
        }
    });
    
    try {
        // First, update the basic reading data
        await updateReading(readingId, updateData);

        // Then, check if progress was changed and update it separately
        const currentPercentField = document.getElementById('editCurrentPercent');
        if (currentPercentField && currentPercentField.value) {
            const newPercent = parseFloat(currentPercentField.value);
            const originalPercent = parseFloat(currentPercentField.dataset.originalValue || '0');

            console.log(`Progress check: original=${originalPercent}%, new=${newPercent}%, diff=${Math.abs(newPercent - originalPercent)}`);

            // Only update if it's a valid number AND it changed
            if (!isNaN(newPercent) && newPercent >= 0 && newPercent <= 100 &&
                Math.abs(newPercent - originalPercent) > 0.01) {
                console.log(`Calling progress API: ${newPercent}%`);
                await apiCall(`/readings/${readingId}/progress`, {
                    method: 'PUT',
                    params: { current_percent: newPercent }
                });
                console.log('Progress API call completed');
            } else {
                console.log('Progress not changed, skipping API call');
            }
        }

        showToast('Reading updated successfully!', 'success');

        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('editReadingModal'));
        modal.hide();

        // Refresh the page or update the display
        if (typeof refreshReadings === 'function') {
            refreshReadings();
        } else {
            location.reload();
        }
    } catch (error) {
        // Error already handled by apiCall
    }
}

// Initialize drag and drop
function initializeDragAndDrop(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    new Sortable(container, {
        animation: 150,
        ghostClass: 'sortable-ghost',
        chosenClass: 'sortable-chosen',
        dragClass: 'sortable-drag',
        handle: '.drag-handle',
        onEnd: async function(evt) {
            const readingId = evt.item.dataset.readingId;
            const newPosition = evt.newIndex;
            
            try {
                await reorderReadings(readingId, newPosition);
                showToast('Reading reordered successfully!', 'success');
            } catch (error) {
                // Revert the change
                if (evt.oldIndex < evt.newIndex) {
                    evt.to.insertBefore(evt.item, evt.to.children[evt.oldIndex]);
                } else {
                    evt.to.insertBefore(evt.item, evt.to.children[evt.oldIndex + 1]);
                }
            }
        }
    });
}

// Global event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});

// Export functions for global use
window.GreatReads = {
    showToast,
    formatDate,
    formatRating,
    getStatusBadge,
    getStatusClass,
    apiCall,
    updateReading,
    finishReading,
    pauseReading,
    unpauseReading,
    startReading,
    reorderReadings,
    recalculateChains,
    showEditModal,
    saveReadingChanges,
    initializeDragAndDrop,
    initEmojiRating,
    initAllEmojiRatings,
    setEmojiRating,
    updateEmojiDisplay
};
