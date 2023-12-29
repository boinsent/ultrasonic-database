from flask import Flask, render_template, jsonify, request, redirect, url_for
import RPi.GPIO as GPIO
from ultrasonic import measure_distance
from insert_into_database import insert_distance_into_database, cursor
from firebase_connection import firebase_app

main = Flask(__name__)
app = Flask(__name__, static_url_path='/static')

TRIG_PIN = 17
ECHO_PIN = 18


def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TRIG_PIN, GPIO.OUT)
    GPIO.setup(ECHO_PIN, GPIO.IN)


@main.route('/')
def login_form():
    setup_gpio()
    return render_template('index.html')


@main.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    # Example query (modify as needed)
    query = "SELECT * FROM users WHERE username=%s AND password=%s"
    cursor.execute(query, (username, password))
    result = cursor.fetchone()

    if result:
        # Successful login, redirect to the dashboard
        return redirect(url_for('dashboard'))
    else:
        # Invalid username or password, return an error message
        return 'Invalid Username or Password.'


@main.route('/get_distance')
def get_distance():
    distance = measure_distance(TRIG_PIN, ECHO_PIN)

    # Databasemeasure_distance
    insert_distance_into_database(distance)

    # Firebase
    firebase_app.put('/ultrasonic', 'distance', distance)

    return jsonify(distance=distance)


@main.route('/dashboard')
def dashboard():
    distance = measure_distance(TRIG_PIN, ECHO_PIN)

    # Database
    insert_distance_into_database(distance)

    # Firebase
    firebase_app.put('/ultrasonic', 'distance', distance)

    return render_template('dashboard.html', distance=distance)


if __name__ == '__main__':
    main.run(debug=True, host='0.0.0.0', port=8000)


# For github reference
# name ng database = admin
# password ng database = rainharvesting
# Database name = ultrasonic
# Table name = ultrasonicdata
