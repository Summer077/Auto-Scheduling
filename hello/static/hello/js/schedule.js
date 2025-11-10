console.log('schedule.js loaded successfully');

let currentSectionId = null;
let currentTimeField = null;
let currentEditScheduleId = null;
let selectedHour = 7;
let selectedMinute = 30;
let selectedPeriod = 'AM';

// ===============================
// TAB SWITCHING
// ===============================
function switchTab(tabName) {
    // Remove active class from all tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    // Add active class to selected tab
    if (tabName === 'generate') {
        document.querySelector('.tab-btn:first-child').classList.add('active');
        document.getElementById('generateTab').classList.add('active');
    } else {
        document.querySelector('.tab-btn:last-child').classList.add('active');
        document.getElementById('manualTab').classList.add('active');
    }
}

// ===============================
// MODAL MANAGEMENT
// ===============================
function openScheduleModal() {
    switchTab('manual'); // Default to manual tab
    openModal('scheduleModal');
}

function openModal(modalId) {
    const el = document.getElementById(modalId);
    if (el) el.style.display = 'block';
}

function closeModal(modalId) {
    const el = document.getElementById(modalId);
    if (el) el.style.display = 'none';
}

// ===============================
// ALERT SYSTEM
// ===============================
function showAlert(message, type = 'info') {
    const container = document.querySelector('.alert-container') || createAlertContainer();
    
    const alert = document.createElement('div');
    alert.className = `alert ${type}`;
    
    let icon = '';
    switch(type) {
        case 'success':
            icon = '<svg stroke="currentColor" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"></path></svg>';
            break;
        case 'warning':
            icon = '<svg stroke="currentColor" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"></path></svg>';
            break;
        case 'error':
            icon = '<svg stroke="currentColor" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"></path></svg>';
            break;
        default: // info
            icon = '<svg stroke="currentColor" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M13 16h-1v-4h1m0-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"></path></svg>';
    }
    
    alert.innerHTML = `
        ${icon}
        <p class="alert-text">${message}</p>
    `;
    
    container.appendChild(alert);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        alert.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => alert.remove(), 300);
    }, 5000);
    
    // Click to dismiss
    alert.addEventListener('click', () => {
        alert.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => alert.remove(), 300);
    });
}

function createAlertContainer() {
    const container = document.createElement('div');
    container.className = 'alert-container';
    document.body.appendChild(container);
    return container;
}

// ===============================
// LOADING OVERLAY
// ===============================
function showLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.add('show');
    }
}

function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.remove('show');
    }
}

// ===============================
// GENERATE SCHEDULE
// ===============================
function updateGenerateFilters() {
    const select = document.getElementById('generate_section_select');
    const selectedOption = select.options[select.selectedIndex];
    
    if (selectedOption.value) {
        document.getElementById('generate_curriculum_display').value = selectedOption.dataset.curriculum;
        
        const yearLevel = selectedOption.dataset.year;
        const yearText = yearLevel == 1 ? '1st Year' : yearLevel == 2 ? '2nd Year' : yearLevel == 3 ? '3rd Year' : '4th Year';
        document.getElementById('generate_year_display').value = yearText;
        
        const semester = selectedOption.dataset.semester;
        const semText = semester == 1 ? '1st Semester' : '2nd Semester';
        document.getElementById('generate_semester_display').value = semText;
    } else {
        document.getElementById('generate_curriculum_display').value = '';
        document.getElementById('generate_year_display').value = '';
        document.getElementById('generate_semester_display').value = '';
    }
}

