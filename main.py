from logging import fatal
from typing import Type
import discord
from discord.enums import try_enum
from discord.ext import commands
# from pretty_help import PrettyHelp
from nltk.corpus import words as all_words_list
from english_words import english_words_lower_alpha_set
from inflector import Inflector
import json
import random
import datetime
from PIL import Image, ImageDraw, ImageFont
import io

with open("config.json","r") as f:
    config = json.load(f)
PREFIX = config["default_prefix"]
WORD_LENGTH_MIN = config["word_length_min"]
WORD_LENGTH_MAX = config["word_length_max"]
TOKEN = config["bot_key"]

words = {}
all_words_1 = set(all_words_list.words())
all_words_2 = english_words_lower_alpha_set
all_words = set.union(all_words_1, all_words_2)
print(len(all_words_1), "words in all_words_1,", len(all_words_2), "words in all_words_2.")
print(len(all_words), "words altogether once combined.")

inflect = Inflector()


def init_prefix(bot, message):
    if message.guild:
        with open("guilds.json", "r") as f:
            guilds = json.load(f)

        return guilds[str(message.guild.id)]["prefix"]
    else:
        return PREFIX

# Generate word image using colored squares and the chosen word
async def generate(words, all_squares, channel):
    if words == [] or all_squares == []:
        await channel.send("No log available")
        return
    l = 100
    padding = 20
    text_height_padding = 15
    img = Image.new("RGB", (l*len(words[0]),l*len(words)))
    draw = ImageDraw.Draw(img)
    myfont = ImageFont.truetype("C:/Users/Hyun/AppData/Local/Microsoft/Windows/Fonts/RedHatMono-VariableFont_wght.ttf", size=100)
    for j in range(len(words)):
        word = words[j].upper()
        squares = all_squares[j].split(" ")
        for i in range(len(word)):
            # Draw squares
            if squares[i] == ":green_square:":
                draw.rectangle([(i*l,j*l), ((i+1)*l,(j+1)*l)], fill="green", outline="white", width=5)
                draw.text((i*l+padding,j*l-text_height_padding),word[i],font=myfont, fill="black")
            elif squares[i] == ":yellow_square:":
                draw.rectangle([(i*l,j*l), ((i+1)*l,(j+1)*l)], fill="yellow", outline="white", width=5)
                draw.text((i*l+padding,j*l-text_height_padding),word[i],font=myfont, fill="black")
            else:
                draw.rectangle([(i*l,j*l), ((i+1)*l,(j+1)*l)], fill="black", outline="white", width=5)
                draw.text((i*l+padding,j*l-text_height_padding),word[i],font=myfont, fill="white")
        

    # Send image to specified channel (Source: https://stackoverflow.com/a/66094487)
    with io.BytesIO() as image_binary:
        img.save(image_binary, 'PNG')
        image_binary.seek(0)
        await channel.send(file=discord.File(fp=image_binary, filename='image.png'))

# Generate keyboard layout with all used letters
async def keyboard(channel, green, yellow, black):
    l = 100
    padding = 28
    row_padding = 0
    text_height_padding = 0
    img = Image.new("RGBA", (l*10, l*3), color=None)
    draw = ImageDraw.Draw(img)
    myfont = ImageFont.truetype("C:/Users/Hyun/AppData/Local/Microsoft/Windows/Fonts/RedHatMono-VariableFont_wght.ttf", size=75)

    qwerty = ["qwertyuiop","asdfghjkl","zxcvbnm"]
    for j in range(len(qwerty)):
        row_padding += 50*j
        for i in range(len(qwerty[j])):
            # Draw squares
            letter = qwerty[j][i]
            if letter in green:
                draw.rectangle([(i*l + row_padding,j*l), ((i+1)*l + row_padding,(j+1)*l)], fill="green", outline="white", width=5)
                draw.text((i*l+padding+row_padding,j*l-text_height_padding),letter.upper(),font=myfont, fill="black")
            elif letter in yellow:
                draw.rectangle([(i*l + row_padding,j*l), ((i+1)*l + row_padding,(j+1)*l)], fill="yellow", outline="white", width=5)
                draw.text((i*l+padding+row_padding,j*l-text_height_padding),letter.upper(),font=myfont, fill="black")
            elif letter in black:
                draw.rectangle([(i*l + row_padding,j*l), ((i+1)*l + row_padding,(j+1)*l)], fill="black", outline="white", width=5)
                draw.text((i*l+padding+row_padding,j*l-text_height_padding),letter.upper(),font=myfont, fill="white")
            else:
                draw.rectangle([(i*l + row_padding,j*l), ((i+1)*l + row_padding,(j+1)*l)], fill="grey", outline="white", width=5)
                draw.text((i*l+padding+row_padding,j*l-text_height_padding),letter.upper(),font=myfont, fill="black")
    
    # Send image to specified channel (Source: https://stackoverflow.com/a/66094487)
    with io.BytesIO() as image_binary:
        img.save(image_binary, 'PNG')
        image_binary.seek(0)
        await channel.send(file=discord.File(fp=image_binary, filename='image.png'))

