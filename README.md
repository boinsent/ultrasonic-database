This code will display ultrasonic data value in a web page from time to time. Values from sensor also store in database.
-- created by boinsent --

ADDED CODE
sept 3 2024

from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import subprocess
from Sensor import get_flow_value, distance, floatSensor
import RPi.GPIO as GPIO
import time
import threading
import asyncio
from AIpredict import get_predicted_time_fill
from database import cursor, database, input_rain_table,view_rain_table
from email.mime.text import MIMEText
from email.message import EmailMessage
import smtplib
import random
import string
#import requests
import datetime
import serial
import threading

serial_port = '/dev/ttyUSB0'
baud_rate = 9600 

app = Flask(__name__)
app.secret_key = 'rainharvest1'


# GET PH level from arduino via serial com
@app.route('/PH_level', methods=['GET'])
def PH_level():
    try:
        # Open serial port
        ser = serial.Serial(serial_port, baud_rate, timeout=1)
        # print("Serial port opened successfully")
        ser.reset_input_buffer()
        ser.flush()
        
        time.sleep(1)

        # Read data from serial port until newline character is received
        serial_data = ser.readline().decode().strip()
        ph_level = float(serial_data)
        # Print the received data
#         print("Received:", serial_data)
        try:
            
            if ph_level < 6.5:   #CHLORINE THRES
                GPIO.output(20, GPIO.LOW)  # Turn on GPIO 21
                threading.Timer(10.0, lambda: GPIO.output(21, GPIO.HIGH)).start()
            else:
                GPIO.output(20, GPIO.HIGH)   # Turn off GPIO 21
        except ValueError:
            print("Received invalid PH level data")
            
        return jsonify(serial_data)

    except serial.SerialException as e:
        # print("Error opening serial port:", e)
        return jsonify({ "fooking eyyror" })
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            # print("Serial port closed")
        
        
# main route
@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('landingpage.html')


# GPIO setup
GPIO.setmode(GPIO.BCM)  # Set GPIO numbering mode to BCM

# Define GPIO pins and initial states
pins = {
    16: {'name': 'Relay 2', 'state': GPIO.HIGH},
    12: {'name': 'Relay 3', 'state': GPIO.HIGH},
    21: {'name': 'Relay 4', 'state': GPIO.HIGH},
    6: {'name': 'Pump', 'state': GPIO.HIGH},  # GPIO 6 setup
    20: {'name': 'Chlorine', 'state': GPIO.HIGH}  # Chlorine
}

# Initialize GPIO pins
for pin in pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.HIGH if pins[pin]['state'] == GPIO.HIGH else GPIO.LOW)


# login
@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor.execute('SELECT * FROM accounts WHERE username = %s AND password = %s', (username, password))
        account = cursor.fetchone()

        if account:
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template('wrong_password.html')


# log out
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# send email code FROM LINE 52 TO 96


def email_exists(email):
    cursor.execute('SELECT COUNT(*) FROM accounts WHERE email = %s', (email,))
    count = cursor.fetchone()[0]
    return count > 0


def generate_password(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))


# Function para sa send email
def send_email(email, password):
    sender_email = 'aiotrainharvest@gmail.com'
    receiver_email = email
    password = password

    message = MIMEText(f"Your new password is: {password}")
    message['Subject'] = 'New Password'
    message['From'] = sender_email
    message['To'] = receiver_email
    smtp_server = smtplib.SMTP('smtp.gmail.com', 587)
    smtp_server.starttls()
    smtp_server.login(sender_email, 'tztr irkl xxbi ynpf')
    smtp_server.sendmail(sender_email, receiver_email, message.as_string())
    smtp_server.quit()


# Send email button sa forgot_password.html
@app.route('/forg_pw', methods=['POST'])
def send_to_email():
    email = request.form['email']
    if email_exists(email):
        new_password = generate_password()
        send_email(email, new_password)

        # Update pass
        cursor.execute('UPDATE accounts SET password = %s WHERE email = %s', (new_password, email))
        database.commit()

        return redirect(url_for('redirect_to_success_page'))
    else:
        return redirect(url_for('unsuccessful_send'))


