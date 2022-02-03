from datetime import datetime
import os
import asyncio
from random import *
import mi
import sys
import configparser
import threading
from pathlib import Path
from mi import Note
from mi.ext import commands, tasks
from mi.note import Note
from mi.router import Router
from roboduck import *



#Load Misskey configuration
config = configparser.ConfigParser()
config.read((Path(__file__).parent).joinpath('bot.cfg'))
uri="wss://"+config.get("misskey","instance_write")+"/streaming"
token=config.get("misskey","token")


class MyBot(commands.Bot):
    text_model = None #Holds the markov object, so it won't be recreated everytime
    
    def __init__(self):
        super().__init__()            
        
    @tasks.loop(3600)
    async def loop_1h(self):
        text = create_sentence()
        await bot.client.note.send(content=text)
    
    @tasks.loop(43200)
    async def loop_12h(self):
            thread_update = threading.Thread(target=update)
            thread_update.setDaemon(True)
            thread_update.start()

    async def on_ready(self, ws):
        await Router(ws).connect_channel(["global", "main"])  #Connect to global and main channels
        await bot.client.note.send(content=datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " :roboduck: Bot started!", visibility="specified")
        self.loop_12h.start()  #Launching renew posts every 12 hours
        self.loop_1h.start() #
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S')+" Roboduck Bot started!")
        
        
    async def on_mention(self, note: Note):
        text=""
        if (not note.author.is_bot):
            inhalt=note.content
            if (note.author.host is None):
                text = "@" + note.author.name + " " #Building the reply on same instance
            else:
                text = "@" + note.author.name + "@" + note.author.host + " " #Building the reply on foreign instance
            
            text += create_sentence()
            
            await note.reply(content=text) #Reply to a note


if __name__ == "__main__":
    databasepath = (Path(__file__).parent).joinpath('roboduck.db')

    if (not (os.path.exists(databasepath) and os.stat(databasepath).st_size != 0)):
        init_bot()
    
    
    bot = MyBot()
    asyncio.run(bot.start(uri, token, timeout=600))
   