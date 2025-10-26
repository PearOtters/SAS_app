let dataFromDjango = window.eventsDataJson || '';

const fallbackEvents = [
];
let rawEvents = []; 

try {
    if (typeof dataFromDjango === 'string' && dataFromDjango.trim() !== '') {
        rawEvents = JSON.parse(dataFromDjango);
        
        if (!Array.isArray(rawEvents)) {
            throw new Error("Parsed data is not an array.");
        }
        
    } else {
        console.warn("Django context (events_json) was empty or not a string. Using fallback data.");
        rawEvents = fallbackEvents;
    }
} catch (e) {
    console.error("Error processing events data. Using fallback data.", e);
    rawEvents = fallbackEvents;
}

const events = rawEvents.map(event => ({
    ...event,
    date: new Date(event.date_ms)
}));

let currentDate = new Date();
let selectedEventId = null;
let map = null;
let markers = {};


function formatDate(date) {
    return date.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });
}

function formatDuration(duration) {
      return duration ? `${duration} hour${duration > 1 ? 's' : ''}` : 'N/A';
}

const getBudgetSymbol = (budgetCode) => {
    if (budgetCode === 'LOW') return '£';
    if (budgetCode === 'MEDIUM') return '££';
    if (budgetCode === 'HIGH') return '£££';
    return 'N/A';
};


function updateEventDisplay(event) {
    
    if (event) {
        document.getElementById('dispName').textContent = event.name || 'N/A';
        document.getElementById('dispDateTime').textContent = `${formatDate(event.date)} at ${event.time || 'N/A'}`;
        document.getElementById('dispLocation').textContent = event.location.address || 'N/A';
        document.getElementById('dispCategory').textContent = event.category || 'N/A';
        document.getElementById('dispDuration').textContent = formatDuration(event.duration);
        document.getElementById('dispAttendees').textContent = event.attendees ? `${event.attendees}` : 'N/A';
        document.getElementById('dispDescription').textContent = event.description || 'No description provided.';

        const displayGrid = document.getElementById('eventDisplay').querySelector('.display-grid');
        let budgetGroup = document.getElementById('dispBudgetGroup');
        
        if (!budgetGroup) {
            budgetGroup = document.createElement('div');
            budgetGroup.id = 'dispBudgetGroup';
            budgetGroup.className = 'display-group';
            budgetGroup.innerHTML = `
                <div class="display-label">Price / Budget</div>
                <div class="display-value" id="dispBudget">${getBudgetSymbol(event.budget)}</div>
            `;
            const lastFullWidthGroup = displayGrid.querySelector('.display-group.full-width:last-child');
            if (lastFullWidthGroup) {
                displayGrid.insertBefore(budgetGroup, lastFullWidthGroup);
            } else {
                displayGrid.appendChild(budgetGroup);
            }
        } else {
            document.getElementById('dispBudget').textContent = getBudgetSymbol(event.budget);
        }

    } else {
        document.getElementById('dispName').textContent = 'Select an event from the list or map.';
        document.getElementById('dispDateTime').textContent = '-';
        document.getElementById('dispLocation').textContent = '-';
        document.getElementById('dispCategory').textContent = '-';
        document.getElementById('dispDuration').textContent = '-';
        document.getElementById('dispAttendees').textContent = '-';
        document.getElementById('dispDescription').textContent = '...';

        let budgetGroup = document.getElementById('dispBudgetGroup');
        if (budgetGroup) {
            document.getElementById('dispBudget').textContent = '-'; 
        }
    }
}

function renderEventList() {
    const eventList = document.getElementById('eventList');

    if (events.length === 0) {
        eventList.innerHTML = `
            <div class="no-events">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 00-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"></path>
                </svg>
                <p>No events available</p>
            </div>
        `;
        return;
    }

    eventList.innerHTML = events.map(event => {
    const dateStr = event.date instanceof Date && !isNaN(event.date)
        ? event.date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
        : 'N/A';
    const isSelected = selectedEventId === event.id;
    
    const budgetSymbol = getBudgetSymbol(event.budget);

    return `
        <div class="event-item ${isSelected ? 'selected' : ''}" onclick="selectEvent(${event.id})">
            <div class="event-item-header">
                <div>
                    <div class="event-item-title">${event.name}</div>
                </div>
                <span class="event-item-category">${event.category}</span>
            </div>
            <div class="event-item-details">
                <div class="event-item-detail">
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                    </svg>
                    <span>${dateStr} at ${event.time}</span>
                </div>
                <div class="event-item-detail">
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                    </svg>
                    <span>${event.location.address}</span>
                </div>
                <div class="event-item-detail">
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c1.657 0 3 .895 3 2s-1.343 2-3 2-3-.895-3-2 1.343-2 3-2zM12 8V4m-4 8h8m-8 4h8"></path>
                    </svg>
                    <span>Price/Budget: ${budgetSymbol}</span> </div>
                <div class="event-item-detail">
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
                    </svg>
                    <span>${event.attendees} attendees</span>
                </div>
            </div>
            <div class="event-item-description">${event.description}</div>
        </div>
    `;
}).join('');

    if (events.length > 0 && selectedEventId === null) {
        selectEvent(events[0].id);
    } else if (events.length === 0) {
        updateEventDisplay(null);
    }
}