# CHANGE PASSWORD 07/21/24
@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'username' not in session:
        return redirect(url_for('back_to_index'))

    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
            return render_template('doesnt_match_password.html')

        if old_password == new_password:
            return render_template('cannot_same_password.html')

        if len(new_password) < 5 or len(confirm_password) < 5:
            return render_template('less_than5_password.html')

        username = session['username']

        query = "SELECT * FROM accounts WHERE username=%s AND password=%s"
        cursor.execute(query, (username, old_password))
        result = cursor.fetchone()

        if result:
            update_query = "UPDATE accounts SET password=%s WHERE username=%s"
            cursor.execute(update_query, (new_password, username))
            database.commit()
            session.clear()
            return render_template('change_password.html')
        else:
            return render_template('old_password_doesnt_match.html')

    return render_template('dashboard.html')


# CONTACT | EMAIL SUPPORT

@app.route('/send_to_support', methods=['POST'])
def send_to_support():
    user_name = request.form['user_name']
    user_email = request.form['user_email']
    user_message = request.form['user_message']

    if not user_email.endswith('@gmail.com'):
        return 'Invalid email address.'

    if not user_message.strip():
        return 'Message cannot be empty.'

    email_address = 'aiotrainharvest@gmail.com'
    email_password = 'tztr irkl xxbi ynpf'

    subject = 'New Message From Rain Harvest Application'
    message = EmailMessage()
    message['From'] = user_email, user_name
    message['To'] = email_address
    message['Subject'] = subject
    message.set_content(f'Name: {user_name}, \n, Email: {user_email}, \n, {user_message}')

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(email_address, email_password)
            server.send_message(message)
        return redirect(url_for('message_sent'))
    except Exception as e:
        return f'Error occurred: {str(e)}'

# Redirections


@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        # Update pin states based on GPIO input
        for pin in pins:
            pins[pin]['state'] = GPIO.input(pin)
        return render_template('dashboard.html', pins=pins)
    else:
        return redirect(url_for('index'))




# control GPIO pins route
@app.route('/<int:pin>/<string:action>')
def control_pin(pin, action):
    if pin in pins:
        if action == "off":
            GPIO.output(pin, GPIO.HIGH)
            # Update the pin state
            pins[pin]['state'] = GPIO.HIGH

            # Check if any of the specific pins (12, 16, 21) is still in the ON state
            important_pins = [12, 16, 21]
            any_important_pin_on = any(pins.get(p, {}).get('state') == GPIO.LOW for p in important_pins)

            if not any_important_pin_on:
                GPIO.output(6, GPIO.HIGH)  # Turn off GPIO 6 only if none of the important pins are ON

        elif action == "on":
            GPIO.output(pin, GPIO.LOW)
            # Update the pin state
            pins[pin]['state'] = GPIO.LOW

            # Turn GPIO 6 on if any of the important pins are ON
            important_pins = [12, 16, 21]
            any_important_pin_on = any(pins.get(p, {}).get('state') == GPIO.LOW for p in important_pins)
            if any_important_pin_on:
                GPIO.output(6, GPIO.LOW)  # Turn on GPIO 6 if any of the important pins are ON

    return redirect(url_for('dashboard'))
# settings
@app.route('/settings')
def settings():
    if 'username' in session:
        return render_template('settings.html')
    else:
        return redirect(url_for('index'))


@app.route('/water_reading')
def water_reading():
    if 'username' in session:
        return render_template('Water_meter_reading.html')
    else:
        return redirect(url_for('index'))


# redirect sa landing page
@app.route('/back_to_index', methods=['POST'])
def back_to_index():
    return render_template('/landingpage.html')


@app.route('/back_to_dashboard', methods=['POST'])
def back_to_dashboard():
    return redirect(url_for('dashboard'))
# Success page
@app.route('/redirect_to_success_page')
def redirect_to_success_page():
    return render_template('/success_send.html')


# unsuccessful send
@app.route('/unsuccessful_send')
def unsuccessful_send():
    return render_template('/unsuccessful_send.html')


