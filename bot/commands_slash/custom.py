from datetime import datetime, timedelta, timezone
from enum import Enum

from MFramework import register, Groups, Context, Interaction, Embed, Embed_Footer, Embed_Thumbnail, Embed_Author, Discord_Paths, Channel_Types
from MFramework.commands.decorators import Chance

@register(group=Groups.MODERATOR, guild=289739584546275339)
async def docket(ctx: Context, interaction: Interaction, docket: str, description: str='', publish: bool=True):
    '''
    Sends new docket in an embed
    
    Params
    ------
    docket:
        Docket code
    description:
        Optional description of docket
    publish:
        Whether message should be auto published to following channels or not (Works only in announcement)
    '''
    await ctx.deferred(private=True)
    if description != '':
        description = f"\n{description}\n"
    embed = Embed(
        description=f"New Docket Code: {docket.upper()}\n{description}\n[Redeem Here](https://techland.gg/redeem?code={docket.replace(' ','')})",
        color=13602095,
        timestamp=datetime.utcnow(),
        footer=Embed_Footer(
            text=interaction.member.nick or interaction.member.user.username,
            icon_url=interaction.member.user.get_avatar()
        ),
        thumbnail=Embed_Thumbnail(height=128, width=128,
            url="https://cdn.discordapp.com/emojis/545912886074015745.png",
        ),
        author=Embed_Author(
            name=docket.upper(), url=f"https://techland.gg/redeem?code={docket.replace(' ','')}",
            icon_url="https://cdn.discordapp.com/emojis/545912886074015745.png"
        ),
    )
    msg = await ctx.send("<@&545856777623961611>", embeds=[embed], allowed_mentions=None, channel_id=ctx.channel_id)
    await ctx.reply("Docket sent!", private=True)
    if publish and ctx.channel.type == Channel_Types.GUILD_NEWS.value:
        await msg.publish()

@register(group=Groups.MODERATOR, interaction=False)
async def bookmark(ctx: Context, title: str=None):
    '''
    Bookmark a moment in chat to save in your DMs for easy navigation
    Params
    ------
    title:
        title of the bookmark
    '''
    title = title or "Your bookmark"
    await ctx.send_dm(content=title+': \n'+Discord_Paths.MessageLink.link.format(guild_id=ctx.guild_id, channel_id=ctx.channel_id, message_id=ctx.message_id))

