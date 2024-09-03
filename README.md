This code will display ultrasonic data value in a web page from time to time. Values from sensor also store in database.
-- created by boinsent --

ADDED CODE
sept 3 2024

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>GPIO Control</title>
    <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
    <script>
        var socket = io();

        socket.on('status_update', function(data) {
            for (const pin in data) {
                const pinInfo = data[pin];
                document.getElementById(`status-${pin}`).innerText = pinInfo.state === 1 ? 'Inactive' : 'Active';
                document.getElementById(`status-${pin}`).className = pinInfo.state === 1 ? '' : 'warning';
                document.getElementById(`on-${pin}`).disabled = pinInfo.state === 0;
                document.getElementById(`off-${pin}`).disabled = pinInfo.state === 1;
            }
        });

        window.onload = function() {
            socket.emit('request_status');
        };
    </script>
    <style>
        .warning {
            color: red;
        }
    </style>
</head>
<body>
    <table>
        <thead>
            <tr>
                <th>Name</th>
                <th>Status</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for pin, pin_info in pins.items() %}
            <tr>
                <td>{{ pin_info.name }}</td>
                <td id="status-{{ pin }}" class="{{ 'warning' if pin_info.state == GPIO.LOW else '' }}">
                    {{ 'Inactive' if pin_info.state == GPIO.HIGH else 'Active' }}
                </td>
                <td>
                    <button id="on-{{ pin }}" onclick="window.location.href='{{ url_for('control_pin', pin=pin, action='on') }}'" {{ 'disabled' if pin_info.state == GPIO.LOW else '' }}>On</button>
                    <button id="off-{{ pin }}" onclick="window.location.href='{{ url_for('control_pin', pin=pin, action='off') }}'" {{ 'disabled' if pin_info.state == GPIO.HIGH else '' }}>Off</button>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>


PYTHON

|

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import RPi.GPIO as GPIO

app = Flask(__name__)
socketio = SocketIO(app)

pins = {
    16: {'name': 'Relay 2', 'state': GPIO.HIGH},
    12: {'name': 'Relay 3', 'state': GPIO.HIGH},
    21: {'name': 'Relay 4', 'state': GPIO.HIGH},
    6: {'name': 'Pump', 'state': GPIO.HIGH},
    20: {'name': 'Chlorine', 'state': GPIO.HIGH}
}

@app.route('/')
def index():
    return render_template('index.html', pins=pins)

@app.route('/<int:pin>/<string:action>')
def control_pin(pin, action):
    if pin in pins:
        if action == "off":
            GPIO.output(pin, GPIO.HIGH)
            pins[pin]['state'] = GPIO.HIGH

            important_pins = [12, 16, 21]
            any_important_pin_on = any(pins.get(p, {}).get('state') == GPIO.LOW for p in important_pins)

            if not any_important_pin_on:
                GPIO.output(6, GPIO.HIGH)

        elif action == "on":
            GPIO.output(pin, GPIO.LOW)
            pins[pin]['state'] = GPIO.LOW

            important_pins = [12, 16, 21]
            any_important_pin_on = any(pins.get(p, {}).get('state') == GPIO.LOW for p in important_pins)
            if any_important_pin_on:
                GPIO.output(6, GPIO.LOW)

        # Emit status update
        socketio.emit('status_update', pins, broadcast=True)

    return render_template('index.html', pins=pins)

@socketio.on('request_status')
def handle_request_status():
    emit('status_update', pins)

if __name__ == '__main__':
    app.run(
        debug=True,
        host='0.0.0.0',
        port=8000,
        threaded=True)

    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
