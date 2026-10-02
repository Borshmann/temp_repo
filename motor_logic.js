let speedTimeout;

const handState = {};

$(document).ready(function() {

    $('[id^="hand"]').each(function() {

        const motorId = $(this).attr('id');

        const initialAngle = parseInt($(`#speed_${motorId}`).val()) || 90;

        const initialStatus = $(`#isopen_${motorId}`).attr('data-status') === "1" ? 1 : 0;

        handState[motorId] = {
            angle: initialAngle,
            status: initialStatus
        };

        const statusBtn = $(`#isopen_${motorId}`);
        statusBtn.text(initialStatus === 1 ? "OPEN" : "CLOSED")
                 .css({
                     'background-color': initialStatus === 1 ? '#FFA500' : '#008fff',
                     'color': 'white'
                 });
    });
});

$(document).off('click', '[id^="isopen_"]').on('click', '[id^="isopen_"]', function() {
    const button = $(this);
    const motorId = button.closest('.card').attr('id');
    const state = handState[motorId];

    // Toggle status
    state.status = state.status === 1 ? 0 : 1;

    // Update button appearance
    button.text(state.status === 1 ? "OPEN" : "CLOSED")
          .css({
              'background-color': state.status === 1 ? '#FFA500' : '#008fff',
              'color': 'white'
          });

    // Send command with CURRENT angle and NEW status
    console.log(`[Status changed] motorId: ${motorId}, angle: ${state.angle}, status: ${state.status}`);

    sendHandCommand(motorId, state.angle, state.status);
});

// Handler for "Start" button (send angle)
$(document).off('click', '[id^="hand_start_"]').on('click', '[id^="hand_start_"]', function() {
    const button = $(this);
    const motorId = button.closest('.card').attr('id');
    const state = handState[motorId];

    // Read angle from input field
    const newAngle = parseInt($(`#speed_${motorId}`).val());

    if (isNaN(newAngle) || newAngle < 0 || newAngle > 270) {
        alert("Angle must be between 0 and 270");
        return;
    }

    // Update angle in state
    state.angle = newAngle;

    // Toggle icons
    button.find('.icon-start').toggle();
    button.find('.icon-stop').toggle();
    button.css('background-color', state.status === 1 ? '#F63235' : '#008fff');

    // Send command with NEW angle and CURRENT status
    console.log(`[Sending angle] motorId: ${motorId}, angle: ${state.angle}, status: ${state.status}`);

    sendHandCommand(motorId, state.angle, state.status);
});

// Universal function to send hand command
function sendHandCommand(motorId, angle, status) {
    fetch('/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            motorId: motorId,
            value: parseInt(angle),
            status: parseInt(status)
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('? Server response:', data);
        if (data.status === "success") {
            console.log("Success: " + data.message);
        }
    })
    .catch(error => {
        console.error('? Error:', error);
        alert("Error sending hand command");
    });
}

function toggleButton(motorId, type, value) {
    const hiddenField = $(`#${type}_${motorId}`);
    hiddenField.val(value);
    $(`#${motorId} .btn-min[onclick*="toggleButton('${motorId}', '${type}'"]`).removeClass('active');
    $(`#${motorId} .btn-min[onclick*="toggleButton('${motorId}', '${type}', '${value}')"]`).addClass('active');
}

// Function to send data to server
function sendData(motorId, speed, direction, startType) {
    console.log("motordata");
    const processedData = {
        motorId: motorId,
        speed: parseInt(speed),
        direction: direction,
        startType: startType
    };
    fetch('/submit', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(processedData)
    })
    .then(response => response.json())
    .then(data => {
        console.log('Data sent successfully:', data);
    })
    .catch(error => {
        console.error('Error sending data:', error);
    });
}

// Function to send servo data to server
function sendServoData(motorId, value, status) {
    console.log("serdata");
    const processedData = {
        motorId: motorId,
        value: parseInt(value),
        status: status 
    };
    fetch('/submit', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(processedData)
    })
    .then(response => response.json())
    .then(data => {
        console.log('Data sent successfully:', data);
    })
    .catch(error => {
        console.error('Error sending data:', error);
    });
}

// Handler for "Set Weight" button
$('.set-weight').click(function() {
    const button = $(this);
    const motorId = button.closest('.numeric-form').attr('id'); 
    const value = $(`#numericInput_${motorId}`).val();

    if (!value || isNaN(value)) {
        console.error('Invalid weight value');
        return;
    }

    const statusButton = $(`#servo_start_${motorId}`);
    const status = statusButton.attr('data-status');

    sendServoData(motorId, value, status);
});

// Universal handler for all "Start Servo" buttons
$('[id^="servo_start_"]').click(function() {
    const button = $(this);
    const motorId = button.closest('.numeric-form').attr('id');
    const value = $(`#numericInput_${motorId}`).val();
    
    if (!value || isNaN(value)) {
        console.error('Invalid weight value');
        return;
    }

    let status = button.attr('data-status');
    if (status === undefined) {
        status = 0;
    }

    if (status == 0) {
        button.attr('data-status', 1);
        button.css({
            'background-color': '#F63235',
            'color': 'white'
        });
        button.find('.icon-start').hide();
        button.find('.icon-stop').show();
        sendServoData(motorId, value, 1);
    } else {
        button.attr('data-status', 0);
        button.css({
            'background-color': '#008fff',
            'color': 'black'
        });
        button.find('.icon-start').show();
        button.find('.icon-stop').hide();
        sendServoData(motorId, value, 0);
    }
});

