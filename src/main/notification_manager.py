'''
    notification_manager module with classes used for handling message distribution
    sync/async is isolated, so the app calling class' instance is free to stay sync only
    TODO:
        > get discord UID by other means (e.g. messaging the bot)
        > add multi-user support  
        > add e-mail support
'''
import discord, asyncio, threading, os
from utils.logging_config import get_logger


logger = get_logger(os.path.basename(__file__))


class DiscordNotificationBot:
    def __init__(self, bot_token):
        self.bot_token = bot_token

        intents = discord.Intents.default()
        intents.messages = True
        intents.dm_messages = True
        self.client = discord.Client(intents=intents)

        self.bot_event_loop = asyncio.new_event_loop()
        self.client_ready_event = threading.Event()
        
        @self.client.event
        async def on_ready():
            print(f"[DiscordNotificationBot] Bot logged in as {self.client.user}")
            self.client_ready_event.set()

    def start(self):
        self.bot_thread = threading.Thread(target=self._run_bot, daemon=True)
        self.bot_thread.start()
        self.client_ready_event.wait()

    def _run_bot(self):
        asyncio.set_event_loop(self.bot_event_loop)
        self.bot_event_loop.run_until_complete(self.client.start(self.bot_token))

    async def _send_dm(self, user_id, message_text):
        try:
            user = await self.client.fetch_user(user_id)
            await user.send(message_text)
            print(f"[DiscordNotificationBot] DM sent to user {user_id}")
        except Exception as e:
            print(f"[DiscordNotificationBot] Error sending DM: {e}")

    def send_dm(self, user_id, message_text):
        asyncio.run_coroutine_threadsafe(self._send_dm(user_id, message_text), self.bot_event_loop)

    async def _close_client(self):
        await self.client.close()

    def close(self):
        asyncio.run_coroutine_threadsafe(self._close_client(), self.bot_event_loop)
        self.bot_thread.join()