function submitGenerateSchedule(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const sectionId = formData.get('section');
    
    if (!sectionId) {
        showAlert('Please select a section', 'error');
        return;
    }
    
    // Show loading
    showLoading();
    closeModal('scheduleModal');
    
    fetchWithCSRF('/admin/schedule/generate/', {
        method: 'POST',
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        hideLoading();
        
        if (data.success) {
            let message = `Successfully generated ${data.schedules_created} schedule entries!`;
            
            if (data.conflicts && data.conflicts.length > 0) {
                showAlert(`${message} Some conflicts detected.`, 'warning');
                console.log('Conflicts:', data.conflicts);
            } else {
                showAlert(message, 'success');
            }
            
            // Reload the schedule view
            if (data.section_id) {
                const sectionCard = document.querySelector(`[data-section-id="${data.section_id}"]`);
                if (sectionCard) {
                    const sectionName = sectionCard.querySelector('.card-title').textContent;
                    const curriculum = sectionCard.querySelector('.card-subtitle').textContent;
                    setTimeout(() => loadScheduleView(data.section_id, sectionName, curriculum), 500);
                }
            }
        } else {
            const err = data.errors ? data.errors.join(', ') : (data.error || 'Unknown error');
            showAlert('Error generating schedule: ' + err, 'error');
        }
    })
    .catch(err => {
        hideLoading();
        console.error('submitGenerateSchedule error', err);
        showAlert('Error generating schedule', 'error');
    });
}

// ===============================
// MANUAL SCHEDULE CREATION
// ===============================
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
            showAlert('Schedule created successfully!', 'success');
            closeModal('scheduleModal');
            if (currentSectionId) {
                setTimeout(() => {
                    const sectionName = document.getElementById('scheduleSectionName').textContent;
                    const curriculum = document.getElementById('scheduleCurriculum').textContent;
                    loadScheduleView(currentSectionId, sectionName, curriculum);
                }, 500);
            } else {
                setTimeout(() => window.location.reload(), 800);
            }
        } else {
            const err = data.errors ? data.errors.join(', ') : (data.error || 'Unknown error');
            showAlert('Error creating schedule: ' + err, 'error');
        }
    })
    .catch(err => {
        console.error('submitCreateSchedule error', err);
        showAlert('Error creating schedule', 'error');
    });
}

// ===============================
// EDIT SCHEDULE
// ===============================
function openEditScheduleModal(scheduleId) {
    currentEditScheduleId = scheduleId;
    
    // Fetch schedule data
    fetch(`/admin/schedule/edit/${scheduleId}/`)
        .then(res => res.json())
        .then(data => {
            document.getElementById('edit_schedule_id').value = data.id;
            document.getElementById('edit_course_select').value = data.course;
            document.getElementById('edit_faculty_select').value = data.faculty;
            document.getElementById('edit_room_select').value = data.room;
            document.getElementById('edit_day_select').value = data.day;
            
            // Set times
            document.getElementById('edit_start_time').value = data.start_time;
            document.getElementById('edit_end_time').value = data.end_time;
            
            const [startTime, startPeriod] = convertTo12Hour(data.start_time);
            document.getElementById('edit_start_time_display').textContent = `${startTime} ${startPeriod}`;
            
            const [endTime, endPeriod] = convertTo12Hour(data.end_time);
            document.getElementById('edit_end_time_display').textContent = `${endTime} ${endPeriod}`;
            
            openModal('editScheduleModal');
        })
        .catch(err => {
            console.error('Error fetching schedule data:', err);
            showAlert('Error loading schedule data', 'error');
        });
}

function submitEditSchedule(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const scheduleId = document.getElementById('edit_schedule_id').value;
    
    fetchWithCSRF(`/admin/schedule/edit/${scheduleId}/`, {
        method: 'POST',
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showAlert('Schedule updated successfully!', 'success');
            closeModal('editScheduleModal');
            if (currentSectionId) {
                setTimeout(() => {
                    const sectionName = document.getElementById('scheduleSectionName').textContent;
                    const curriculum = document.getElementById('scheduleCurriculum').textContent;
                    loadScheduleView(currentSectionId, sectionName, curriculum);
                }, 500);
            }
        } else {
            const err = data.errors ? data.errors.join(', ') : (data.error || 'Unknown error');
            showAlert('Error updating schedule: ' + err, 'error');
        }
    })
    .catch(err => {
        console.error('submitEditSchedule error', err);
        showAlert('Error updating schedule', 'error');
    });
}

