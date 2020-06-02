import discord
import io
import textwrap
import re
from typing import Union, List, Set, Callable

async def splitAndSend(message:str,channel:discord.channel.TextChannel,removeMentions=False,sendAsEmbed=False):
    async def genericSplit(text:str,threshold:int, splitFunction:Callable[[str],List[str]]) -> List[str]:
        initialSegments = splitFunction(text)
        finalSegments = list()
        currentlyAssembledFinalSegment = ''
        for segment in initialSegments:
            if len(segment) > threshold:
                if currentlyAssembledFinalSegment != '':
                    finalSegments.append(currentlyAssembledFinalSegment)
                finalSegments.append(segment)
                currentlyAssembledFinalSegment = ''
            elif len(currentlyAssembledFinalSegment+segment) > threshold:
                finalSegments.append(currentlyAssembledFinalSegment)
                currentlyAssembledFinalSegment = segment
            else:
                currentlyAssembledFinalSegment += segment
        finalSegments.append(currentlyAssembledFinalSegment)
        return finalSegments
    def safeGoodMessageAppend(message:str):
        if message.strip() != '':
            goodMessages.append(message)

    MAXIMUM_LENGHT = 2000
    
    if removeMentions:
        message = discord.utils.escape_mentions(message)

    if len(message) <= MAXIMUM_LENGHT:
        await channel.send(message)
    else:
        goodMessages : List[str] = list()
        
        lineSplitMesseges = await genericSplit(message,MAXIMUM_LENGHT,lambda x: x.splitlines(True))
        for lineSplitMessage in lineSplitMesseges:
            if len(lineSplitMessage) <= MAXIMUM_LENGHT:
                safeGoodMessageAppend(lineSplitMessage)
            else:
                sentenceSplitMesseges = await genericSplit(lineSplitMessage,MAXIMUM_LENGHT,lambda x: re.split(r'((?<=[.?!])\s)', x))
                for senteceSplitMessage in  sentenceSplitMesseges:
                    if len(senteceSplitMessage) <= MAXIMUM_LENGHT:
                        safeGoodMessageAppend(senteceSplitMessage)
                    else:
                        for characterSplitMessage in textwrap.wrap(senteceSplitMessage,width=MAXIMUM_LENGHT,expand_tabs=False,replace_whitespace=False,drop_whitespace=False):
                            safeGoodMessageAppend(characterSplitMessage)
        
        for goodMessage in goodMessages:
            if sendAsEmbed:
                await channel.send(embed=discord.Embed(description=goodMessage))
            else:
                await channel.send(goodMessage)

async def convertAttachementToFile(attachment:discord.Attachment) -> discord.File:
    attachmentData = await attachment.read()
    proccessedAttachmentData = io.BytesIO(attachmentData)
    return discord.File(proccessedAttachmentData,filename=attachment.filename,spoiler=attachment.is_spoiler())

async def safeCopyMessagesToChannel(messages:List[discord.Message],channel:discord.TextChannel,removeMentions=False):
    attachmentsWhichAreTooBig:List[discord.File] = list()
    MAXIMUM_ATTACHMENT_SIZE : int = channel.guild.filesize_limit

    for message in messages:
        goodFiles : List[discord.Attachment] = list()
        attachment:discord.Attachment
        for attachment in message.attachments:
            if attachment.size > MAXIMUM_ATTACHMENT_SIZE:
                attachmentsWhichAreTooBig.append(attachment)
            else:
                goodFiles.append(await convertAttachementToFile(attachment))
        if message.content != '' or len(goodFiles) > 0:
            await channel.send(message.content,files=goodFiles)
    
    if len(attachmentsWhichAreTooBig) > 0:
        message = 'Some attachments were too large to send; please save them somewhere, lest they be lost when the links expire:\n'
        for attachment in attachmentsWhichAreTooBig:
            message += attachment.proxy_url+'\n'
        await splitAndSend(message,channel,removeMentions)

#Returns all of a user's messages in a given channel (sorted from oldest to newest [using 'created_at', like you would do if you scrolled through a channel]).
async def getUserMessagesInChannel(channel:discord.TextChannel,user:Union[discord.Member,discord.User]) -> List[discord.Message]:
    messages = list()
    async for message in channel.history(limit=None,oldest_first=True):
        if message.author == user:
            messages.append(message)
    
    return messages
