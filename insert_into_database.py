import mysql.connector
# from flask import render_template, request

db_connection = mysql.connector.connect(
    host="localhost",
    user="admin",
    password="rainharvest",
    database="ultrasonic"
)

cursor = db_connection.cursor()


# ultrasonic
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