# Method for player to guess a word
async def guess(msg):
    guess = msg.content.lower()
    ctx = await bot.get_context(msg)
    with open("users.json", "r") as f:
        users = json.load(f)
    player = users[str(ctx.author.id)]
    correct = player["word"]
    

    # If the player guesses a word but there is no word to guess
    if correct == None:
        return

    if len(guess) != len(correct):
        # print nothing for non-commands like "yes"
        return

    # If the player guesses a word not on the word list
    if guess not in all_words:
        # Try singularizing the word, it may be a plural
        guess_plural = inflect.singularize(guess)
        if guess_plural not in all_words:
            await ctx.send("Your guess is not a word in our dictionary, try a different word.")
            return

    player["guesses"].append(guess)
    player["num_guesses"] -= 1
    squares = []
    guess_used = set() # set of indexes already used by yellow check (prevent duplicate yellows)
    for i in range(len(guess)):
        if guess[i] == correct[i]:
            squares.append(":green_square:")
            guess_used.add(i)
            if guess[i] not in player["green"]:
                player["green"].append(guess[i])
        elif guess[i] in correct:
            found = False
            for j in range(len(guess)):
                if j in guess_used or i == j:
                    continue
                elif guess[i] == correct[j] and guess[j] != correct[j]:
                        squares.append(":yellow_square:")
                        guess_used.add(j)
                        found = True
                        if guess[i] not in player["yellow"]:
                            player["yellow"].append(guess[i])
                        break
            if not found:
                squares.append(":white_large_square:")
                if guess[i] not in player["black"]:
                    player["black"].append(guess[i])
        else:
            squares.append(":white_large_square:")
            if guess[i] not in player["black"]:
                player["black"].append(guess[i])
    squares = ' '.join(squares)
    player["squares"].append(squares)
    
    await generate([guess], [squares], ctx.channel)
    await keyboard(ctx.channel, player["green"], player["yellow"], player["black"])

    if guess == correct:
        # Update wins and winstreak
        if player["mode"] == "daily":
            # A daily win
            if player["last_daily"]:
                last_win = datetime.datetime.strptime(player["last_daily"], "%Y-%m-%d").date()
                today = datetime.date.today()
                if (today-last_win).days == 1:
                    player["daily_win_streak"] += 1
            else:
                player["daily_win_streak"] += 1
            player["last_daily"] = str(datetime.date.today())
        
        
        if len(correct) != 1:
            player["wins"] += 1

        channel = bot.get_channel(player["channel"])
        if len(correct) == 1:
            # Separate win text for Letterle
            await ctx.send(f"{ctx.author.mention}, you've found the letter!")
        elif player["auto_post_results"] == True and not isinstance(channel, discord.channel.DMChannel):
            if player["mode"] == "daily":
                # Include daily win streak
                await channel.send(f"{ctx.author.mention} found the hidden word! {player['daily_win_streak']} daily win streak! Here are the results:\n" + '\n'.join(player["squares"]))
                await ctx.send(f"{ctx.author.mention}, you've found the word! Total {player['wins']} wins and a {player['daily_win_streak']} daily win streak.\nYour results have been posted on {channel.guild}'s {channel.mention}")
            else:
                await channel.send(f"{ctx.author.mention} found the hidden word! Here are the results:\n" + '\n'.join(player["squares"]))
                await ctx.send(f"{ctx.author.mention}, you've found the word! Total {player['wins']} wins. Your results have been posted on {channel.guild}'s {channel.mention}")
        else:
            if player["mode"] == "daily":
                # Include daily win streak
                await ctx.send(f"{ctx.author.mention}, you've found the word! {player['daily_win_streak']} daily win streak! Total {player['wins']} wins.")
            else:
                await ctx.send(f"{ctx.author.mention}, you've found the word! Total {player['wins']} wins.")

        # Clean the rest of the data
        player["mode"] = None
        player["word"] = None
        player["channel"] = None
        player["num_guesses"] = 0

    elif len(correct) == 1:
        pass
    elif player["num_guesses"] > 0:
        await ctx.send(f"{player['num_guesses']} guesses remaining")
    else:
        await ctx.send('\n'.join(player["squares"]))
        await ctx.send(f"{ctx.author.mention}, you have run out of tries!")
        # Clean player data
        player["word"] = None
        player["channel"] = None
        player["mode"] = None
            
    with open("users.json", "w") as f:
        json.dump(users, f, indent=4)