# successfully send to support
@app.route('/message_sent')
def message_sent():
    return render_template('send_to_support.html')


# redirect to old password is doesnt match password page
@app.route('/password_doesnt_match')
def password_doesnt_match():
    return render_template('doesnt_match_password.html')

# forgot password page
@app.route('/forgot_password')
def forgot_password():
    return render_template('/forgot_password.html')


# CODE PARA SA MGA SENSORS

@app.route('/get_sensor_data', methods=['GET'])
def get_sensor_data():
    try:

        dist = distance()
        flow = get_flow_value()
        
         #Get current time
        current_time = datetime.datetime.now().time()
        # Daniel dito mo palitan
        if current_time.hour == 22 and current_time.minute == 00:
            input_rain_table(float(dist))
            
            #input_rain_table(float(dist))
            
        if floatSensor() == GPIO.HIGH:
            flow = 0
            
        print("flowrate: ",flow)
        print("dist: ",dist)
        
        return jsonify({
            'distance': dist,
            'flow': flow
            })
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        app.logger.error(error_message)
        print(error_message)
        
        return jsonify({
            'distance': 0.05,
            'flow': 1
            }),200
        # return jsonify({'error': str(e)}), 500


@app.route('/predicted_time', methods=['POST'])
def predicted_time():
    try:
        
        data = request.json
        timefill = get_predicted_time_fill(float(data['distance'])* 1000,float(data['flow']))
        
        if floatSensor() == GPIO.HIGH:
            timefill = "00.00"
        
        return jsonify({
            'timefill': timefill
            })

    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        app.logger.error(error_message)
        return jsonify({'error': str(e)}), 500


def display_sensor():
    dist = distance()
    flow = get_flow_value()
    print("distance:", dist)
    print("flow:", flow)


@app.route('/get_rain_table', methods=['GET'])
def get_rain_table():
    try:

        return jsonify(view_rain_table())
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        app.logger.error(error_message)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':

    app.run(
        debug=True,
        host='0.0.0.0',
        port=8000,
        threaded=True)

XXX

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document</title>
    <link rel="stylesheet" href="static/css/style.css">
    <link rel="stylesheet" href="https://fonts.googleapis.com/icon?familiy=Material+Icons+Sharp">
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns"></script>
</head>
<style>
        /* Custom button styles */
        .btn-on {
            background-color: green;
            color: white;
            padding: 5px;
            border-radius: 5px;
        }
        .btn-off {
            background-color: red;
            color: white;
            padding: 5px;
            border-radius: 5px;
        }
        .tank-container {
    width: 100px; /* Adjust the width of the tank */
    height: 150px; /* Adjust the height of the tank */
    position: relative;
    background-color: #ddd; /* Tank color */
    border-radius: 10px; /* Rounded corners for tank */
    overflow: hidden;
}

.tank-water {
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100%;
    background-color: blue; /* Water color */
    transition: height 1s ease; /* Smooth transition for filling animation */
    animation: wave 2s ease-in-out infinite alternate; /* Wave animation */
}

.water_level .middle .progress {
    display: none; /* Hide the percentage circle */
}

.water-level-text {
    position: absolute;
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    font-size: 14px;
    color: white;
}

@keyframes wave {
    0% {
        transform: translateY(-5px);
    }
    100% {
        transform: translateY(5px);
    }
}
  #waterLevelChart {

    height: 400px; /* Keep the height of the chart canvas */
    width: 100%;
}

/* Default styles for larger screens */
.waterlevelchart_container {
    position: sticky;
    max-width: 800px; /* Adjust as needed */
    width: 100%;
    margin: 0 auto;
    padding: 20px;
    box-sizing: border-box;
    margin-top: -100px;
}

#waterLevelChart {
    max-width: 100%;
    height: auto;
    display: block;
}
@media screen and (max-height: 700px) {
.waterlevelchart_container {
  margin-top: 10px;
}
}

/* Media query for smaller screens (e.g., mobile phones) */
@media screen and (max-width: 900px) {
    .waterlevelchart_container {
       /* Adjust padding for smaller screens */
        /* Full viewport height */
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin-top:auto;
    }


    #waterLevelChart {
        max-width: 100%;
        height: 100%; /* Full height of its container */
    }
}






    </style>
