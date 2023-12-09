from flask import Flask, render_template, jsonify
import RPi.GPIO as GPIO
import mysql.connector
from ultrasonic import measure_distance

main = Flask(__name__)
app = Flask(__name__, static_url_path='/static')
TRIG_PIN = 17
ECHO_PIN = 18

# Values
maximum_value = 4.4
minimum_value = 17.2

db_connection = mysql.connector.connect(
    host="localhost",
    user="admin",
    password="rainharvest",
    database="ultrasonic"
)

# Create a cursor object to interact with the database
cursor = db_connection.cursor()


def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TRIG_PIN, GPIO.OUT)
    GPIO.setup(ECHO_PIN, GPIO.IN)


# connection sa website
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


def insert_distance_into_database(distance):
    sql = "INSERT INTO ultrasonicdata (distance) VALUES (%s)"

    data = (distance,)

    try:
        cursor.execute(sql, data)

        db_connection.commit()

        print("insert successfully.")

    except Exception as e:
        db_connection.rollback()
        print("Error inserting data:", str(e))


if __name__ == '__main__':
    main.run(debug=True, port=8000)

# For github reference
# name ng database = admin
# password ng database = rainharvesting
# Database name = ultrasonic
# Table name = ultrasonicdata

