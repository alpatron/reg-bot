import asyncio
import discord
from typing import Union, List, Set
from datetime import datetime, timedelta
from discord.ext import commands
from configuration import Configuration
from main import RegBot

class ConfigurationCommands(commands.Cog):
    def __init__(self,bot:RegBot,configuration:Configuration):
        self.bot = bot
        self.configuration = configuration

    async def registerRoleplayCategoryChannel(self,ctx:commands.context.Context,category:discord.CategoryChannel):
        addedChannels = list()
        notAddedChannels = list()
        invalidChannels = list()

        for channel in category.channels:
            if await self.configuration.roleplayChannelExists(channel.id):
                notAddedChannels.append(channel)
            elif isinstance(channel,discord.TextChannel):
                await self.configuration.saveRoleplayChannel(channel.id)
                addedChannels.append(channel)
            else:
                invalidChannels.append(channel)
        
        message =  f'Adding channel category {category.name} to the roleplay channel list.\n'
        message += f'Added {len(addedChannels)} channels to the list:\n'
        for channel in addedChannels:
            message += channel.mention+'\n'
        message += f'{len(notAddedChannels)} channels were already in the list:\n'
        for channel in notAddedChannels:
            message += channel.mention+'\n'
        message += f'{len(invalidChannels)} channels are not text channels:\n'
        for channel in invalidChannels:
            message += channel.mention+'\n'
        await ctx.send(message)

    async def unregisterRoleplayCategoryChannel(self,ctx:commands.context.Context,category:discord.CategoryChannel):
        removedChannels = list()
        notRemovedChannels = list()
        invalidChannels = list()

        for channel in category.channels:
            if await self.configuration.roleplayChannelExists(channel.id):
                await self.configuration.removeRoleplayChannel(channel.id)
                removedChannels.append(channel)
            elif isinstance(channel,discord.TextChannel):
                notRemovedChannels.append(channel)
            else:
                invalidChannels.append(channel)
        
        message =  f'Removing channel category {category.mention} from the roleplay channel list.\n'
        message += f'Removed {len(removedChannels)} channels from the list:\n'
        for channel in removedChannels:
            message += channel.mention+'\n'
        message += f'{len(notRemovedChannels)} channels already weren\'t in the list:\n'
        for channel in notRemovedChannels:
            message += channel.mention+'\n'
        message += f'{len(invalidChannels)} channels are not text channels:\n'
        for channel in invalidChannels:
            message += channel.mention+'\n'
        await ctx.send(message)

    async def registerRoleplayTextChannel(self,ctx:commands.context.Context,channel:discord.TextChannel):
        if await self.configuration.roleplayChannelExists(channel.id):
                await ctx.send(f'This channel ({channel.mention}) is already registered in the roleplay list.')
        else:
            await self.configuration.saveRoleplayChannel(channel.id)
            await ctx.send(f'The channel {channel.mention} has been registered as a roleplay channel.')

    async def unregisterRoleplayTextChannel(self,ctx:commands.context.Context,channel:discord.TextChannel):
        if await self.configuration.roleplayChannelExists(channel.id):
            await self.configuration.removeRoleplayChannel(channel.id)
            await ctx.send(f'Removed channel {channel.mention} from the list of roleplay channels.')
        else:
            await ctx.send(f'The channel {channel.mention} already isn\'t in the roleplay channel list.')
    
    @commands.command(help='Registers a channel or group of channels into the roleplay channel list. This list is used to determine users\' roleplay activity.')
    @commands.has_permissions(administrator=True)
    async def registerRoleplayChannel(self,ctx:commands.context.Context,*,channel:Union[discord.TextChannel,discord.CategoryChannel]):
        if isinstance(channel,discord.TextChannel):
            await self.registerRoleplayTextChannel(ctx,channel)
        elif isinstance (channel,discord.CategoryChannel):
            await self.registerRoleplayCategoryChannel(ctx,channel)
        else:
            await ctx.send('This line of code should never run but you did it. Bravo. Please contact Alpatron.')

    @commands.command(help='Removes a channel or group of channels from the roleplay channel list. This list is used to determine users\' roleplay activity.')
    @commands.has_permissions(administrator=True)
    async def unregisterRoleplayChannel(self,ctx:commands.context.Context,*,channel:Union[discord.TextChannel,discord.CategoryChannel]):
        if isinstance(channel,discord.TextChannel):
            await self.unregisterRoleplayTextChannel(ctx,channel)
        elif isinstance(channel,discord.CategoryChannel):
            await self.unregisterRoleplayCategoryChannel(ctx,channel)
        else:
            await ctx.send('This line of code should never run but you did it. Bravo. Please contact Alpatron.')

    @commands.command(help='Displays a list of roleplay channels. (Used to determine roleplay activity.)')
    async def listRoleplayChannels(self,ctx:commands.context.Context):
        roleplayChannels = await self.configuration.getRoleplayChannels()
        output = 'Roleplay channels are:\n'
        if len(roleplayChannels) != 0:
            for channel in roleplayChannels:
                mention = channel.mention
                output += f'{mention}\n'
        else:
            output += 'There are no roleplay channels set.'
        await ctx.send(output)

    @commands.command(help='Adds a role to the list of roleplaying roles. (Used in to determine who is a roleplayer and which roles to remove while archiving.)',ignore_extra=False)
    @commands.has_permissions(administrator=True)
    async def registerRoleplayRole(self,ctx:commands.context.Context,*,role:discord.Role):
        if await self.configuration.roleplayRoleExists(role.id):
            await ctx.send(f'The role {role.name} is already regisered.')
        else:
            await self.configuration.saveRoleplayRole(role.id)
            await ctx.send(f'Added role {role.name} into the roleplay role list.')

    @commands.command(help='Removes a role from the list of roleplaying roles. (Used in to determine who is a roleplayer and which roles to remove while archiving.)')
    @commands.has_permissions(administrator=True)
    async def unregisterRoleplayRole(self,ctx:commands.context.Context,*,role:discord.Role):
        if await self.configuration.roleplayRoleExists(role.id):
            await self.configuration.removeRoleplayRole(role.id)
            await ctx.send(f'Added role {role.name} into the roleplay role list.')
        else:
            await ctx.send(f'The role {role.name} already isn\'t already regisered.')

    @commands.command(help='Displays a list of roleplay roles. (Used in to determine who is a roleplayer and which roles to remove while archiving.)')
    async def listRoleplayRoles(self,ctx:commands.context.Context):
        roleplayRoles = await self.configuration.getRoleplayRoles(ctx)
        output = 'Roleplay roles are:\n'
        if len(roleplayRoles) != 0:
            for role in roleplayRoles:
                output += f'{role.name}\n'
        else:
            output += 'There are no roleplay roles set.'
        await ctx.send(output)

    @commands.command(help='Sets the channel where active characters are stored.')
    @commands.has_permissions(administrator=True)
    async def setActiveCharacterChannel(self,ctx:commands.context.Context,*,channel:discord.TextChannel):
        await self.configuration.setConfiguration(self.configuration.CONFIG_ACTIVE_CHARACTER_CHANNEL,str(channel.id))
        await ctx.send(f'Set the channel {channel.mention} as the active-character channel.')

    @commands.command(help='Displays the set channel where active characters are stored.')
    async def displayActiveCharacterChannel(self,ctx:commands.context.Context):
        channel = await self.configuration.getActiveCharacterChannel()
        if channel != None:
            await ctx.send(f'The set active character channel is {channel.mention}.')
        else:
            await ctx.send(f'There is no active character channel set.')

    @commands.command(help='Sets the channel where characters are archived.')
    @commands.has_permissions(administrator=True)
    async def setCharacterArchiveChannel(self,ctx:commands.context.Context,*,channel:discord.TextChannel):
        await self.configuration.setConfiguration(self.configuration.CONFIG_CHARACTER_ARCHIVE_CHANNEL,str(channel.id))
        await ctx.send(f'Set the channel {channel.mention} as the character-archive channel.')

    @commands.command(help='Displays the set channel where characters are archived.')
    async def displayCharacterArchiveChannel(self,ctx:commands.context.Context):
        channel = await self.configuration.getCharacterArchiveChannel()
        if channel != None:
            await ctx.send(f'The set character-archive channel is {channel.mention}.')
        else:
            await ctx.send(f'There is no character-archive channel set.')

    @commands.command(help='Sets the role for inactive players.')
    @commands.has_permissions(administrator=True)
    async def setInactivePlayerRole(self,ctx:commands.context.Context,*,role:discord.Role):
        await self.configuration.setConfiguration(self.configuration.CONFIG_INACTIVE_PLAYER_ROLE,str(role.id))
        await ctx.send(f'Set the role {role.name} as the inactive-player role.')


    @commands.command(help='Sets the threshold (in days) to determine player activity. Players who last posted more than the threshold number of days are deemed inactive.',ignore_extra=False)
    @commands.has_permissions(administrator=True)
    async def setInactivityThreshold(self,ctx:commands.context.Context,threshold:int):
        lookupLimit = await self.configuration.getActivityReportLookupLimit()
        if threshold < 1:
            await ctx.send('Irredeemable! The inactivity threshold must be a positive integer!')
        elif lookupLimit != None and threshold > lookupLimit:
            await ctx.send(f'Please set the inactivity threshold to a number equal to or lower than the activity-report lookup limit ({lookupLimit} days).')
        else:
            await self.configuration.setConfiguration(self.configuration.CONFIG_INACTIVITY_THRESHOLD,str(threshold))
            await ctx.send(f'Set {threshold} days as the inactivity threshold.')

    @commands.command(help='Sets up to how many days back the activity report function should look at to determine roleplay activity. Players whose last activity cannot be determined within that limit will she shown as "never played or played more than N days ago".',ignore_extra=False)
    @commands.has_permissions(administrator=True)
    async def setActivityReportLookupLimit(self,ctx:commands.context.Context,limit:int):
        inactivityThreshold = await self.configuration.getInactivityThreshold()
        if limit < 1:
            await ctx.send('Irredeemable! The lookup limit must be a positive integer!')
        elif inactivityThreshold != None and limit < inactivityThreshold:
            await ctx.send(f'Please set the lookup limit to a number equal to or higher than the inactivity threshold ({inactivityThreshold} days).')
        else:
            await self.configuration.setConfiguration(self.configuration.CONFIG_ACTIVITY_LOOKUP_LIMIT,str(limit))
            await ctx.send(f'Set {limit} days as the lookup limit.')

    @commands.command(help='Displays the set the role for inactive players.')
    async def displayInactivePlayerRole(self,ctx:commands.context.Context):
        role = await self.configuration.getInactivePlayerRole(ctx)
        if role != None:
            await ctx.send(f'The set inactive-player role is {role.name}.')
        else:
            await ctx.send(f'There is no inactive-player role set.')
    
    @commands.command(help='Displays the threshold (in days) to determine player activity. Players who last posted more than the threshold number of days are deemed inactive.')
    async def displayInactivityThreshold(self,ctx:commands.context.Context):
        inactivityThreshold = await self.configuration.getInactivityThreshold()
        if inactivityThreshold == None:
            await ctx.send('The inactivity threshold is not set.')
        else:
            await ctx.send(f'The inactivity threshold is set to {inactivityThreshold} days.')

    @commands.command(help='Displays up to how many days back the activity report function should look at to determine roleplay activity. Players whose last activity cannot be determined within that limit will she shown as "never played or played more than N days ago')
    async def displayActivityReportLookupLimit(self,ctx:commands.context.Context):
        lookupLimit = await self.configuration.getActivityReportLookupLimit()
        if lookupLimit == None:
            await ctx.send('The activity-report–lookup limit is not set.')
        else:
            await ctx.send(f'The activity-report–lookup limit is set to {lookupLimit} days.')
