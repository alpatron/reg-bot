import asyncio
import asyncpg
import discord
from typing import Union, List, Set
from discord.ext import commands
from main import RegBot

class Configuration(commands.Cog):
    def __init__(self,bot:RegBot):
        self.bot = bot
        self.ROLEPLAY_CHANNEL_TABLE = 'roleplay_channels'
        self.CONFIG_TABLE = 'configuration'
        self.CONFIG_ACTIVE_CHARACTER_CHANNEL = 'active_character_channel'
        self.CONFIG_CHARACTER_ARCHIVE_CHANNEL = 'character_archive_channel'
        self.CONFIG_INACTIVE_PLAYER_ROLE = 'inactive_player_role'
        self.CONFIG_INACTIVITY_THRESHOLD = 'inactivity_threshold'
        self.CONFIG_ACTIVITY_LOOKUP_LIMIT = 'activity_lookup_limit'
        self.ROLEPLAY_ROLES_TABLE = 'roleplay_roles'

    #fetchRow returns either a record, if it found something, or None, if it didn't find anything
    async def roleplayChannelExists(self,channelID:int) -> bool:
        return await self.bot.db.fetchrow(f'SELECT * FROM {self.ROLEPLAY_CHANNEL_TABLE} WHERE channel_id = ($1)', str(channelID)) != None

    async def roleplayRoleExists(self,roleID:int)  -> bool:
        return await self.bot.db.fetchrow(f'SELECT * FROM {self.ROLEPLAY_ROLES_TABLE} WHERE role_id = ($1)', str(roleID)) != None

    async def saveRoleplayRole(self,roleID:int):
        await self.bot.db.execute(f'INSERT INTO {self.ROLEPLAY_ROLES_TABLE}(role_id) VALUES ($1)',str(roleID))

    async def removeRoleplayRole(self,roleID:int):
        await self.bot.db.execute(f'DELETE FROM {self.ROLEPLAY_ROLES_TABLE} WHERE role_id = ($1)',str(roleID))

    async def saveRoleplayChannel(self,ID:int):
        await self.bot.db.execute(f'INSERT INTO {self.ROLEPLAY_CHANNEL_TABLE}(channel_id) VALUES ($1)',str(ID))
    
    async def removeRoleplayChannel(self,ID:int):
        await self.bot.db.execute(f'DELETE FROM {self.ROLEPLAY_CHANNEL_TABLE} WHERE channel_id = ($1)',str(ID))

    async def getConfiguration(self,name:str) -> Union[asyncpg.Record, None]:
        return await self.bot.db.fetchrow(f'SELECT * FROM {self.CONFIG_TABLE} WHERE name = ($1)', name)

    async def setConfiguration(self,name:str,value:str):
        if await self.getConfiguration(name) != None:
            await self.bot.db.execute(f'UPDATE {self.CONFIG_TABLE} SET value = ($1) WHERE name = \'{name}\'', value)
        else:
            await self.bot.db.execute(f'INSERT INTO {self.CONFIG_TABLE} (name,value) VALUES ($1,$2)',name, value)

    async def getChannelFromConfiguration(self,name:str) -> Union[discord.TextChannel, None]:
        channel = await self.getConfiguration(name)
        if channel == None:
            return None
        else:
            return self.bot.get_channel(int(channel['value']))

    async def getIntFromConfiguration(self,name:str) -> Union[int, None]:
        integer = await self.getConfiguration(name)
        if integer == None:
            return None
        else:
            return int(integer['value'])

    async def getActiveCharacterChannel(self) -> Union[discord.TextChannel, None]:
        return await self.getChannelFromConfiguration(self.CONFIG_ACTIVE_CHARACTER_CHANNEL)

    async def getCharacterArchiveChannel(self) -> Union[discord.TextChannel, None]:
        return await self.getChannelFromConfiguration(self.CONFIG_CHARACTER_ARCHIVE_CHANNEL)

    async def getInactivePlayerRole(self,ctx:commands.context.Context) -> Union[discord.Role, None]:
        role = await self.getConfiguration(self.CONFIG_INACTIVE_PLAYER_ROLE)
        if role == None:
            return None
        else:
            return ctx.guild.get_role(int(role['value'])) #No need for await here for some reason.

    async def getRoleplayRoles(self,ctx:commands.context.Context) -> Set[discord.Role]:
        roleplayRoles = set()
        roleplayRoleIDs = await self.bot.db.fetch(f'SELECT * FROM {self.ROLEPLAY_ROLES_TABLE}')
        for roleID in roleplayRoleIDs:
            roleplayRoles.add(ctx.guild.get_role(int(roleID['role_id'])))
        return roleplayRoles

    async def getInactivityThreshold(self) -> Union[int, None]:
        return await self.getIntFromConfiguration(self.CONFIG_INACTIVITY_THRESHOLD)
    
    async def getActivityReportLookupLimit(self) -> Union[int, None]:
        return await self.getIntFromConfiguration(self.CONFIG_ACTIVITY_LOOKUP_LIMIT)

    async def getRoleplayChannels(self) -> Set[discord.TextChannel]:
        roleplayChannelsFromDatabase = await self.bot.db.fetch(f'SELECT * FROM {self.ROLEPLAY_CHANNEL_TABLE}')
        roleplayChannels = set()
        for channel in roleplayChannelsFromDatabase:
            roleplayChannels.add(self.bot.get_channel(int(channel["channel_id"])))
        return roleplayChannels