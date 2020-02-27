import asyncio
import asyncpg
import discord
import aiohttp
from helperFunction import getUserMessagesInChannel
from typing import Union, List, Set, Dict
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
        import commandsCommands
        self.add_cog(commandsCommands.CommandsCommands(self))
        self.http_session = aiohttp.ClientSession()
    
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

    async def getCharacterSheet(self,user:Union[discord.Member,discord.User]) -> List[discord.Message]:
        activeCharacterChannel = await self.get_cog('Configuration').getActiveCharacterChannel()
        if activeCharacterChannel == None:
            raise Exception('The active-character channel is not set.')
        else:
            return await getUserMessagesInChannel(activeCharacterChannel,user)

    async def getLastActivity(self,now:datetime) -> Dict[discord.User,discord.Message]:
        playerActivities = dict()
        lookupBegin = now - timedelta(days=await self.get_cog('Configuration').getActivityReportLookupLimit())
        for channel in await self.get_cog('Configuration').getRoleplayChannels():
            async for message in channel.history(limit=None,after=lookupBegin):
                if message.author in playerActivities:
                    if message.created_at > playerActivities[message.author].created_at:
                        playerActivities[message.author] = message
                else:
                    playerActivities[message.author] = message
        return playerActivities    

    async def getDeadPlayerAccounts(self) -> Set[discord.User]:
        ACTIVE_CHARACTER_CHANNEL = await self.get_cog('Configuration').getActiveCharacterChannel()
        deadAccounts = set()
        message : discord.Message
        async for message in ACTIVE_CHARACTER_CHANNEL.history(limit=None):
            if isinstance(message.author,discord.User): #message.author returns discord.member if submitter is on server; discord.user otherwise
                deadAccounts.add(message.author)
        return deadAccounts

    async def getPlayersWithApprovedCharacter(self, guild:discord.Guild) -> Set[discord.Member]:
        ROLEPLAY_ROLES : Set[discord.Role] = await self.get_cog('Configuration').getRoleplayRoles(guild)
        activePlayers = set()
        for member in guild.members:
            if len(set(member.roles).intersection(ROLEPLAY_ROLES)) != 0:
                activePlayers.add(member)
        return activePlayers

    def run(self,token):
        super().run(token)
