import asyncio, itertools, string, sqlite3
import discord
from discord.ext import commands
from json import load, dump

'''File loader/saving'''

def loaddisk(file):
    try:
        with open(file) as f:
            print(f'{file} accessed!')
            return load(f)
    except FileNotFoundError:
        print(f"""Please follow the instructions found in README.md,
        otherwise if error still occurs please report issues on GitHub.
        Missing file: {file}""")

def loaddb(file):
    return sqlite3.connect(file)

def save(memory, file, db=None):
    with open(file, 'w') as f:
        print('Saving to disk..')
        dump(memory, f, indent=4)
        print('Saved successfully!')
    if db:
        db.commit()
        
CONFIG = loaddisk('config.json')

'''Special functions'''

def merge_dict(source, destination):
    for key, value in source.items():
        try:
            value.items()
        except:
            destination[key] = value
        else:
            node = destination.setdefault(key, {})
            merge_dict(value, node)

def nested_dict(source, destination):
    if len(source) > 1:
        node = destination.setdefault(source[0], {})
        return nested_dict(source[1:], node)
    else:
        destination[source[0]] = {}
        return destination[source[0]]

'''Bot memory'''

class db:
    conn = loaddb(CONFIG['dbfilename'])
    cursor = conn.cursor()
    tables = [('prefixes', 'serverID text, prefix char(3)')]
    for table in tables:
        cursor.execute(f'CREATE TABLE IF NOT EXISTS {table[0]}({table[1]});')
    def __new__(cls):
        return db.cursor
    def fetch(sql, *parameters):
        db.cursor.execute(sql, *parameters)
        return db.cursor.fetchone()

class json:
    json = loaddisk(CONFIG['filename'])
    def __new__(cls):
        return json.json
    def overwrite(path, value):
            append = {}
            path = path.split('/')
            node = nested_dict(path[:-1], append)
            node[path[-1]] = value
            merge_dict(append, json())

async def autosave(memory, file, interval=None):
    interval = interval*60
    while True:
        await asyncio.sleep(interval)
        save(memory, file)

def setting(ctx, item):
    try:
        return json()[str(ctx.guild.id)]['settings'][item] # type: ignore
    except KeyError:
        return json()['global']['settings'][item] # type: ignore

def command_prefix(bot, ctx):
    owo = db.fetch('SELECT prefix FROM prefixes WHERE serverID=?;', (ctx.guild.id,))
    if not owo:
        owo = CONFIG['defaultprefix']
    return owo

'''Bot Logic'''

BOT = commands.Bot(command_prefix=command_prefix)

@BOT.event
async def on_ready():
    print(f'Logged on as {BOT.user} ({BOT.user.id})')
    if CONFIG['autosave']:
        asyncio.create_task(autosave(json(), CONFIG['filename'], CONFIG['autosaveinterval']))

@BOT.event
async def on_message(message):
    print(f'{message.author} from {message.channel}: {message.content}')
    await BOT.process_commands(message)

class CMD:
    def __new__(cls, ctx=None, command=None):
        guild_id = str(ctx.guild.id)
        if command:
            command = ctx.message.content[len(ctx.prefix):].split()
            if len(command) > 1:
                args = command[1:]
            command[0] = command[0].lower()

        if ctx and command:
            for key, value in json()[guild_id]['commands'].items():
                if command[0] in key:
                    return value
            raise KeyError(f'Command `{command}`')
        elif command:
            for key,value in json()['global']['commands'].items():
                if command[0] in key:
                    return value
            raise KeyError(f'Command `{command}`')
        elif ctx:
            return json()[guild_id]['commands']
        else:
            pass
        
    def if_global(command):
        for key, value in json()['global']['commands'].items():
            if command in key:
                return True
        return False
    def if_local(ctx, command):
        for key,value in json()[str(ctx.guild.id)]['commands'].items():
            if command in key:
                return True
        return False
    def if_unused(ctx, command):
        if CMD.if_global(command) or CMD.if_local(ctx, command):
            return False
        else:
            return True

@BOT.event
async def on_command_error(ctx, error):
    errortype = type(error)
    if errortype is commands.CommandNotFound:
        try:
            output = CMD(ctx, ctx.message.content)
        except KeyError:
            if setting(ctx, 'command_error'):
                    embed = discord.Embed.from_dict({"description":"Command not found", "color":16711680})
                    await ctx.send(embed=embed)
        else:
            send = {}
            items = ctx.message
            for key, value in output.items():
                # need to copy instead of pointing to output var'
                if key in ['content','tts','embed','file']:
                    send[key] = string.Template(value).safe_substitute(**items)
            if 'embed' in send:
                send['embed'] = discord.Embed.from_dict(send['embed'])
            await ctx.send(**send)
    if errortype is asyncio.TimeoutError:
        pass
    else:
        if setting(ctx, 'command_error'):
                embed = discord.Embed.from_dict({'description':'An error occured', 'color':16711680}) ###
                await ctx.send(embed=embed)
        raise error

### Playing around a bit here
#@BOT.event
#async def on_raw_message_delete(payload):
#    channel = await BOT.fetch_channel(payload.channel_id)
#    if payload.cached_message:
#        await channel.send(content=payload.cached_message.content)
#        if payload.cached_message.embeds:
#            for embed in payload.cached_message.embeds:
#                await channel.send(embed=embed)
#    else:
#        await channel.send('A message was deleted')
        
EMBED_TIMEOUT = CONFIG['embedtimeout']

