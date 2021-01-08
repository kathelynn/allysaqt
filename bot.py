import asyncio
import discord
from discord.ext import commands

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

async def savedisk(memory, file, autosave=False):
    interval = CONFIG['autosaveinterval']*60
    def save():
        from json import dump
        with open(file, 'w') as f:
            print('Saving to disk..')
            dump(memory, f, indent=4)
            print('Saved successfully!')
    save()
    while autosave:
        await asyncio.sleep(interval)
        save()

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
    def append(directory, item):
        if isinstance(item, list) and len(item) == 2:
            append = {}
            node = nested_dict(directory.split('/'), append)
            node[item[0]] = item[1]
            merge_dict(append, MEMORY.database)
        else:
            raise Exception

class CMD:
    def __new__(cls):
        return MEMORY['commands']
    

def command_prefix(bot, ctx):
    try:
        return MEMORY['settings'][ctx.guild.id]['prefix']
    except KeyError:
        return MEMORY['settings']['global']['prefix']

BOT = commands.Bot(command_prefix=command_prefix)

@BOT.event
async def on_ready():
    print(f'Logged on as {BOT.user} ({BOT.user.id})')
    await savedisk(MEMORY, CONFIG['filename'], CONFIG['autosave'])

@BOT.event
async def on_message(message):
    print('{0.author} from {0.channel}: {0.content}'.format(message))
    await BOT.process_commands(message)

@BOT.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        try:
            command = 

@BOT.command(aliases=['set'])
async def settings(ctx, *args):
    path = args
    try:
        while path:
            embed = {}
            choices = []

            guild_name = ctx.guild.name
            guild_icon = ctx.guild.icon_url
            choices = ['prefix']
            embed = {
                "author": {
                    "name": guild_name,
                    "icon_url": str(guild_icon)
                },
                "title": "Settings", 
                "fields": { [
                    {
                        "name": "Prefix",
                        "value": f"{ctx.prefix}set prefix [input]"
                    },
                    {
                        "name": "Error Messages",
                        "value": ""
                    }
                ] }
            }
            if path[0] == 'prefix':
                prefix = ctx.prefix
                def change_prefix(arg1):
                    if path != 2:
                        embed = {
                            "author": {
                                "name": f"{guild_name} / Prefix ",
                                "icon_url": str(guild_icon)
                            },
                            "title": "Prefix",
                            "description": f"*{prefix}*"
                        }
                    else:
                        if not ctx.author.guild_permissions.manage_guild:
                            raise Exception('`manage_guild` permission')
                        elif prefix == arg1:
                            raise Exception('Pick a different prefix')
                        elif len(arg1) > 3:
                            raise Exception('Arg is too long')
                        else:
                            source = {}
                            MEMORY = merge_dict()