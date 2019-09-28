import asyncio
import asyncpg
import discord
from typing import Union, List, Set
from datetime import datetime, timedelta
from discord.ext import commands

class RegBot(commands.Bot):
    def __init__(self,db:asyncpg.pool.Pool):
        super().__init__(
            command_prefix='!reg ',
            activity=discord.Game('type "!reg help" for help'),
            description='Hello, I\'m Reg. I help with managing this server. Contact Alpatron if I go haywire. My commands are:'
        )
        self.db = db
        import configuration #This is to prevent circular dependicy errors. Come to think about it, cogs are circularly dependent! All cogs must know about the bot, and the bot needs to know about cogs!
        self.add_cog(configuration.Configuration(self))
        import configurationCommands
        self.add_cog(configurationCommands.ConfigurationCommands(self,self.get_cog('Configuration')))
        import adminCommands
        self.add_cog(adminCommands.AdminCommands(self,self.get_cog('Configuration')))
        self.add_command(_bodge)
        self.add_command(say)
    
    async def on_command_error(self,ctx,exception):
        #Wait, can I not make the message part of the exception class or something? It'd perhaps be worth to look into.
        if isinstance(exception, commands.CheckFailure):
            await ctx.send('Irredeemable. You do not have the necessary rights to run this command.')
        elif isinstance(exception,commands.CommandNotFound):
            await ctx.send(f'I don\'t know that command. Type `{self.command_prefix}help` for the list of commands.')
        elif isinstance(exception,(commands.MissingRequiredArgument,commands.TooManyArguments)):
            #Perhaps list the entire content sometime.
            await ctx.send(f'You sent too few or too many arguments. Type `{self.command_prefix}help` for help.')
        elif isinstance(exception,(commands.BadArgument,commands.BadUnionArgument)):
            await ctx.send(exception) #after commands.BadArgument exception becomes better, upgrade this to send nicer error messages
        else:
            await super().on_command_error(ctx,exception)

    def run(self,token):
        super().run(token)

#Bodge because I want to have "say it" as one command with a space in the name, but Discord.py doesn't support this.
@commands.command(name='say it',brief='Sigh. Makes me say it.')
async def _bodge(ctx):
    pass

@commands.group(hidden=True)
async def say(ctx):
    pass

@say.command(rest_is_raw=True,help='Please don\'t use this command.',hidden=True,ignore_extra=False)
async def it(ctx):
    async with ctx.message.channel.typing():
        await asyncio.sleep(1)
        await ctx.send('*sigh* If you insist...')
        await asyncio.sleep(1)
    async with ctx.message.channel.typing():
        await asyncio.sleep(3)
        await ctx.send('Irredeemable!')
