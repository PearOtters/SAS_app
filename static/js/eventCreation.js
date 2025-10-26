let currentDate = new Date();
    let selectedDate = null;
    let map = null;
    let marker = null;
    
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
        
        const currentDay = new Date(year, month, i);
        
        if (selectedDate && 
            selectedDate.toDateString() === currentDay.toDateString()) {
          day.classList.add('selected');
        }
        
        day.addEventListener('click', () => selectDate(i, month, year));
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

    function selectDate(day, month, year) {
      selectedDate = new Date(year, month, day);
      
      const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      const displayOptions = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
      
      document.getElementById('selectedDate').textContent = selectedDate.toLocaleDateString('en-US', displayOptions);
      document.getElementById('selectedDateInput').value = dateStr; 
      
      renderCalendar();
    }

    function previousMonth() {
      currentDate.setMonth(currentDate.getMonth() - 1);
      renderCalendar();
    }

    function nextMonth() {
      currentDate.setMonth(currentDate.getMonth() + 1);
      renderCalendar();
    }

    function initMap() {
      map = L.map('map').setView([55.8642, -4.2518], 13);
      
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
      }).addTo(map);
      
      map.on('click', function(e) {
        const lat = e.latlng.lat.toFixed(6);
        const lng = e.latlng.lng.toFixed(6);
        
        if (marker) map.removeLayer(marker);
        marker = L.marker([e.latlng.lat, e.latlng.lng]).addTo(map);
        
        document.getElementById('selectedLocation').textContent = `Lat: ${lat}, Lng: ${lng}`;
        document.getElementById('mapInfo').textContent = `Location set to coordinates: (${lat}, ${lng})`;
        
        document.getElementById('selectedLatInput').value = lat;
        document.getElementById('selectedLngInput').value = lng;
        document.getElementById('locationNameInput').value = ''; 
      });
      
      document.getElementById('mapSearch').addEventListener('keypress', function(e) {
          if (e.key === 'Enter') {
              e.preventDefault();
              const query = this.value;
              if (query.trim() === '') return;

              const nominatimUrl = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}, Glasgow, UK&limit=1`;

              document.getElementById('mapInfo').textContent = `Searching for "${query}"...`;

              fetch(nominatimUrl)
                  .then(response => response.json())
                  .then(data => {
                      if (data.length > 0) {
                          const lat = parseFloat(data[0].lat).toFixed(6);
                          const lng = parseFloat(data[0].lon).toFixed(6);
                          const displayName = data[0].display_name;

                          map.setView([lat, lng], 15);
                          document.getElementById('mapInfo').textContent = `Location found: ${displayName}`;

                          if (marker) map.removeLayer(marker);
                          marker = L.marker([lat, lng]).addTo(map);
                          marker.bindPopup(displayName).openPopup();

                          document.getElementById('selectedLatInput').value = lat;
                          document.getElementById('selectedLngInput').value = lng;
                          document.getElementById('locationNameInput').value = displayName;
                          document.getElementById('selectedLocation').textContent = displayName;
                          
                      } else {
                          document.getElementById('mapInfo').textContent = `Could not find location for "${query}". Try a different address or postcode.`;
                      }
                  })
                  .catch(error => {
                      console.error('Geocoding error:', error);
                      document.getElementById('mapInfo').textContent = 'Error during location search. Please try again.';
                  });
          }
      });
    }

    document.getElementById('eventForm').addEventListener('submit', function(e) {
        if (!document.getElementById('selectedDateInput').value) {
            e.preventDefault();
            alert('Please select a date from the calendar.');
            return;
        }
        
        if (!document.getElementById('selectedLatInput').value || !document.getElementById('selectedLngInput').value) {
            e.preventDefault();
            alert('Please select a location on the map or use the search bar.');
            return;
        }
    });

    renderCalendar();
    window.addEventListener('load', initMap);