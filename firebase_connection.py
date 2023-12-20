from firebase import firebase

firebase_config = {
    "apiKey": "AIzaSyCoqiwOhIjnJ7l-XbIJRECcwn_h0U5WxIk",
    "authDomain": "aiotrainharvest-e346e.firebaseapp.com",
    "databaseURL": "https://aiotrainharvest-e346e-default-rtdb.asia-southeast1.firebasedatabase.app",
    "projectId": "aiotrainharvest-e346e",
    "storageBucket": "aiotrainharvest-e346e.appspot.com",
    "messagingSenderId": "701221410738",
    "appId": "1:701221410738:web:9f29a26ac45112f0ff76ab",
    "measurementId": "G-B57P5N0Y0M"
}

firebase_app = firebase.FirebaseApplication(firebase_config['databaseURL'], None)
