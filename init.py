import os
import asyncio
import asyncpg
from discord.ext import commands
from main import RegBot

def init():
    #Change this line to suit your environment; it's set-up now for deployment to Heroku.
    credentials = {"dsn":os.environ['DATABASE_URL']}
    
    loop = asyncio.get_event_loop()

    try:
        db = loop.run_until_complete(
           asyncpg.create_pool(**credentials)
        )
    except Exception:
        print('Database connection error!')
        return

    bot = RegBot(db)
    #Input your Discord-bot token here.
    bot.run()

init()