function deleteScheduleFromEdit() {
    const scheduleId = document.getElementById('edit_schedule_id').value;
    
    if (!confirm('Are you sure you want to delete this schedule?')) {
        return;
    }
    
    fetchWithCSRF(`/admin/schedule/delete/${scheduleId}/`, {
        method: 'POST'
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showAlert('Schedule deleted successfully!', 'success');
            closeModal('editScheduleModal');
            if (currentSectionId) {
                setTimeout(() => {
                    const sectionName = document.getElementById('scheduleSectionName').textContent;
                    const curriculum = document.getElementById('scheduleCurriculum').textContent;
                    loadScheduleView(currentSectionId, sectionName, curriculum);
                }, 500);
            }
        } else {
            showAlert('Error deleting schedule', 'error');
        }
    })
    .catch(err => {
        console.error('deleteScheduleFromEdit error', err);
        showAlert('Error deleting schedule', 'error');
    });
}

// ===============================
// SCHEDULE BLOCK CLICK HANDLER
// ===============================
function handleScheduleBlockClick(scheduleId) {
    openEditScheduleModal(scheduleId);
}

// ===============================
// LOAD SCHEDULE VIEW
// ===============================
function loadScheduleView(sectionId, sectionName, curriculum) {
    currentSectionId = sectionId;
    
    // Update header
    document.getElementById('scheduleSectionName').textContent = sectionName;
    document.getElementById('scheduleCurriculum').textContent = curriculum;
    document.getElementById('sidebarCurriculum').textContent = curriculum;
    
    // Show schedule view, hide empty state
    document.getElementById('scheduleEmptyState').style.display = 'none';
    document.getElementById('scheduleView').style.display = 'flex';
    
    // Fetch schedule data
    fetch(`/admin/section/${sectionId}/schedule-data/`)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                renderScheduleGrid(data.schedules, sectionName);
                renderCoursesSidebar(data.courses);
            } else {
                showAlert('Error loading schedule data', 'error');
            }
        })
        .catch(err => {
            console.error('Error loading schedule:', err);
            showAlert('Error loading schedule', 'error');
        });
}

// ===============================
// RENDER SCHEDULE GRID
// ===============================
function renderScheduleGrid(schedules, sectionName = '') {
    // Clear existing schedule blocks
    document.querySelectorAll('.schedule-block').forEach(block => block.remove());
    
    // Render time labels
    renderTimeLabels();
    
    // Render each schedule
    schedules.forEach(schedule => {
        const dayColumn = document.querySelector(`.schedule-day-column[data-day="${schedule.day}"]`);
        if (!dayColumn) return;
        
        const block = document.createElement('div');
        block.className = 'schedule-block';
        block.dataset.scheduleId = schedule.id;
        block.style.borderLeftColor = schedule.course_color;
        block.style.background = `${schedule.course_color}15`;
        
        // Calculate position and height (matching section.html logic)
        const top = calculateTopPosition(schedule.start_time);
        const duration = calculateDuration(schedule.start_time, schedule.end_time);
        const height = (duration / 30) * 60; // 60px per 30 minutes
        
        block.style.top = `${top}px`;
        block.style.height = `${height}px`;
        
        // Use section_name from API or fallback to passed sectionName
        const displaySectionName = schedule.section_name || sectionName;
        
        block.innerHTML = `
            <div class="schedule-course-code">${schedule.course_code}</div>
            <div class="schedule-details">${schedule.start_time} - ${schedule.end_time}</div>
            <div class="schedule-details">Room: ${schedule.room}</div>
            <div class="schedule-details">Section: ${displaySectionName}</div>
        `;
        
        // Add click handler
        block.addEventListener('click', () => handleScheduleBlockClick(schedule.id));
        
        dayColumn.appendChild(block);
    });
}

function renderTimeLabels() {
    const timeColumn = document.getElementById('timeColumn');
    timeColumn.innerHTML = '';
    
    // Generate time labels from 7:30 AM to 9:30 PM (matching section.html format)
    const times = generateTimeSlots();
    
    times.forEach((time) => {
        const label = document.createElement('div');
        label.className = 'time-label';
        label.textContent = time;  // Use 24-hour format without AM/PM
        label.style.top = `${calculateTopPosition(time)}px`;
        timeColumn.appendChild(label);
    });
}

