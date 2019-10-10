import asyncio
import discord
from helperFunction import splitAndSend
from discord.ext import commands
from main import RegBot

#This class is used to hold commands of no special significance, those which may be used by any user.
class CommandsCommands(commands.Cog, name='commands'):
    def __init__(self,bot:RegBot):
        self.bot = bot
    
    @commands.command(help='Loads a Pastebin paste and splits it into Discord messages (so that you don\'t have to split it yourself)!')
    async def pastebinSplit(self,ctx:commands.Context,pastebinID:str):
        async with ctx.message.channel.typing():
            URL = 'https://pastebin.com/raw/'
            async with self.bot.http_session.get(URL+pastebinID) as response:
                if response.status == 200:
                    await splitAndSend(await response.text(),ctx.channel)
                else:
                    await ctx.send('There was a problem with getting the paste.')


    #Bodge because I want to have "say it" as one command with a space in the name, but Discord.py doesn't support this.
    @commands.command(name='say it',brief='Sigh. Makes me say it.')
    async def _bodge(self,ctx:commands.Context):
        pass

    @commands.group(hidden=True)
    async def say(self,ctx:commands.Context):
        pass

    @say.command(rest_is_raw=True,help='Please don\'t use this command.',hidden=True,ignore_extra=False)
    async def it(self,ctx:commands.Context):
        async with ctx.message.channel.typing():
            await asyncio.sleep(1)
            await ctx.send('*sigh* If you insist...')
            await asyncio.sleep(1)
        async with ctx.message.channel.typing():
            await asyncio.sleep(3)
            await ctx.send('Irredeemable!')