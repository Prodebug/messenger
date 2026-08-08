import asyncio
import websockets
import json
import datetime

clients = {}
message_history = []

async def handler(websocket, path):
    try:
        # Получаем имя пользователя
        data = await websocket.recv()
        username = json.loads(data).get('username', 'Anonymous')
        clients[websocket] = username
        
        # Отправляем историю
        for msg in message_history[-50:]:
            await websocket.send(json.dumps(msg))
        
        # Оповещаем всех
        await broadcast({
            'type': 'system',
            'message': f"👤 {username} присоединился",
            'time': datetime.datetime.now().strftime("%H:%M")
        })
        await send_user_list()
        
        # Обрабатываем сообщения
        async for message in websocket:
            try:
                msg = json.loads(message)
                msg['time'] = datetime.datetime.now().strftime("%H:%M")
                msg['sender'] = username
                
                if msg.get('type') == 'message':
                    message_history.append(msg)
                    await broadcast(msg)
                elif msg.get('type') == 'private':
                    target = msg.get('target')
                    for client, name in clients.items():
                        if name == target:
                            try:
                                await client.send(json.dumps(msg))
                            except: pass
                            break
            except: pass
            
    except:
        pass
    finally:
        if websocket in clients:
            username = clients[websocket]
            del clients[websocket]
            await broadcast({
                'type': 'system',
                'message': f"👋 {username} покинул чат",
                'time': datetime.datetime.now().strftime("%H:%M")
            })
            await send_user_list()

async def broadcast(message):
    data = json.dumps(message)
    for client in list(clients.keys()):
        try:
            await client.send(data)
        except: pass

async def send_user_list():
    await broadcast({
        'type': 'user_list',
        'users': list(clients.values()),
        'count': len(clients)
    })

async def main():
    print("=" * 50)
    print("📱 Мессенджер Сервер")
    print("=" * 50)
    
    # Получаем IP
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        print(f"📡 Сервер доступен по адресу: ws://{ip}:5555")
        print(f"📡 Локальный: ws://127.0.0.1:5555")
    except: pass
    
    print("=" * 50)
    print("✅ Сервер запущен! Ждём подключений...")
    
    async with websockets.serve(handler, "0.0.0.0", 5555):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())