function generateTimeSlots() {
    const slots = [];
    // Start at 7:30 AM
    slots.push('07:30');
    // 8:00 to 21:00
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

function timeToMinutes(time) {
    const [hours, minutes] = time.split(':').map(Number);
    return hours * 60 + minutes;
}

// Calculate top position from time string (60px per 30 minutes, offset from 7:00 AM)
function calculateTopPosition(timeStr) {
    const [hours, minutes] = timeStr.split(':').map(Number);
    const totalMinutes = (hours * 60 + minutes) - (7 * 60); // Offset from 7:00 AM
    return (totalMinutes / 30) * 60; // 60px per 30 minutes
}

// Calculate duration in minutes between two times
function calculateDuration(startTime, endTime) {
    const startMinutes = timeToMinutes(startTime);
    const endMinutes = timeToMinutes(endTime);
    return endMinutes - startMinutes;
}

// ===============================
// RENDER COURSES SIDEBAR
// ===============================
function renderCoursesSidebar(courses) {
    const coursesList = document.getElementById('coursesList');
    coursesList.innerHTML = '';
    
    if (courses.length === 0) {
        coursesList.innerHTML = '<p style="color: #6C757D; font-size: 0.875rem;">No courses scheduled yet.</p>';
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
                    <span>Lec: ${course.lecture_hours}h | Lab: ${course.laboratory_hours}h</span>
                    <span>Units: ${course.credit_units}</span>
                </div>
            </div>
        `;
        
        coursesList.appendChild(courseItem);
    });
}

// ===============================
// TIME PICKER (Keep existing code)
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

function populateTimePicker() {
    const hoursList = document.getElementById('hoursList');
    const minutesList = document.getElementById('minutesList');
    const periodList = document.getElementById('periodList');

    hoursList.innerHTML = '';
    minutesList.innerHTML = '';
    periodList.innerHTML = '';

    // HOURS
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

    // MINUTES
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

    // PERIOD
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

    if (!hoursList.dataset.added) {
        hoursList.addEventListener('scroll', () => handleInfiniteScroll(hoursList, 'hour'));
        hoursList.dataset.added = true;
    }
    if (!minutesList.dataset.added) {
        minutesList.addEventListener('scroll', () => handleInfiniteScroll(minutesList, 'minute'));
        minutesList.dataset.added = true;
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

// ===============================
// SEARCH AND FILTER
// ===============================
function filterSections() {
    const searchInput = document.getElementById('searchInput').value.toLowerCase();
    const sectionCards = document.querySelectorAll('.section-card');
    
    sectionCards.forEach(card => {
        const sectionName = card.dataset.sectionName;
        const curriculum = card.dataset.curriculum;
        
        if (sectionName.includes(searchInput) || curriculum.includes(searchInput)) {
            card.style.display = 'flex';
        } else {
            card.style.display = 'none';
        }
    });
}

// ===============================
// SECTION MENU TOGGLE
// ===============================
function toggleSectionMenu(event, sectionId) {
    event.stopPropagation();
    
    // Close all other menus
    document.querySelectorAll('.section-dropdown-menu').forEach(menu => {
        if (menu.id !== `sectionMenu${sectionId}`) {
            menu.classList.remove('show');
        }
    });
    
    // Toggle current menu
    const menu = document.getElementById(`sectionMenu${sectionId}`);
    menu.classList.toggle('show');
}

// Close menus when clicking outside
document.addEventListener('click', (event) => {
    if (!event.target.closest('.dropdown-menu-container')) {
        document.querySelectorAll('.section-dropdown-menu').forEach(menu => {
            menu.classList.remove('show');
        });
    }
});

// ===============================
// DROPDOWN TOGGLE (Admin)
// ===============================
function toggleDropdown() {
    const dropdown = document.getElementById('dropdownMenu');
    dropdown.classList.toggle('show');
}

// Close dropdown when clicking outside
document.addEventListener('click', (event) => {
    if (!event.target.closest('.admin-section')) {
        const dropdown = document.getElementById('dropdownMenu');
        if (dropdown) {
            dropdown.classList.remove('show');
        }
    }
});

// ===============================
// STATUS TOGGLE
// ===============================
function toggleStatus(event, sectionId) {
    event.stopPropagation();
    
    if (!confirm('Are you sure you want to toggle the status of this section?')) {
        return;
    }
    
    fetchWithCSRF(`/admin/section/${sectionId}/toggle-status/`, {
        method: 'POST'
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            const statusElement = document.getElementById(`status-${sectionId}`);
            statusElement.textContent = data.status_display;
            showAlert('Status updated successfully!', 'success');
        } else {
            showAlert('Error updating status', 'error');
        }
    })
    .catch(err => {
        console.error('toggleStatus error', err);
        showAlert('Error updating status', 'error');
    });
}

// ===============================
// SECTION CRUD OPERATIONS
// ===============================
function openEditSectionModal(sectionId) {
    // This function would need to be implemented similar to edit schedule
    // For now, show a placeholder
    showAlert('Edit section functionality - to be implemented', 'info');
}

function deleteSection(sectionId, sectionName) {
    if (!confirm(`Are you sure you want to delete section ${sectionName}? This action cannot be undone.`)) {
        return;
    }
    
    fetchWithCSRF(`/admin/section/delete/${sectionId}/`, {
        method: 'POST'
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showAlert(`Section ${sectionName} deleted successfully!`, 'success');
            setTimeout(() => window.location.reload(), 1000);
        } else {
            const err = data.errors ? data.errors.join(', ') : 'Unknown error';
            showAlert(`Error deleting section: ${err}`, 'error');
        }
    })
    .catch(err => {
        console.error('deleteSection error', err);
        showAlert('Error deleting section', 'error');
    });
}

// ===============================
// EXPORT AND PRINT FUNCTIONS
// ===============================
function exportSchedule() {
    if (!currentSectionId) {
        showAlert('Please select a section first', 'warning');
        return;
    }
    
    showAlert('Export to PDF functionality - to be implemented', 'info');
    // TODO: Implement PDF export functionality
}

function printSchedule() {
    if (!currentSectionId) {
        showAlert('Please select a section first', 'warning');
        return;
    }
    
    const scheduleView = document.getElementById('scheduleView');
    const printWindow = window.open('', '_blank');
    
    printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>Schedule - ${document.getElementById('scheduleSectionName').textContent}</title>
            <style>
                body {
                    font-family: 'Lexend', Arial, sans-serif;
                    padding: 20px;
                }
                h1 {
                    text-align: center;
                    margin-bottom: 10px;
                }
                .subtitle {
                    text-align: center;
                    color: #666;
                    margin-bottom: 30px;
                }
                .schedule-grid-wrapper {
                    border: 1px solid #CED4DA;
                    border-radius: 8px;
                    overflow: hidden;
                }
                /* Copy relevant CSS for schedule grid */
                @media print {
                    .no-print {
                        display: none;
                    }
                }
            </style>
        </head>
        <body>
            <h1>${document.getElementById('scheduleSectionName').textContent}</h1>
            <div class="subtitle">${document.getElementById('scheduleCurriculum').textContent}</div>
            ${scheduleView.innerHTML}
        </body>
        </html>
    `);
    
    printWindow.document.close();
    setTimeout(() => {
        printWindow.print();
    }, 500);
}

// ===============================
// INITIALIZATION
// ===============================
document.addEventListener('DOMContentLoaded', () => {
    console.log('Schedule page initialized');
    
    // Create alert container if it doesn't exist
    if (!document.querySelector('.alert-container')) {
        createAlertContainer();
    }
    
    // Add loading overlay if it doesn't exist
    if (!document.getElementById('loadingOverlay')) {
        const overlay = document.createElement('div');
        overlay.id = 'loadingOverlay';
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `
            <div class="loader"></div>
            <p class="loading-text">Generating Schedule...</p>
        `;
        document.body.appendChild(overlay);
    }
});