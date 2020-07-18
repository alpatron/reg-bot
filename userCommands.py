import asyncio
import discord
from helperFunction import splitAndSend
from discord.ext import commands
from main import RegBot
from configuration import Configuration
from datetime import datetime, timedelta

#This class is used to hold commands of no special significance, those which may be used by any user.
class UserCommands(commands.Cog, name='UserCommands'):
    def __init__(self,bot:RegBot,configuration:Configuration):
        self.bot = bot
        self.configuration = configuration
    
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
            UNAPPROVED_PLAYERS = await self.bot.getPlayersWaitingForApproval(ctx.guild)

            message = f'Activity report ({NOW.isoformat()})\n\n'
            message += f'Players who left the server, but still have some posts in {CHARACTER_CHANNEL.mention}:\n'
            if len(DEAD_PLAYERS) != 0:
                for deadPlayer in DEAD_PLAYERS:
                    message += f'{discord.utils.escape_markdown(deadPlayer.display_name)}\n'
            else:
                message += 'There are none.\n'
            
            message += f'\nPlayers with unapproved sheets (edit times don\'t reflect Google Docs edits and similar):\n'
            if len(UNAPPROVED_PLAYERS) != 0:
                def unapprovedPlayersSort(x):
                    lastMessage = max(x[1],key=lambda message:message.edited_at if message.edited_at is not None else message.created_at)
                    return lastMessage.edited_at if lastMessage.edited_at is not None else lastMessage.created_at
                sortedUnapprovedPlayers = sorted(UNAPPROVED_PLAYERS.items(),key=unapprovedPlayersSort)
                for player, sheet in sortedUnapprovedPlayers:
                    lastMessage = max(sheet,key=lambda message:message.edited_at if message.edited_at is not None else message.created_at)
                    message += f'{discord.utils.escape_markdown(player.display_name)} (last edited: {(NOW - (lastMessage.edited_at if lastMessage.edited_at is not None else lastMessage.created_at)).days} days ago) [jump]({lastMessage.jump_url})\n'
            else:
                message += 'There are none.\n'

            message += '\nInactive players:\n'
            #lastMessage[1] is the player's last roleplay message
            #lastMessage[0] is the dict key, i.e. the player object
            inactivePlayers = dict(filter(lambda lastMessage: (NOW - lastMessage[1].created_at).days >= INACTIVITY_THRESHOLD and lastMessage[0] in PLAYERS_WITH_APPROVED_CHARACTER,PLAYER_ACTIVITIES.items()))
            inactiveBeyondLookupLimitPlayers = set(filter(lambda player: player not in PLAYER_ACTIVITIES,PLAYERS_WITH_APPROVED_CHARACTER))
            if len(inactivePlayers) > 0 or len(inactiveBeyondLookupLimitPlayers) > 0:
                for player in inactiveBeyondLookupLimitPlayers:
                        message += f'{discord.utils.escape_markdown(player.display_name)} (last activity: more than {LOOKUP_LIMIT} days ago)\n'
                player : discord.Member
                lastMessage: discord.Message
                for player, lastMessage in sorted(inactivePlayers.items(),key=lambda x: x[1].created_at):
                        message += f'{discord.utils.escape_markdown(player.display_name)} (last activity: {(NOW - lastMessage.created_at).days} days ago in {lastMessage.channel.mention} [jump]({lastMessage.jump_url}))\n'
            else:
                message += 'No inactive players.\n'
            
            activePlayers = dict(filter(lambda lastMessage: (NOW - lastMessage[1].created_at).days < INACTIVITY_THRESHOLD and lastMessage[0] in PLAYERS_WITH_APPROVED_CHARACTER,PLAYER_ACTIVITIES.items()))
            message += '\nActive players:\n'
            if len(activePlayers) > 0:
                player : discord.Member
                lastMessage: discord.Message
                for player, lastMessage in sorted(activePlayers.items(),key=lambda x:x[1].created_at):
                    message += f'{discord.utils.escape_markdown(player.display_name)} (last activity: {(NOW - lastMessage.created_at).days} days ago in {lastMessage.channel.mention} [jump]({lastMessage.jump_url}))\n'
            else:
                message += '*sob* Irredeemable! There are no active players. Is the server dead? Hello, anyone?'
            await splitAndSend(message,ctx.channel,sendAsEmbed=True)

    @commands.command(help='Loads a Pastebin paste and splits it into Discord messages (so that you don\'t have to split it yourself)! User mentions (including \'everyone\' and \'here\' are stripped.)')
    async def pastebinSplit(self,ctx:commands.Context,pastebinID:str):
        async with ctx.message.channel.typing():
            URL = 'https://pastebin.com/raw/'
            async with self.bot.http_session.get(URL+pastebinID) as response:
                if response.status == 200:
                    await splitAndSend(await response.text(),ctx.channel,removeMentions=True)
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