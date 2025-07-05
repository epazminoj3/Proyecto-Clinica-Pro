/**
 * Calendar Widget for Medical Appointments
 * Displays a calendar with appointment scheduling functionality
 */
class CalendarWidget {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            apiUrl: '/doctor/api/calendar/data/',
            availabilityUrl: '/doctor/api/calendar/availability/',
            createUrl: '/doctor/cita_medica/crear/',
            updateStatusUrl: '/doctor/api/citas/update-status/',
            ...options
        };
        
        this.currentDate = new Date();
        this.selectedDate = null;
        this.calendarData = null;
        this.isLoading = false;
        
        this.init();
        
        // Inicializar verificación automática de citas pasadas
        this.checkAndUpdatePastAppointments();
        this.setupPeriodicCheck();
    }
    
    init() {
        this.render();
        this.loadCalendarData();
        this.bindEvents();
        // Verificar y actualizar citas pasadas automáticamente
        this.checkAndUpdatePastAppointments();
        // Configurar verificación periódica (cada 30 minutos)
        this.setupPeriodicCheck();
    }
    
    render() {
        this.container.innerHTML = `
            <div class="calendar-widget">
                <button class="calendar-toggle" id="calendarToggle">
                    <i class="fas fa-calendar-check"></i>
                    <span>Calendario</span>
                </button>
                <div class="calendar-popup" id="calendarPopup">
                    <div class="calendar-header">
                        <div class="calendar-header-left">
                            <div class="calendar-selectors">
                                <select id="monthSelector" class="calendar-select">
                                    <option value="0">Enero</option>
                                    <option value="1">Febrero</option>
                                    <option value="2">Marzo</option>
                                    <option value="3">Abril</option>
                                    <option value="4">Mayo</option>
                                    <option value="5">Junio</option>
                                    <option value="6">Julio</option>
                                    <option value="7">Agosto</option>
                                    <option value="8">Septiembre</option>
                                    <option value="9">Octubre</option>
                                    <option value="10">Noviembre</option>
                                    <option value="11">Diciembre</option>
                                </select>
                                <select id="yearSelector" class="calendar-select">
                                    <!-- Years will be populated dynamically -->
                                </select>
                            </div>
                        </div>
                        <div class="calendar-nav">
                            <button id="prevMonth"><i class="fas fa-chevron-left"></i></button>
                            <button id="nextMonth"><i class="fas fa-chevron-right"></i></button>
                        </div>
                    </div>
                    <div class="calendar-legend">
                        <div class="legend-item">
                            <span class="legend-color day-available"></span>
                            <span>Sin citas</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-color day-partial"></span>
                            <span>Hay horarios disponibles</span>
                        </div>
                        <div class="legend-item">
                            <span class="legend-color day-full"></span>
                            <span>Día completo</span>
                        </div>
                    </div>
                    <div class="calendar-container">
                        <div class="calendar-body" id="calendarBody">
                            <div class="calendar-loading">
                                <i class="fas fa-spinner fa-spin"></i>
                                <span style="margin-left: 8px;">Cargando calendario...</span>
                            </div>
                        </div>
                        <div class="calendar-sidebar" id="calendarSidebar">
                            <div class="sidebar-content">
                                <h4><i class="fas fa-calendar-day"></i> Citas de Hoy</h4>
                                <div id="today-appointments"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    bindEvents() {
        const toggle = document.getElementById('calendarToggle');
        const popup = document.getElementById('calendarPopup');
        const prevBtn = document.getElementById('prevMonth');
        const nextBtn = document.getElementById('nextMonth');
        const monthSelector = document.getElementById('monthSelector');
        const yearSelector = document.getElementById('yearSelector');
        
        // Populate year selector
        this.populateYearSelector();
        
        // Toggle calendar visibility
        toggle.addEventListener('click', (e) => {
            e.stopPropagation();
            popup.classList.toggle('active');
        });
        
        // Close calendar when clicking outside, but NOT when clicking inside
        document.addEventListener('click', (e) => {
            if (!this.container.contains(e.target)) {
                popup.classList.remove('active');
            }
        });
        
        // Prevent popup from closing when clicking inside it
        popup.addEventListener('click', (e) => {
            e.stopPropagation();
        });
        
        // Navigation buttons
        prevBtn.addEventListener('click', () => this.navigateMonth(-1));
        nextBtn.addEventListener('click', () => this.navigateMonth(1));
        
        // Month and year selectors
        monthSelector.addEventListener('change', (e) => {
            const selectedMonth = parseInt(e.target.value);
            this.currentDate.setMonth(selectedMonth);
            this.selectedDate = null; // Reset selected date
            this.loadCalendarData();
        });
        
        yearSelector.addEventListener('change', (e) => {
            const selectedYear = parseInt(e.target.value);
            this.currentDate.setFullYear(selectedYear);
            this.selectedDate = null; // Reset selected date
            this.loadCalendarData();
        });
    }
    
    async loadCalendarData() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        const year = this.currentDate.getFullYear();
        const month = this.currentDate.getMonth() + 1;
        
        try {
            const response = await fetch(`${this.options.apiUrl}?year=${year}&month=${month}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            this.calendarData = await response.json();
            this.renderCalendar();
        } catch (error) {
            console.error('Error loading calendar data:', error);
            this.renderError('Error al cargar el calendario. Verifique su conexión.');
        } finally {
            this.isLoading = false;
        }
    }
    
    renderCalendar() {
        const body = document.getElementById('calendarBody');
        
        if (!this.calendarData) {
            this.renderError('No se pudieron cargar los datos del calendario');
            return;
        }
        
        // Actualizar los selectores
        this.updateSelectors();
        
        const calendarHTML = this.generateCalendarHTML();
        body.innerHTML = calendarHTML;
        
        this.bindCalendarEvents();
        
        // Actualizar el sidebar
        this.updateSidebar();
    }
    
    updateSidebar() {
        console.log('=== updateSidebar called ===');
        const sidebar = document.getElementById('calendarSidebar');
        console.log('Sidebar element:', sidebar);
        console.log('Selected date:', this.selectedDate);
        
        if (!this.selectedDate) {
            console.log('No selected date - showing empty sidebar');
            sidebar.innerHTML = `
                <div class="sidebar-empty">
                    <i class="fas fa-calendar-day"></i>
                    <p>Selecciona un día para ver las citas y horarios disponibles</p>
                </div>
            `;
            return;
        }
        
        const selectedDay = this.selectedDate.getDate();
        const appointments = this.calendarData.citas_por_dia[selectedDay] || [];
        console.log('Selected day:', selectedDay);
        console.log('Appointments for day:', appointments);
        
        let html = `
            <div class="sidebar-content">
                <h4>
                    <i class="fas fa-calendar-day"></i>
                    ${this.formatDateWithCorrectDay(this.selectedDate)}
                </h4>
        `;
        
        // Mostrar citas existentes
        if (appointments.length > 0) {
            html += '<div class="sidebar-section"><h5>Citas programadas</h5>';
            appointments.forEach(appointment => {
                console.log('Processing appointment:', appointment); // Debug
                const statusClass = appointment.estado.toLowerCase();
                
                // Mapear estados a textos legibles
                const statusText = {
                    'disponible': 'Disponible',
                    'ocupado': 'Ocupado',
                    'atendido': 'Atendido',
                    'no_asistio': 'No asistió',
                    'completada': 'Completada'
                }[appointment.estado] || appointment.estado;
                
                // Usar estilos inline solo para las citas, no afectar los slots
                const appointmentHtml = `
                    <div class="appointment-item-calendar" data-status="${appointment.estado}" style="display: flex; align-items: center; gap: 12px; padding: 10px; background: white; border-radius: 8px; margin-bottom: 8px; border: 1px solid #e5e7eb;">
                        <div style="font-size: 14px; font-weight: 700; color: #0f4c75; min-width: 50px;">${appointment.hora}</div>
                        <div style="flex: 1;">
                            <div style="font-size: 13px; font-weight: 500; color: #374151; margin-bottom: 2px;">${appointment.paciente}</div>
                            <div class="appointment-status" style="font-size: 12px; color: #6b7280;">${statusText}</div>
                        </div>
                        <button onclick="window.viewAppointmentDetail(${appointment.id})" 
                                style="background: #3b82f6; border: none; padding: 8px 10px; border-radius: 6px; cursor: pointer; color: white; font-size: 14px; min-width: 40px; height: 36px; display: flex; align-items: center; justify-content: center;"
                                title="Ver detalles de la cita"
                                onmouseover="this.style.background='#2563eb'"
                                onmouseout="this.style.background='#3b82f6'">
                            👁️
                        </button>
                    </div>
                `;
                html += appointmentHtml;
            });
            html += '</div>';
        } else {
            html += '<div class="sidebar-section"><p class="no-appointments">No hay citas programadas</p></div>';
        }
        
        // Mostrar horarios disponibles para fechas futuras y para hoy
        const today = new Date();
        const todayOnly = new Date();
        todayOnly.setHours(0, 0, 0, 0);
        const selectedDateOnly = new Date(this.selectedDate);
        selectedDateOnly.setHours(0, 0, 0, 0);
        
        if (selectedDateOnly >= todayOnly) {
            console.log('Generating available slots...');
            try {
                const slotsHtml = this.generateSidebarAvailableSlots();
                console.log('Slots HTML generated:', slotsHtml.substring(0, 100) + '...');
                html += slotsHtml;
            } catch (error) {
                console.error('Error generating slots:', error);
                html += '<div class="sidebar-section"><p class="error">Error al cargar horarios disponibles</p></div>';
            }
        }
        
        html += '</div></div>';
        
        // Agregar espacio adicional al final para permitir scroll completo
        html += '<div class="sidebar-spacer"></div>';
        
        console.log('Setting sidebar HTML:', html.substring(0, 200) + '...');
        sidebar.innerHTML = html;
        console.log('Sidebar updated successfully');
        
        // Vincular eventos de los horarios disponibles
        this.bindTimeSlotEvents();
    }
    
    bindTimeSlotEvents() {
        const availableSlots = document.querySelectorAll('.slot-sidebar[data-clickable="true"]');
        console.log('Binding events to', availableSlots.length, 'available slots');
        
        availableSlots.forEach(slot => {
            slot.addEventListener('click', () => {
                const time = slot.dataset.slot;
                console.log('Time slot clicked:', time);
                this.selectTimeSlot(time);
            });
        });
    }
    
    generateCalendarHTML() {
        const { calendar_matrix, citas_por_dia, horarios_disponibles } = this.calendarData;
        const today = new Date();
        const currentMonth = this.currentDate.getMonth();
        const currentYear = this.currentDate.getFullYear();
        
        let html = `
            <div class="calendar-grid">
                <div class="calendar-day-header">Dom</div>
                <div class="calendar-day-header">Lun</div>
                <div class="calendar-day-header">Mar</div>
                <div class="calendar-day-header">Mié</div>
                <div class="calendar-day-header">Jue</div>
                <div class="calendar-day-header">Vie</div>
                <div class="calendar-day-header">Sáb</div>
        `;
        
        calendar_matrix.forEach(week => {
            week.forEach(day => {
                if (day === 0) {
                    html += '<div class="calendar-day other-month"></div>';
                } else {
                    const dayDate = new Date(currentYear, currentMonth, day);
                    const isToday = this.isSameDate(dayDate, today);
                    const dayAppointments = citas_por_dia[day] || [];
                    const isSelected = this.selectedDate && this.isSameDate(dayDate, this.selectedDate);
                    
                    // Determinar disponibilidad del día
                    const availability = this.getDayAvailability(dayDate, dayAppointments, horarios_disponibles);
                    
                    let classes = ['calendar-day'];
                    if (isToday) classes.push('today');
                    if (isSelected) classes.push('selected');
                    classes.push(availability.class);
                    
                    // Contar citas únicas por hora para el indicador
                    const uniqueHours = new Set();
                    dayAppointments.forEach(appointment => {
                        const hour = appointment.hora.split(':')[0];
                        uniqueHours.add(hour);
                    });
                    const uniqueAppointmentCount = uniqueHours.size;
                    
                    html += `
                        <div class="${classes.join(' ')}" data-day="${day}">
                            ${day}
                            ${uniqueAppointmentCount > 0 ? `<span class="appointment-indicator ${uniqueAppointmentCount >= 8 ? 'full-day' : 'partial-day'}">${uniqueAppointmentCount}</span>` : ''}
                        </div>
                    `;
                }
            });
        });
        
        html += '</div>';
        return html;
    }
    
    getDayAvailability(dayDate, appointments, horarios) {
        // Si es un día pasado, no mostrar disponibilidad
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        dayDate.setHours(0, 0, 0, 0);
        
        if (dayDate < today) {
            return { class: 'day-past', slots: 0, total: 0 };
        }
        
        // Obtener horario para este día de la semana
        const dayName = this.getDayNameFromDate(dayDate);
        const daySchedule = horarios.find(h => 
            h.dia_semana.toLowerCase() === dayName.toLowerCase()
        );
        
        if (!daySchedule || !daySchedule.slots || daySchedule.slots.length === 0) {
            return { class: 'day-no-schedule', slots: 0, total: 0 };
        }
        
        const totalSlots = daySchedule.slots.length;
        
        // Contar citas únicas por hora (no por minutos exactos)
        const appointmentHours = new Set();
        appointments.forEach(appointment => {
            const hour = appointment.hora.split(':')[0];
            appointmentHours.add(hour);
        });
        
        const occupiedSlots = appointmentHours.size;
        const availableSlots = totalSlots - occupiedSlots;
        
        if (occupiedSlots === 0) {
            return { class: 'day-available', slots: availableSlots, total: totalSlots };
        } else if (availableSlots > 0) {
            return { class: 'day-partial', slots: availableSlots, total: totalSlots };
        } else {
            return { class: 'day-full', slots: 0, total: totalSlots };
        }
    }
    

    
    generateSidebarAvailableSlots() {
        // Usar el día de la semana correcto considerando el desfase del calendario
        const dayName = this.getDayNameFromDate(this.selectedDate);
        const horarios = this.calendarData.horarios_disponibles || [];
        
        // Find schedule for this day
        const daySchedule = horarios.find(h => 
            h.dia_semana.toLowerCase() === dayName.toLowerCase()
        );
        
        // DEBUG: Mostrar información de debugging (solo en desarrollo)
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            console.log('=== DEBUG HORARIOS ===');
            console.log('Fecha seleccionada:', this.selectedDate);
            console.log('Día extraído:', dayName);
            console.log('Horarios disponibles:', horarios.map(h => h.dia_semana));
            console.log('Horario encontrado:', daySchedule);
        }
        
        if (!daySchedule) {
            return `
                <div class="sidebar-section">
                    <h5>Horarios disponibles</h5>
                    <p class="no-schedule">No hay horarios de atención configurados para ${dayName}</p>
                </div>
            `;
        }
        
        const selectedDay = this.selectedDate.getDate();
        const appointedHours = (this.calendarData.citas_por_dia[selectedDay] || []).map(a => a.hora);
        
        // Obtener la hora actual para filtrar horarios pasados si es hoy
        const now = new Date();
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const selectedDateOnly = new Date(this.selectedDate);
        selectedDateOnly.setHours(0, 0, 0, 0);
        const isToday = selectedDateOnly.getTime() === today.getTime();
        
        let html = `
            <div class="sidebar-section">
                <h5>Horarios disponibles</h5>
                <div class="slots-sidebar">
        `;
        
        let availableSlots = [];
        
        daySchedule.slots.forEach(slot => {
            // Si es hoy, verificar que el horario sea futuro
            if (isToday) {
                const [hours, minutes] = slot.split(':').map(Number);
                const slotTime = new Date();
                slotTime.setHours(hours, minutes, 0, 0);
                
                // Solo mostrar horarios que sean al menos 1 hora en el futuro
                const oneHourFromNow = new Date(now.getTime() + 60 * 60 * 1000);
                if (slotTime <= oneHourFromNow) {
                    return; // Saltar este horario
                }
            }
            
            // Verificar si hay alguna cita en esa hora (comparando solo la hora, no minutos exactos)
            const slotHour = slot.split(':')[0];
            const isOccupied = appointedHours.some(appointedHour => {
                const appointedHourOnly = appointedHour.split(':')[0];
                return appointedHourOnly === slotHour;
            });
            
            if (!isOccupied) {
                availableSlots.push(slot);
            }
            
            const slotClass = isOccupied ? 'slot-sidebar occupied' : 'slot-sidebar available';
            
            html += `
                <div class="${slotClass}" 
                     data-slot="${slot}" 
                     ${!isOccupied ? 'data-clickable="true"' : ''}>
                    <span class="slot-time">${slot}</span>
                    <span class="slot-status">
                        ${isOccupied ? '<i class="fas fa-times"></i> Ocupado' : '<i class="fas fa-plus"></i> Disponible'}
                    </span>
                </div>
            `;
        });
        
        // Si no hay horarios disponibles, mostrar mensaje
        if (availableSlots.length === 0) {
            html += '<p class="no-slots">No hay horarios disponibles</p>';
        }
        
        html += '</div></div>';
        return html;
    }
    
    mapDayNameToSpanish(dayName) {
        const mapping = {
            'monday': 'lunes',
            'tuesday': 'martes',
            'wednesday': 'miercoles',
            'thursday': 'jueves',
            'friday': 'viernes',
            'saturday': 'sabado',
            'sunday': 'domingo',
            'lunes': 'lunes',
            'martes': 'martes',
            'miércoles': 'miercoles',
            'jueves': 'jueves',
            'viernes': 'viernes',
            'sábado': 'sabado',
            'domingo': 'domingo'
        };
        return mapping[dayName.toLowerCase()] || dayName.toLowerCase();
    }
    
    getDayNameFromDate(date) {
        const dayNames = ['domingo', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado'];
        return dayNames[date.getDay()];
    }
    
    bindCalendarEvents() {
        const days = document.querySelectorAll('.calendar-day:not(.other-month)');
        days.forEach(day => {
            day.addEventListener('click', () => {
                const dayNum = parseInt(day.dataset.day);
                this.selectDate(dayNum);
            });
        });
    }
    
    selectDate(day) {
        console.log('=== selectDate called ===');
        console.log('Day selected:', day);
        console.log('Current date:', this.currentDate);
        
        this.selectedDate = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth(), day);
        console.log('Selected date created:', this.selectedDate);
        
        this.renderCalendar(); // Esto actualizará tanto el calendario como el sidebar
    }
    
    async selectTimeSlot(time) {
        if (!this.selectedDate) return;
        
        const selectedDay = this.selectedDate.getDate();
        const appointedHours = (this.calendarData.citas_por_dia[selectedDay] || []).map(a => a.hora);
        
        // Verificar si hay alguna cita en esa hora (comparando solo la hora, no minutos exactos)
        const timeHour = time.split(':')[0];
        const isOccupied = appointedHours.some(appointedHour => {
            const appointedHourOnly = appointedHour.split(':')[0];
            return appointedHourOnly === timeHour;
        });
        
        if (isOccupied) {
            alert('Ya hay una cita programada en esta hora');
            return;
        }
        
        const fecha = this.formatDateForAPI(this.selectedDate);
        
        // Mostrar mensaje de confirmación
        const confirmed = confirm(`¿Desea crear una cita para el ${this.formatDateWithCorrectDay(this.selectedDate)} a las ${time}?`);
        
        if (!confirmed) {
            return;
        }
        
        // Redirigir directamente al formulario de crear cita con los parámetros
        const createUrl = `${this.options.createUrl}?fecha=${fecha}&hora=${time}`;
        console.log('Redirigiendo a:', createUrl); // Para debug
        window.location.href = createUrl;
    }
    
    navigateMonth(direction) {
        this.currentDate.setMonth(this.currentDate.getMonth() + direction);
        this.selectedDate = null; // Reset selection when navigating
        this.loadCalendarData();
    }
    
    formatDate(date) {
        return date.toLocaleDateString('es-ES', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }
    
    formatDateWithCorrectDay(date) {
        const dayName = this.getDayNameFromDate(date);
        const dateString = date.toLocaleDateString('es-ES', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        return `${dayName}, ${dateString}`;
    }
    
    formatDateForAPI(date) {
        return date.toISOString().split('T')[0];
    }
    
    isSameDate(date1, date2) {
        return date1.getDate() === date2.getDate() &&
               date1.getMonth() === date2.getMonth() &&
               date1.getFullYear() === date2.getFullYear();
    }
    
    getCSRFToken() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        return '';
    }
    
    renderError(message) {
        const body = document.getElementById('calendarBody');
        body.innerHTML = `
            <div class="calendar-error">
                <i class="fas fa-exclamation-triangle"></i>
                <span style="margin-left: 8px;">${message}</span>
            </div>
        `;
    }
    
    /**
     * Navigate to appointment detail view
     */
    viewAppointmentDetail(appointmentId) {
        console.log('=== viewAppointmentDetail called ===');
        console.log('Appointment ID:', appointmentId);
        
        // Validate appointment ID
        if (!appointmentId || appointmentId === 'undefined') {
            console.error('Invalid appointment ID:', appointmentId);
            alert('Error: ID de cita inválido');
            return;
        }
        
        // Construct the URL for the appointment detail page
        const detailUrl = `/doctor/cita_medica/${appointmentId}/`;
        console.log('Navigating to:', detailUrl);
        
        // Navigate to the detail page
        window.location.href = detailUrl;
    }
    
    populateYearSelector() {
        const yearSelector = document.getElementById('yearSelector');
        const currentYear = new Date().getFullYear();
        const startYear = currentYear - 5; // 5 años atrás
        const endYear = currentYear + 5;   // 5 años adelante
        
        yearSelector.innerHTML = '';
        
        for (let year = startYear; year <= endYear; year++) {
            const option = document.createElement('option');
            option.value = year;
            option.textContent = year;
            if (year === this.currentDate.getFullYear()) {
                option.selected = true;
            }
            yearSelector.appendChild(option);
        }
    }
    
    updateSelectors() {
        const monthSelector = document.getElementById('monthSelector');
        const yearSelector = document.getElementById('yearSelector');
        
        if (monthSelector) {
            monthSelector.value = this.currentDate.getMonth();
        }
        
        if (yearSelector) {
            yearSelector.value = this.currentDate.getFullYear();
        }
    }
    
    // Función para verificar y actualizar citas pasadas
    async checkAndUpdatePastAppointments() {
        if (!this.calendarData || !this.calendarData.citas_por_dia) {
            await this.loadCalendarData();
        }
        
        const today = new Date();
        today.setHours(0, 0, 0, 0); // Normalizar a medianoche
        
        const pastAppointments = [];
        
        // Buscar citas pasadas que aún no estén marcadas como "No asistió"
        Object.keys(this.calendarData.citas_por_dia).forEach(day => {
            const dayNum = parseInt(day);
            const appointmentDate = new Date(this.calendarData.year, this.calendarData.month - 1, dayNum);
            appointmentDate.setHours(0, 0, 0, 0);
            
            if (appointmentDate < today) {
                this.calendarData.citas_por_dia[day].forEach(appointment => {
                    if (appointment.estado !== 'no_asistio' && appointment.estado !== 'completada' && appointment.estado !== 'atendido') {
                        pastAppointments.push({
                            id: appointment.id,
                            fecha: `${this.calendarData.year}-${String(this.calendarData.month).padStart(2, '0')}-${String(dayNum).padStart(2, '0')}`,
                            paciente: appointment.paciente,
                            hora: appointment.hora
                        });
                    }
                });
            }
        });
        
        // Actualizar citas pasadas en el backend
        if (pastAppointments.length > 0) {
            await this.updatePastAppointmentsStatus(pastAppointments);
        }
    }
    
    // Función para actualizar el estado de las citas pasadas
    async updatePastAppointmentsStatus(pastAppointments) {
        try {
            const response = await fetch(this.options.updateStatusUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    appointments: pastAppointments
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    console.log(`${result.updated_count} citas actualizadas como "No asistió"`);
                    
                    // Actualizar los datos del calendario localmente
                    pastAppointments.forEach(appointment => {
                        const appointmentDate = new Date(appointment.fecha);
                        const dayNum = appointmentDate.getDate();
                        
                        if (this.calendarData.citas_por_dia[dayNum]) {
                            this.calendarData.citas_por_dia[dayNum].forEach(appt => {
                                if (appt.id === appointment.id) {
                                    appt.estado = 'no_asistio';
                                }
                            });
                        }
                    });
                    
                    // Recargar la vista del calendario
                    this.renderCalendar();
                    this.updateSidebar();
                    
                    // Mostrar notificación si hay actualizaciones
                    if (result.updated_count > 0) {
                        this.showNotification(`${result.updated_count} citas pasadas han sido marcadas como "No asistió"`, 'info');
                    }
                }
            } else {
                console.error('Error al actualizar citas pasadas:', response.statusText);
            }
        } catch (error) {
            console.error('Error en la actualización automática:', error);
        }
    }
    
    // Función para configurar verificación periódica
    setupPeriodicCheck() {
        // Verificar cada hora (3600000 ms)
        setInterval(() => {
            this.checkAndUpdatePastAppointments();
        }, 3600000);
        
        // También verificar cuando la página recupera el foco
        window.addEventListener('focus', () => {
            this.checkAndUpdatePastAppointments();
        });
    }
    
    // Función para mostrar notificaciones
    showNotification(message, type = 'info') {
        // Crear elemento de notificación
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'info' ? 'info' : 'warning'} alert-dismissible fade show`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            max-width: 400px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        `;
        
        notification.innerHTML = `
            <i class="fas fa-${type === 'info' ? 'info-circle' : 'exclamation-triangle'} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remover después de 5 segundos
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
}

// Initialize calendar when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Check if user has calendar permissions (this will be set by Django template)
    if (window.hasCalendarPermission) {
        window.calendar = new CalendarWidget('calendarContainer');
    }
});

// Global function to view appointment details
window.viewAppointmentDetail = function(appointmentId) {
    console.log('=== Global viewAppointmentDetail called ===');
    console.log('Appointment ID:', appointmentId);
    console.log('Type of appointmentId:', typeof appointmentId);
    
    // Validate appointment ID
    if (!appointmentId || appointmentId === 'undefined') {
        console.error('Invalid appointment ID:', appointmentId);
        alert('Error: ID de cita inválido');
        return;
    }
    
    // Construct the URL for the appointment detail page
    const detailUrl = `/doctor/cita_medica/${appointmentId}/`;
    console.log('Navigating to:', detailUrl);
    
    // Navigate to the detail page
    window.location.href = detailUrl;
};