@register(group=Groups.GLOBAL, guild=340185368655560704)
async def loadout(ctx: Context) -> Embed:
    '''
    Losuje ekwipunek
    '''
    eq = {
        "primary_weapon": [
            "R-201", "R-101", "Cykuta BF-R", "G2A5", "V-47 Kostucha",
            "CAR", "Alternator", "Wolt", "R97",
            "Spitfire", "L-STAR", "X-55 Oddanie",
            ["Kraber-AP", {"Szybki i Wściekły": "Rykoszet"}], ["D-2 Dublet", {"Szybki i Wściekły": "Rykoszet"}], "Longbow-DMR",
            "EVA-8 Auto", "Mastiff",
            "Grzechotnik SMR", "EPG-1", "R-6P Softball", "EM-4 Zimna Wojna",
            ["Elitarny Skrzydowy", {"Zmiana Broni": "Rykoszet"}], "SA-3 Mozambik"
        ],
        "primary_mods": ["Szybkie Przeładowanie", "Szybki i Wściekły", "Rewolwerowiec", "Zmiana Broni", "Taktyczna Eliminacja", "Dodatkowa Amunicja"],
        "secondary_weapon": ["RE-45 Auto", "Hammond P2016", "Skrzydłowy B3"],
        "secondary_mods": ["Szybkie Przeładowanie", "Tłumik", "Szybki i Wściekły", "Rewolwerowiec", "Taktyczna Eliminacja", "Dodatkowa Amunicja"],
        "anti_titan_weapon": [["Karabin Ładunkowy",{"Szybkie Przeładowanie": "Hakowanie Ładowania"}], "Wyrzutnia Magnetyczna WGM", "LG-97 Grom", "Łucznik"],
        "anti_titan_mods": ["Szybkie Przeładowanie", "Rewolwerowiec", "Dobycie Broni", "Dodatkowa Amunicja"],
        "ordnance": ["Odłamkowy", "Łukowy", "Gwiazda Ognista", "Gwiazda Grawitacyjna", "Elektro-Dymny", "Ładunek Wybuchowy"],
        "booster": ["Wzmocniona Broń", "Kleszcze", "Wieżyczka Przeciw Pilotom", "Hakowanie Mapy", "Zapasowa Bateria", "Zakłócacz Radaru", "Wieżyczka Przeciw Tytanom", "Pistolet Cyfrowy", "Przewinięcie Fazowe", "Twarda Osłona", "Multi Holopilot", "Rzut Kostką"],

        "faction": ["Korpus Łupieżców", "Łowcy Alfa", "Vinson Dynamics", "Elita Miasta Aniołów", "6-4", "Dywizja ARES", "Marvińska Elita"],

        "pilot_tactical": ["Maskowanie", "Ostrze Pulsacyjne", "Lina z Hakiem", "Stymulant", "Ściana Energetyczna", "Przeskok Fazowy", "Holopilot"],
        "pilot_kit": ["Bateria", "Szybka Regeneracja", "Gadżeciarz", "Wejście Fazowe"],
        "pilot_kit_2": ["Raport o Poległych", "Ścianołaz", "Zawis", "Cichociemny", "Łowca Tytanów"],

        "titan": {
            "Kationa":["Splątana Energia", "Mina Wiązkowa", "Wzmacniacz Wirowy", "Megadziałko", "Soczewka Refrakcyjna"], 
            "Spopielacz":["Pożoga", "Wzmocnione Poszycie", "Piekielna Tarcza", "Zapas Paliwa", "Spalona Ziemia"], 
            "Polaris":["Strzał Penetrujący", "Zwiększony Ładunek", "Podwójne Pułapki", "Silniki pomocnicze Żmija", "Optyka Detektorowa"], 
            "Ronin":["Naboje Rykoszetujące", "Gromowładny", "Anomalia Czasowa", "Fechmistrz", "Unik Fazowy"], 
            "Ton":["Pociski Śledzące +", "Wzmocniona Ściana Energetyczna", "Echo Pulsowe", "Rakietowa Salwa", "Zasobnik Seryjny"], 
            "Legion":["Większy Zasób Amunicji", "Siatka Czujników", "Zapora", "Lekkie Materiały", "Ukryta Komora"], 
            "Monarcha":["Wzmacniacz Tarczy", "Złodziej Energii", "Szybkie Przezbrojenie", "Przetrwają Najsilniejsi"]
        },
        "titan_kit": ["Chip Szturmowy", "Katapulta z Maskowaniem", "Silnik Turbo", "Doładowanie Rdzenia", "Nuklearna Katapulta", "Gotowa Riposta"],
        "titanfall_kit": ["Tarcza Sklepieniowa", "Hiperzrzut"],

        "mode": {"Wyniszczenie": True, "Starcie Pilotów": True, "Obrona Umocnień": False, "Łowy": True, "Walka o Flagę": False, "Do Ostatniego Tytana": True, "Piloci Kontra Piloci": False, "Szybki Szturm": False, "Na Celowniku": False, "Starcie Tytanów": True, "Obrona Kresów": True, "Koloseum": True},
        "map": {"Baza Kodai": True, "Wybuchowo": False, "Gospodarstwo": True, "Egzoplaneta": True, "Kanał ,,Czarna Toń''": True, "Eden": False, "Suchy Dok": True, "Miejsce Katastrofy": False, "Kompleks": False, "Miasto Aniołów": True, "Kolonia": False, "Błąd": False, "Relikt": False, "Gry Wojenne": True, "Powstanie": True, "Stosy": False, "Pokład": False, "Łąka": False, "Ruch Uliczny": False, "Miasto": False, "UMA": False}
    }
    cores = {
        1: ["Pociski Łukowe", "Zasobink Rakietowy", "Transfer Energii"],
        2: ["Przezbrojenie i Przeładowanie", "Wir", "Pole Energetyczne"],
        3: ["Wielokrotne Namierzanie", "Udoskonalony Kadłub", "Akcelerator XO-16"]
    }

    from random import SystemRandom
    random = SystemRandom()

    r = {}
    mods_overwrite = {}
    for k, v in eq.items():
        if type(v) is dict:
            _v = [i for i in v.keys()]
        else:
            _v = v
        if 'mods' in k:
            c = random.sample(_v, k=2)
            mods = []
            for i in c:
                if i in mods_overwrite:
                    i = mods_overwrite[i]
                mods.append(i)
            mods_overwrite = {}

            c = "\n- ".join([""]+mods)
            r[k.replace("mods", "weapon")] += c
            continue
        else:
            c = random.choice(_v)
        if type(c) is list:
            mods_overwrite = c[1]
            c = c[0]
        if k == 'map':
            if eq['mode'][r['mode']]:
                if r['mode'] == 'Obrona Kresów':
                    maps = [i[0] for i in filter(lambda i: i[1], eq['map'].items())]
                else:
                    maps = [i for i in eq['map'].keys()][:-6]
                c = random.choice(maps)

        r[k] = c
        if c == 'Monarcha':
            for level, core in cores.items():
                r[f"core_{level}"] = random.choice(core)

        if k == 'titan':
            c = random.choice(v[c])
            r['class_kit'] = c
        if k == 'mode' and r['mode'] == 'Koloseum':
            break

    embed = Embed()
    from mlib.localization import tr
    for k, v in r.items():
        embed.addField(tr("commands.loadout."+k, language='pl'), v, True)

    return embed

