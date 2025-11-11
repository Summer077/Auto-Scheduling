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
    for (let i = 0; i < 4; i++) {
        const spacer = document.createElement('div');
        spacer.className = 'time-picker-item time-picker-spacer';
        spacer.innerHTML = '&nbsp;';
        periodList.appendChild(spacer);
    }
    
    const amItem = document.createElement('button');
    amItem.className = 'time-picker-item';
    amItem.dataset.value = 'AM';
    amItem.textContent = 'AM';
    amItem.onclick = () => selectTimeItem('period', 'AM');
    periodList.appendChild(amItem);
    
    const pmItem = document.createElement('button');
    pmItem.className = 'time-picker-item';
    pmItem.dataset.value = 'PM';
    pmItem.textContent = 'PM';
    pmItem.onclick = () => selectTimeItem('period', 'PM');
    periodList.appendChild(pmItem);
    
    for (let i = 0; i < 4; i++) {
        const spacer = document.createElement('div');
        spacer.className = 'time-picker-item time-picker-spacer';
        spacer.innerHTML = '&nbsp;';
        periodList.appendChild(spacer);
    }

    setTimeout(() => {
        const hoursMiddle = Math.floor(hoursList.scrollHeight / 2);
        const minutesMiddle = Math.floor(minutesList.scrollHeight / 2);
        
        hoursList.scrollTop = hoursMiddle;
        minutesList.scrollTop = minutesMiddle;
        
        scrollToValue(hoursList, selectedHour, 'hour', true);
        scrollToValue(minutesList, selectedMinute, 'minute', true);
        centerPeriod(selectedPeriod);
    }, 100);
}

function centerPeriod(period) {
    const periodList = document.getElementById('periodList');
    const items = Array.from(periodList.querySelectorAll('.time-picker-item'));
    const targetItem = items.find(item => item.dataset.value === period);
    
    if (targetItem) {
        const containerHeight = periodList.clientHeight;
        const itemTop = targetItem.offsetTop;
        const itemHeight = targetItem.offsetHeight;
        periodList.scrollTop = itemTop - (containerHeight / 2) + (itemHeight / 2);
        updateSelectionVisual('period', period);
    }
}

function scrollToValue(container, value, type, instant = false) {
    const items = Array.from(container.querySelectorAll('.time-picker-item'));
    const center = container.getBoundingClientRect().top + container.clientHeight / 2;

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

        if (closest) {
            closest.scrollIntoView({
                behavior: instant ? 'auto' : 'smooth',
                block: 'center'
            });
        }
    }

    updateSelectionVisual(type, value);
}

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

function setupScrollListeners() {
    const hoursList = document.getElementById('hoursList');
    const minutesList = document.getElementById('minutesList');
    const periodList = document.getElementById('periodList');

    if (!hoursList.dataset.added) {
        hoursList.addEventListener('scroll', () => handleInfiniteScroll(hoursList, 'hour'));
        hoursList.dataset.added = true;
    }
    if (!minutesList.dataset.added) {
        minutesList.addEventListener('scroll', () => handleInfiniteScroll(minutesList, 'minute'));
        minutesList.dataset.added = true;
    }
    if (!periodList.dataset.added) {
        periodList.addEventListener('scroll', () => handlePeriodScroll(periodList));
        periodList.dataset.added = true;
    }
}

function handleInfiniteScroll(container, type) {
    if (container.dataset.isAdjusting === 'true') {
        return;
    }

    const scrollTop = container.scrollTop;
    const scrollHeight = container.scrollHeight;
    const clientHeight = container.clientHeight;
    
    const maxScroll = scrollHeight - clientHeight;
    const buffer = clientHeight * 0.5;

    if (scrollTop < buffer) {
        container.dataset.isAdjusting = 'true';
        const offset = scrollTop;
        container.scrollTop = (scrollHeight / 2) + offset;
        setTimeout(() => {
            delete container.dataset.isAdjusting;
        }, 100);
    }
    else if (scrollTop > maxScroll - buffer) {
        container.dataset.isAdjusting = 'true';
        const offset = scrollTop - maxScroll;
        container.scrollTop = (scrollHeight / 2) + offset;
        setTimeout(() => {
            delete container.dataset.isAdjusting;
        }, 100);
    }

    updateSelectedFromScroll(container, type);

    clearTimeout(container.snapTimeout);
    container.snapTimeout = setTimeout(() => {
        snapSelectedToCenter(container, type);
    }, 150);
}

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