""" STARTING THE BOT """
#Privileged intents must be authorized if bot is in 100+ servers
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# Setting help menu using discord-pretty-print
# bot = commands.Bot(command_prefix = init_prefix, help_command=PrettyHelp())
bot = commands.Bot(command_prefix = init_prefix, intents=intents)

""" BOT EVENTS """

@bot.event
async def on_connect():
    # Store the word lists as a dict of arrays for easier grabbing
    with open(f"words_length_1.txt", 'r') as f:
        words[1] = f.read().splitlines()
    for l in range(WORD_LENGTH_MIN, WORD_LENGTH_MAX+1):
        with open(f"words_length_{l}.txt", 'r') as f:
            words[l] = f.read().splitlines()
    print("Word lists ready")


@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))


@bot.event
async def on_guild_join(guild):
    print(f"Wordsmith has been added to {guild.name}, id {guild.id} will be added to guilds.json.")
    # Set up initial prefix
    with open("guilds.json", "r") as f:
        guilds = json.load(f)
    
    guilds[str(guild.id)] = {"prefix": "~"}

    with open("guilds.json", "w") as f:
        json.dump(guilds, f, indent=4)

@bot.event
async def on_guild_remove(guild):
    print(f"Wordsmith has been removed from {guild.name}, id {guild.id} will be removed from guilds.json")
    with open("guilds.json", "r") as f:
        guilds = json.load(f)

    del guilds[str(guild.id)]

    with open("guilds.json", "w") as f:
        json.dump(guilds, f, indent=4)

@bot.event
async def on_message(msg):
    # Ignore if not in database
    with open("users.json", "r") as f:
        users = json.load(f)
    if str(msg.author.id) not in users:
        pass
    # Sends server prefix if @'ed
    elif msg.mentions and msg.mentions[0] == bot.user:
        prefix = await bot.get_prefix(msg)
        await msg.channel.send(f"This server's current message prefix is \'{prefix}\'")
    # If player guesses a word as a DM
    elif msg.guild == None and len(msg.content.split()) == 1 and msg.content.isalpha():
        await guess(msg)
    
    # Allows the bot to listen to commands again
    await bot.process_commands(msg)

@bot.before_invoke
async def add_new_user(ctx):
    # Add user to database if not in yet
    with open("users.json", "r") as f:
        users = json.load(f)
    if str(ctx.author.id) not in users:
        print("Adding new user", ctx.author)
        users[ctx.author.id] = {"word": None, "channel":None, "mode":None, "squares": [], "guesses": [], "num_guesses": 0, "green": [], "yellow": [], "black": [], "wins": 0, "daily_win_streak":0, "last_daily": None, "auto_post_results": True}
        with open("users.json", "w") as f2:
            json.dump(users, f2, indent=4)

""" BOT COMMANDS """
@bot.command(hidden=True)
async def test(ctx):
    if ctx.author.id != 171777619082215424: # Only command for me
        ctx.send("Command only useable by bot creator.");
        return
    print("TEST")
    await ctx.send("TEST MESSAGE :white_large_square: :green_square:")
    with open("users.json", "r") as f:
        users = json.load(f)
        player = users[str(ctx.author.id)]
    await generate(["bepis"], [":green_square: :yellow_square: :white_large_square: :green_square: :white_large_square:"], ctx.channel)
    await keyboard(ctx.channel, ["a","b","c"],["d","e","f","g"],["h","i","j","k","l"])

@bot.command(aliases = ["cp", "prefix"])
@commands.guild_only()
@commands.has_permissions(administrator=True)
async def changeprefix(ctx, prefix):
    with open("guilds.json", "r") as f:
        guilds = json.load(f)
    
    guilds[str(ctx.guild.id)]["prefix"] = prefix

    with open("guilds.json", "w") as f:
        json.dump(guilds, f, indent=4)

    await ctx.send(f"The prefix was changed to {prefix}")
    

@bot.command(aliases=["p", "start", "s"])
async def play(ctx, mode=None, length=5):
    if (length < WORD_LENGTH_MIN or length > WORD_LENGTH_MAX) and length != 1:
        await ctx.send(f"Word length can be modified to be between {WORD_LENGTH_MIN} and {WORD_LENGTH_MAX}")
        return
    if mode == None or not mode.isalpha():
        await ctx.send("Enter the mode you would like to play (\"Daily\", \"Random\")")
        mode = (await bot.wait_for("message", check=lambda m:m.author==ctx.author and m.channel.id==ctx.channel.id)).content.lower()
    if mode in ("d","daily"):
        await daily(ctx)
    elif mode in ("r", "rand", "random"):
        await rand(ctx, length)
    else:
        await ctx.send("Not a valid mode")
        return