<body>

    <div class="container">
        <aside>
            <div class="top">
                <span class="material-symbols-outlined" style="align-items:center ; color:#7380ec;"> water_drop</span>
                <h2> Rain <span class="warning">Harvesting</span></h2>
                <!-- <div class="close">
                    <span class="material-symbols-outlined">close</span>

                </div> -->
            </div>

          <div class="sidebar">
                <a href="{{url_for('dashboard')}}" class="active">
                    <span class="material-symbols-outlined">dashboard</span>
                    <h3>Dashboard</h3>
                </a>

<!--               <a href="{{url_for('water_reading')}}" >-->
<!--                    <span class="material-symbols-outlined">data_table</span>-->
<!--                    <h3>Water Reading</h3>-->
<!--                </a>-->

                <a href="{{url_for('settings')}}">
                    <span class="material-symbols-outlined">tune</span>
                    <h3>Settings</h3>
                </a>

                <a href="/logout">
                    <span class="material-symbols-outlined">logout</span>
                    <h3>Logout</h3>
                </a>
         </div>
        </aside>

        <main>
            <h1>Dashboard</h1>
            <div class="date">
                <input type= "date" id="todayDate" style="display: none;">
                <p id="currentTime" style="color: black; font-size: 15px;"></p>
                <p id="formattedDate" style="color: black;"> </p>
            </div>

            <div class="insights">
                <div class="water_level">
                 <div class="water_level-left">
    <span class="material-symbols-outlined">opacity</span>
    <h3 style="padding-top: 1.4rem;">Water Level</h3>
    <div class="middle">
        <div class="left">
            <h1 id="distance">00.00</h1>
            <h3>Cubic meter</h3>
        </div>

<!--        <div class="tank-container">-->
<!--    <div class="tank-water" id="tankWater"></div>-->
<!--    <div class="water-level-text" id="waterLevelText"></div>-->
<!--</div>-->
    </div>
    <small class="text-muted">Last 24 Hours</small>
                     </div>
       <div class="water_level-right">
        <div class="tank-container">
    <div class="tank-water" id="tankWater"></div>
    <div class="water-level-text" id="waterLevelText"></div>
</div>
           </div>
</div>

                <!-- END OF WATER LEVEL -->
                <div class="Flow_rate">
                    <span class="material-symbols-outlined">water</span>
                    <h3 style="padding-top: 1.4rem;">Flow Rate</h3>
                    <div class="middle">
              <div class="left">
                            <h1 id="flow-value">00.00</h1>
                            <h3>Per Minute</h3>
                        </div>
                    </div>
                    <small class="text-muted">Last 24 Hours</small>
                </div>


                  <!-- END OF FLOW RATE -->
                  <div class="Fill_time">
                    <span class="material-symbols-outlined">water_ec</span>
                    <h3 style="padding-top: 1.4rem;">Time to Fill</h3>
                    <div class="middle">
                        <div class="left">
                            <h1 id="predictedTimeFill">00:00</h1>
                            <h3>Hours/min</h3>
                        </div>

                    </div>
                    <small class="text-muted">Last 24 Hours</small>
                </div>
                <!-- END OF FILL TIME -->

            </div>
                <!-- END OF INSIGHTS -->
                <div class="lower_dashboard">
                <div class="Component">

                    <table>
        <thead>
            <tr>
                <th>Component List</th>
                <th>Status</th>
                <th>Action</th>
            </tr>
        </thead>
        <tbody>
            {% for pin, pin_info in pins.items() %}
            <tr>
                <td>{{ pin_info.name }}</td>
                <td class="{{ 'warning' if pin_info.state else '' }}">{{ 'Inactive' if pin_info.state else 'Active' }}</td>
                <td>
                    <a href="{{ url_for('control_pin', pin=pin, action='on') }}"><button class="btn-on">On</button></a>
                    <a href="{{ url_for('control_pin', pin=pin, action='off') }}"><button class="btn-off">Off</button></a>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
                </div>
                <div class="ph_level">
                        <span class="material-symbols-outlined"> water_ph</span>
                        <h3 style="padding-top: 1.4rem;">Water PH</h3>
                        <div class="middle">
                            <div class="left">
                                <h1 id="PH_level">0.0</h1>
                                <h3>Ph Level</h3>
                            </div>
                        </div>
                        <small class="text-muted">Current reading</small>
                    </div>
                    </div>
                <br><br>
                </main>

    </div>
                 <!----------------------------------- CHART  ------------------------------>
            <div class ="waterlevelchart_container">
               <h1>Daily Water Level for One Month</h1>
                    <canvas id="waterLevelChart"></canvas>

               </div>

    <!----------------------------------- AI SCRIPT  ------------------------------>
