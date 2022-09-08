#!/usr/bin/env python3


import json
import asyncio
import itertools
import websockets
import logging
import secrets

import os
import signal

from connect4 import PLAYER1, PLAYER2, Connect4

JOIN = {} # Dictionary w/ joinKey: game, connected (set of ws)

async def start(websocket):
    # Start the game, initialize the set of websocket connections
    game = Connect4() # Connect to the same game
    connected = {websocket}

    join_key = secrets.token_urlsafe(12) # Generates a token for unique game ID
    JOIN[join_key] = game, connected

    try:
        event = {
            "type": "init",
            "join": join_key # Creates an event with the generated key
        }

        await websocket.send(json.dumps(event)) # Send the event to ReceiveMoves() in client

        print("first player started game", id(game))

        async for message in websocket:
            print("first player sent", message)

    finally:
        del JOIN[join_key]

async def error(websocket, message):
    event = {
        "type": "error",
        "message": message
    }
    await websocket.send(json.dumps(event))

async def join(websocket, join_key):
    try:
        game, connected = JOIN[join_key] # Get the game and websocket connections from the join key parameter
    except KeyError:
        await error(websocket, "Game not found")
        return
    
    connected.add(websocket) # Add this websocket connection to the connected list

    try:
        print("second player joined game", id(game))
        async for message in websocket:
            print("second player sent", message)

    finally:
        connected.remove(websocket) # Once connection reaches an exception (closed, etc), cut it off


async def handler(websocket):
    # Waits for a message from the JS (client) side of the program to parse below - InitGame()
    message = await websocket.recv()

    event = json.loads(message) # Rxd the message, load it as JSON
    assert event["type"] == "init" # Check if the event is "init", if not raise an assertion error and quit

    if "join" in event:
        await join(websocket, event["join"]) # A game already exists, join that game with the event numhber
    else:
        await start(websocket) # First player starts game

async def main():
    
    async with websockets.serve(handler, "", 8001):
        await asyncio.Future()
    # Set the stop condition when receiving SIGTERM
    #loop = asyncio.get_running_loop()
    #stop = loop.create_future()
    #loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)

    #port = int(os.environ.get("PORT", "8001")) # For Heroku to listen in

    #async with websockets.serve(handler, "", port): # Starts handler coroutine with host and port as websocket connection
        #await stop # Waits for stop to set the result to stop the program


if __name__ == "__main__":
    asyncio.run(main())

    