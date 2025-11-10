console.log('schedule.js loaded successfully');

let currentSectionId = null;
let currentTimeField = null;
let selectedHour = 7;
let selectedMinute = 30;
let selectedPeriod = 'AM';

// ===============================
// TIME PICKER
// ===============================
function openTimePicker(fieldId) {
    currentTimeField = fieldId;

    const currentTime = document.getElementById(fieldId).value;
    if (currentTime) {
        const [time, period] = convertTo12Hour(currentTime);
        const [hours, minutes] = time.split(':');
        selectedHour = parseInt(hours);
        selectedMinute = parseInt(minutes);
        selectedPeriod = period;
    }

    populateTimePicker();
    document.getElementById('timePickerModal').style.display = 'flex';
    document.getElementById('timePickerTitle').textContent =
        `Select ${fieldId.replace('_', ' ').toUpperCase()}`;

    setTimeout(() => setupScrollListeners(), 200);
}

function closeTimePicker() {
    document.getElementById('timePickerModal').style.display = 'none';
    currentTimeField = null;
}

// ===============================
// POPULATE TIME PICKER
// ===============================
function populateTimePicker() {
    const hoursList = document.getElementById('hoursList');
    const minutesList = document.getElementById('minutesList');
    const periodList = document.getElementById('periodList');

    hoursList.innerHTML = '';
    minutesList.innerHTML = '';
    periodList.innerHTML = '';

    // HOURS - Create array with repeats for infinite scroll
    const hourValues = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];
    const repeatedHours = [];
    for (let i = 0; i < 20; i++) {
        repeatedHours.push(...hourValues);
    }

    repeatedHours.forEach(hour => {
        const item = document.createElement('button');
        item.className = 'time-picker-item';
        item.dataset.value = hour;
        item.textContent = hour.toString().padStart(2, '0');
        item.onclick = () => selectTimeItem('hour', hour);
        hoursList.appendChild(item);
    });

    // MINUTES - Create array with repeats for infinite scroll
    const minuteValues = [];
    for (let m = 0; m < 60; m += 5) minuteValues.push(m);
    const repeatedMinutes = [];
    for (let i = 0; i < 20; i++) {
        repeatedMinutes.push(...minuteValues);
    }

    repeatedMinutes.forEach(minute => {
        const item = document.createElement('button');
        item.className = 'time-picker-item';
        item.dataset.value = minute;
        item.textContent = minute.toString().padStart(2, '0');
        item.onclick = () => selectTimeItem('minute', minute);
        minutesList.appendChild(item);
    });

    // PERIOD - Add spacers for centering
    // Add 4 empty spacers at top
    for (let i = 0; i < 4; i++) {
        const spacer = document.createElement('div');
        spacer.className = 'time-picker-item time-picker-spacer';
        spacer.innerHTML = '&nbsp;';
        periodList.appendChild(spacer);
    }
    
    // Add AM
    const amItem = document.createElement('button');
    amItem.className = 'time-picker-item';
    amItem.dataset.value = 'AM';
    amItem.textContent = 'AM';
    amItem.onclick = () => selectTimeItem('period', 'AM');
    periodList.appendChild(amItem);
    
    // Add PM
    const pmItem = document.createElement('button');
    pmItem.className = 'time-picker-item';
    pmItem.dataset.value = 'PM';
    pmItem.textContent = 'PM';
    pmItem.onclick = () => selectTimeItem('period', 'PM');
    periodList.appendChild(pmItem);
    
    // Add 4 empty spacers at bottom
    for (let i = 0; i < 4; i++) {
        const spacer = document.createElement('div');
        spacer.className = 'time-picker-item time-picker-spacer';
        spacer.innerHTML = '&nbsp;';
        periodList.appendChild(spacer);
    }

    // Initialize scroll positions after DOM is ready
    setTimeout(() => {
        // Start hours and minutes in the middle of their repeated arrays
        const hoursMiddle = Math.floor(hoursList.scrollHeight / 2);
        const minutesMiddle = Math.floor(minutesList.scrollHeight / 2);
        
        hoursList.scrollTop = hoursMiddle;
        minutesList.scrollTop = minutesMiddle;
        
        // Then scroll to selected values
        scrollToValue(hoursList, selectedHour, 'hour', true);
        scrollToValue(minutesList, selectedMinute, 'minute', true);
        
        // Center the selected period
        centerPeriod(selectedPeriod);
    }, 100);
}

