import asyncio
import threading

from mipa.ext import commands, tasks
from mipa.router import Router
from mipac.models import Note
from mipac.util import check_multi_arg

import roboduck

# Load Misskey configuration
config = roboduck.configparser.ConfigParser()
config.read(roboduck.Path(__file__).parent.joinpath('bot.cfg'))
url = "https://" + config.get("misskey", "instance_write")
token = config.get("misskey", "token")

try:
    contentwarning = config.get("misskey", "cw")
    if contentwarning.lower() == "none":
        contentwarning = None
except (TypeError, ValueError, roboduck.configparser.NoOptionError):
    contentwarning = None

if not check_multi_arg(url, token):
    raise Exception("Misskey instance and token are required.")

class MyBot(commands.Bot):

    def __init__(self):
        super().__init__()

    @tasks.loop(3600)
    async def loop_1h(self):
        text = roboduck.create_sentence()
        await bot.client.note.action.send(content=text, visibility="public", cw=contentwarning)

    @tasks.loop(43200)
    async def loop_12h(self):
        thread_update = threading.Thread(target=roboduck.update())
        thread_update.daemon = True
        thread_update.start()

    async def on_ready(self, ws):
        await Router(ws).connect_channel(["global", "main"])  # Connect to global and main channels
        await self.client.note.action.send(content=roboduck.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " Roboduck Bot started!",
                                   visibility="specified")
        self.loop_12h.start()  # Launching renew posts every 12 hours
        self.loop_1h.start()  #
        print(roboduck.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " Roboduck Bot started!")

    async def on_mention(self, note: Note):
        if not note.author.is_bot:
            text = note.author.action.get_mention() + " "
            text += roboduck.create_sentence()

            await note.reply(content=text, cw=contentwarning)  # Reply to a note

    async def on_reconnect(self, ws):
        await Router(ws).connect_channel(["global", "main"])  # Connect to global and main channels

if __name__ == "__main__":
    databasepath = roboduck.Path(__file__).parent.joinpath('roboduck.db')

    if not (roboduck.os.path.exists(databasepath) and roboduck.os.stat(databasepath).st_size != 0):
        roboduck.init_bot()

    bot = MyBot()
    asyncio.run(bot.start(url, token))
