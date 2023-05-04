import websocket
import os
import json
import random
import time

url = f"wss://app.rvrb.one/ws-bot?apiKey={os.environ.get('apikey')}"
channelId = None
password = os.environ.get('password', None)

ws = None
latency = 0
reconnect = True
joinId = None

# Attempt to join my channel
def join():
    global joinId
    joinId = round(random.random() * 100) # Provide an ID to get a response
    joinRequest = {
        "method": "join",
        "params": {
            "channelId": channelId
        },
        "id": joinId
    }
    if password:
        joinRequest["params"]["password"] = password
    ws.send(json.dumps(joinRequest))

# Event handlers for the WebSocket connection
# These are called when the server sends a message
# with a method that matches the key
def keepAwake(data):
    global latency
    # Keep awake is like a ping but also used to measure latency
    latency = data["params"]["latency"]
    print(f"Latency: {latency}ms")
    # Send a stayAwake message back to the server
    # If the server doesn't receive a stayAwake message 3 times in a row
    # The server will close the connection
    ws.send(json.dumps({
        "jsonrpc": "2.0",
        "method": "stayAwake",
        "params": {
            "date": int(time.time() * 1000)
        }
    }))

def ready(data):
    global channelId
    if data.params["channelId"]:
        channelId = data.params["channelId"]
    join() # Server sends ready when it's ready to receive commands

def pushChannelMessage(data):
    print("Received chat message", data["params"])

def pushNotification(data):
    print("Received notification", data["params"]) # Notification from the server

def updateChannel(data):
    print("Received channel update", data["params"]) # Channel name or description change

def updateChannelUsers(data):
    print("Received channel users update", data["params"]) # Users join or leave

def updateUser(data):
    print("Received user update", data["params"]) # User changes name or avatar, etc.

def updateChannelDjs(data):
    print("Received channel djs update", data["params"]) # DJs change

def updateChannelMeter(data):
    print("Received channel meter update", data["params"]) # Users vote

def updateChannelUserStatus(data):
    print("Received channel user status update", data["params"]) # User AFK, active, etc.

def leaveChannel(data):
    print("Received leave channel", data["params"]) # Command to leave channel
    global reconnect
    reconnect = False
    ws.close()

def playChannelTrack(data):
    print("Received play channel track", data["params"]) # Track starts playing

def pauseChannelTrack(data):
    print("Received pause channel track", data["params"]) # Track paused

eventHandlers = {
    "keepAwake": keepAwake,
    "ready": ready,
    "pushChannelMessage": pushChannelMessage,
    "pushNotification": pushNotification,
    "updateChannel": updateChannel,
    "updateChannelUsers": updateChannelUsers,
    "updateUser": updateUser,
    "updateChannelDjs": updateChannelDjs,
    "updateChannelMeter": updateChannelMeter,
    "updateChannelUserStatus": updateChannelUserStatus,
    "leaveChannel": leaveChannel,
    "playChannelTrack": playChannelTrack,
    "pauseChannelTrack": pauseChannelTrack
}

def onMessage(ws, message):
    data = json.loads(message)
    print(f"Received message: {message}")
    # wait for the ready message before sending anything else
    if 'method' in data and data['method'] in eventHandlers:
        eventHandlers[data['method']](data)
    elif 'id' in data and data['id'] == joinId:
        # was join a success?
        if 'error' in data:
            print(f"Error joining channel: {data['error']['message']}")
        else:
            print(f"Joined channel {channelId}")

def onPing(ws, message):
    print("Received ping from server")
    ws.pong()

def onPong(ws, message):
    print("Received pong from server")
    ws.ping()

def onOpen(ws):
    print("Connected to server")

def onClose(ws):
    print("Disconnected from server")
    # reconnect?
    if reconnect:
        ws.run_forever()

def onError(ws, error):
    print(f"WebSocket error: {error}")

def connect():
    global ws
    # attempt to connect to the WebSocket server
    ws = websocket.WebSocketApp(url, on_open=onOpen, on_message=onMessage, on_error=onError, on_close=onClose)
    ws.on_ping = onPing
    ws.on_pong = onPong
    ws.run_forever()

connect()