function snapSelectedToCenter(container, type) {
    if (container.dataset.isAdjusting === 'true') return;
    
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
        closest.scrollIntoView({
            behavior: 'smooth',
            block: 'center'
        });

        const value = parseInt(closest.dataset.value);
        if (!isNaN(value)) {
            if (type === 'hour') selectedHour = value;
            if (type === 'minute') selectedMinute = value;
            updateSelectionVisual(type, value);
        }
    }
}

function handlePeriodScroll(container) {
    const items = Array.from(container.querySelectorAll('.time-picker-item:not(.time-picker-spacer)'));
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
        selectedPeriod = closest.dataset.value;
        updateSelectionVisual('period', selectedPeriod);
    }

    clearTimeout(container.snapTimeout);
    container.snapTimeout = setTimeout(() => {
        snapPeriodToCenter(container);
    }, 150);
}

function snapPeriodToCenter(container) {
    const items = Array.from(container.querySelectorAll('.time-picker-item:not(.time-picker-spacer)'));
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
        closest.scrollIntoView({
            behavior: 'smooth',
            block: 'center'
        });

        selectedPeriod = closest.dataset.value;
        updateSelectionVisual('period', selectedPeriod);
    }
}

function updateSelectionVisual(type, value) {
    try {
        const id = type === 'hour' ? 'hoursList' : type === 'minute' ? 'minutesList' : 'periodList';
        const list = document.getElementById(id);
        if (!list) return;
        
        const items = Array.from(list.querySelectorAll('.time-picker-item'));
        const center = list.getBoundingClientRect().top + list.clientHeight / 2;

        items.forEach(item => item.classList.remove('selected'));

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

function confirmTimeSelection() {
    if (!currentTimeField) return;

    const time24 = convertTo24Hour(selectedHour, selectedMinute, selectedPeriod);
    const display = `${selectedHour.toString().padStart(2, '0')}:${selectedMinute
        .toString().padStart(2, '0')} ${selectedPeriod}`;

    document.getElementById(currentTimeField).value = time24;
    document.getElementById(`${currentTimeField}_display`).textContent = display;

    closeTimePicker();
}

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

// ===============================
// SCHEDULE VIEW FUNCTIONS
// ===============================
function loadScheduleView(sectionId, sectionName, curriculumInfo) {
    currentSectionId = sectionId;
    
    document.getElementById('scheduleEmptyState').style.display = 'none';
    document.getElementById('scheduleView').style.display = 'block';
    
    document.getElementById('scheduleSectionName').textContent = sectionName;
    document.getElementById('scheduleCurriculum').textContent = curriculumInfo;
    document.getElementById('sidebarCurriculum').textContent = 'Curriculum: ' + curriculumInfo;

    document.querySelectorAll('.section-card').forEach(card => card.classList.remove('selected'));
    const cardEl = document.querySelector(`.section-card[data-section-id="${sectionId}"]`);
    if (cardEl) cardEl.classList.add('selected');
    
    fetch(`/admin/section/${sectionId}/schedule-data/`)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                renderSchedule(data.schedules);
                renderCoursesList(data.courses);
            } else {
                console.error('Error loading schedule:', data.error);
                showNotification('Error loading schedule data', 'error');
            }
        })
        .catch(err => {
            console.error('Error loading schedule view:', err);
            showNotification('Error loading schedule', 'error');
        });
}

