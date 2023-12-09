from flask import Flask, render_template, jsonify
import RPi.GPIO as GPIO
from ultrasonic import measure_distance
from insert_into_database import insert_distance_into_database

main = Flask(__name__)
app = Flask(__name__, static_url_path='/static')
TRIG_PIN = 17
ECHO_PIN = 18


def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TRIG_PIN, GPIO.OUT)
    GPIO.setup(ECHO_PIN, GPIO.IN)


@main.route('/')
def index():
    setup_gpio()
    return render_template('dashboard.html')


# data ng sensor to py to js
@main.route('/get_distance')
def get_distance():
    distance = measure_distance(TRIG_PIN, ECHO_PIN)

    insert_distance_into_database(distance)

    return jsonify(distance=distance)


def percentage_value():
    pass


if __name__ == '__main__':
    main.run(debug=True, port=8000)

# For github reference
# name ng database = admin
# password ng database = rainharvesting
# Database name = ultrasonic
# Table name = ultrasonicdata

