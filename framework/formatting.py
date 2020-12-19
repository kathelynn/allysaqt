'''Formatting'''
from string import Template
import discord

def str_format(str_input, stringformat):
    '''String formatter'''
    str_input = Template(str_input)
    return str_input.substitute(**stringformat)

def dict_format(dictionary, stringformat):
    '''Dictionary formatter'''
    for key, value in dictionary.items():
        if isinstance(value, dict):
            dictionary[key] = dict_format(value, stringformat)
        else:
            dictionary[key] = Template(value)
            dictionary[key] = dictionary[key].substitute(**stringformat)
    return dictionary

def json_embed(json, stringformat=None): # translates stuff made from embed visualizer!
    json = json.copy()
    if stringformat:
        json = dict_format(json, stringformat)
    if not 'content' in json:
        json['content'] = None

    set_embed = None
    if 'embed' in json:
        embeddicts = {}
        embedkwargs = {
            "title": discord.Embed.Empty, "description": discord.Embed.Empty,
            "url": discord.Embed.Empty, "color": discord.Embed.Empty,
            "timestamp": discord.Embed.Empty
        }
        for key, value in json['embed'].items():
            if isinstance(value, dict):
                embeddicts[key] = value
            else: embedkwargs[key] = value

        set_embed = discord.Embed(
            title=embedkwargs['title'],
            description=embedkwargs['description'],
            url=embedkwargs['url'],
            color=embedkwargs['color'],
            timestamp=embedkwargs['timestamp']
        )
        for key, value in embeddicts.items():
            print(key, value)
            if key == 'footer':
                if 'text' in value:
                    set_embed.set_footer(text=embeddicts['footer']['text'])
                    if 'icon_url' in value:
                        set_embed.set_footer(text=embeddicts['footer']['text'], icon_url=embeddicts['footer']['icon_url'])
            elif key == 'thumbnail':
                set_embed.set_thumbnail(url=embeddicts['thumnbnail']['url'])
            elif key == 'image':
                set_embed.set_image(url=embeddicts['image']['url'])
            elif key == 'author':
                if 'name' in value:
                    if not 'url' in value:
                        embeddicts['author']['url'] = discord.Embed.Empty
                    if not 'icon_url' in value:
                        embeddicts['author']['icon_url'] = discord.Embed.Empty
                    set_embed.set_author(
                        name=embeddicts['author']['name'],
                        url=embeddicts['author']['url'],
                        icon_url=embeddicts['author']['icon_url']
                    )
            elif key == 'fields':
                print(value)
                if isinstance(value, list) and isinstance(value[0], dict):
                    print(True)
                    for dictionary in value:
                        if 'inline' not in dictionary:
                            dictionary['inline'] = False
                        set_embed.add_field(name=dictionary['name'],
                                            value=dictionary['value'],
                                            inline=dictionary['inline'])
    return {"content":json['content'], "embed":set_embed}

def group(*args):
    '''Group helper'''
    args = ', '.join(list(*args[:len(*args)]))
    args = f'{args}, and {str(*args[len(*args):])}'
    return args

def plurality(num, item):
    '''Wut even?'''
    if num < 2:
        return f'{num} {item}'
    return f'{num} {item}s'

def merge_dict(source, destination): # note: in python 3.9, operator `|=` exists for dictionary.
    '''Helper to merge dictionaries'''
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            merge_dict(value, node)
        else:
            destination[key] = value
    return destination


def make_dict(**kwargs):
    '''Makes a new dict'''
    return kwargs