window.selectEvent = function(eventId) {
    selectedEventId = eventId;
    const event = events.find(e => e.id === eventId);

    if (event) {
        renderEventList();

        if (map && markers[eventId]) {
            map.setView([event.location.lat, event.location.lng], 15);
            markers[eventId].openPopup();
        }

        updateEventDisplay(event);

        document.getElementById('mapInfo').textContent = `Selected: ${event.name} at ${event.location.address}`;
        
    }
}

function renderCalendar() {
    const calendar = document.getElementById('calendar');
    const monthYear = document.getElementById('currentMonth');

    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();

    const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
                         'July', 'August', 'September', 'October', 'November', 'December'];

    monthYear.textContent = `${monthNames[month]} ${year}`;

    calendar.innerHTML = '';

    const dayHeaders = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    dayHeaders.forEach(day => {
        const header = document.createElement('div');
        header.className = 'calendar-day-header';
        header.textContent = day;
        calendar.appendChild(header);
    });

    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const daysInPrevMonth = new Date(year, month, 0).getDate();

    for (let i = firstDay - 1; i >= 0; i--) {
        const day = document.createElement('div');
        day.className = 'calendar-day other-month';
        day.textContent = daysInPrevMonth - i;
        calendar.appendChild(day);
    }

    for (let i = 1; i <= daysInMonth; i++) {
        const day = document.createElement('div');
        day.className = 'calendar-day';
        day.textContent = i;

        const hasEvent = events.some(event => {
            const eventDate = event.date;
            return eventDate instanceof Date && !isNaN(eventDate) &&
                    eventDate.getDate() === i &&
                    eventDate.getMonth() === month &&
                    eventDate.getFullYear() === year;
        });

        if (hasEvent) {
            day.classList.add('has-event');
            const dayDate = new Date(year, month, i);
            day.addEventListener('click', () => showEventsForDate(dayDate));
        }

        calendar.appendChild(day);
    }

    const remainingDays = 42 - (firstDay + daysInMonth);
    for (let i = 1; i <= remainingDays; i++) {
        const day = document.createElement('div');
        day.className = 'calendar-day other-month';
        day.textContent = i;
        calendar.appendChild(day);
    }
}

function showEventsForDate(date) {
    const dateEvents = events.filter(event =>
        event.date.getDate() === date.getDate() &&
        event.date.getMonth() === date.getMonth() &&
        event.date.getFullYear() === date.getFullYear()
    );

    if (dateEvents.length > 0) {
        dateEvents.sort((a, b) => (a.time > b.time) ? 1 : ((b.time > a.time) ? -1 : 0));
        selectEvent(dateEvents[0].id);
    }
}

window.previousMonth = function() {
    currentDate.setMonth(currentDate.getMonth() - 1);
    renderCalendar();
}

window.nextMonth = function() {
    currentDate.setMonth(currentDate.getMonth() + 1);
    renderCalendar();
}

function initMap() {
    if (typeof L === 'undefined') {
        console.error("Leaflet not loaded. Make sure the leaflet.js script tag is in your HTML.");
        return;
    }
    
    const defaultCenter = [55.8642, -4.2518];
    const firstEvent = events.find(e => e.location && e.location.lat && e.location.lng);
    const initialCenter = firstEvent
        ? [firstEvent.location.lat, firstEvent.location.lng]
        : defaultCenter;

    map = L.map('map').setView(initialCenter, 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);

    events.forEach(event => {
        if (event.location && event.location.lat && event.location.lng) {
            const dateStr = event.date.toLocaleDateString();
            const budgetSymbol = getBudgetSymbol(event.budget);
            const marker = L.marker([event.location.lat, event.location.lng])
                .addTo(map)
                .bindPopup(`
                    <div style="color: #1a1a1a; min-width: 200px;">
                        <h3 style="margin: 0 0 8px 0; font-size: 1rem; font-weight: 600;">${event.name}</h3>
                        <p style="margin: 4px 0; font-size: 0.85rem;"><strong>Date:</strong> ${dateStr}</p>
                        <p style="margin: 4px 0; font-size: 0.85rem;"><strong>Time:</strong> ${event.time}</p>
                        <p style="margin: 4px 0; font-size: 0.85rem;"><strong>Location:</strong> ${event.location.address}</p>
                        <p style="margin: 4px 0; font-size: 0.85rem;"><strong>Budget:</strong> ${budgetSymbol}</p>
                        <p style="margin: 8px 0 0 0; font-size: 0.85rem;">${event.description}</p>
                    </div>
                `);

            marker.on('click', () => {
                selectEvent(event.id);
            });

            markers[event.id] = marker;
        }
    });
}

renderEventList();
renderCalendar();

window.addEventListener('load', initMap);