@register(group=Groups.GLOBAL, guild=289739584546275339, private_response=False, only_interaction=True)
async def when(ctx: Context) -> str:
    '''
    Shows remaining delta to release
    '''
    if False:
        try:
            with open("data/bad_words.txt", encoding="utf-8") as word_file:
                bad_words = word_file.read().split("\\n")
            bad_words = set(i.strip() for i in bad_words)
        except:
            bad_words = set()
        if any(i in bad_words for i in arg.lower().split(' ')):
            return "Hey, that's rude! <:pepe_mad:676181484238798868>"

    from random import SystemRandom as random
    from datetime import datetime, timezone
    if ctx.is_message:
        msg = await ctx.reply("New command is `/when`")
        import asyncio
        await asyncio.sleep(10)
        await ctx.delete()
        await msg.delete()
        return

    date = datetime(2022, 2, 4, tzinfo=timezone.utc)
    timestamp = int(date.timestamp())
    delta = date - datetime.now(tz=timezone.utc)
    if delta.total_seconds() < 0:
        return "Released!"

    responses = {
        0.01: "Error",
        0.025: "When it's ready.",
        0.03: "If you put a bread into your toaster, do you also constantly look at it?",
        0.035: "If you set a timer for a few hours, do you also check it every few seconds?",
        0.04: "Good question.",
        0.05: "You aren't alone",
        0.06: "Soon™",
        0.07: "We are getting closer...",
        0.075: f"{delta.seconds}s",
        0.075: f"{delta.days / 2} * 2",
        0.075: f"{delta.days / 3} + {delta.days / 3} * 2 + 2 * x",
        0.1: f"<t:{timestamp}:R>",
        0.1: f"Around `{delta.days}` days to <t:{timestamp}:D>",
        1: f"Remaining `{delta}` until <t:{timestamp}:D> which is <t:{timestamp}:R>"
    }
    return random().choices(list(responses.values()), list(responses.keys()))[0]

class Characters(Enum):
    Ayo = "Hakon_Betrayal"
    Hakon = "HakonStory"

from MFramework.commands.cooldowns import cooldown, CacheCooldown

