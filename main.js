import { createBoard, playMove } from "./connect4.js";

function initGame(websocket){
    websocket.addEventListener("open", () => {
        // Send an init event depending on who's connecting
        const params = new URLSearchParams(window.location.search);
        let event = { type: "init" };

        if (params.has("join")){
            event["join"] = params.get("join")
        }
        else if (params.has("watch")){
            event["watch"] = params.get("watch")
        }
        else {
            
        }
        console.log(event)
        websocket.send(JSON.stringify(event));
    });
}

function sendMoves(board, websocket){
    const params = new URLSearchParams(window.location.search)
    if (params.has("watch")){
        return; // Don't send moves for spectators
    }
    // Add a passive, indefinite event listener for clicks on the board
    board.addEventListener("click", ({target}) => {
        const column = target.dataset.column;
        
        if (column === undefined){
            return;
        }

        const event = {
            type: "play",
            column: parseInt(column, 10)
        };
        websocket.send(JSON.stringify(event))
    })
}

function showMessage(message) {
    window.setTimeout(() => window.alert(message), 50)
}

function receiveMoves(board, websocket){
    websocket.addEventListener("message", ({data}) => {
        const event = JSON.parse(data);
        //print(event);
        switch (event.type){
            case "init":
                document.querySelector(".join").href = "?join=" + event.join; // Initialize the URL with the join key
                document.querySelector(".watch").href = "?watch=" + event.watch;
                break; 
            case "play":
                playMove(board, event.player, event.column, event.row); // connect4.js
                break;
            case "win":
                showMessage(`Player ${event.player} wins!`);
                websocket.close(1000); // Close the connection
                break;
            case "error":
                showMessage(event.message);
                break;
            default:
                throw new Error(`Unsupported event type: ${event.type}.`);
        }
    });
}

function getWebSocketServer(){
    
}

window.addEventListener("DOMContentLoaded", () => {
    const board = document.querySelector(".board");
    createBoard(board);

    // Open Websocket connection to handle events
    const websocket = new WebSocket("ws://localhost:8001");
    initGame(websocket);
    receiveMoves(board, websocket);
    sendMoves(board, websocket);
});
    