<script>

// Water variables
const totalCapacity = 0.051; // Total capacity of the tank in cubic meters

function animation_level(currentWaterLevel){

// Calculate water level percentage
const waterLevelPercentage = (currentWaterLevel / totalCapacity) * 100;

// Set the tank height based on total capacity
const tankHeight = 150; // Assuming 150 pixels for full capacity

// Set the water height based on the water level percentage
const waterHeight = (waterLevelPercentage / 100) * tankHeight;

// Update water level text
const waterLevelTextElement = document.getElementById('waterLevelText');
waterLevelTextElement.textContent = `${waterLevelPercentage.toFixed(2)}%`;

// Update tank water height
const tankWaterElement = document.getElementById('tankWater');
tankWaterElement.style.height = `${waterHeight}px`;
    
    return "running";
}

animation_level(0.0);
       
        async function fetchWaterLevelData() {
           
            const startDate = new Date();
            startDate.setDate(startDate.getDate() - 6); // Go back 6 days from today

            const data = [];
            for (let i = 0; i < 7; i++) {
                const date = new Date(startDate);
                date.setDate(startDate.getDate() + i);
                data.push({
                    date: date.toISOString().split('T')[0], // Format date as YYYY-MM-DD
                    water_level: Math.floor(Math.random() * 100) // Random water level between 0 and 99
                });
            }
            return data;
        }

        
        async function generateChart() {
            const data = await get_rain_table();


            // console.log(data);
            
            

            
            const dates = data.map(entry => entry.date);
            const waterLevels = data.map(entry => entry.water_level);

           
            const ctx = document.getElementById('waterLevelChart').getContext('2d');
            const waterLevelChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: dates,
                    datasets: [{
                        label: 'Water Level',
                        data: waterLevels,
                        borderColor: 'rgba(75, 192, 192, 1)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        fill: false,
                        borderWidth: 1
                    }]
                },
                options: 
                
                {
                    scales: {
                        x: {
                            type: 'time',
                            time: {
                                unit: 'day',
                                tooltipFormat: 'yyyy-MM-dd',
                                displayFormats: {
                                    day: 'yyyy-MM-dd'
                                }
                            }
                        },
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        
    async function get_rain_table() {
    try {
        const response = await fetch('/get_rain_table');
        if (!response.ok) {
            throw new Error('Failed to fetch data');
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching sensor data:', error);
        return null;
    }
}

       generateChart();
       setInterval(generateChart,1000);


    // to get water level
    async function updateSensorData() {
        await fetch('/get_sensor_data')
            .then(response => response.json())
            .then(data => {
                // const timeFillElement = document.getElementById('predictedTimeFill');
                // timeFillElement.textContent = data.timefill;
                
                // get water level distance
                document.getElementById('distance').textContent = data.distance;
                
     
             console.log(animation_level(parseFloat(data.distance)));
                document.getElementById('flow-value').textContent = data.flow;
            })
            .catch(error => {
             console.log(animation_level(parseFloat(0.000)));
                // console.error('Error fetching sensor data:', error);
            });
    }
        
     // AI Prediction
     async function predictedData() {
         await fetch('/predicted_time',{
            method: 'POST',
            headers: {
               'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                distance: document.getElementById('distance').textContent,
                flow: document.getElementById('flow-value').textContent
            })
        })
        .then(response => response.json())
            .then(data => {
                const timeFillElement = document.getElementById('predictedTimeFill');
                timeFillElement.textContent = data.timefill;
               

            })
            .catch(error => {
                console.error('Error fetching sensor data:', error);
            });
    }
    
    // to get PH LEVEL
    async function PH_level() {
         await fetch('/PH_level',{
            method: 'GET',
            headers: {
               'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
            .then(data => {
                const timeFillElement = document.getElementById('PH_level');
                timeFillElement.textContent = "Serial Data: " + data;
                // console.log(data);
               

            })
            .catch(error => {
                console.error('Error fetching sensor data:', error);
            });
    }

    updateSensorData();
    predictedData();
    PH_level();
    
    setInterval(updateSensorData,2000);
    setInterval(predictedData,1500);
    setInterval(PH_level,2000);
</script>
<!--     <script>-->
<!--    function updatePredictedTimeFill() {-->
<!--        fetch('/get_filltime')-->
<!--            .then(response => response.json())-->
<!--            .then(data => {-->
<!--                const timeFillElement = document.getElementById('predictedTimeFill');-->
<!--                timeFillElement.textContent = data.timefill;-->
<!--            })-->
<!--            .catch(error => {-->
<!--                console.error('Error fetching predicted time fill:', error);-->
<!--            });-->
<!--    }-->

<!--    // Update predicted time fill every second-->


<!--    // Initial call to update time fill immediately-->

<!--</script>-->
<!--    &lt;!&ndash;-&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45; SENSOR SCRIPT  &#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&ndash;&gt;-->
<!--                    &lt;!&ndash;-&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;  ULTRASONIC &#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&#45;&ndash;&gt;-->
<!--    <script>-->
<!--        function updateDistance() {-->
<!--            fetch('/get_distance')-->
<!--                .then(response => response.json())-->
<!--                .then(data => {-->
<!--                    document.getElementById('distance').innerText = data.distance.toFixed(2);-->
<!--                });-->
<!--        }-->
<!--        setInterval(updateDistance, 1000);-->

<!--        // Initial update-->
<!--        updateDistance();-->
<!--    </script>-->
<!--                               &lt;!&ndash;&#45;&#45;&#45;&#45;  FLOW RATE  -&#45;&#45;&#45;&#45;&ndash;&gt;-->
<!--    <script>-->
<!--        // Function to update the flow value every 5 seconds-->
<!--        setInterval(function() {-->
<!--            // Make a request to the server to get the updated flow value-->
<!--            fetch('/get_flow')-->
<!--                .then(response => response.json())-->
<!--                .then(data => {-->
<!--                    // Update the displayed value with 2 decimal places-->
<!--                    const formattedFlow = data.flow.toFixed(2);-->
<!--                    document.getElementById('flow-value').innerText = formattedFlow;-->
<!--                })-->
<!--                .catch(error => console.error('Error:', error));-->
<!--        },1000);-->
<!--    </script>-->


            <!------  END SENSOR SCRIPT  ------->
    <script>
        // Get today's date in the format "Day name, Month day no."
        function getFormattedDate() {
            const options = { weekday: 'long', month: 'long', day: 'numeric' };
            const today = new Date();
            return today.toLocaleDateString('en-US', options);
        }

        // Set the default value of the input to today's date in the standard format
        const todayDateInput = document.getElementById('todayDate');
        todayDateInput.value = new Date().toISOString().split('T')[0]; // Standard "YYYY-MM-DD" format

        // Display the formatted date in a separate element
        const formattedDateElement = document.getElementById('formattedDate');
        formattedDateElement.textContent = `${getFormattedDate()}`;
    </script>
    <script>
        // Get the current time in 12-hour format with hours and minutes
        function getCurrentTime() {
            const options = { hour: 'numeric', minute: 'numeric', hour12: true };
            const currentTime = new Date();
            return currentTime.toLocaleTimeString('en-US', options);
        }

        // Display the current time in the specified format
        const currentTimeElement = document.getElementById('currentTime');
        currentTimeElement.textContent = `${getCurrentTime()}`;
    </script>

</body>
</html>
