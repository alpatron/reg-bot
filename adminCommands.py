import asyncio
import discord
from helperFunction import splitAndSend, convertAttachementToFile, safeCopyMessagesToChannel
from typing import Union, List, Set
from datetime import datetime, timedelta
from discord.ext import commands
from main import RegBot
from configuration import Configuration

class AdminCommands(commands.Cog):
    def __init__(self,bot:RegBot,configuration:Configuration):
        self.bot = bot
        self.configuration = configuration

    #To workaround the problem that discord.py's User converter does not convert
    #users who no longer are on the server, there is this converter which just calls
    #fetch_user if the argument is a number. This should be better implemented, but
    #it works for now, and I've found this fix, so I just want to be done with it.
    class ClientIdConverter(commands.Converter):
        async def convert(self,ctx:commands.Context,argument) -> Union[discord.User,None]:
            try:
                iD = int(argument)
            except:
                raise commands.BadArgument('Not a number')
            user = await ctx.bot.fetch_user(iD)
            if user is not None:
                return user
            else:
                raise commands.BadArgument('Couldn\'t resolve ID')

    @commands.command(help='Archives the player\'s character. Note: All user mentions are stripped from the archived character sheet. If the user has left the server, you most probably need to use the command with the user\'s ID.')
    @commands.has_permissions(administrator=True)
    async def archive(self,ctx:commands.context.Context,reason:str,*,player:Union[discord.Member,discord.User,ClientIdConverter]):
        with ctx.message.channel.typing():
            PLAYER_CHARACTER_SHEET:List[discord.Message] = await self.bot.getCharacterSheet(player)
            ACTIVE_CHARACTER_CHANNEL = await self.configuration.getActiveCharacterChannel()
            CHARACTER_ARCHIVE_CHANNEL = await self.configuration.getCharacterArchiveChannel()
            INACTIVE_PLAYER_ROLE = await self.configuration.getInactivePlayerRole(ctx)
            ROLEPLAY_ROLES = await self.configuration.getRoleplayRoles(ctx.guild)

            if ACTIVE_CHARACTER_CHANNEL == None:
                await ctx.send('The active-character channel is not set. Character archival cannot be performed. Please, set the active-character channel.')
                return
            if CHARACTER_ARCHIVE_CHANNEL == None:
                await ctx.send('The character-archive channel is not set. Character archival cannot be performed. Please, set the character-archive channel.')
                return
            if INACTIVE_PLAYER_ROLE == None:
                await ctx.send('The inactive-player role is not set. Character archival cannot be performed. PLease, set the inactive-character role.')
                return

            if len(PLAYER_CHARACTER_SHEET) == 0:
                await ctx.send(f'The user {player.display_name} does not havy any posts in {ACTIVE_CHARACTER_CHANNEL.mention}.\n Performed no actions.')
                return
            else:
                await CHARACTER_ARCHIVE_CHANNEL.send('-------------------------------------------')
                await CHARACTER_ARCHIVE_CHANNEL.send(f'Owner: {player.mention}\nArchival reason: {reason}')
                
                await safeCopyMessagesToChannel(PLAYER_CHARACTER_SHEET,CHARACTER_ARCHIVE_CHANNEL,removeMentions=True)

                if isinstance(player,discord.Member):
                    playerRoles = set(player.roles)
                    if not playerRoles.isdisjoint(ROLEPLAY_ROLES): #Only modify the user's roles if they already have one or more roleplay roles, as to not add the inactive-player role to players who've never had an approved sheet.
                        playerRoles.difference_update(ROLEPLAY_ROLES)
                        playerRoles.add(INACTIVE_PLAYER_ROLE)
                        await player.edit(roles=list(playerRoles),reason='Performing automatic character archival.')

                await ctx.send(f'Archived {player.display_name}\'s character from {ACTIVE_CHARACTER_CHANNEL.mention} and updated the player\'s roles if they are on the server and need be.\nCheck {CHARACTER_ARCHIVE_CHANNEL.mention} if archival was successful.\nIf it was, remove the original posts in {ACTIVE_CHARACTER_CHANNEL.mention}.\nBe also sure to check {CHARACTER_ARCHIVE_CHANNEL.mention} if any attachments were not able to be archived.')

    @commands.command(help='Displays an activty report of players: For players who are still on the server, the function shows how long it has been since their last activity and whether that is enough to be deemed inactive by the threshold. It also shows members who left but still have a character sheet in the active-characters channel. A player is defined as someone who has any of the set roleplay roles.')
    async def activityReport(self,ctx:commands.context.Context):
        with ctx.message.channel.typing():
            NOW = datetime.utcnow()
            INACTIVITY_THRESHOLD = await self.configuration.getInactivityThreshold()
            if INACTIVITY_THRESHOLD == None:
                await ctx.send('Please set the inactivity threshold first.')
                return
            LOOKUP_LIMIT = await self.configuration.getActivityReportLookupLimit()
            if LOOKUP_LIMIT == None:
                await ctx.send('Please set the lookup limit first.')
                return
            CHARACTER_CHANNEL = await self.configuration.getActiveCharacterChannel()
            if CHARACTER_CHANNEL == None:
                await ctx.send('Please set the active-character channel first.')
                return
            PLAYERS_WITH_APPROVED_CHARACTER = await self.bot.getPlayersWithApprovedCharacter(ctx.guild)
            DEAD_PLAYERS = await self.bot.getDeadPlayerAccounts()
            PLAYER_ACTIVITIES = await self.bot.getLastActivity(NOW)
            
            message = f'Activity report ({NOW.isoformat()})\n\n'
            
            message += f'Players who left the server, but still have some posts in {CHARACTER_CHANNEL.mention}:\n'
            if len(DEAD_PLAYERS) != 0:
                for deadPlayer in DEAD_PLAYERS:
                    message += f'{deadPlayer.display_name}\n'
            else:
                message += 'There are none.\n'
            
            message += '\nInactive players:\n'
            #lastMessage[1] is the player's last roleplay message
            #lastMessage[0] is the dict key, i.e. the player object
            inactivePlayers = dict(filter(lambda lastMessage: (NOW - lastMessage[1].created_at).days >= INACTIVITY_THRESHOLD and lastMessage[0] in PLAYERS_WITH_APPROVED_CHARACTER,PLAYER_ACTIVITIES.items()))
            inactiveBeyondLookupLimitPlayers = set(filter(lambda player: player not in PLAYER_ACTIVITIES,PLAYERS_WITH_APPROVED_CHARACTER))
            if len(inactivePlayers) > 0 or len(inactiveBeyondLookupLimitPlayers) > 0:
                for player in inactiveBeyondLookupLimitPlayers:
                        message += f'{player.display_name} (last activity: more than {LOOKUP_LIMIT} days ago)\n'
                player : discord.Member
                lastMessage: discord.Message
                for player, lastMessage in sorted(inactivePlayers.items(),key=lambda x: x[1]):
                        message += f'{player.display_name} (last activity: {(NOW - lastMessage.created_at).days} days ago in {lastMessage.channel.mention} <{lastMessage.jump_url}>)\n'
            else:
                message += 'No inactive players.\n'
            
            activePlayers = dict(filter(lambda lastMessage: (NOW - lastMessage[1].created_at).days < INACTIVITY_THRESHOLD and lastMessage[0] in PLAYERS_WITH_APPROVED_CHARACTER,PLAYER_ACTIVITIES.items()))
            message += '\nActive players:\n'
            if len(activePlayers) > 0:
                player : discord.Member
                lastMessage: discord.Message
                for player, lastMessage in sorted(activePlayers.items(),key=lambda x:x[1].created_at):
                    message += f'{player.display_name} (last activity: {(NOW - lastMessage.created_at).days} days ago in {lastMessage.channel.mention} <{lastMessage.jump_url}>)\n'
            else:
                message += '*sob* Irredeemable! There are no active players. Is the server dead? Hello, anyone?'
            await splitAndSend(message,ctx.channel)