import asyncio
from os import listxattr
import discord
from discord import channel
from discord.ext import commands
import string

def loaddisk(file):
    try:
        from json import load
        with open(file) as f:
            print(f'{file} accessed!')
            return load(f)
    except FileNotFoundError:
        print(f"""Please follow the instructions found in README.md,
        otherwise if error still occurs please report issues on GitHub.
        Missing file: {file}""")
        
CONFIG = loaddisk('config.json')

class savedisk:
    def save(memory, file):
        from json import dump
        with open(file, 'w') as f:
            print('Saving to disk..')
            dump(memory, f, indent=4)
            print('Saved successfully!')
    async def autosave(memory, file, interval=None):
        interval = interval*60
        while True:
            await asyncio.sleep(interval)
            savedisk.save(memory, file)

def merge_dict(source, destination):
    for key, value in source.items():
        if isinstance(value, dict):
            node = destination.setdefault(key, {})
            merge_dict(value, node)
        else:
            destination[key] = value

def nested_dict(source, destination):
    if len(source) > 1:
        node = destination.setdefault(source[0], {})
        return nested_dict(source[1:], node)
    else:
        destination[source[0]] = {}
        return destination[source[0]]

class MEMORY:
    database = loaddisk(CONFIG['filename'])
    def __new__(cls):
        return MEMORY.database
    def merge(path, value):
            append = {}
            path = path.split('/')
            node = nested_dict(path[:-1], append)
            node[path[-1]] = value
            merge_dict(append, MEMORY.database)

class CMD:
    def __new__(cls, ctx=None, command=None):
        if command:
            command = ctx.message.content[len(ctx.prefix):].split()
            if command > 1:
                args = command[1:]
            command[0] = command[0].upper()
        if ctx and command:
            for key, value in MEMORY()[ctx.guild.id]['commands'].items():
                if command[0] in key:
                    return value
            raise KeyError(f'Command `{command}`')
        elif command:
            for key,value in MEMORY()['global']['commands'].items():
                if command[0] in key:
                    return value
            raise KeyError(f'Command `{command}`')
        elif ctx:
            return MEMORY()[str(ctx.guild.id)]
        else:
            pass
        
    def if_global(command):
        for key, value in MEMORY()['global']['commands'].items():
            if command in key:
                return True
        return False
    def if_local(ctx, command):
        for key,value in MEMORY()[str(ctx.guild.id)]['commands'].items():
            if command in key:
                return True
        return False
    def if_unused(ctx, command):
        if CMD.if_global(command) or CMD.if_local(ctx, command):
            return False
        else:
            return True

def command_prefix(bot, ctx):
    try:
        return MEMORY()[str(ctx.guild.id)]['settings']['prefix'] # type: ignore
    except KeyError:
        return MEMORY()['global']['settings']['prefix'] # type: ignore

BOT = commands.Bot(command_prefix=command_prefix)

@BOT.event
async def on_ready():
    print(f'Logged on as {BOT.user} ({BOT.user.id})')
    if CONFIG['autosave']:
        await savedisk.autosave(MEMORY(), CONFIG['filename'], CONFIG['autosaveinterval']) 

@BOT.event
async def on_message(message):
    print(f'{message.author} from {message.channel}: {message.content}')
    await BOT.process_commands(message)

@BOT.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        pass
    else:
        embed = discord.Embed.from_dict({'description':'An error occured', 'color':16711680}) ###
        await ctx.send(embed=embed)
        raise error


class userinput:
    # Just a class to tell that the command allows user input
    def __init__(self, description):
        self.description = description

EMBED_TIMEOUT = CONFIG['embedtimeout']
EMBED_BUTTONS = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

async def interactive_embed(ctx, botmsg, choices):
    if isinstance(choices, list):
        buttons = [button for button in EMBED_BUTTONS[:len(choices)]] + ['❎']
    elif isinstance(choices, userinput):
        buttons = ['✏', '❎']

    for reaction in buttons:
        await botmsg.add_reaction(reaction)
    print(ctx.author.id)
    print(ctx.message.id)
    def check(reaction, user):
        print(user.id)
        print(reaction.message.id)
        return str(reaction.emoji) in buttons and user.id == ctx.author.id and reaction.message.id == botmsg.id
    reaction, user = await BOT.wait_for('reaction_add', check=check, timeout=EMBED_TIMEOUT)
    emoji = str(reaction.emoji)

    if emoji == '✏':
        await botmsg.clear_reactions()
        embed = {'description': choices.description}
        await botmsg.edit(embed=discord.Embed(description=choices.description))
        def check(message):
            return message.author == ctx.author and message.channel == botmsg.channel
        message = await BOT.wait_for('message', check=check, timeout=EMBED_TIMEOUT)
        return message.content
    elif emoji == '❎':
        await botmsg.clear_reactions()
        return -1
    else:
        path = buttons.index(emoji)
        return choices[path]

@BOT.command(aliases=['set'])
async def settings(ctx, *args, botmsg=None):
    try:
        embed = {}
        choices = []

        guild_name = ctx.guild.name
        guild_icon = ctx.guild.icon_url
        
        if not args:
            choices = ['prefix']
            embed = {
                "author": {
                    "name": guild_name,
                    "icon_url": str(guild_icon)
                },
                "title": "Settings", 
                "fields": [
                    {
                        "name": "1️⃣ Prefix",
                        "value": f"{ctx.prefix}set prefix [input]"
                    },
                    {
                        "name": "2️⃣ Unknown Command Error",
                        "value": f"Coming soon" ###
                    }
                ]
            }
        elif len(args) < 3 and args[0] == 'prefix':
            if len(args) < 2:
                if ctx.author.guild_permissions.manage_guild:
                    choices = userinput('Change the command')
                embed = {
                    "author": {
                        "name": f"{guild_name} / Prefix ",
                        "icon_url": str(guild_icon)
                    },
                    "title": "Prefix",
                    "description": f"*{ctx.prefix}*"
                }
            else:
                if not ctx.author.guild_permissions.manage_guild:
                    raise Exception('`manage_guild` permission missing') ###
                elif ctx.prefix == args[1]:
                    raise Exception('Pick a different prefix') ###
                elif len(args[1]) > 3:
                    raise Exception('Arg is too long') ###
                else:
                    for character in args[1]:
                        if character not in string.hexdigits + string.punctuation:
                            raise Exception(f'Invalid character {character}') ###
                    MEMORY.merge(f'{str(ctx.guild.id)}/settings/prefix', args[1])
                    embed = {
                        "description": f"Prefix for this server has been changed to `{MEMORY()[str(ctx.guild.id)]['settings']['prefix']}`.",
                        "color": 65280
                    }
        else:
            raise Exception('Arguments are incorrect')
        
        embed = discord.Embed.from_dict(embed)
        print(botmsg)
        if botmsg:
            await botmsg.clear_reactions()
            await botmsg.edit(embed=embed)
        else:
            botmsg = await ctx.send(embed=embed)

        if choices:
            path = await interactive_embed(ctx, botmsg, choices)
            if path != -1:
                await settings(ctx, *args, path, botmsg=botmsg)

    except Exception as e:
        if isinstance(e, asyncio.TimeoutError):
            await botmsg.clear_reactions()
        else:
            embed = discord.Embed.from_dict({'description': e, 'color': 16711680})
            if 'botmsg' in locals():
                await botmsg.clear_reactions()
                await botmsg.edit(embed=embed)
            else:
                await ctx.send(embed=embed)


import atexit
atexit.register(savedisk.save, MEMORY.database, CONFIG['filename'])
BOT.run(CONFIG['token'])