@register(group=Groups.GLOBAL, guild=289739584546275339)#, interaction=False)
@cooldown(minutes=5, logic=CacheCooldown)
async def truth(ctx: Context, character: Characters, captions: str=None):
    '''
    Shows what happened with previous bot
    Params
    ------
    character:
        Who's story to show
    captions:
        text to place on image
    '''
    if ctx.is_message:
        await ctx.deferred(True)
        return "This command works only as `/` one, try again with `/truth`"
    await ctx.deferred()
    chars = {
        Characters.Ayo: "Farewell, we will tell people you went to Harran for Olympics",
        Characters.Hakon: "Hakon, visiting Ayo so soon?",
    }
    if not captions:
        captions = chars.get(character)
    from PIL import Image, ImageDraw, ImageFont
    img = Image.open(f'data/{character.value}.png')
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("data/Roboto-Regular.ttf", size=65)
    from textwrap import wrap
    captions = wrap(captions, 38)
    y = 470
    draw.multiline_text((10,y), "\n".join(captions), fill=(255,255,255), font=font, align='center', stroke_fill=(0,0,0), stroke_width=4)
    from mlib.colors import buffered_image
    img_str = buffered_image(img)
    await ctx.reply("Sending...")
    await ctx.bot.create_message(ctx.channel_id, file=img_str, filename="SPOILER_WhatReallyHappened.png")

from MFramework import Guild_Member
@register(group=Groups.OWNER, guild=289739584546275339)
@cooldown(minutes=5, logic=CacheCooldown)
@Chance(10, "You missed")
async def ak47(ctx: Context, user: Guild_Member):
    '''
    Timeout person for a day!
    Params
    ------
    user:
        user you want to timeout
    '''
    t = datetime.utcnow() + timedelta(days=1)
    await ctx.bot.modify_guild_member(ctx.guild_id, user.user.id, mute=None, deaf=None, communication_disabled_until=t, reason="AK-47")
    return "Shots fired!"

@register(group=Groups.GLOBAL, guild=340185368655560704)
async def serverlist(ctx: Context) -> Embed:
    '''
    Pokazuje listę serwerów na Northstar z wolnymi miejscami
    '''
    url = "https://northstar.tf/client/servers"
    import requests
    servers = requests.get(url).json()
    maps = {
      "mp_angel_city" : "Angel City",
      "mp_black_water_canal" : "Black Water Canal",
      "mp_grave" : "Boomtown",
      "mp_colony02" : "Colony",
      "mp_complex3" : "Complex",
      "mp_crashsite3" : "Crashsite",
      "mp_drydock" : "DryDock",
      "mp_eden" : "Eden",
      "mp_thaw" : "Exoplanet",
      "mp_forwardbase_kodai" : "Forward Base Kodai",
      "mp_glitch" : "Glitch",
      "mp_homestead" : "Homestead",
      "mp_relic02" : "Relic",
      "mp_rise" : "Rise",
      "mp_wargames" : "Wargames",
      "mp_lobby" : "Lobby",
      "mp_lf_deck" : "Deck",
      "mp_lf_meadow" : "Meadow",
      "mp_lf_stacks" : "Stacks",
      "mp_lf_township" : "Township",
      "mp_lf_traffic" : "Traffic",
      "mp_lf_uma" : "UMA",
      "mp_coliseum" : "The Coliseum",
      "mp_coliseum_column" : "Pillars",
    }
    playlists = {
        "tdm" : "Team Death Match",
        "cp" : "Amped Hardpoint",
        "at" : "Bounty Hunt",
        "ctf" : "Capture the Flag",
        "lts" : "Last Titan Standing",
        "ps" : "Pilots vs Pilots",
        "ffa" : "Free For All",
        "coliseum": "Coliseum",
        "aitdm" : "Attrition",
        "speedball" : "Live Fire",
        "mfd" : "Marked For Death",
        "ttdm" : "Titan Brawl",
        "fra" : "Free Agents",
        "fd" : "Frontier Defense",
        "gg" : "Gun Game",
        "inf" : "Infection",
        "fw" : "Frontier Wars",
        "tt" : "Titan Tag",
        "kr" : "Amped Killrace",
        "fastball" : "Fast Ball",
        "arena" : "1v1",
        "ctf_comp" : "Competitive Capture the Flag",
        "hs" : "Hide and Seek"
    }
    ls = {}
    full_servers = 0
    for server in sorted(servers, key=lambda x: x.get("playerCount", 0), reverse=True):
        if server.get("playerCount", 0) < server.get("maxPlayers", 0) and not server.get("hasPassword", False):
            playlist = playlists.get(server.get("playlist", "Unknown"), server.get("playlist", "Unknown"))
            smap = maps.get(server.get("map", "Unknown"), server.get("map", "Unknown"))
            if playlist not in ls:
                ls[playlist] = []
            ls[playlist].append(f'{server.get("playerCount", "?")}/{server.get("maxPlayers", "?")} - {server.get("name", "Server Name")} - {smap}')
        else:
            full_servers += 1
    e = Embed()
    for playlist, _servers in ls.items():
        e.addFields(playlist, "\n".join(_servers))
    e.setFooter(f"Full or Private Servers: {full_servers}/{len(servers)}")
    return e