function renderSchedule(schedules) {
            console.log('Rendering schedules:', schedules);
            
            // Generate time slots and labels
            const timeSlots = generateTimeSlots();
            const timeColumn = document.getElementById('timeColumn');
            timeColumn.innerHTML = '';
            
            // Add time labels at proper positions
            timeSlots.forEach(time => {
                const label = document.createElement('div');
                label.className = 'time-label';
                label.textContent = time;
                label.style.top = `${calculateTopPosition(time)}px`;
                timeColumn.appendChild(label);
            });
            
            // Clear all day columns
            document.querySelectorAll('.schedule-day-column').forEach(col => {
                col.innerHTML = '';
            });
            
            // Render schedule blocks
            schedules.forEach(schedule => {
                const dayColumn = document.querySelector(`.schedule-day-column[data-day="${schedule.day}"]`);
                if (!dayColumn) return;
                
                const block = document.createElement('div');
                block.className = 'schedule-block';
                
                // Calculate position and height
                const topPos = calculateTopPosition(schedule.start_time);
                const duration = schedule.duration || calculateDuration(schedule.start_time, schedule.end_time);
                const height = (duration / 30) * 60; // 60px per 30 minutes
                
                // Apply styles
                const hexColor = schedule.course_color;
                block.style.backgroundColor = hexToRGBA(hexColor, 0.25);
                block.style.borderLeftColor = hexColor;
                block.style.top = `${topPos}px`;
                block.style.height = `${height}px`;
                
                // Add content
                block.innerHTML = `
                    <div class="schedule-course-code">${schedule.course_code}</div>
                    <div class="schedule-details">${schedule.start_time} - ${schedule.end_time}</div>
                    <div class="schedule-details">Room: ${schedule.room}</div>
                    <div class="schedule-details">Section: ${schedule.section_name}</div>
                `;
                
                dayColumn.appendChild(block);
            });
        }
        
        // Calculate top position based on time (7:00 AM = 0px)
        function calculateTopPosition(timeStr) {
            const [hours, minutes] = timeStr.split(':').map(Number);
            const totalMinutes = (hours * 60 + minutes) - (7 * 60); // Offset from 7:00 AM
            return (totalMinutes / 30) * 60; // 60px per 30 minutes
        }
        
        // Helper function to convert hex to rgba
        function hexToRGBA(hex, alpha) {
            const r = parseInt(hex.slice(1, 3), 16);
            const g = parseInt(hex.slice(3, 5), 16);
            const b = parseInt(hex.slice(5, 7), 16);
            return `rgba(${r}, ${g}, ${b}, ${alpha})`;
        }

        function renderCoursesList(courses) {
            console.log('Rendering courses:', courses);
            
            const coursesList = document.getElementById('coursesList');
            coursesList.innerHTML = '';
            
            if (!courses || courses.length === 0) {
                coursesList.innerHTML = '<div class="card-empty-message">No courses available</div>';
                return;
            }
            
            courses.forEach(course => {
                const courseItem = document.createElement('div');
                courseItem.className = 'course-item';
                courseItem.style.borderLeftColor = course.color;
                courseItem.innerHTML = `
                    <div class="course-details">
                        <div class="course-code">${course.course_code}</div>
                        <div class="course-title">${course.descriptive_title}</div>
                        <div class="course-info">
                            <span>Lecture: ${course.lecture_hours}h</span>
                            <span>Laboratory: ${course.laboratory_hours}h</span>
                            <span>Credit Unit: ${course.credit_units}</span>
                        </div>
                    </div>
                `;
                coursesList.appendChild(courseItem);
            });
        }

        function generateTimeSlots() {
            const slots = [];
            // Start at 7:30 AM
            slots.push('07:30');
            // 8:00 to 9:00 PM (21:00)
            for (let hour = 8; hour <= 21; hour++) {
                slots.push(`${hour.toString().padStart(2, '0')}:00`);
                if (hour < 21) {
                    slots.push(`${hour.toString().padStart(2, '0')}:30`);
                }
            }
            // End at 9:30 PM
            slots.push('21:30');
            return slots;
        }

        function calculateDuration(startTime, endTime) {
            const [startHour, startMin] = startTime.split(':').map(Number);
            const [endHour, endMin] = endTime.split(':').map(Number);
            const duration = (endHour * 60 + endMin) - (startHour * 60 + startMin);
            return duration;
        }

        function exportSchedule() {
            if (currentSectionId) {
                window.location.href = `/admin/section/${currentSectionId}/export-pdf/`;
            }
        }

        function printSchedule() {
            if (currentSectionId) {
                window.print();
            }
        }
        
function filterSections() {
    const searchInput = document.getElementById('searchInput').value.toLowerCase();
    const sectionCards = document.querySelectorAll('.section-card');
    
    sectionCards.forEach(card => {
        const name = card.dataset.sectionName || '';
        const curriculum = card.dataset.curriculum || '';
        
        if (name.includes(searchInput) || curriculum.includes(searchInput)) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

function toggleSectionMenu(event, sectionId) {
    event.stopPropagation();
    const menu = document.getElementById(`sectionMenu${sectionId}`);
    if (menu) {
        menu.classList.toggle('show');
    }
}

function openEditSectionModal(sectionId) {
    console.log('Edit section:', sectionId);
}

function deleteSection(sectionId, sectionName) {
    if (confirm(`Are you sure you want to delete ${sectionName}?`)) {
        fetchWithCSRF(`/admin/section/delete/${sectionId}/`, {
            method: 'POST'
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showNotification('Section deleted successfully!', 'success');
                setTimeout(() => window.location.reload(), 1000);
            } else {
                showNotification('Error deleting section', 'error');
            }
        });
    }
}

function toggleStatus(event, sectionId) {
    event.stopPropagation();
    fetchWithCSRF(`/admin/section/${sectionId}/toggle-status/`, {
        method: 'POST'
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            const statusEl = document.getElementById(`status-${sectionId}`);
            if (statusEl) {
                statusEl.textContent = data.status_display;
                statusEl.style.color = data.status === 'complete' ? '#28a745' : '#dc3545';
            }
        }
    });
}