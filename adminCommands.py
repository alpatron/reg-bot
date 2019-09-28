import asyncio
import asyncpg
import discord
from helperFunction import splitAndSend
from typing import Union, List, Set
from datetime import datetime, timedelta
from discord.ext import commands
from main import RegBot
from configuration import Configuration

class AdminCommands(commands.Cog):
    def __init__(self,bot:RegBot,configuration:Configuration):
        self.bot = bot
        self.configuration = configuration

    @commands.command(help='Archives the player\'s character.')
    @commands.has_permissions(administrator=True)
    async def archive(self,ctx:commands.context.Context,reason:str,*,player:Union[discord.Member,discord.User]):
        playerCharacterSheet:List[discord.Message] = list()
        activeCharacterChannel = await self.configuration.getActiveCharacterChannel()
        characterArchiveChannel = await self.configuration.getCharacterArchiveChannel()
        inactivePlayerRole = await self.configuration.getInactivePlayerRole(ctx)

        if activeCharacterChannel == None:
            await ctx.send('The active-character channel is not set. Character archival cannot be performed. Please, set the active-character channel.')
            return
        if characterArchiveChannel == None:
            await ctx.send('The character-archive channel is not set. Character archival cannot be performed. Please, set the character-archive channel.')
            return

        async for message in activeCharacterChannel.history(limit=None,oldest_first=True):
            if message.author == player:
                playerCharacterSheet.append(message)

        if len(playerCharacterSheet) == 0:
            await ctx.send(f'The user {player.display_name} does not havy any posts in {activeCharacterChannel.mention}.\n Performed no actions.')
            return
        else:
            await characterArchiveChannel.send('-------------------------------------------')
            await characterArchiveChannel.send(f'Owner: {player.mention}\nArchival reason: {reason}')
            for message in playerCharacterSheet:
                archiveMessage:str = message.content+'\n'
                for attachment in message.attachments:
                    archiveMessage += attachment.url
                await splitAndSend(archiveMessage,characterArchiveChannel)
            
            if isinstance(player,discord.Member):
                playerRoles = player.roles
                for roleplayRole in await self.configuration.getRoleplayRoles(ctx):
                    try:
                        playerRoles.remove(roleplayRole)
                    except:
                        pass
                
                if not inactivePlayerRole in playerRoles:
                    playerRoles.append(inactivePlayerRole)

                await player.edit(roles=playerRoles,reason='Performing automatic character archival.')

            await ctx.send(f'Archived {player.display_name}\'s character from {activeCharacterChannel.mention} and updated the player\'s roles if they are on the server.\nCheck {characterArchiveChannel.mention} if archival was successful.\nIf it was, remove the original posts in {activeCharacterChannel.mention}.')

    @commands.command(help='Displays an activty report of players: For players who are still on the server, the function shows how long it has been since their last activity and whether that is enough to be deemed inactive by the threshold. It also shows members who left but still have a character sheet in the active-characters channel. A player is defined as someone who has any of the set roleplay roles.')
    async def activityReport(self,ctx:commands.context.Context):
        async def getPlayersWithApprovedCharacter() -> Set[discord.Member]:
            activePlayers = set()
            for member in ctx.guild.members:
                if len(set(member.roles).intersection(roleplayRoles)) != 0:
                    activePlayers.add(member)
            return activePlayers
        async def getDeadAccounts() -> Set[discord.User]:
            deadAccounts = set()
            async for message in characterChannel.history(limit=None):
                if isinstance(message.author,discord.User): #message.author returns discord.member if submitter is on server, discord.user otherwise
                    deadAccounts.add(message.author)
            return deadAccounts
        async def getLastActivity():
            playerActivities = dict()
            lookupBegin = now - timedelta(days=lookupLimit)
            for channel in roleplayChannels:
                async for message in channel.history(limit=None,after=lookupBegin):
                    if message.author in playerActivities:
                        if message.created_at > playerActivities[message.author]:
                            playerActivities[message.author] = message.created_at
                    else:
                        playerActivities[message.author] = message.created_at
            return playerActivities
        with ctx.message.channel.typing():
            now = datetime.utcnow()
            inactivityThreshold = await self.configuration.getInactivityThreshold()
            if inactivityThreshold == None:
                await ctx.send('Please set the inactivity threshold first.')
                return
            lookupLimit = await self.configuration.getActivityReportLookupLimit()
            if lookupLimit == None:
                await ctx.send('Please set the lookup limit first.')
                return
            characterChannel = await self.configuration.getActiveCharacterChannel()
            if lookupLimit == None:
                await ctx.send('Please set the active-character channel first.')
                return
            roleplayRoles = await self.configuration.getRoleplayRoles(ctx)
            if len(roleplayRoles) == 0:
                await ctx.send('The number of set roleplay roles is zero; please, set some roleplay roles first.')
                return
            roleplayChannels = await self.configuration.getRoleplayChannels()
            if len(roleplayChannels) == 0:
                await ctx.send('The number of set roleplay channels is zero; please, set some roleplay channels first.')
                return
            playersWithApprovedCharacter = await getPlayersWithApprovedCharacter()
            deadPlayers = await getDeadAccounts()
            playerActivities = await getLastActivity()
            
            message = f'Activity report ({now.isoformat()})\n\n'
            
            message += f'Players who left the server, but still have some posts in {characterChannel.mention}:\n'
            if len(deadPlayers) != 0:
                for deadPlayer in deadPlayers:
                    message += f'{deadPlayer.display_name}\n'
            else:
                message += 'There are none.\n'
            
            message += '\nInactive players:\n'
            #lastActivity[1] is the time of the player's last activity
            #lastActivity[0] is the dict key, i.e. the player object
            inactivePlayers = dict(filter(lambda lastActivity: (now - lastActivity[1]).days >= inactivityThreshold and lastActivity[0] in playersWithApprovedCharacter,playerActivities.items()))
            inactiveBeyondLookupLimitPlayers = set(filter(lambda player: player not in playerActivities,playersWithApprovedCharacter))
            if len(inactivePlayers) > 0 or len(inactiveBeyondLookupLimitPlayers) > 0:
                for player in inactiveBeyondLookupLimitPlayers:
                        message += f'{player.display_name} (last activity: more than {lookupLimit} days ago)\n'
                for player, lastActivity in sorted(inactivePlayers.items(),key=lambda x: x[1]):
                        message += f'{player.display_name} (last activity: {(now - lastActivity).days} days ago)\n'
            else:
                message += 'No inactive players.\n'
            
            activePlayers = dict(filter(lambda lastActivity: (now - lastActivity[1]).days < inactivityThreshold and lastActivity[0] in playersWithApprovedCharacter,playerActivities.items()))
            message += '\nActive players:\n'
            if len(activePlayers) > 0:
                for player, lastActivity in sorted(activePlayers.items(),key=lambda x:x[1]):
                    message += f'{player.display_name} (last activity: {(now - lastActivity).days} days ago)\n'
            else:
                message += '*sob* Irredeemable! There are no active players. Is the server dead? Hello, anyone?'
            await splitAndSend(message,ctx.channel)