import sqlalchemy as sa
from mlib.database import Base

class ReviewScores(Base):
    user_id = sa.Column(sa.BigInteger, primary_key=True)
    score = sa.Column(sa.Integer)

@register(group=Groups.GLOBAL, guild=289739584546275339, private_response=True)
async def review(ctx: Context, score: int, your_review: str) -> str:
    '''
    Leave a Review!
    Params
    ------
    score:
        Your Score. Value between 1 and 10
    your_review:
        3-4 sentences
    '''
    s = ctx.db.sql.session()
    if s.query(ReviewScores).filter(ReviewScores.user_id == ctx.user_id).first():
        return "You've already sent your review"
    if score > 10 or score < 1:
        return "Invalid score. Make sure it's between 1 and 10"
    if len(your_review.split(".")) > 4 or len(your_review) > 200:
        return "Make your review with up to 4 sentences"
    embed = Embed().setDescription(your_review).setAuthor(str(ctx.user), icon_url=ctx.user.get_avatar())
    if score >= 7:
        color = "#48B80F"
    elif score >= 4:
        color = "#FFB300"
    else:
        color = "#FF2929"
    embed.setColor(color)
    s.add(ReviewScores(user_id=ctx.user_id, score=score))
    s.commit()
    await ctx.bot.create_message(938473018500464700, embeds=[embed])
    return "Thank you for your review!"

@register(group=Groups.MODERATOR, guild=289739584546275339)
async def reviews(ctx: Context):
    '''
    Shows average Review score
    '''
    s = ctx.db.sql.session()
    r = s.query(sa.func.avg(ReviewScores.score)).first()
    return f"{r[0]:.2f}"

@register(group=Groups.GLOBAL, guild=289739584546275339, private_response=True)
async def biomarker(ctx: Interaction) -> Embed:
    '''
    Shows your infection state
    '''
    from bot.dispatch.xp import progress
    return await progress(ctx)

@register(group=Groups.GLOBAL, guild=289739584546275339)
async def lfg(ctx: Context, platform: str, amount: str, when: str, progress: str, voice: bool, additional_description: str = None):
    '''
    Looking for a Group?
    Params
    ------
    platform:
        Platform you are looking for poeple to play on
        Choices:
            PC = PC
            PlayStation 4 = Play Station 4
            PlayStation 5 = Play Station 5
            XBox One = XBox One
            XBox S/X = XBox SX
    amount:
        How many players are you looking for?
        Choices:
            One = 1
            Two = 2
            Three = 3
    when:
        When do you want to play?
        Choices:
            Right Now = 0
            In 5 minutes = 300
            In an hour = 3600
            in a day = 86400
    progress:
        Players with what progression you are looking for?
        Choices:
            Story Finished = Story Finished
            Story not beaten = Story not beaten
            New Game = New Game
            Achievement Hunt = Achievement Hunt
            Collectible Search = Searching for Collectibles
            Chill = Chilling
    voice:
        Is a microphone required to play?
    additional_description:
        Anything else you would like to add?
    '''
    e = (
        Embed()
        .setAuthor(str(ctx.user), icon_url=ctx.user.get_avatar())
        .addField("Platform", platform, True)
        .addField("Players needed", str(amount), True)
        .addField("When?", f"<t:{int((datetime.now(tz=timezone.utc) + timedelta(seconds=int(when))).timestamp())}>", True)
        .addField("Game Progress", progress, True)
        .addField("Microphone", "Required" if voice else "Not necessary", True)
        .setDescription(additional_description)
    )
    for channel_id in ctx.cache.voice:
        if ctx.user_id in ctx.cache.voice[channel_id]:
            e.addField("Voice Channel", f"<#{channel_id}>", True)
            break
    return e
