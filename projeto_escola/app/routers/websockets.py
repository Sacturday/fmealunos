from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from collections import defaultdict

from ..security import decodificar_token

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.rooms: dict[int, list[WebSocket]] = defaultdict(list)

    async def connect(self, websocket: WebSocket, escola_id: int):
        await websocket.accept()
        self.rooms[escola_id].append(websocket)

    def disconnect(self, websocket: WebSocket, escola_id: int):
        self.rooms[escola_id].remove(websocket)

    async def broadcast_to_escola(self, escola_id: int, message: str):
        for ws in self.rooms.get(escola_id, []):
            await ws.send_text(message)


websocket_manager = ConnectionManager()


@router.websocket("/ws/dashboard/{escola_id}")
async def dashboard_ws(websocket: WebSocket, escola_id: int):
    token = websocket.cookies.get("access_token")
    if not token or decodificar_token(token) is None:
        await websocket.close(code=1008)
        return

    await websocket_manager.connect(websocket, escola_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, escola_id)