// ===============================
// CENTER PERIOD
// ===============================
function centerPeriod(period) {
    const periodList = document.getElementById('periodList');
    const items = Array.from(periodList.querySelectorAll('.time-picker-item'));
    const targetItem = items.find(item => item.dataset.value === period);
    
    if (targetItem) {
        const containerHeight = periodList.clientHeight;
        const itemTop = targetItem.offsetTop;
        const itemHeight = targetItem.offsetHeight;
        
        // Calculate scroll position to center the item
        periodList.scrollTop = itemTop - (containerHeight / 2) + (itemHeight / 2);
        
        updateSelectionVisual('period', period);
    }
}

// ===============================
// SCROLL TO VALUE
// ===============================
function scrollToValue(container, value, type, instant = false) {
    const items = Array.from(container.querySelectorAll('.time-picker-item'));
    const center = container.getBoundingClientRect().top + container.clientHeight / 2;

    // Find all matching items
    const matching = items.filter(i => {
        if (type === 'period') return i.dataset.value === value;
        return parseInt(i.dataset.value) === value;
    });

    if (matching.length) {
        // Find the one closest to current center
        let closest = matching[0];
        let minDist = Infinity;
        matching.forEach(item => {
            const rect = item.getBoundingClientRect();
            const mid = rect.top + rect.height / 2;
            const dist = Math.abs(center - mid);
            if (dist < minDist) {
                minDist = dist;
                closest = item;
            }
        });

        if (closest) {
            closest.scrollIntoView({
                behavior: instant ? 'auto' : 'smooth',
                block: 'center'
            });
        }
    }

    updateSelectionVisual(type, value);
}

// ===============================
// SELECT ITEM
// ===============================
function selectTimeItem(type, value) {
    if (type === 'hour') {
        selectedHour = value;
        const list = document.getElementById('hoursList');
        scrollToValue(list, value, type);
    } else if (type === 'minute') {
        selectedMinute = value;
        const list = document.getElementById('minutesList');
        scrollToValue(list, value, type);
    } else if (type === 'period') {
        selectedPeriod = value;
        centerPeriod(value);
    }
}

// ===============================
// SCROLL LISTENERS
// ===============================
function setupScrollListeners() {
    const hoursList = document.getElementById('hoursList');
    const minutesList = document.getElementById('minutesList');

    if (!hoursList.dataset.added) {
        hoursList.addEventListener('scroll', () => handleInfiniteScroll(hoursList, 'hour'));
        hoursList.dataset.added = true;
    }
    if (!minutesList.dataset.added) {
        minutesList.addEventListener('scroll', () => handleInfiniteScroll(minutesList, 'minute'));
        minutesList.dataset.added = true;
    }
}

// ===============================
// INFINITE SCROLL HANDLER
// ===============================
function handleInfiniteScroll(container, type) {
    // Prevent recursive calls
    if (container.dataset.isAdjusting === 'true') {
        return;
    }

    const scrollTop = container.scrollTop;
    const scrollHeight = container.scrollHeight;
    const clientHeight = container.clientHeight;
    
    const maxScroll = scrollHeight - clientHeight;
    const buffer = clientHeight * 0.5; // 50% buffer zone

    // When scrolling near the top, jump to equivalent position near bottom
    if (scrollTop < buffer) {
        container.dataset.isAdjusting = 'true';
        const offset = scrollTop;
        container.scrollTop = (scrollHeight / 2) + offset;
        setTimeout(() => {
            delete container.dataset.isAdjusting;
        }, 100);
    }
    
    // When scrolling near the bottom, jump to equivalent position near top
    else if (scrollTop > maxScroll - buffer) {
        container.dataset.isAdjusting = 'true';
        const offset = scrollTop - maxScroll;
        container.scrollTop = (scrollHeight / 2) + offset;
        setTimeout(() => {
            delete container.dataset.isAdjusting;
        }, 100);
    }

    // Update selected value based on center
    updateSelectedFromScroll(container, type);
}

