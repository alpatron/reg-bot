import os
import asyncio
import asyncpg
from discord.ext import commands
from main import RegBot

def init():
    loop = asyncio.get_event_loop()
    
    try:
        db = loop.run_until_complete(
           asyncpg.create_pool(dsn=os.environ['DATABASE_URL'],ssl='require')
        )
    except Exception as e:
        print('Database connection error!')
        print(e)
        return

    bot = RegBot(db)
    #Input your Discord-bot token here.
    bot.run()

init()