@bot.command(aliases=["pd", "sd"])
async def daily(ctx):
    today = datetime.date.today()
    # First make sure user has not already played the daily
    with open("users.json", "r") as f:
        users = json.load(f)
    player = users[str(ctx.author.id)]
    if player["mode"] == "daily":
        if player["num_guesses"] > 0:
            await ctx.send(f"You've already started today's word. You cannot restart this word.")
            return
        await ctx.send(f"You've already played today's word. You can play a new word using {ctx.prefix}play random *length*")
        return
    random.seed(today.day + today.month*100 + today.year*10000)

    word = random.choice(words[5])
    print("The daily word is", word)
        
    # Updates user in the database
    player = users[str(ctx.author.id)]
    player["mode"] = "daily"
    player["word"] = word
    player["guesses"] = []
    player["num_guesses"] = 6
    #player["last_daily"] = str(today)
    player["channel"] = ctx.channel.id
    player["squares"] = []
    player["green"] = []
    player["yellow"] = []
    player["black"] = []

    await ctx.author.send(f"Daily Word started! You have {player['num_guesses']} tries to guess the hidden word.\nMake a guess by messaging me a single word in this DM channel.")

    with open("users.json", "w") as f:
        json.dump(users, f, indent=4)

@bot.command(aliases=["random", "pr", "sr"])
async def rand(ctx, length=5):
    with open("users.json", "r") as f:
            users = json.load(f)
    player = users[str(ctx.author.id)]
    # Checks if user is still playing a previous unfinished game
    if player["num_guesses"] > 0:
        await ctx.send("You still have remaining guesses for your previous game. Start a new one anyways? (y/n)")
        response = await bot.wait_for("message", check=lambda m:m.author==ctx.author and m.channel.id==ctx.channel.id)
        if response.content.lower() in ("y", "yes", "yeah"):
            await ctx.send("Generating a new random word...")
        elif response.content.lower() in ("n", "no", "nah"):
            await ctx.send("New game aborted. You may continue your previous game.")
            return
        else:
            await ctx.send("Not a valid answer, aborting command.")
            return

    random.seed(random.randint(1,9999))
    word = random.choice(words[length])
    print(f"{ctx.author}'s random word is {word}")
    
    # Updates user in the database
    player = users[str(ctx.author.id)]
    player["mode"] = "random"
    player["word"] = word
    player["guesses"] = []
    if length == 1:
        player["num_guesses"] = 26
    else:
        player["num_guesses"] = length + 1
    player["channel"] = ctx.channel.id
    player["squares"] = []
    player["green"] = []
    player["yellow"] = []
    player["black"] = []

    if length == 1:
        await ctx.author.send("Letterle mode started! Try to guess the hidden letter in as little guesses as you can!")
    else:
        await ctx.author.send(f"Random Word started! You have {player['num_guesses']} tries to guess the hidden word.\nMake a guess by messaging me a single word in this DM channel.")

    with open("users.json", "w") as f:
        json.dump(users, f, indent=4)
        

@bot.command(aliases=["l"])
async def log(ctx, flags=""):
    flags = flags.lower()
    with open("users.json", "r") as f:
        users = json.load(f)
    player = users[str(ctx.author.id)]
    guesses = player["guesses"]
    squares = player["squares"]
    if 'l' in flags or 'f' in flags:
        await generate(guesses, squares, ctx.channel)
    elif 'e' in flags or flags == "":
        await ctx.send('\n'.join(squares))
    if 'k' in flags or 'f' in flags:
        await keyboard(ctx.channel, player["green"], player["yellow"], player["black"])

@bot.command(aliases = ["letters", "logletters", "logl", "ll"])
async def log_letters(ctx):
    await log(ctx, "l")

@bot.command(aliases = ["keyboard", "k", "logkeyboard", "logk", "lk"])
async def log_keyboard(ctx):
    await log(ctx, "k")

@bot.command(aliases=["logfull", "logf", "lf"])
async def log_full(ctx):
    await log(ctx, "f")

@bot.command(aliases=["resetwins","rw"])
async def reset_wins(ctx):
    with open("users.json", "r") as f:
        users = json.load(f)
    player = users[str(ctx.author.id)]
    player["wins"] = 0
    player["win_streak"] = 0




bot.run(TOKEN)