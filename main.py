import discord
import datetime
import os
import random
import requests
from replit import db

bot_token = os.environ['discord_token']
client = discord.Client()

qcheck = db.prefix("quotes")
if not qcheck:
    db["quotes"] = {}

def store_quote(quote, guild, user):
    print("Saving quote \n")
    label = str(datetime.datetime.now().timestamp())
    db["quotes"][label] = {}
    db["quotes"][label]["quote"] = quote
    db["quotes"][label]["guild"] = guild
    db["quotes"][label]["user"] = user

def get_quote(user, guild):
    quote_list = []
    for quote in db["quotes"]:
        if db["quotes"][quote]["user"] == user:
            quote_list.append(db["quotes"][quote]["quote"])
    if quote_list:
        quote_pick = random.choice(quote_list)
        quote = quote_pick
    else:
        quote = None
    return quote

def get_meme(quote):
    list_text = quote.split(' ')

    top_list = list_text[:len(list_text)//2]
    bottom_list = list_text[len(list_text)//2:]

    top_join = ' '.join(top_list)
    bottom_join = ' '.join(bottom_list)

    print("Creating meme...")
    imgflip_memes = "https://api.imgflip.com/get_memes"
    memes = requests.get(imgflip_memes).json()
    meme_id = None
    while not meme_id:
        meme = random.choice(memes["data"]["memes"])
        if meme["box_count"] != 2:
            print("Box Count is not 2, trying again: " + str(meme["box_count"]))
            continue
        meme_id = meme["id"]

    payload = {'template_id': meme_id, 'text0': top_join, 'text1': bottom_join, 'username': os.environ['imgflip_user'], 'password': os.environ['imgflip_pass']}
    r = requests.post("https://api.imgflip.com/caption_image", data=payload)
    response = r.json()

    meme_url = response["data"]["url"].strip('\\')
    print("Meme url Generated: " + meme_url)

    return meme_url

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_reaction_add(reaction, user):

    print('Reaction found!')

    quote = reaction.message.content
    guild = reaction.message.guild.id
    quoted_user = reaction.message.author
    quoting_user = user

    if not reaction.message.attachments:
        print("No attachments")
        url = None
    else:
        url = reaction.message.attachments[0].url
        print("url found")

    if (reaction.emoji == "\U0001F4A1"):
        print("lightbulb!")
        if (quoted_user == quoting_user):
            print("Cheater detected!")
            await reaction.message.channel.send("You can't quote yourself, {}".format(quoting_user.name))
        elif (url):
            print("url found! Saving url")
            store_quote(url, guild, quoted_user.id)
            await reaction.message.channel.send('New attachment for {}'.format(quoted_user.name))
        elif (quote):
            print("Quote found! Saving quote")
            store_quote(quote, guild, quoted_user.id)
            await reaction.message.channel.send('New quote for {}'.format(quoted_user.name))
        else:
            print("Nothing found. Nani?!")

    if (reaction.emoji == "\U0001F602"):
        if (quoted_user == quoting_user):
            #await reaction.message.channel.send("You can't meme yourself, {}".format(quoting_user.name))
        #else:
            meme_for_message = get_meme(quote)
            response = '{} \n'.format(meme_for_message)
            await reaction.message.channel.send(response)

@client.event
async def on_message(message):

    if message.author == client.user:
        return

    if message.content.startswith('!quote'):
        names = message.mentions
        named = []

        for name in names:
            user_id = name.id
            named.append(user_id)

        if (len(message.content) == 6) or (not names):
            instructions = ("Emoji react to a message with \U0001F4A1 to save a quote. \n"
                "Recall a random quote with: \n"
                "!quote @user")

            await message.channel.send(instructions)
        elif len(named) > 1:
            error = ("Multiple users mentioned. Usage: !quote @user\n")

            await message.channel.send(error)
        else:
            found_quote = get_quote(named[0], message.guild.id)
            if not found_quote:
                print("No quote found")
                response = 'No quotes found.'
            else:
                print("Quote found, sending...")
                response = '{} \n'.format(found_quote)

            await message.channel.send(response)

    if message.content.startswith('!meme'):
        names = message.mentions
        named = []

        for name in names:
            user_id = name.id
            named.append(user_id)

        if (len(message.content) == 5) or (not names):
            instructions = ("Create a meme with !meme @user")

            await message.channel.send(instructions)
        elif len(named) > 1:
            error = ("Multiple users mentioned. Usage: !meme @user\n")

            await message.channel.send(error)
        else:
            found_quote = get_quote(named[0], message.guild.id)
            if not found_quote:
                print("No quote found")
                response = 'No quotes found.'
            elif found_quote.find("http") != -1:
                print("Quote with url found, sending...")
                response = '{} \n'.format(found_quote)
            else:
                print("Quote found, sending...")
                meme_for_message = get_meme(found_quote)
                response = '{} \n'.format(meme_for_message)

            await message.channel.send(response)

client.run(bot_token)