// Function to update speed
function updateSpeed(motorId, value) {
    $(`#speed_value_${motorId}`).text(value);

    const buttonId = motorId.replace('motor', 'motor_start_');
    const button = $(`#${buttonId}`);
    
    if (!button.find('.icon-stop').is(':visible')) {
        return; // If motor is not running - don't send
    }
    const direction = $(`#direction_${motorId}`).val();
    const startType = $(`#start_type_${motorId}`).val();
    clearTimeout(speedTimeout);
    speedTimeout = setTimeout(() => {
        sendData(motorId, value, direction, startType);
    }, 500);
}

$('[id^="motor_start_"]').click(function() {
    const button = $(this);
    const card = button.closest('.card');
    
    // Check that we found the card and it has an ID
    if (!card.length || !card.attr('id')) {
        console.error('Failed to find card ID');
        return;
    }
    
    const motorId = card.attr('id'); // Now this is a string with the ID
    const rangeSlider = $(`#range_${motorId}`);
    const speedInput = $(`#speed_${motorId}`);
    const speedDisplay = $(`#speed_value_${motorId}`);

    // Check that all control elements exist
    if (!rangeSlider.length || !speedInput.length) {
        console.error('Control elements not found for motor', motorId);
        return;
    }

    // Toggle icons
    button.find('.icon-start').toggle();
    button.find('.icon-stop').toggle();
    
    let speed;
    if (button.find('.icon-stop').is(':visible')) {
        // Start - take value from slider
        speed = rangeSlider.val();
        button.css({
            'background-color': '#F63235',
            'color': 'white'
        });
    } else {
        // Stop - set to 0
        speed = 0;
        button.css({
            'background-color': '#008fff',
            'color': 'white'
        });
    }

    const direction = $(`#direction_${motorId}`).val();
    const startType = $(`#start_type_${motorId}`).val();
    
    sendData(motorId, speed, direction, startType);
});

$('[id^="polish_start_"]').click(function() {
    const button = $(this);
    const card = button.closest('.card');
    
    // Check that we found the card and it has an ID
    if (!card.length || !card.attr('id')) {
        console.error('Failed to find card ID');
        return;
    }
    
    const polishId = card.attr('id'); // Now this is a string with the ID
    const rangeSlider = $(`#range_${polishId}`);
    const speedInput = $(`#speed_${polishId}`);
    const speedDisplay = $(`#speed_value_${polishId}`);

    // Check that all control elements exist
    if (!rangeSlider.length || !speedInput.length) {
        console.error('Control elements not found for motor', polishId);
        return;
    }

    // Toggle icons
    button.find('.icon-start').toggle();
    button.find('.icon-stop').toggle();
    
    let speed;
    if (button.find('.icon-stop').is(':visible')) {
        // Start - take value from slider
        speed = rangeSlider.val();
        button.css({
            'background-color': '#F63235',
            'color': 'white'
        });
    } else {
        // Stop - set to 0
        speed = 0;
        rangeSlider.val(0); // Reset slider
        speedInput.val(0); // Reset hidden field
        if (speedDisplay.length) speedDisplay.text(0); // Update display if exists
        button.css({
            'background-color': '#008fff',
            'color': 'white'
        });
    }

    const direction = $(`#direction_${polishId}`).val();
    const startType = $(`#start_type_${polishId}`).val();
    
    sendData(polishId, speed, direction, startType);
});

// Function to send service data to server
function sendServiceData(state) {
    const processedData = {
        state: parseInt(state)
    };

    fetch('/submit_service', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(processedData)
    })
    .then(response => response.json())
    .then(data => {
        console.log('Data sent successfully:', data);
    })
    .catch(error => {
        console.error('Error sending data:', error);
    });
}

// Handler for "Service Mode" button
$('.btn-icon[data-state]').click(function() {
    const button = $(this);
    let state = button.attr('data-state'); 

    if (state == 0) {
        state = 1; 
        button.attr('data-state', 1);
        button.css({
            'background-color': '#F08383', 
            'color': 'white'
        });
    } else {
        state = 0; // Disable service mode
        button.attr('data-state', 0); 
        button.css({
            'background-color': '#C6DCED', 
            'color': 'black'
        });
    }
    sendServiceData(state);
});

$('#kill_btn').click(function() {
    const button = $(this);
    let state = button.attr('data-state');
    activeElementsToToggle = $('.active, .red-active');
    const elementsToToggle = $('.blue, .red'); // All elements with these classes
    const rangeElements = $('.range'); // Sliders with .range class

    if (state == 0) {
        // Activate "red" mode
        state = 1;
        button.attr('data-state', 1);
        $('.hidden_box').css('display', 'block');

        // Switch classes
        activeElementsToToggle.removeClass('active').addClass('red-active');
        elementsToToggle.removeClass('blue').addClass('red');

        // Change slider accent color to red
        rangeElements.css('accent-color', 'rgb(246, 50, 53)');
    }
    else {
        // Activate "blue" mode
        state = 0;
        button.attr('data-state', 0);
        $('.hidden_box').css('display', 'none');

        // Switch classes
        activeElementsToToggle.removeClass('red-active').addClass('active');
        elementsToToggle.removeClass('red').addClass('blue');

        // Change slider accent color to blue
        rangeElements.css('accent-color', '#4861FF');
    }

    // Send data to server
    fetch('/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            motorId: "killall",
            status: state
        })
    })
    .then(response => response.json())
    .then(data => console.log('Success:', data))
    .catch(error => console.error('Error:', error));
});
