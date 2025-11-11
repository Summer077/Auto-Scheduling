let currentSectionId = null;
        let currentTimeField = null;
        let currentEditScheduleId = null;
        let selectedHour = 7;
        let selectedMinute = 30;
        let selectedPeriod = 'AM';

        // Tab switching
        function switchTab(tabName) {
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            if (tabName === 'generate') {
                document.querySelector('.tab-btn:first-child').classList.add('active');
                document.getElementById('generateTab').classList.add('active');
            } else {
                document.querySelector('.tab-btn:last-child').classList.add('active');
                document.getElementById('manualTab').classList.add('active');
            }
        }

        // Modal management
        function openScheduleModal() {
            switchTab('manual');
            openModal('scheduleModal');
        }

        function openModal(modalId) {
            document.getElementById(modalId).style.display = 'block';
        }

        function closeModal(modalId) {
            document.getElementById(modalId).style.display = 'none';
        }

        // Alert system
        function showAlert(message, type = 'info') {
            let container = document.querySelector('.alert-container');
            if (!container) {
                container = document.createElement('div');
                container.className = 'alert-container';
                document.body.appendChild(container);
            }
            
            const alert = document.createElement('div');
            alert.className = `alert ${type}`;
            
            const icons = {
                success: '<svg stroke="currentColor" viewBox="0 0 24 24" fill="none"><path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"></path></svg>',
                warning: '<svg stroke="currentColor" viewBox="0 0 24 24" fill="none"><path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"></path></svg>',
                error: '<svg stroke="currentColor" viewBox="0 0 24 24" fill="none"><path d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"></path></svg>',
                info: '<svg stroke="currentColor" viewBox="0 0 24 24" fill="none"><path d="M13 16h-1v-4h1m0-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"></path></svg>'
            };
            
            alert.innerHTML = `${icons[type] || icons.info}<p class="alert-text">${message}</p>`;
            container.appendChild(alert);
            
            setTimeout(() => {
                alert.style.animation = 'fadeOut 0.3s ease';
                setTimeout(() => alert.remove(), 300);
            }, 5000);
            
            alert.addEventListener('click', () => {
                alert.style.animation = 'fadeOut 0.3s ease';
                setTimeout(() => alert.remove(), 300);
            });
        }

        // Loading overlay
        function showLoading() {
            document.getElementById('loadingOverlay').classList.add('show');
        }

        function hideLoading() {
            document.getElementById('loadingOverlay').classList.remove('show');
        }

        // Generate filters update
        function updateGenerateFilters() {
            const select = document.getElementById('generate_section_select');
            const option = select.options[select.selectedIndex];
            
            if (option.value) {
                document.getElementById('generate_curriculum_display').value = option.dataset.curriculum;
                const year = option.dataset.year;
                const yearText = year == 1 ? '1st Year' : year == 2 ? '2nd Year' : year == 3 ? '3rd Year' : '4th Year';
                document.getElementById('generate_year_display').value = yearText;
                const semester = option.dataset.semester;
                document.getElementById('generate_semester_display').value = semester == 1 ? '1st Semester' : '2nd Semester';
            } else {
                document.getElementById('generate_curriculum_display').value = '';
                document.getElementById('generate_year_display').value = '';
                document.getElementById('generate_semester_display').value = '';
            }
        }

        // CSRF helper
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

        // Generate schedule submission
        function submitGenerateSchedule(event) {
            event.preventDefault();
            const formData = new FormData(event.target);
            const sectionId = formData.get('section');
            
            if (!sectionId) {
                showAlert('Please select a section', 'error');
                return;
            }
            
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
                    const message = `Successfully generated ${data.schedules_created} schedule entries!`;
                    
                    if (data.notes && data.notes.length > 0) {
                        showAlert(`${message} Check notes below.`, 'info');
                        console.log('Scheduling Notes:', data.notes);
                        // Log notes to console
                        data.notes.forEach(note => console.log('📌', note));
                    } else {
                        showAlert(message, 'success');
                    }
                    
                    if (data.section_id) {
                        const card = document.querySelector(`[data-section-id="${data.section_id}"]`);
                        if (card) {
                            const sectionName = card.querySelector('.card-title').textContent;
                            const curriculum = card.querySelector('.card-subtitle').textContent;
                            // Load schedule view immediately and show confirmation modal
                            loadScheduleView(data.section_id, sectionName, curriculum);
                            // Show confirmation modal after schedule loads
                            setTimeout(() => showScheduleConfirmation(data.section_id, data.notes), 800);
                        }
                    }
                } else {
                    const err = data.errors ? data.errors.join(', ') : (data.error || 'Unknown error');
                    showAlert('Error generating schedule: ' + err, 'error');
                }
            })
            .catch(err => {
                hideLoading();
                console.error('Generate error:', err);
                showAlert('Error generating schedule', 'error');
            });
        }

        // Show schedule confirmation modal
        function showScheduleConfirmation(sectionId, notes) {
            const confirmModal = document.createElement('div');
            confirmModal.className = 'modal';
            confirmModal.id = 'scheduleConfirmModal';
            confirmModal.style.display = 'block';
            
            let notesHtml = '';
            if (notes && notes.length > 0) {
                notesHtml = `
                    <div style="background-color: #e7f3ff; border-left: 4px solid #2196F3; padding: 12px; margin-bottom: 15px; border-radius: 4px;">
                        <strong style="color: #1976D2;">Scheduling Notes:</strong>
                        <ul style="margin: 8px 0 0 20px; color: #495057; font-size: 0.9rem;">
                            ${notes.map(note => `<li style="margin: 4px 0;">${note}</li>`).join('')}
                        </ul>
                    </div>
                `;
            }
            
            confirmModal.innerHTML = `
                <div class="modal-content" style="max-width: 600px;">
                    <div class="modal-header">
                        <h2>Schedule Generated</h2>
                        <span class="close" onclick="closeScheduleConfirmation()">&times;</span>
                    </div>
                    <div style="padding: 30px;">
                        ${notesHtml}
                        <p style="font-size: 1rem; color: #495057; margin-bottom: 20px; line-height: 1.6;">
                            The schedule has been generated successfully. Please review the schedule on the right panel.
                        </p>
                        <p style="font-size: 0.95rem; color: #6C757D; margin-bottom: 0; line-height: 1.5;">
                            You can click on any schedule block to edit the details, or finalize the schedule if everything looks good.
                        </p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn-secondary" onclick="regenerateSchedule(${sectionId})">
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18">
                                <path fill="currentColor" d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/>
                            </svg>
                            Regenerate
                        </button>
                        <button type="button" class="btn-primary" onclick="finalizeSchedule(${sectionId})">
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18">
                                <path fill="currentColor" d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z"/>
                            </svg>
                            Finalize Schedule
                        </button>
                    </div>
                </div>
            `;
            document.body.appendChild(confirmModal);
        }

        function closeScheduleConfirmation() {
            const modal = document.getElementById('scheduleConfirmModal');
            if (modal) {
                modal.remove();
            }
        }

        function regenerateSchedule(sectionId) {
            closeScheduleConfirmation();
            const section = document.querySelector(`[data-section-id="${sectionId}"]`);
            if (section) {
                const selectElement = document.getElementById('generate_section_select');
                selectElement.value = sectionId;
                updateGenerateFilters();
                switchTab('generate');
                openModal('scheduleModal');
            }
        }

        function finalizeSchedule(sectionId) {
            fetchWithCSRF(`/admin/section/${sectionId}/toggle-status/`, {
                method: 'POST'
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showAlert('Schedule finalized successfully!', 'success');
                    closeScheduleConfirmation();
                    // Update the status display on the card
                    const statusElement = document.getElementById(`status-${sectionId}`);
                    if (statusElement) {
                        statusElement.textContent = data.status_display;
                        statusElement.style.color = data.status === 'complete' ? '#28a745' : '#dc3545';
                    }
                } else {
                    showAlert('Error finalizing schedule', 'error');
                }
            })
            .catch(err => {
                console.error('Error finalizing schedule:', err);
                showAlert('Error finalizing schedule', 'error');
            });
        }

        // Manual schedule submission
        function submitCreateSchedule(event) {
            event.preventDefault();
            const formData = new FormData(event.target);

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
                console.error('Create error:', err);
                showAlert('Error creating schedule', 'error');
            });
        }

        // Edit schedule functions
        function openEditScheduleModal(scheduleId) {
            currentEditScheduleId = scheduleId;
            
            fetch(`/admin/schedule/edit/${scheduleId}/`)
                .then(res => res.json())
                .then(data => {
                    document.getElementById('edit_schedule_id').value = data.id;
                    document.getElementById('edit_course_select').value = data.course;
                    document.getElementById('edit_faculty_select').value = data.faculty;
                    document.getElementById('edit_room_select').value = data.room;
                    document.getElementById('edit_day_select').value = data.day;
                    
                    document.getElementById('edit_start_time').value = data.start_time;
                    document.getElementById('edit_end_time').value = data.end_time;
                    
                    const [startTime, startPeriod] = convertTo12Hour(data.start_time);
                    document.getElementById('edit_start_time_display').textContent = `${startTime} ${startPeriod}`;
                    
                    const [endTime, endPeriod] = convertTo12Hour(data.end_time);
                    document.getElementById('edit_end_time_display').textContent = `${endTime} ${endPeriod}`;
                    
                    openModal('editScheduleModal');
                })
                .catch(err => {
                    console.error('Error loading schedule:', err);
                    showAlert('Error loading schedule data', 'error');
                });
        }

        function submitEditSchedule(event) {
            event.preventDefault();
            const formData = new FormData(event.target);
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
                console.error('Edit error:', err);
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
                console.error('Delete error:', err);
                showAlert('Error deleting schedule', 'error');
            });
        }

        // Load schedule view
        function loadScheduleView(sectionId, sectionName, curriculum) {
            currentSectionId = sectionId;
            
            document.getElementById('scheduleSectionName').textContent = sectionName;
            document.getElementById('scheduleCurriculum').textContent = curriculum;
            document.getElementById('sidebarCurriculum').textContent = curriculum;
            
            document.getElementById('scheduleEmptyState').style.display = 'none';
            // Use block to match Section page rendering
            document.getElementById('scheduleView').style.display = 'block';
            
            document.querySelectorAll('.section-card').forEach(card => card.classList.remove('selected'));
            const cardEl = document.querySelector(`.section-card[data-section-id="${sectionId}"]`);
            if (cardEl) cardEl.classList.add('selected');
            
            fetch(`/admin/section/${sectionId}/schedule-data/`)
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        renderScheduleGrid(data.schedules);
                        renderCoursesSidebar(data.courses);
                    } else {
                        console.error('Error loading schedule:', data.error);
                        showAlert('Error loading schedule data', 'error');
                    }
                })
                .catch(err => {
                    console.error('Error loading schedule view:', err);
                    showAlert('Error loading schedule', 'error');
                });
        }

        // Render schedule grid
        function renderScheduleGrid(schedules) {
            const timeColumn = document.getElementById('timeColumn');
            timeColumn.innerHTML = '';

            // Use the same time slot generation as Section page
            const timeSlots = generateTimeSlots();

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
                    // Allow flexible day formats from server (0-5, 1-6, or weekday names)
                    const dayColumn = findDayColumn(schedule.day);
                if (!dayColumn) return;

                const block = document.createElement('div');
                block.className = 'schedule-block';
                // attach schedule id so handlers can reference it
                block.dataset.scheduleId = schedule.id;

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

                // Add content (match Section page)
                block.innerHTML = `
                    <div class="schedule-course-code">${schedule.course_code}</div>
                    <div class="schedule-details">${schedule.start_time} - ${schedule.end_time}</div>
                    <div class="schedule-details">Room: ${schedule.room}</div>
                    <div class="schedule-details">Section: ${schedule.section_name || ''}</div>
                    <div class="schedule-details">Professor: ${schedule.faculty || 'TBA'}</div>
                `;

                // debugging: log each schedule rendered to the browser console
                try {
                    console.debug('renderScheduleGrid item', schedule.id, schedule.course_code, 'day', schedule.day, schedule.start_time + '-' + schedule.end_time, 'top', topPos, 'height', height);
                } catch (e) {
                    // ignore if console not available
                }

                // clicking a block should open the edit modal (delete/edit from there)
                block.addEventListener('click', (e) => {
                    e.stopPropagation();
                    openEditScheduleModal(schedule.id);
                });

                dayColumn.appendChild(block);
            });
        }

        function calculateTopPosition(timeStr) {
            const [hours, minutes] = timeStr.split(':').map(Number);
                // Grid starts at 07:00 so subtract 7*60 = 420 minutes
                const gridStart = 7 * 60;
            const totalMinutes = (hours * 60 + minutes) - gridStart;
            return (totalMinutes / 30) * 60;
        }

        // Normalize/resolve different day formats coming from server
        function findDayColumn(dayValue) {
            // If already a column element was passed accidentally, return it
            if (dayValue instanceof Element && dayValue.classList.contains('schedule-day-column')) return dayValue;

            let idx = null;

            // numeric-like values
            if (typeof dayValue === 'number' || (/^\d+$/.test(String(dayValue)))) {
                const n = parseInt(dayValue, 10);
                // If server sends 0..5 (our template) use directly
                if (n >= 0 && n <= 5) idx = n;
                // If server uses 1..6 (Mon=1..Sat=6) convert to 0..5
                else if (n >= 1 && n <= 6) idx = n - 1;
                // If it's 7 or larger, map 7->6 (Sunday) but we don't have Sunday column -> return null
                else idx = null;
            } else if (typeof dayValue === 'string') {
                const s = dayValue.trim().toLowerCase();
                const nameMap = { monday: 0, tuesday: 1, wednesday: 2, thursday: 3, friday: 4, saturday: 5 };
                if (nameMap.hasOwnProperty(s)) idx = nameMap[s];
                else if (/^\d+$/.test(s)) {
                    const n = parseInt(s, 10);
                    if (n >= 0 && n <= 5) idx = n;
                    else if (n >= 1 && n <= 6) idx = n - 1;
                }
            }

            if (idx === null) {
                // no matching column
                console.warn('Unrecognized schedule.day value:', dayValue);
                return null;
            }

            return document.querySelector(`.schedule-day-column[data-day="${idx}"]`);
        }

        function hexToRGBA(hex, alpha) {
            const r = parseInt(hex.slice(1, 3), 16);
            const g = parseInt(hex.slice(3, 5), 16);
            const b = parseInt(hex.slice(5, 7), 16);
            return `rgba(${r}, ${g}, ${b}, ${alpha})`;
        }

        function calculateDuration(startTime, endTime) {
            const [startHour, startMin] = startTime.split(':').map(Number);
            const [endHour, endMin] = endTime.split(':').map(Number);
            return (endHour * 60 + endMin) - (startHour * 60 + startMin);
        }

        function renderCoursesSidebar(courses) {
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

        // Time picker functions
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
            document.getElementById('timePickerTitle').textContent = `Select ${fieldId.replace(/_/g, ' ').toUpperCase()}`;
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

            const hourValues = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];
            const repeatedHours = [];
            for (let i = 0; i < 20; i++) repeatedHours.push(...hourValues);
            repeatedHours.forEach(hour => {
                const item = document.createElement('button');
                item.className = 'time-picker-item';
                item.dataset.value = hour;
                item.textContent = hour.toString().padStart(2, '0');
                item.onclick = () => selectTimeItem('hour', hour);
                hoursList.appendChild(item);
            });

            const minuteValues = [];
            for (let m = 0; m < 60; m += 5) minuteValues.push(m);
            const repeatedMinutes = [];
            for (let i = 0; i < 20; i++) repeatedMinutes.push(...minuteValues);
            repeatedMinutes.forEach(minute => {
                const item = document.createElement('button');
                item.className = 'time-picker-item';
                item.dataset.value = minute;
                item.textContent = minute.toString().padStart(2, '0');
                item.onclick = () => selectTimeItem('minute', minute);
                minutesList.appendChild(item);
            });

            for (let i = 0; i < 4; i++) {
                const spacer = document.createElement('div');
                spacer.className = 'time-picker-item time-picker-spacer';
                spacer.innerHTML = '&nbsp;';
                periodList.appendChild(spacer);
            }
            ['AM', 'PM'].forEach(period => {
                const item = document.createElement('button');
                item.className = 'time-picker-item';
                item.dataset.value = period;
                item.textContent = period;
                item.onclick = () => selectTimeItem('period', period);
                periodList.appendChild(item);
            });
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
                scrollToValue(document.getElementById('hoursList'), value, type);
            } else if (type === 'minute') {
                selectedMinute = value;
                scrollToValue(document.getElementById('minutesList'), value, type);
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
                hoursList.addEventListener('scroll', () => {
                    handleInfiniteScroll(hoursList, 'hour');
                    scheduleCenterAfterScroll(hoursList);
                });
                hoursList.dataset.added = true;
            }

            if (!minutesList.dataset.added) {
                minutesList.addEventListener('scroll', () => {
                    handleInfiniteScroll(minutesList, 'minute');
                    scheduleCenterAfterScroll(minutesList);
                });
                minutesList.dataset.added = true;
            }

            // FIX FOR PERIOD LIST AUTO-CENTERING
            if (!periodList.dataset.added) {
                periodList.addEventListener('scroll', () => {
                    updateSelectedFromScroll(periodList, 'period');
                    scheduleCenterAfterScroll(periodList);
                });
                periodList.dataset.added = true;
            }
        }


        // Debounced centering: after user stops scrolling, center the .selected item
        function scheduleCenterAfterScroll(container) {
            try {
                // clear previous timer
                if (container._centerTimer) clearTimeout(container._centerTimer);
                container._centerTimer = setTimeout(() => {
                    // find selected item in this container
                    const sel = container.querySelector('.time-picker-item.selected');
                    if (sel) {
                        // Smoothly center the selected item
                        sel.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    } else {
                        // If none selected, try to compute closest and center it
                        const items = Array.from(container.querySelectorAll('.time-picker-item'));
                        if (items.length) {
                            const center = container.getBoundingClientRect().top + container.clientHeight / 2;
                            let closest = null;
                            let minDist = Infinity;
                            items.forEach(item => {
                                const rect = item.getBoundingClientRect();
                                const mid = rect.top + rect.height / 2;
                                const dist = Math.abs(center - mid);
                                if (dist < minDist) { minDist = dist; closest = item; }
                            });
                            if (closest) closest.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        }
                    }
                }, 120);
            } catch (e) {
                console.error('scheduleCenterAfterScroll error', e);
            }
        }

        function handleInfiniteScroll(container, type) {
            // Disable infinite scroll for AM/PM list
            if (type === 'period') {
                updateSelectedFromScroll(container, type);
                return;
            }

            if (container.dataset.isAdjusting === 'true') return;

            const scrollTop = container.scrollTop;
            const scrollHeight = container.scrollHeight;
            const clientHeight = container.clientHeight;
            const maxScroll = scrollHeight - clientHeight;
            const buffer = clientHeight * 0.5;

            if (scrollTop < buffer) {
                container.dataset.isAdjusting = 'true';
                const offset = scrollTop;
                container.scrollTop = (scrollHeight / 2) + offset;
                setTimeout(() => { delete container.dataset.isAdjusting; }, 100);
            } else if (scrollTop > maxScroll - buffer) {
                container.dataset.isAdjusting = 'true';
                const offset = scrollTop - maxScroll;
                container.scrollTop = (scrollHeight / 2) + offset;
                setTimeout(() => { delete container.dataset.isAdjusting; }, 100);
            }

            updateSelectedFromScroll(container, type);
        }


        function updateSelectedFromScroll(container, type) {
            const items = Array.from(container.querySelectorAll('.time-picker-item'));
            const center = container.getBoundingClientRect().top + container.clientHeight / 2;

            let closest = null;
            let minDist = Infinity;

            items.forEach(item => {
                // skip blank spacers
                if (item.classList.contains('time-picker-spacer')) return;

                const rect = item.getBoundingClientRect();
                const mid = rect.top + rect.height / 2;
                const dist = Math.abs(center - mid);

                if (dist < minDist) {
                    minDist = dist;
                    closest = item;
                }
            });

            if (!closest) return;

            if (type === 'period') {
                selectedPeriod = closest.dataset.value;
                updateSelectionVisual('period', selectedPeriod);
            } else {
                const val = parseInt(closest.dataset.value);
                if (!isNaN(val)) {
                    if (type === 'hour') selectedHour = val;
                    if (type === 'minute') selectedMinute = val;
                    updateSelectionVisual(type, val);
                }
            }
        }


        function updateSelectionVisual(type, value) {
            const id = type === 'hour' ? 'hoursList'
                    : type === 'minute' ? 'minutesList'
                    : 'periodList';

            const list = document.getElementById(id);
            if (!list) return;

            const items = Array.from(list.querySelectorAll('.time-picker-item'));
            const center = list.getBoundingClientRect().top + list.clientHeight / 2;

            items.forEach(item => item.classList.remove('selected'));

            const matching = items.filter(item => {
                if (item.classList.contains('time-picker-spacer')) return false;   // ignore blanks
                if (type === 'period') return item.dataset.value === value;
                return parseInt(item.dataset.value) === value;
            });

            if (!matching.length) return;

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

            closest.classList.add('selected');
        }

        function confirmTimeSelection() {
            if (!currentTimeField) return;
            const time24 = convertTo24Hour(selectedHour, selectedMinute, selectedPeriod);
            const display = `${selectedHour.toString().padStart(2, '0')}:${selectedMinute.toString().padStart(2, '0')} ${selectedPeriod}`;
            // Enforce allowed window 07:30 - 21:30 on client side
            try {
                const [h, m] = time24.split(':').map(Number);
                const minutes = h * 60 + m;
                const minAllowed = 7 * 60 + 30;
                const maxAllowed = 21 * 60 + 30;
                if (minutes < minAllowed || minutes > maxAllowed) {
                    showAlert('Allowed schedule window is 07:30 to 21:30. Please choose a time within this range.', 'error');
                    return;
                }
            } catch (e) {
                // If parsing fails, still allow model/server to validate
            }

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

        // Utility functions
        function filterSections() {
            const searchInput = document.getElementById('searchInput').value.toLowerCase();
            const sectionCards = document.querySelectorAll('.section-card');
            sectionCards.forEach(card => {
                const name = card.dataset.sectionName || '';
                const curriculum = card.dataset.curriculum || '';
                if (name.includes(searchInput) || curriculum.includes(searchInput)) {
                    card.style.display = 'flex';
                } else {
                    card.style.display = 'none';
                }
            });
        }

        function toggleSectionMenu(event, sectionId) {
            event.stopPropagation();
            document.querySelectorAll('.section-dropdown-menu').forEach(menu => {
                if (menu.id !== `sectionMenu${sectionId}`) {
                    menu.classList.remove('show');
                }
            });
            const menu = document.getElementById(`sectionMenu${sectionId}`);
            if (menu) menu.classList.toggle('show');
        }

        function toggleDropdown(event) {
            if (event && event.stopPropagation) event.stopPropagation();
            const trigger = event ? (event.currentTarget || event.target.closest('.account-section') || event.target.closest('.admin-section')) : null;
            const dropdown = (trigger && (trigger.querySelector('.account-dropdown-menu') || trigger.querySelector('.dropdown-menu'))) || document.querySelector('.account-dropdown-menu') || document.querySelector('.dropdown-menu');
            if (dropdown) dropdown.classList.toggle('show');
        }

        function toggleStatus(event, sectionId) {
            event.stopPropagation();
            if (!confirm('Are you sure you want to toggle the status of this section?')) return;
            fetchWithCSRF(`/admin/section/${sectionId}/toggle-status/`, {
                method: 'POST'
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const statusElement = document.getElementById(`status-${sectionId}`);
                    statusElement.textContent = data.status_display;
                    statusElement.style.color = data.status === 'complete' ? '#28a745' : '#dc3545';
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

        function openEditSectionModal(sectionId) {
            // Open the inline edit modal on the schedule page by fetching the
            // section data and populating the modal fields.
            fetch(`/admin/section/edit/${sectionId}/`)
                .then(res => {
                    if (!res.ok) throw new Error('Network response not ok');
                    return res.json();
                })
                .then(data => {
                    // If endpoint returned success=false, handle gracefully
                    if (data.success === false) {
                        showAlert('Unable to load section data for editing.', 'error');
                        return;
                    }

                    // Populate modal fields (IDs match those used in schedule.html)
                    document.getElementById('edit_section_id').value = data.id;
                    document.getElementById('edit_name').value = data.name;
                    // curriculum may be an id
                    try {
                        const curSel = document.getElementById('edit_curriculum');
                        if (curSel) curSel.value = data.curriculum;
                    } catch (e) {}
                    document.getElementById('edit_year_level').value = data.year_level;
                    document.getElementById('edit_semester').value = data.semester;
                    document.getElementById('edit_max_students').value = data.max_students;

                    openModal('editSectionModal');
                })
                .catch(err => {
                    console.error('openEditSectionModal error', err);
                    showAlert('Error loading section for edit', 'error');
                });
        }

        function deleteSection(sectionId, sectionName) {
            if (!confirm(`Are you sure you want to delete section ${sectionName}? This action cannot be undone.`)) return;
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

        // Submit edit section form from schedule page
        function submitEditSectionFromSchedule(event) {
            event.preventDefault();
            const form = document.getElementById('editSectionForm');
            const formData = new FormData(form);
            const sectionId = formData.get('section_id') || document.getElementById('edit_section_id').value;

            // Validate name format: CPE[year][semester]S[number]
            const sectionName = formData.get('name');
            const pattern = /^([A-Z]+)(\d)(\d)S(\d+)$/;
            const match = sectionName.match(pattern);
            if (!match) {
                showAlert('Section name must follow format: CPE[year][semester]S[number] Example: CPE11S1', 'error');
                return;
            }

            fetchWithCSRF(`/admin/section/edit/${sectionId}/`, {
                method: 'POST',
                body: formData
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showAlert('Section updated successfully!', 'success');
                    setTimeout(() => window.location.reload(), 800);
                } else {
                    const err = data.errors ? data.errors.join('\n') : 'Error updating section';
                    showAlert(err, 'error');
                }
            })
            .catch(err => {
                console.error('submitEditSectionFromSchedule error', err);
                showAlert('Error updating section', 'error');
            });
        }

        function exportSchedule() {
            if (!currentSectionId) {
                showAlert('Please select a section first', 'warning');
                return;
            }
            showAlert('Export to PDF functionality - to be implemented', 'info');
        }

        function printSchedule() {
            if (!currentSectionId) {
                showAlert('Please select a section first', 'warning');
                return;
            }
            window.print();
        }

        // Close dropdowns when clicking outside
        document.addEventListener('click', (event) => {
            if (!event.target.closest('.admin-section') && !event.target.closest('.account-section') && !event.target.closest('.dropdown-menu')) {
                document.querySelectorAll('.account-dropdown-menu, .dropdown-menu').forEach(m => m.classList.remove('show'));
            }
            if (!event.target.closest('.dropdown-menu-container')) {
                document.querySelectorAll('.section-dropdown-menu').forEach(menu => {
                    menu.classList.remove('show');
                });
            }
        });