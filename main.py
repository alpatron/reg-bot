import asyncio
import asyncpg
import discord
import aiohttp
from helperFunction import getUserMessagesInChannel
from typing import Union, List, Set, Dict, Union
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
        import userCommands
        self.add_cog(userCommands.UserCommands(self,self.get_cog('Configuration')))
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

    async def getPlayersInCharacterSheetChannel(self) -> Set[Union[discord.Member,discord.User]]:
        ACTIVE_CHARACTER_CHANNEL = await self.get_cog('Configuration').getActiveCharacterChannel()
        accounts = set()
        message : discord.Message
        async for message in ACTIVE_CHARACTER_CHANNEL.history(limit=None):
            accounts.add(message.author)
        return accounts

    async def getDeadPlayerAccounts(self) -> Set[discord.User]:
        accounts : Set[Union[discord.Member,discord.User]] = await self.getPlayersInCharacterSheetChannel()
        return set(filter(lambda account:isinstance(account,discord.User),accounts))

    #Returns a dictionary of players who are waiting for sheet approval as the keys, and their sheets as dictionary values
    async def getPlayersWaitingForApproval(self, guild: discord.Guild) -> Dict[discord.Member,List[discord.Message]]:
        ROLEPLAY_ROLES : Set[discord.Role] = await self.get_cog('Configuration').getRoleplayRoles(guild)
        accountsInSheetChannel = await self.getPlayersInCharacterSheetChannel()
        #Someone who's waiting for approval is an instance of 'discord.member', i.e. they are ON the server and have not left, and they have no roleplay roles (yet).
        playersWaitingForApproval = filter(lambda account: isinstance(account,discord.Member) and len(set(account.roles).intersection(ROLEPLAY_ROLES)) == 0,accountsInSheetChannel)
        finalDictionary = dict()
        for player in playersWaitingForApproval:
            finalDictionary[player] = await self.getCharacterSheet(player)
        return finalDictionary

    #Returns all players who have an approved character, determing if so by whether they have roles.
    #This means that people with player roles and no sheet ARE categorised as people with an approved characater.
    async def getPlayersWithApprovedCharacter(self, guild:discord.Guild) -> Set[discord.Member]:
        ROLEPLAY_ROLES : Set[discord.Role] = await self.get_cog('Configuration').getRoleplayRoles(guild)
        return set(filter(lambda member: len(set(member.roles).intersection(ROLEPLAY_ROLES)) != 0,guild.members))

    def run(self,token):
        super().run(token)
