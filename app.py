#!/usr/bin/env python3


import json
import asyncio
import itertools
import websockets
import logging
import secrets

from connect4 import PLAYER1, PLAYER2, Connect4

JOIN = {} # Dictionary w/ joinKey: game, connected (set of ws)

async def start(websocket):
    # Start the game, initialize the set of websocket connections
    game = Connect4()
    connected = {websocket}

    join_key = secrets.token_urlsafe(12) # Generates a token for unique game ID
    JOIN[join_key] = game, connected

    try:
        event = {
            "type": "init",
            "join": join_key # Creates an event with the generated key
        }

        await websocket.send(json.dumps(event))

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
        print("second player joined game")
        async for message in websocket:
            print("second player sent", message)

    finally:
        connected.remove(websocket) # Once connection reaches an exception (closed, etc), cut it off


async def handler(websocket):
    # Recieve and parse the init event from the User Interface
    message = await websocket.recv()
    event = json.loads(message)
    assert event["type"] == "init"

    if "join" in event:
        await join(websocket, event["join"])
    # First player starts game
    else:
        await start(websocket)

async def main():
    async with websockets.serve(handler, "", 8001):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())

    