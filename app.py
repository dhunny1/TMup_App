from flask import Flask, request, render_template #we are importing  flask and request and rednertemplate
from flask_socketio import SocketIO, emit, join_room

import sqlite3 #built in  database library
import uuid # built in unique ID generator

def init_db():
    conn = sqlite3.connect("rooms.db") #creates  rooms.db file if it doesn't exist
    c = conn.cursor()
    # room table
    c.execute('''CREATE TABLE IF NOT EXISTS rooms (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              code  TEXT UNIQUE,
              creator TEXT
              )''')
    # participants table
    c.execute('''CREATE TABLE IF NOT EXISTS participants (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              room_code TEXT,
              name TEXT
              )''')
    conn.commit()
    conn.close()

#then we are createing an web app
app = Flask(__name__)

# initializing
socketio = SocketIO(app)

#calls the funtion init_db to and creates  the room.db if doens't exist
init_db()


# this define a homepage route
@app.route("/")
# home function runs when someone vists "/"
def home():
    return render_template("index.html")

@app.route("/create-room", methods=["POST"])
def create_room():
    #generate  a short unique code  ( first 6 characcters of a UUID)
    code = str(uuid.uuid4())[:6]
    create = request.form.get("username","Anonymous")

    #save to database
    conn = sqlite3.connect("rooms.db")
    c = conn.cursor()
    c.execute("INSERT INTO rooms (code, creator) VALUES (?, ?)", (code,create))
    conn.commit()
    conn.close()
    return f"room created! share this code: {code}"

@app.route("/join-room", methods=["POST"])
def join_room():
    # get the code entered by user
    code = request.form.get("code")
    name = request.form.get("name", "GUEST")

    conn = sqlite3.connect("rooms.db")
    c = conn.cursor()
    c.execute("SELECT * FROM rooms WHERE code=?", (code,))
    room = c.fetchone()


    if room:
        #add participant
        c.execute("INSERT INTO participants (room_code, name) VALUES (?,?)", (code,name))
        conn.commit()

        #Get all participants
        c.execute("Select name FROM participants WHERE room_code=?", (code,))
        participants = [row[0] for row in c.fetchall()]  
        conn.close()

        socketio.emit("update_participants",{
            "code":code,
            "participants": participants
        }, room =code)

        return render_template("room.html", code=code, creator=room[2], participants=participants)
    #loock up the room in the database
    else:
        conn.close()
        return "Invalid  room code!"

@socketio.on("join")
def handle_join(data):
    code = data["code"]
    join_room(code)


# start the server locally with debugging
# if __name__ == "__main__":
#     socketio.run(app, debug=True)
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000)

    