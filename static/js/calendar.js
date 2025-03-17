document.addEventListener('DOMContentLoaded', function() {
    var calendarEl = document.getElementById('calendar');
    var calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        events: '/api/calendar_data',
        selectable: true,
        eventClick: function(info) {
            if (info.event.extendedProps.editable === false) {
                alert('Holidays cannot be modified.');
                return;
            }
            openModal(info.event.startStr, info.event.title);
        },
        dateClick: function(info) {
            openModal(info.dateStr, '');
        }
    });
    calendar.render();

    function openModal(date, currentType) {
        var modal = new bootstrap.Modal(document.getElementById('dayModal'));
        document.getElementById('modalDate').textContent = 'Set Day: ' + date;
        
        var radios = document.getElementsByName('day_type');
        var hoursField = document.getElementById('hours_field');
        var deleteBtn = document.getElementById('deleteBtn');
        
        radios.forEach(radio => radio.checked = currentType.toLowerCase().startsWith(radio.value));
        hoursField.style.display = currentType.toLowerCase().startsWith('working') ? 'block' : 'none';
        deleteBtn.style.display = currentType ? 'inline-block' : 'none';

        document.getElementById('type_working').addEventListener('change', function() {
            hoursField.style.display = this.checked ? 'block' : 'none';
        });

        document.getElementById('dayForm').onsubmit = function(e) {
            e.preventDefault();
            var dayType = document.querySelector('input[name="day_type"]:checked');
            var hours = document.getElementById('hours').value;
            var payload = { day_type: dayType ? dayType.value : 'none' };
            if (dayType && dayType.value === 'working') payload.hours_worked = hours;

            fetch('/api/day/' + date, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                } else {
                    updateCounters(data.remaining_vacation_days, data.remaining_sick_days);
                    calendar.refetchEvents();
                    modal.hide();
                }
            })
            .catch(error => console.error('Error:', error));
        };

        document.getElementById('deleteBtn').onclick = function() {
            fetch('/api/day/' + date, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ day_type: 'none' })
            })
            .then(response => response.json())
            .then(data => {
                updateCounters(data.remaining_vacation_days, data.remaining_sick_days);
                calendar.refetchEvents();
                modal.hide();
            })
            .catch(error => console.error('Error:', error));
        };

        modal.show();
    }

    function updateCounters(vacationRemaining, sickUsed) {
        console.log('Updating counters:', vacationRemaining, sickUsed);
        document.getElementById('vacation-counter').textContent = vacationRemaining;
        document.getElementById('sick-counter').textContent = sickUsed;
    }
});