const WebSocket = require('ws')

// const url = `wss://app.rvrb.one/ws-bot?apiKey=${process.env.apikey}`
const url = `wss://app.rvrb.one/ws-bot?apiKey=${process.env.apikey}`

let channelId = null
const password = process.env.password || null

let ws = null
let latency = 0
const reconnect = true
let joinId = null

// attempt to join my channel
const join = () => {
  joinId = Math.round(Math.random() * 100) // provide an id to get a response
  const joinRequest = {
    method: 'join',
    params: {
      channelId
    },
    id: joinId
  }
  if (password) {
    joinRequest.params.password = password
  }
  ws.send(JSON.stringify(joinRequest))
}

// event handlers for the WebSocket connection
// these are called when the server sends a message
// with a method that matches the key
const eventHandlers = {
  keepAwake: (data) => {
    // keep awake is like a ping but also used to measure latency
    latency = data.params.latency
    console.log(`Latency: ${latency}ms`)
    // send a stayAwake message back to the server
    // if the server doesn't receive a stayAwake message 3 times in a row
    // the server will close the connection
    ws.send(JSON.stringify({
      jsonrpc: '2.0',
      method: 'stayAwake',
      params: {
        date: Date.now()
      }
    }))
  },
  ready: (data) => {
    if ('channelId' in data.params) {
      channelId = data.params.channelId
      join() // server sends ready when it's ready to receive commands
    }
  }
}

const connect = () => {
  // attempt to connect to the WebSocket server
  ws = new WebSocket(url)

  ws.on('open', () => {
    console.log('Connected to server')
  })

  ws.on('close', () => {
    console.log('Disconnected from server')
    // reconnect?
    if (reconnect) {
      setTimeout(() => {
        connect()
      }, 1000)
    }
  })

  ws.on('error', (error) => {
    console.error(`WebSocket error: ${error}`)
  })

  ws.on('message', (data) => {
    console.log(`Received message: ${data}`)
    try {
      data = JSON.parse(data)
    } catch (e) {
      console.error(`Error parsing JSON: ${e}`)
      return
    }
    // wait for the ready message before sending anything else
    if (data.method in eventHandlers) {
      eventHandlers[data.method](data)
    } else if (data.id === joinId) {
      // was join a success?
      if (data.error) {
        console.error(`Error joining channel: ${data.error.message}`)
      } else {
        console.log(`Joined channel ${channelId}`)
      }
    }
  })

  ws.on('ping', () => {
    console.log('Received ping from server')
    ws.pong()
  })

  ws.on('pong', () => {
    console.log('Received pong from server')
    ws.ping()
  })
}

connect()
