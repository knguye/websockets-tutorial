#!/usr/bin/env python3


import json
import asyncio
import itertools
import websockets
import logging

from connect4 import PLAYER1, PLAYER2, Connect4

JOIN = {} # Dictionary w/ joinKey: game, connected (set of ws)

async def handler(websocket):
    # Start the game, initialize the set of websocket connections
    game = Connect4()
    connected = {websocket}

    join_key = secrets.token_urlsafe(12) # Generates a token for unique game ID
    JOIN[join_key] = game, connected

    try:
        turns = itertools.cycle([PLAYER1, PLAYER2])
        player = next(turns)

        # Get an event of type play from server
        async for message in websocket:
            print(message)
            event = json.loads(message)

            assert event["type"] == "play"
            column = event["column"]

            try:
                row = game.play(player, column)     # Play that event with play() method from Connect4()
            except RuntimeError as e:
                event = {
                    "type": "error",
                    "message": str(e),
                }
                await websocket.send(json.dumps(event)) # Send Error
            finally:
                event = {
                    "type": "play",
                    "player": player,
                    "column": column,
                    "row": row
                }
                await websocket.send(json.dumps(event))
        
            if game.winner != None:
                event = {
                    "type": "win",
                    "player": game.winner
                }
                await websocket.send(json.dumps(event))
            


            logging.basicConfig(format="%(message)s", level=logging.DEBUG)

            player = next(turns)
    finally:
        del JOIN[join_key]
        
async def main():
    async with websockets.serve(handler, "", 8001):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())

    