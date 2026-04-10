import atexit
import json
import socket
from flask import Flask, render_template, request
from flask_socketio import SocketIO
from threading import Lock
import os.path
import selectors
import types


thread = None
thread_lock = Lock()


# global HOST, PORT, bufferSize 
HOST = "127.0.0.1"  
PORT = 4004
bufferSize = 1024

# full path is neccessary for the Systemtest
app = Flask("MultiSpectator", template_folder=os.path.dirname(__file__) + "/templates/")
app.config['SECRET_KEY'] = 'donsky!'
socketio = SocketIO(app, cors_allowed_origins='*')


global tcpServerConn
# establish tcp connection to the MultiSpectator Application
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST,PORT))
    s.listen()
    tcpServerConn, addr = s.accept()

print(f"Listening on {(HOST,PORT)}")


"""
Background Thread
"""
#receive System status information from swarm-element-loop
def background_thread():

    global tcpServerConn, bufferSize 
    print("bgTh Started")   
    while(True):
        if tcpServerConn is None:
            continue  # Wait until the socket is initialized
        msg = tcpServerConn.recv(bufferSize) # BLOCKS
        print(msg.decode())
        socketio.emit('updateSensorData', msg.decode())

"""
Serve root index file
"""
@app.route('/')
def index():

    return render_template('swarmDisplay.html') 


"""
Decorator for connect
"""
@socketio.on('connect')
def connect():
    global thread
    print('Client connected')
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)
  

"""
Decorator for disconnect
"""
@socketio.on('disconnect')
def disconnect():
    print('Client disconnected',  request.sid)

"""
Decorator for Receiving formData
"""
# receive goal from webapp and send it to MultiSpectatorApp
@socketio.on('runAction')
def getInput(args):
    global updClientSocket
    print(args)
    print(tcpServerConn)
    if(tcpServerConn != None):
        tcpServerConn.send(str.encode(json.dumps(args) + "\n"))
        msg = tcpServerConn.recv(bufferSize) # BLOCKS
        socketio.emit('updateSensorData', msg.decode())


def cleanup():
    global stop_thread, tcpServerConn
    stop_thread = True
    print("Cleaning up sockets")
    try:
        tcpServerConn.close()
    except Exception as e:
        print(f"Error during cleanup: {e}")

atexit.register(cleanup)

if __name__ == '__main__':
    socketio.run(app)