class interactive_embed:
    class reaction:
        def __init__(self, iterable, up=False):
            self.reactions = iterable
            self.up = up
    class message:
        def __init__(self, message, up=False):
            self.message = message
            self.up = up

    async def __new__(cls, ctx, botmsg, userinput):
        buttons = []
        # replace isinstance with classes 
        if isinstance(userinput, interactive_embed.reaction):
            if userinput.up:
                buttons.append('◀')
            buttons = itertools.chain(buttons, [button for button in itertools.chain([key for key, value in userinput.reactions.items()], ['❎'])])
        elif isinstance(userinput, interactive_embed.message):
            buttons = itertools.chain(buttons, ['✏', '◀', '❎'])
        else:
            raise Exception() ###
        
        tasks = set()
        for reaction in buttons:
            tasks.add(asyncio.ensure_future(botmsg.add_reaction(reaction)))
        def check(reaction, user):
            return str(reaction.emoji) in userinput.reactions and user.id is ctx.author.id and reaction.message.id is botmsg.id
        reaction, user = await BOT.wait_for('reaction_add', check=check, timeout=EMBED_TIMEOUT)
        emoji = str(reaction.emoji)

        if emoji == '✏':
            await botmsg.clear_reactions()
            embed = {'description': userinput.message}
            await botmsg.edit(embed=discord.Embed(description=userinput.description))
            def check(message):
                return message.author is ctx.author and message.channel is botmsg.channel
            message = await BOT.wait_for('message', check=check, timeout=EMBED_TIMEOUT)
            await message.delete(delay=0) # delay puts task in background and ignores if it cant be deleted
            return message.content, botmsg
        elif emoji == '◀':
            return '..'
        elif emoji == '❎':
            await botmsg.clear_reactions()
            return 0, botmsg
        else:
            return userinput.reactions[emoji], botmsg

@BOT.command(aliases=['set'])
async def settings(ctx, *args, botmsg=None):
    embed = {}
    userinput = None
    guild_id = str(ctx.guild.id)

    def prefix(new):
        owo = db.fetch('SELECT * FROM prefixes WHERE serverID=?', (str(ctx.guild.id),))
        if owo == new:
            raise Exception('Pick a different prefix') ###
        characters = f'{string.digits}{string.ascii_letters}{string.punctuation}'
        for character in new:
            if character not in characters:
                raise Exception(f'Invalid character {character}') ###
        if owo:
            db().execute('UPDATE prefixes SET prefix = ? WHERE serverID = ?;', (new, str(ctx.guild.id)))
        else:
            db().execute('INSERT INTO prefixes (prefix, serverID) VALUES (?, ?);', (new, str(ctx.guild.id)))
        return {
            "description": f"Prefix for this server has been changed to `{db.fetch('SELECT prefix FROM prefixes WHERE serverID=?', (str(ctx.guild.id),))[0]}`.", # the index cleans up the tuple
            "color": 65280
        }
    
    def cmdalerts(new):
            json.overwrite(f'{guild_id}/settings/command_error', new)
            return {
                "description": f"Command alerts for this server is set to `{json()[guild_id]['settings']['command_error']}`.",
                "color": 65280
            }

    ### work in progress
    template = {
        "header": {
            "name": f"{' / '.join([x.title() for x in itertools.chain((ctx.guild.name,), args)])}",
            "icon_url": str(ctx.guild.icon_url)
        },
        "default": {
            "embed": {
                "title": "Settings",
                "description": f"{ctx.prefix}set ..."
            },
            "links": ['prefix', 'cmdalerts']
        },
        "prefix": {
            "title": "Prefix",
            "icon": "1️⃣",
            "info": f"{ctx.prefix}",
            "action": {
                "permission": ctx.author.guild_permissions.manage_guild,
                "do": prefix
            }
        },
        "cmdalerts": {
            "title": "Command Alerts",
            "icon": "2️⃣",
            "info":  f"{setting(ctx, 'command_error')}",
            "action": {
                "permission": ctx.author.guild_permissions.manage_guild,
                "do": cmdalerts
            }
        }
    }

    if not args:
        embed = template['default']['embed']
        embed['fields'] = []
        userinput = {}
        for name in template['default']['links']:
            icon = template[name]['icon']
            userinput[icon] = name
            embed['fields'].append( {
                "name": f"{icon} {template[name]['title']}",
                "value": f"{name} {template[name]['info']}"
            } )
        userinput = interactive_embed.reaction(userinput)
    else:
        navigate = template[args[0]]
        for arg in args[1:]:
            if arg in navigate:
                navigate = navigate[arg]
            else:
                if 'action' in navigate and navigate['action']['permission']:
                    async with ctx.channel.typing():
                        botmsg = None
                        embed = navigate['action']['do'](*args[args.index(arg):]) ### will probably need a faster initiative
                if 'links' in navigate:
                    for name in template['default']['links']:
                        icon = template[name]['icon']
                        userinput[icon] = name
                        embed['fields'].append( {
                            "name": f"{icon} {template[name]['title']}",
                            "value": f"{name} {template[name]['info']}"
                        } )
                    userinput = interactive_embed.reaction(userinput)
        if not embed:
            embed = {
                "title": navigate['title'], 
                "description": navigate['info'] 
            }
        if 'action' in navigate and not navigate['action']['permission']:
            embed['footer'] = {'text': 'You do not have permission to change this setting'} ###

    embed['author'] = template['header']
    
    embed = discord.Embed.from_dict(embed)
    if botmsg:
        await botmsg.edit(embed=embed)
    else:
        botmsg = await ctx.send(embed=embed)

    if userinput:
        userinput.up = len(args) > 0
        path, botmsg = await interactive_embed(ctx, botmsg, userinput)
        if path == '..':
            await asyncio.create_task(settings(ctx, *args[:-1], botmsg=botmsg))
        elif path:
            await asyncio.create_task(settings(ctx, *args, path, botmsg=botmsg))
        await botmsg.clear_reactions()

import atexit
atexit.register(save, json(), CONFIG['filename'], db=db.conn)
BOT.run(CONFIG['token'])