window.onload = function() {
        
            var map = L.map('map').setView([37.7749, -122.4194], 13);
            var markerLayer = L.layerGroup().addTo(map);

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 19,
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }).addTo(map);

            var events = [
                { "name": "Music Festival", "lat": 37.7749, "lng": -122.4194, "type": "music", "datetime": "2025-10-26T14:00:00" },
                { "name": "Art Exhibition", "lat": 37.7849, "lng": -122.4094, "type": "art", "datetime": "2025-10-27T10:00:00" },
                { "name": "Food Fair", "lat": 37.7649, "lng": -122.4294, "type": "food", "datetime": "2025-10-26T12:00:00" }
            ];

            function displayEvents(eventsToShow) {
                markerLayer.clearLayers();

                eventsToShow.forEach(function(event) {
                    
                    var eventDate = new Date(event.datetime);
                    var displayTime = eventDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                    var displayDate = eventDate.toLocaleDateString([], { month: 'short', day: 'numeric' });

                    L.marker([event.lat, event.lng]).addTo(markerLayer)
                        .bindPopup(
                            '<b style="font-size: 1.1em;">' + event.name + '</b><br>' +
                            '<b>Date:</b> ' + displayDate + '<br>' +
                            '<b>Time:</b> ' + displayTime
                        );
                });
            }

            var typeFilterElement = document.getElementById('event-type-filter');
            var dateFilterElement = document.getElementById('event-date-filter');
            var timeFilterElement = document.getElementById('event-time-filter');
            var resetFilterButton = document.getElementById('reset-filters');

            function updateMapFilters() {
                var selectedType = typeFilterElement.value;
                var selectedDate = dateFilterElement.value;
                var selectedTime = timeFilterElement.value;

                var filteredEvents = events.filter(function(event) {
                    var typeMatch = (selectedType === 'all') || (event.type === selectedType);

                    var eventDate = event.datetime.split('T')[0];
                    var dateMatch = (selectedDate === "") || (eventDate === selectedDate);
                    
                    var eventTime = event.datetime.split('T')[1].substring(0, 5);
                    var timeMatch = (selectedTime === "") || (eventTime === selectedTime);

                    return typeMatch && dateMatch && timeMatch;
                });

                displayEvents(filteredEvents);
            }

            function resetFilters() {
                typeFilterElement.value = 'all';
                dateFilterElement.value = '';
                timeFilterElement.value = '';
                updateMapFilters();
            }

            typeFilterElement.addEventListener('change', updateMapFilters);
            dateFilterElement.addEventListener('change', updateMapFilters);
            timeFilterElement.addEventListener('change', updateMapFilters);
            resetFilterButton.addEventListener('click', resetFilters);

            displayEvents(events);

        };