$(document).ready(function() {
    console.log('Initializing FullCalendar...');
    var calendar = $('#calendar').fullCalendar({
        header: {
            left: 'prev,next today',
            center: 'title',
            right: 'month,agendaWeek,agendaDay'
        },
        editable: true,
        events: function(start, end, timezone, callback) {
            console.log('Fetching events from ' + start.format() + ' to ' + end.format());
            $.ajax({
                url: '/get_entries',
                data: {
                    start: start.format('YYYY-MM-DD'),
                    end: end.format('YYYY-MM-DD')
                },
                success: function(data) {
                    console.log('Received events:', data.events);
                    callback(data.events);
                },
                error: function(xhr, status, error) {
                    console.error('Error fetching events:', error);
                }
            });
        },
        eventRender: function(event, element) {
            console.log('Rendering event:', event);
            element.css('background-color', event.backgroundColor);
            element.css('border-color', event.backgroundColor);
            element.find('.fc-title').text(event.title);
            element.find('.fc-content').css('color', '#333');
        },
        dayClick: function(date, jsEvent, view) {
            var selectedDate = date.format('YYYY-MM-DD');
            $('#selectedDate').val(selectedDate);
            $('#modalDate').text('Set Day: ' + selectedDate);
            var modal = new bootstrap.Modal(document.getElementById('entryModal'));

            var events = calendar.fullCalendar('clientEvents', function(event) {
                return event.start.format('YYYY-MM-DD') === selectedDate;
            });
            if (events.length > 0) {
                var event = events[0];
                $('#entryType').val(event.type);
                if (event.type === 'Work' && event.title.includes('h')) {
                    $('#hours').val(event.title.split(': ')[1].replace('h', ''));
                } else {
                    $('#hours').val('');
                }
            } else {
                $('#entryType').val('Work');
                $('#hours').val('');
            }
            toggleHoursField($('#entryType').val());
            modal.show();
        }
    });

    // Fetch initial counters
    $.getJSON('/get_entries', function(data) {
        updateCounters(data.remaining_vacation_days, data.remaining_sick_days);
    });

    // Toggle hours field
    $('#entryType').change(function() {
        toggleHoursField($(this).val());
    });

    function toggleHoursField(entryType) {
        if (entryType === 'Work') {
            $('#hours_field').show();
        } else {
            $('#hours_field').hide();
            $('#hours').val('');
        }
    }

    // Entry Form Submission
    $('#entryForm').submit(function(e) {
        e.preventDefault();
        const formData = {
            date: $('#selectedDate').val(),
            entry_type: $('#entryType').val(),
            hours: $('#entryType').val() === 'Work' ? $('#hours').val() : null
        };

        $.ajax({
            url: '/add_entry',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(formData),
            success: function(response) {
                console.log('Entry added:', response);
                calendar.fullCalendar('refetchEvents');
                updateCounters(response.remaining_vacation_days, response.remaining_sick_days);
                alert(response.message);
                var modal = bootstrap.Modal.getInstance(document.getElementById('entryModal'));
                modal.hide();
            },
            error: function(error) {
                console.error('Error adding entry:', error);
                alert(error.responseJSON.error);
            }
        });
    });

    // Delete Entry Button
    $('#deleteEntryBtn').click(function() {
        const selectedDate = $('#selectedDate').val();
        if (!selectedDate) {
            alert('Please select a date first!');
            return;
        }

        $.post('/delete_entry', { date: selectedDate }, function(response) {
            console.log('Entry deleted:', response);
            calendar.fullCalendar('refetchEvents');
            updateCounters(response.remaining_vacation_days, response.remaining_sick_days);
            alert(response.message);
            var modal = bootstrap.Modal.getInstance(document.getElementById('entryModal'));
            modal.hide();
        }).fail(function(error) {
            console.error('Error deleting entry:', error);
            alert(error.responseJSON.error);
        });
    });

    // Update Counters
    function updateCounters(vacationRemaining, sickUsed) {
        $('#vacation-counter').text(vacationRemaining);
        $('#sick-counter').text(sickUsed);
    }

    // Sidebar Toggle
    const burgerBtn = document.getElementById('burgerBtn');
    const closeSidebarBtn = document.getElementById('closeSidebarBtn');
    const sidebar = document.getElementById('accountSidebar');

    burgerBtn.addEventListener('click', function() {
        sidebar.classList.add('active');
        burgerBtn.style.display = 'none';
    });

    closeSidebarBtn.addEventListener('click', function() {
        sidebar.classList.remove('active');
        burgerBtn.style.display = 'block';
    });

    document.addEventListener('click', function(event) {
        if (!sidebar.contains(event.target) && !burgerBtn.contains(event.target)) {
            sidebar.classList.remove('active');
            burgerBtn.style.display = 'block';
        }
    });
});