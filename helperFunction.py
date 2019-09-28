import discord
async def splitAndSend(message:str,channel:discord.channel.TextChannel):
    if len(message) < 2000:
        await channel.send(message)
    else:
        lines = message.splitlines(True)
        messages = list()
        currentMessage = ''
        for line in lines:
            if len(currentMessage+line) > 2000:
                messages.append(currentMessage)
                currentMessage = ''
            else:
                currentMessage += line
        for goodMessage in messages:
            await channel.send(goodMessage)