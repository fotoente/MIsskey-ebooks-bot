from datetime import datetime
import os
import asyncio
from random import *
import mi
import sys
import configparser
from mi import Note
from mi.ext import commands, tasks
from mi.note import Note
from mi.router import Router
from roboduck import *



#Load Misskey configuration
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), 'bot.cfg'))
uri="wss://"+config.get("misskey","instance_write")+"/streaming"
token=config.get("misskey","token")


class MyBot(commands.Bot):
    text_model = None #Holds the markov object, so it won't be recreated everytime
    
    def __init__(self):
        super().__init__()
        #self.text_model = read_posts()
        #print(datetime.now().strftime('%Y-%m-%d %H:%M:%S')+" Posts initialized!")            
        
    @tasks.loop(3600)
    async def loop_1h(self):
        if (bot.text_model is not None): #Just a check to see that there is a object stored
            await bot.client.note.send(content=create_post(bot.text_model))
    
    @tasks.loop(43200)
    async def loop_12h(self):
        bot.text_model = read_posts()
        print(datetime.now().strftime('%Y-%m-%d %H:%M:%S')+" Posts loaded!")

    async def on_ready(self, ws):
        await Router(ws).connect_channel(["global", "main"])  #Connect to global and main channels
        await bot.client.note.send(content=datetime.now().strftime('%Y-%m-%d %H:%M:%S')+" :roboduck: Bot started!", visibility="specified")
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
            
            if (bot.text_model is not None):
                markov = create_post(bot.text_model)
            else:
                markov = "Error loading markov chain object!" 
            
            if markov is not None: # better: if item is not None
                text+=markov
            else:        
                text+="Error in markov chain sentence creation: Couldn't calculate sentence!\n\n☹ Please try again! " 
            
            await note.reply(content=text) #Reply to a note


if __name__ == "__main__":
    bot = MyBot()
    asyncio.run(bot.start(uri, token))
   