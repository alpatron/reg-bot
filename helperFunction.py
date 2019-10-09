import discord
import io
from typing import Union, List, Set

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

async def convertAttachementToFile(attachment:discord.Attachment) -> discord.File:
    attachmentData = await attachment.read()
    proccessedAttachmentData = io.BytesIO(attachmentData)
    return discord.File(proccessedAttachmentData,filename=attachment.filename,spoiler=attachment.is_spoiler())

async def safeCopyMessagesToChannel(messages:List[discord.Message],channel:discord.TextChannel):
    attachmentsWhichAreTooBig:List[discord.File] = list()
    MAXIMUM_ATTACHMENT_SIZE : int = channel.guild.filesize_limit

    for message in messages:
        files : List[discord.Attachment] = list()
        attachment:discord.Attachment
        for attachment in message.attachments:
            if attachment.size > MAXIMUM_ATTACHMENT_SIZE:
                attachmentsWhichAreTooBig.append(attachment)
            else:
                files.append(await convertAttachementToFile(attachment))
        if message.content != '' or len(files) > 0:
            await channel.send(message.content,files=files)
    
    if len(attachmentsWhichAreTooBig) > 0:
        message = 'Some attachments were too large to send; please save them somewhere, lest they be lost when the links expire:\n'
        for attachment in attachmentsWhichAreTooBig:
            message += attachment.proxy_url+'\n'
        await splitAndSend(message,channel)

async def getUserMessagesInChannel(channel:discord.TextChannel,user:Union[discord.Member,discord.User]) -> List[discord.Message]:
    messages = list()
    async for message in channel.history(limit=None,oldest_first=True):
        if message.author == user:
            messages.append(message)
    
    return messages
