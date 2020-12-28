import asyncio
import json
from django.contrib.auth import get_user_model
from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async

from .models import Thread, ChatMessage


class ChatConsumer(AsyncConsumer):
    async def websocket_connect(self, event):
        print("connected", event)
        # await asyncio.sleep(5)
        other_user = self.scope['url_route']['kwargs']['username']
        me = self.scope['user']
        thread_obj = await self.get_thread(me, other_user)
        self.thread_obj = thread_obj
        
        chat_room = f"thread_{thread_obj.id}"
        self.chat_room = chat_room
        await self.channel_layer.group_add(
            chat_room,
            self.channel_name
        )
        await self.send({
            "type": "websocket.accept"
        })

    async def websocket_receive(self, event):
        # when a message is received from the websocket
        #print("receive", event)
        front_text = event.get('text', None)
        if front_text is not None:
            loaded_dict_data = json.loads(front_text)
            msg = loaded_dict_data.get('message')
            # print(msg)
            user = self.scope['user']
            username = 'default'
            if user.is_authenticated:
                username = user.username
            myResponse = {
                'message': msg,
                'username': username
            }
            new_event = {
                "type": 'chat_message',
                "text": json.dumps(myResponse)
            }
            await self.create_chat_message(user, msg)
            await self.channel_layer.group_send(
                self.chat_room,
                new_event
            )
        #{'type': 'websocket.receive', 'text': '{"message":"another !!"}'}

    # Receive message from room group
    async def chat_message(self, event):
        front_text = event.get('text', None)
        if front_text is not None:
            loaded_dict_data = json.loads(front_text)
            msg = loaded_dict_data.get('message')
            username = loaded_dict_data.get('username')
            # user = self.scope['user']
            # username = 'default'
            # if user.is_authenticated:
            #     username = user.username
            myResponse = {
                'message': msg,
                'username': username
            }

            # Send message to WebSocket

            await self.send({
                'type': 'websocket.send',
                'text': json.dumps(myResponse)
            })

    async def websocket_disconnect(self, event):
        print("disconnected", event)

    @database_sync_to_async
    def get_thread(self, user, other_username):
        return Thread.objects.get_or_new(user, other_username)[0]

    @database_sync_to_async
    def create_chat_message(self, me, msg):
        thread_obj = self.thread_obj
        return ChatMessage.objects.create(thread=thread_obj, user=me, message=msg)
