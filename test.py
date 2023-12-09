import mysql.connector

db_connection = mysql.connector.connect(
    host="localhost",
    user="id21645509_rainharvest",
    password="Rainharvest23!",
    database="ultrasonicdata"
)
cursor = db_connection.cursor()
data = 12
insert_query = "INSERT INTO ultrasonic (distance) VALUES (%s)"
cursor.execute(insert_query, data)

db_connection.commit()
cursor.close()
db_connection.close()