// ===============================
// UPDATE SELECTED FROM SCROLL
// ===============================
function updateSelectedFromScroll(container, type) {
    const items = Array.from(container.querySelectorAll('.time-picker-item'));
    const center = container.getBoundingClientRect().top + container.clientHeight / 2;
    
    let closest = null;
    let minDist = Infinity;

    items.forEach(item => {
        const rect = item.getBoundingClientRect();
        const mid = rect.top + rect.height / 2;
        const dist = Math.abs(center - mid);
        if (dist < minDist) {
            minDist = dist;
            closest = item;
        }
    });

    if (closest) {
        const value = parseInt(closest.dataset.value);
        if (!isNaN(value)) {
            if (type === 'hour') selectedHour = value;
            if (type === 'minute') selectedMinute = value;
            updateSelectionVisual(type, value);
        }
    }
}

// ===============================
// Update selection visuals
// ===============================
function updateSelectionVisual(type, value) {
    try {
        const id = type === 'hour' ? 'hoursList' : type === 'minute' ? 'minutesList' : 'periodList';
        const list = document.getElementById(id);
        if (!list) return;
        
        const items = Array.from(list.querySelectorAll('.time-picker-item'));
        const center = list.getBoundingClientRect().top + list.clientHeight / 2;

        items.forEach(item => item.classList.remove('selected'));

        // For repeated lists (hours/minutes) pick the matching item closest to center
        const matching = items.filter(i => {
            if (type === 'period') return i.dataset.value === value;
            return parseInt(i.dataset.value) === value;
        });

        if (matching.length) {
            let closest = matching[0];
            let minDist = Infinity;
            matching.forEach(item => {
                const rect = item.getBoundingClientRect();
                const mid = rect.top + rect.height / 2;
                const dist = Math.abs(center - mid);
                if (dist < minDist) {
                    minDist = dist;
                    closest = item;
                }
            });

            if (closest) closest.classList.add('selected');
        }
    } catch (e) {
        console.error('updateSelectionVisual error', e);
    }
}

// ===============================
// FINALIZE SELECTION
// ===============================
function confirmTimeSelection() {
    if (!currentTimeField) return;

    const time24 = convertTo24Hour(selectedHour, selectedMinute, selectedPeriod);
    const display = `${selectedHour.toString().padStart(2, '0')}:${selectedMinute
        .toString().padStart(2, '0')} ${selectedPeriod}`;

    document.getElementById(currentTimeField).value = time24;
    document.getElementById(`${currentTimeField}_display`).textContent = display;

    closeTimePicker();
}

// ===============================
// TIME CONVERSION
// ===============================
function convertTo12Hour(t) {
    const [h, m] = t.split(':').map(Number);
    const period = h >= 12 ? 'PM' : 'AM';
    const h12 = h % 12 || 12;
    return [`${h12.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`, period];
}

function convertTo24Hour(h12, m, p) {
    let h = h12;
    if (p === 'PM' && h12 !== 12) h += 12;
    if (p === 'AM' && h12 === 12) h = 0;
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
}

// ===============================
// CSRF and Fetch helpers
// ===============================
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function fetchWithCSRF(url, options = {}) {
    if (!options.headers) options.headers = {};
    options.headers['X-CSRFToken'] = getCookie('csrftoken');
    return fetch(url, options);
}

function openModal(modalId) {
    const el = document.getElementById(modalId);
    if (el) el.style.display = 'block';
}

function closeModal(modalId) {
    const el = document.getElementById(modalId);
    if (el) el.style.display = 'none';
}

function openCreateScheduleModal() {
    openModal('createScheduleModal');
}

function showNotification(message, type='info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type} show`;
    notification.textContent = message;
    document.body.appendChild(notification);
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function submitCreateSchedule(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);

    fetchWithCSRF('/admin/schedule/add/', {
        method: 'POST',
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showNotification('Schedule created successfully!', 'success');
            closeModal('createScheduleModal');
            if (currentSectionId) {
                setTimeout(() => loadScheduleView(currentSectionId, document.getElementById('scheduleSectionName').textContent, document.getElementById('scheduleCurriculum').textContent), 500);
            } else {
                setTimeout(() => window.location.reload(), 800);
            }
        } else {
            const err = data.errors ? data.errors.join(', ') : (data.error || 'Unknown error');
            showNotification('Error creating schedule: ' + err, 'error');
        }
    })
    .catch(err => {
        console.error('submitCreateSchedule error', err);
        showNotification('Error creating schedule', 'error');
    });
}