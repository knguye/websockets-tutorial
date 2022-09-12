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

logging.basicConfig(format="%(message)s", level=logging.DEBUG)

JOIN = {} # Dictionary w/ joinKey: game, connected (set of ws)
WATCH = {} # Spectators

async def start(websocket):
    # Start the game, initialize the set of websocket connections
    game = Connect4() # Connect to the initialized game
    connected = {websocket}

    join_key = secrets.token_urlsafe(12) # Generates a token for unique game ID
    JOIN[join_key] = game, connected
    
    watch_key = secrets.token_urlsafe(12)
    WATCH[watch_key] = game, connected

    try:
        event = {
            "type": "init",
            "join": join_key, # Creates an event with the generated key
            "watch" : watch_key
        }

        await websocket.send(json.dumps(event)) # Send the event to ReceiveMoves() in client
        await play(websocket, game, PLAYER1, connected)

    finally:
        del JOIN[join_key]
        del WATCH[watch_key]

async def replay(websocket, game):
    # Send previous moves to prevent exception in disorganized turns

    for player, column, row in game.moves.copy():
        event = {
            "type": "play",
            "player": player,
            "column": column,
            "row": row
        }
        await websocket.send(json.dumps(event))

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
        await replay(websocket, game)
        await play(websocket, game, PLAYER2, connected)

    finally:
        connected.remove(websocket) # Once connection reaches an exception (closed, etc), cut it off

async def watch(websocket, watch_key):
    try:
        game, connected = WATCH[watch_key]
    except KeyError:
        await error(websocket, "Game not found")
        return

    connected.add(websocket)
    
    try:
        await replay(websocket, game) # Replay previous moves in case of mid-game spectating
        await websocket.wait_closed()
    finally:
        connected.remove(websocket)

async def play(websocket, game, player, connected):
    # Choose the turns with itertools
    # select the next player

    # Get a "play" event from the server
    #turns = itertools.cycle([PLAYER1, PLAYER2])
    #current = next(turns)

    async for message in websocket:
        print(message)
        event = json.loads(message)

        assert event["type"] == "play"
        # assert current == player
        column = event["column"]

        try:
            row = game.play(player, column)
        except RuntimeError as e:
            error(websocket, str(e))
            continue
        
        event = {
            "type": "play",
            "player": player,
            "column": column,
            "row": row
        }
        websockets.broadcast(connected, json.dumps(event))

        if game.winner is not None:
            event = {
                "type": "win",
                "player": game.player
            }
            websockets.broadcast(connected, json.dumps(event))



async def handler(websocket):
    # Waits for a message from the JS (client) side of the program to parse below - InitGame()
    message = await websocket.recv()

    event = json.loads(message) # Rxd the message, load it as JSON
    assert event["type"] == "init" # Check if the event is "init", if not raise an assertion error and quit

    if "join" in event:
        await join(websocket, event["join"]) # A game already exists, join that game with the event numhber
    elif "watch" in event:
        await watch(websocket, event["watch"])
    else:
        await start(websocket) # First player starts game

async def main():
    # Set the stop condition when receiving SIGTERM
    loop = asyncio.get_running_loop()
    stop = loop.create_future()
    loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)

    port = int(os.environ.get("PORT", "8001")) # For Heroku to listen in

    async with websockets.serve(handler, "", port): # Starts handler coroutine with host and port as websocket connection
        await stop # Waits for stop to set the result to stop the program


if __name__ == "__main__":
    asyncio.run(main())

    