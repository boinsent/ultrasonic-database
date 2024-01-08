import mysql.connector

account_connector = mysql.connector.connect(
    host="localhost",
    user="admin",
    password="rainharvest",
    database="users"
)

account_cursor = account_connector.cursor()