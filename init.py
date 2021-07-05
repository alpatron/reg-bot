import os
import asyncio
import asyncpg
from discord.ext import commands
from main import RegBot

def init():
    loop = asyncio.get_event_loop()
    
    try:
        db = loop.run_until_complete(
           #I use this URL for local testing: postgres://postgres@127.0.0.1/RP_server_bot
           asyncpg.create_pool(dsn=os.environ['DATABASE_URL'],ssl='require') #The SSL require value is set so that connection to the database work on Heroku. Change for your environment.
        )
    except Exception as e:
        print('Database connection error!')
        print(e)
        return

    bot = RegBot(db)
    bot.run(os.environ['REG_BOT_KEY'])

init()