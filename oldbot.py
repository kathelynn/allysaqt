'''Ally is a qt'''
testing = False
import asyncio
import discord
from discord.ext import commands
import framework

BOT = commands.Bot(command_prefix=framework.loadstufftomemory.prefix)

async def autosave():
    '''Autosaves storage in case of power failure, etc.'''
    INTERVAL = framework.loadstufftomemory.config('autosaveinterval')*60
    while True:
        await asyncio.sleep(INTERVAL)
        framework.loadstufftomemory.access(mode='s')

@BOT.event
async def on_ready():
    '''Runs when the bot connects to discord'''
    print(f'Logged on as {BOT.user}!')
    await autosave()

@BOT.event
async def on_message(message):
    '''Runs when the bot logs a message'''
    print('{0.author} from {0.channel}: {0.content}'.format(message))
    await BOT.process_commands(message)

EMBED_TIMEOUT = framework.loadstufftomemory.config('embedtimeout')
EMBED_BUTTONS = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

@BOT.event
async def on_command_error(ctx, error):
    '''To check if the command is a runtime command'''
    if isinstance(error, commands.CommandNotFound):
        try:
            command = framework.commandsonruntime.load(ctx=ctx)
            if 'embed' in command:
                command['embed'] = discord.Embed.from_dict(command['embed'])
            await ctx.send(**command)
        except Exception as e:
            embed = discord.Embed.from_dict({"title":"Error", "description":str(e), "color":16711680})
            await ctx.send(embed=embed)
    else:
        embed = discord.Embed.from_dict({"title":"⚠️ Error", "description":str(error), "color":16711680})
        await ctx.send(embed=embed)
        raise error

@BOT.command(aliases=['setting', 'set'])
async def settings(ctx, arg=None, arg2=None):
    '''Settings command'''
    guild = ctx.guild
    author_guildperms = ctx.author.guild_permissions
    permission_error = lambda arg, perm: f"Sorry, you need `{perm}` permission to access `{arg}` setting."

    embed = {}
    embed['author'] = {'name': guild.name, 'icon_url': str(guild.icon_url)}
    embed['title'] = "⚙️ Settings"
    embed['description'] = f"`prefix`: `{ctx.prefix}`"
    embed['color'] = 2896440

    if arg == 'prefix':
        embed['title'] = f"{embed['title']} > Prefix"
        embed['description'] = f"Prefix for `{guild.id}`: `{ctx.prefix}`"
        if arg2:
            if not author_guildperms.manage_guild:
                # 'Guild' is 'Server' in Discord UX context
                embed['description'] = permission_error('prefix', 'Manage Server')
                embed['color'] = 16711680
            elif len(arg2) > 3:
                embed['description'] += f"\nSorry! `{arg2}` is {framework.formatting.plurality(len(arg2) - 3, 'character')} too long."
                embed['color'] = 16711680
            else:
                pfx = framework.loadstufftomemory.prefix(guild_id=guild.id, mode='w', prefix=arg2)
                embed['description'] += f"> `{pfx}`\nBot prefix has been changed!"
                embed['color'] = 65280

    await ctx.send(embed=discord.Embed.from_dict(embed))
            

@BOT.command(aliases=['ccommands', 'cc'])
async def customcommands(ctx, args=None):
    '''Custom commands command'''
    path = args
    try:
        while path:
            embed = {}
            choices = []

            if path == []:
                choices = ['create']
                embed['author'] = {'name': guild.name, 'icon_url': str(guild.icon_url)}
                embed['title'] = 'Custom Commands'
                embed['fields'] = [{'name': f'`{ctx.prefix}{ctx.invoked_with} create`', 'value':'Initialize embed creation tool'}]
                embed['color'] = 800868 
            elif path[1] == 'create':
                choices = ['make']
                embed['title'] = f"{embed['title']} > Create"
                embed['description'] = "Work in Progress\n`1.` Foo\n`2.` Bar"
                if path[0] == '0':
                    embed['description'] = 'End'
                elif path[0] == '1':
                    choices = ['10', '11']
                    embed['description'] = "Work in progress\n`1.` Foobar\n`2.` Barfoo"
                    if path[1] == '0':
                        embed['description'] = "Foobar picked!"
                    if path[1] == '1':
                        embed['description'] = "Barfoo picked!"
            
            if 'botmsg' in locals():
                await botmsg.clear_reactions()
                await botmsg.edit(embed=discord.Embed.from_dict(embed))
            else:
                botmsg = await ctx.send(embed=discord.Embed.from_dict(embed))
            
            
            if choices and path not in choices:
                for i in range(0, len(choices)):
                    await botmsg.add_reaction(EMBED_BUTTONS[i])
                await botmsg.add_reaction('❎')
                def check(reaction, user):
                    return str(reaction.emoji) in EMBED_BUTTONS + ['❎'] and user == ctx.author and reaction.message == ctx.message
                reaction = await BOT.wait_for('reaction_add', check=check, timeout=EMBED_TIMEOUT)
                path = EMBED_BUTTONS.index(str(reaction.emoji))
                path = choices[path]
                del choices
            else:
                break
    except Exception as e:
        if isinstance(e, asyncio.TimeoutError):
            e = 'Timeout'
        embed.clear()
        embed['description'] = e
        embed['color'] = 16711680
        await botmsg.edit(embed=discord.Embed.from_dict(embed))
            

# '''For modules'''
# from os import listdir, getcwd
# from os.path import isfile, join
# modules = [f for f in listdir(f"{getcwd()}/modules") if isfile(join(f"{getcwd()}/modules", f))]
# modules.remove('__init__.py')
# for x in range(0, len(modules)):
#     modules[x] = modules[x][:len(modules[x])3]
#     print(modules[x])
# print(modules)
# loadedmodule = []
# for module in modules:
#     try:
#         exec(f"from modules import {module}")
#         globals()[module].setup(BOT)
#         loadedmodule.append(module)
#     except Exception as e:
#         print(e)
# print(f"Modules loaded: {[module for module in loadedmodule]}")

TOKEN = framework.loadstufftomemory.config('token')
import atexit
atexit.register(framework.loadstufftomemory.access, **{'mode':'s'})
BOT.run(TOKEN)