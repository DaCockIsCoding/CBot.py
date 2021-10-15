from datetime import timedelta, datetime, timezone
from typing import Tuple, List, Optional, Dict, Any
from enum import Enum
from random import SystemRandom
from mlib.localization import tr

def _t(key: str, language: str='en', **kwargs):
    return tr("events.halloween."+key, language, **kwargs)

import sqlalchemy as sa

from mlib.database import Base, Timestamp
from MFramework import Context, User, Snowflake, Groups, Embed, register, EventBetween, Chance
from MFramework.commands.cooldowns import cooldown, CacheCooldown
from MFramework.database.alchemy.mixins import ServerID
from ...database.types import Statistic, HalloweenRaces as Race
from ...database.mixins import UserID

# When | Where | Who | to Whom | to What | From what?

class HalloweenCooldown(CacheCooldown):
    current_faction: int = 0
    target_faction: int = 0
    remaining_factions: int = 0
    def __init__(self, ctx: Context, cooldown: timedelta, cooldown_type: str, func_args: Dict[str, Any], target_user: Optional[Snowflake] = None) -> None:
        super().__init__(ctx=ctx, cooldown=cooldown, cooldown_type=cooldown_type)
        s = func_args.get("session", None)
        this_user = func_args.get("this_user", None)
        self.session = s or self.ctx.db.sql.session()
        #session.query(db.Inventory).filter(db.Inventory.user_id == ctx.user_id, db.Inventory.item_id in list(Race)).first()
        self.race = this_user or self.session.query(Halloween.race).filter(Halloween.server_id == ctx.guild_id, Halloween.user_id == ctx.user_id).first() or Race.Human
        self.get_race_counts(func_args.get("user", ctx.user).id)
    
    @property
    def cooldown(self) -> timedelta:
        return self._cooldown + self.cooldown_var

    @property
    def is_top_faction(self) -> bool:
        '''Whether it's currently a top faction'''
        return (self.remaining_factions // 2) < self.current_faction

    @property
    def faction_difference(self) -> int:
        '''Difference to other factions'''
        return self.current_faction - (self.remaining_factions // 2)

    @property
    def cooldown_var(self) -> timedelta:
        '''Current Cooldown Variance based on difference to other factions'''
        difference = self.faction_difference
        if not self.is_top_faction:
            difference = difference * 2
        return timedelta(minutes=difference * 3)

    def get_race_counts(self, target_user_id: Snowflake) -> Tuple[int, int, int]:
        '''Returns count for current user faction, user's target faction and collectively remaining factions'''
        user = Halloween.fetch_or_add(self.session, server_id=self.ctx.guild_id, user_id=self.ctx.user_id)
        if user.race not in IMMUNE_TABLE.keys():
            return
        total = Halloween.get_total(self.session, self.ctx.guild_id, user.race)
        self.current_faction = total.get(user.race, 1)

        target_user = Halloween.fetch_or_add(self.session, server_id=self.ctx.guild_id, user_id=target_user_id)
        #Halloween.get_total(session, self.ctx.guild_id, target_user.race)
        self.target_faction = total.get(target_user.race, 1)

        remaining_monsters = list(i for i in IMMUNE_TABLE.keys() if i not in (user.race, target_user.race))
        #Halloween.get_total(session, self.ctx.guild_id, remaining_monsters[0])
        self.remaining_factions = total.get(remaining_monsters[0], 1) + self.target_faction

from MFramework.commands._utils import Error
class HalloweenException(Error):
    _key = ""
    def __init__(self, key: str, language: str='en', *args: object, **kwargs) -> None:
        value = _t(self._key+key, language, default=_t(self._key+"generic", language), **kwargs)
        super().__init__(value, *args)

class Cant(HalloweenException):
    """User has wrong state"""
    _key = "cant_"

class Failed(HalloweenException):
    """Failed to bite or cure"""
    _key = "failed_"

class Immune(HalloweenException):
    """Target is on the same side or is immune"""
    _key = "immune_"

class COOLDOWNS(Enum):
    DEFEND = timedelta(hours=1)
    CURE = timedelta(hours=2)
    BITE = timedelta(hours=3)
    BETRAY = timedelta(hours=4)

IMMUNE_TABLE = {
    Race.Vampire: Race.Hunter,
    Race.Werewolf: Race.Huntsmen,
    Race.Zombie: Race.Enchanter
}

HUNTERS = IMMUNE_TABLE.values()
CURE_TABLE = {v:k for k, v in IMMUNE_TABLE.items()}

class DRINKS(Enum):
    Nightmare = "Random"#Race.Human
    Wine = "Vampire"#Race.Vampire
    Moonshine = "Werewolf"#Race.Werewolf
    Vodka = "Zombie"#Race.Zombie

class Guilds(Enum):
    Dawnguards = "Hunter"#Race.Hunter
    Rangers = "Huntsmen"#Race.Huntsmen
    Inquisition = "Enchanter"#Race.Enchanter

ROLES = {}

class HalloweenLog(ServerID, UserID, Timestamp, Base):
    timestamp: datetime = sa.Column(sa.TIMESTAMP(timezone=True), primary_key=True, server_default=sa.func.now())
    target_id: User = sa.Column(sa.ForeignKey("User.id", ondelete='Cascade', onupdate='Cascade'), primary_key=False, nullable=False)
    race: Race = sa.Column(sa.Enum(Race))
    previous: Race = sa.Column(sa.Enum(Race))

class Halloween(ServerID, UserID, Base):
    server_id: Snowflake = sa.Column(sa.ForeignKey("Server.id", ondelete='Cascade', onupdate='Cascade'), primary_key=True, nullable=False, default=0)
    user_id: Snowflake = sa.Column(sa.ForeignKey("User.id", ondelete='Cascade', onupdate='Cascade'), primary_key=True, nullable=False, default=0)
    race: Race = sa.Column(sa.Enum(Race), default=Race.Human)
    protected: datetime = sa.Column(sa.TIMESTAMP(timezone=True))
    @classmethod
    def fetch_or_add(cls: 'Halloween', s: sa.orm.Session, user_id: Snowflake, server_id: Snowflake, **kwargs) -> 'Halloween':
        from ...database.models import User
        user = User.fetch_or_add(s, id=user_id)
        r = super().fetch_or_add(s, user_id=user_id, server_id=server_id, **kwargs)
        if r.race == None:
            r.race = Race.Human
            s.commit()
        return r
    @classmethod
    def get_total(cls, s: sa.orm.Session, guild_id: Snowflake, race: Race = None) -> Dict[Race, int]:
        q = s.query(sa.func.count(cls.race), cls.race).filter(cls.server_id == guild_id)
        if race:
            q.filter(cls.race == race)
        r = q.group_by(cls.race).all()#.count()
        return {k:v for v, k in r}

    def turn_another(self, s: sa.orm.Session, target_user: Snowflake, race: Race = None) -> List[Race]:
        if self.race is Race.Human:
            if self.user_id == target_user:
                t = self
        else:
            t = Halloween.fetch_or_add(s, server_id=self.server_id, user_id = target_user)
        
            if t.protected and (t.protected > datetime.now(tz=timezone.utc)):
                raise HalloweenException("error_protected")
        
        remaining = Halloween.get_total(s, self.server_id, t.race).get(t.race, 1)
        if (self.race in IMMUNE_TABLE and (t.race in IMMUNE_TABLE or IMMUNE_TABLE.get(self.race) == t.race or self.race == t.race)) or remaining == 1:
            raise Immune("target")
        elif self.race in HUNTERS and CURE_TABLE.get(self.race, None) != t.race:
            raise HalloweenException("error_cure", currentClass=CURE_TABLE.get(self.race))

        if race:
            pass
        elif self.race in HUNTERS:
            race = Race.Human
        elif self.race in IMMUNE_TABLE.keys():
            race = self.race
        
        previous = t.race
        s.add(HalloweenLog(server_id = self.server_id, user_id = self.user_id, target_id=target_user, race = race, previous = previous))
        t.race = race
        s.commit()
        return previous, race

async def update_user_roles(ctx: Context, user_id: Snowflake, previous_race: Race, new_race: Race, s: sa.orm.Session):
    '''Updates roles of user to reflect race change'''
    get_roles(ctx.guild_id, s)
    if type(previous_race) is Race or previous_race in list(i.name for i in Race):
        if type(previous_race) is Race:
            previous_race = previous_race.name
        p_role = ROLES.get(ctx.guild_id, {}).get(previous_race, None)
        if p_role:
            await ctx.bot.remove_guild_member_role(ctx.guild_id, user_id, p_role, "Halloween Minigame")
    if type(new_race) is Race or new_race in list(i.name for i in Race):
        if type(new_race) is Race:
            new_race = new_race.name
        role = ROLES.get(ctx.guild_id, {}).get(new_race, None)
        if role:
            await ctx.bot.add_guild_member_role(ctx.guild_id, user_id, role, "Halloween Minigame")

async def turn(ctx: Context, s: sa.orm.Session, this_user: Halloween, target_user_id: Snowflake, to_race: Race = None, action: str = None) -> str:
    '''Turns target user into race of invoking user or provided race'''
    p, r = this_user.turn_another(s, target_user_id, to_race)
    await update_user_roles(ctx, target_user_id, p, r, s=s)
    return _t(f"success_{action}", ctx.language, author=ctx.user_id, target=target_user_id, currentClass=r, previousClass=p)

def get_total(total: List[Statistic]) -> Tuple[int, int]:
    '''Returns total bites and population'''
    pass

# Factions
#   reinforce - send reinforcments (turn x% of users on that server into that faction) to another server - only for leading faction on a server!

@register(group=Groups.GLOBAL)
@EventBetween(after_month=10, after_day=14, before_month=11, before_day=7)
async def halloween():
    '''Halloween Event commands'''
    pass

@register(group=Groups.ADMIN, main=halloween)
async def settings():
    '''Shows settings for Halloween Event'''
    pass

def get_roles(guild_id, s):
    from MFramework.database.alchemy import Role
    from MFramework.database.alchemy.types import Setting
    if guild_id not in ROLES:
        ROLES[guild_id] = {}
        roles = s.query(Role).filter(Role.server_id == guild_id, Role.settings.any(name=Setting.Special)).all()
        for role in roles:
            ROLES[guild_id][role.get_setting(Setting.Special)] = role.id
    return ROLES[guild_id]

@register(group=Groups.ADMIN, main=settings)
async def roles(ctx: Context, delete:bool=False, update_permissions: bool=False):
    '''Create and/or add roles related to Halloween Event
    Params
    ------
    delete:
        Delete Event roles (*Only ones that were made by bot)
    update_permissions:
        Sets permissions for commands to be only used by appropriate race
    '''
    s = ctx.db.sql.session()
    roles = get_roles(ctx.guild_id, s)
    if roles:
        #if update_permissions:
        #    permissions = []
        #    commands = []
        #    for cmd in commands:
        #        command_permissions = []
        #        from MFramework import Application_Command_Permissions, Application_Command_Permission_Type, Guild_Application_Command_Permissions
        #        for role in roles: #TODO: get only roles according to faction by command
        #            command_permissions.append(Application_Command_Permissions(
        #                id=role,
        #                type=Application_Command_Permission_Type.ROLE,
        #                permission=True
        #            ))
        #        if command_permissions != []:
        #            permissions.append(Guild_Application_Command_Permissions(
        #                id = cmd.id,
        #                permissions=command_permissions
        #            ))
        #    await ctx.bot.batch_edit_application_command_permissions(ctx.bot.application.id, ctx.guild_id, permissions)

        users = s.query(Halloween).filter(Halloween.server_id == ctx.guild_id).all()
        for user in users:
            await ctx.bot.add_guild_member_role(ctx.guild_id, user.user_id, roles.get(user.race.name), "Halloween Minigame")
    else:
        for race in Race:
            role = await ctx.bot.create_guild_role(ctx.guild_id, _t(race.name.lower().replace(' ','_'), ctx.language, count=1).title(), 0, reason="Created Role for Halloween Minigame")
            from MFramework.database.alchemy import Role
            from MFramework.database.alchemy.types import Setting
            r = Role.fetch_or_add(s, server_id=ctx.guild_id, id=role.id)
            r.add_setting(Setting.Special, race.name)
        s.commit()

import functools

def inner(f, races: List[Race], main: object, should_register: bool = True):
    @EventBetween(after_month=10, after_day=14, before_month=11, before_day=7)
    @functools.wraps(f)
    def wrapped(ctx: Context, s: sa.orm.Session=None, this_user: Halloween = None, **kwargs):
        s = s or ctx.db.sql.session()
        user = this_user or Halloween.fetch_or_add(s, server_id=ctx.guild_id, user_id=ctx.user_id)
        if user.race in races:
            return f(ctx=ctx, session=s, this_user=user, **kwargs)
        elif user.race is Race.Human:
            raise Error("You want to do what?")
        raise Cant(f.__name__)
    if should_register:
        register(group=Groups.GLOBAL, main=main)(wrapped)
    return wrapped

##########
# HUMANS #
##########

@register(group=Groups.GLOBAL, main=halloween)
def humans(cls=None, *, should_register: bool=True):
    '''Commands related to humans'''
    i = functools.partial(inner, races=[Race.Human], main=humans, should_register=should_register)
    if cls:
        return i(cls)
    return i

@humans
async def enlist(ctx: Context, guild: Guilds, *, session: sa.orm.Session, this_user: Halloween) -> str:
    '''Enlist as a hunter
    Params
    ------
    guild:
        Hunter's guild you want to join'''
    return await turn(ctx, session, this_user, ctx.user_id, guild.value, action="enlist")

@humans
async def drink(ctx: Context, type: DRINKS, *, session: sa.orm.Session, this_user: Halloween) -> str:
    '''Drink an unknown beverage to become a monster
    Params
    ------
    type:
        Drink you want to drink'''
    previous = session.query(HalloweenLog).filter(HalloweenLog.server_id == ctx.guild_id, HalloweenLog.user_id == ctx.user_id).first()
    if previous and type is not DRINKS.Nightmare:
        return "Sadly, you can choose your poison only first time around as a freshblood. Nightmarish potion is your only option to drink now."

    if type is DRINKS.Nightmare:
        total = sorted(Halloween.get_total(session, ctx.guild_id).items(), key=lambda x: x[1])
        if total:
            for race in total:
                if race[0] in IMMUNE_TABLE:
                    type = race[0]
                    break
        else:
            from random import SystemRandom
            type = SystemRandom().choice([Race.Vampire, Race.Werewolf, Race.Zombie])
    return await turn(ctx, session, this_user, ctx.user_id, type.value, action="drink")

############
# MONSTERS #
############

@register(group=Groups.GLOBAL, main=halloween)
def monsters(cls=None, *, should_register: bool=True):
    '''Commands related to Monster's factions'''
    i = functools.partial(inner, races=IMMUNE_TABLE.keys(), main=monsters, should_register=should_register)
    if cls:
        return i(cls)
    return i

@monsters
@cooldown(hours=3, logic=HalloweenCooldown)
async def bite(ctx: Context, target: User, *, session: sa.orm.Session, this_user: Halloween) -> str:
    '''Bite your target to turn into one of your own kin
    Params
    ------
    target:
        Target you want to bite'''
    return await turn(ctx, session, this_user, target.id, action="bite")

###########
# HUNTERS #
###########

@register(group=Groups.GLOBAL, main=halloween)
def hunters(cls=None, *, should_register: bool=True):
    '''Commands related to Hunter's factions'''
    i = functools.partial(inner, races=HUNTERS, main=hunters, should_register=should_register)
    if cls:
        return i(cls)
    return i

@hunters
@cooldown(hours=2, logic=HalloweenCooldown)
async def cure(ctx: Context, target: User, *, session: sa.orm.Session, this_user: Halloween) -> str:
    '''Cure your target from the darkness back into human being
    Params
    ------
    target:
        Target you want to cure'''
    return await turn(ctx, session, this_user, target.id, action="cure")

@hunters
@cooldown(hours=1, logic=HalloweenCooldown)
async def defend(ctx: Context, target: User, *, session: sa.orm.Session, this_user: Halloween) -> str:
    '''Protect fellow hunter from being bitten 
    Params
    ------
    target:
        Target you want to protect'''
    if target.id == ctx.user_id:
        raise HalloweenException("error_defend", ctx.language)

    target_user = session.query(Halloween).filter(Halloween.server_id == ctx.guild_id, Halloween.user_id == target.id).first()
    
    if target_user.race not in HUNTERS:
        raise Failed("defend", ctx.language)

    now = datetime.now(tz=timezone.utc)
    if target_user.protected is None or target_user.protected < now:
        duration = SystemRandom().randint(5, 40)
        delta = now + timedelta(minutes=duration)
        target_user.protected = delta
        session.add(HalloweenLog(server_id=ctx.guild_id, target_id=target.id, previous=target_user.race, race=target_user.race, user_id=this_user.user_id))
        session.commit()
        return _t("success_defend", ctx.language, duration=duration)

    raise HalloweenException("error_protected", ctx.language)

@hunters
@cooldown(hours=4, logic=HalloweenCooldown)
@Chance(8, fail_message="Couldn't convince them to betray their kind.")
async def betray(ctx: Context, target: User, *, session: sa.orm.Session, this_user: Halloween) -> str:
    '''Attempt to convince a monster you are hunting to join the cause and fight with the darkness instead
    Params
    ------
    target:
        Target you want to convince'''
    return await turn(ctx, session, this_user, target.id, this_user.race, action="betray")

@register(group=Groups.GLOBAL, name="Defend or Betray")
@hunters(should_register=False)
async def defend_or_betray(ctx: Context, user: User, *, session: sa.orm.Session, this_user: Halloween):
    '''
    Defend fellow hunter or convince monster depending on target's class
    '''
    target_user = session.query(Halloween).filter(Halloween.server_id == ctx.guild_id, Halloween.user_id == user.id).first()
    if target_user.race in HUNTERS:
        return await defend(ctx, target=user, s=session, this_user=this_user)
    elif target_user.race is CURE_TABLE.get(this_user.race):
        return await betray(ctx, target=user, s=session, this_user=this_user)
    await ctx.deferred(private=True)
    raise Cant("generic", ctx.language)

@register(group=Groups.GLOBAL, name="Bite or Cure")
async def bite_or_cure(ctx: Context, user: User):
    '''
    Bite or cure user depending on your class
    '''
    session = ctx.db.sql.session()
    this_user = session.query(Halloween).filter(Halloween.server_id == ctx.guild_id, Halloween.user_id == ctx.user.id).first()
    if this_user.race in IMMUNE_TABLE:
        return await bite(ctx, target=user, s=session, this_user=this_user)
    elif this_user.race in HUNTERS:
        return await cure(ctx, target=user, s=session, this_user=this_user)
    await ctx.deferred(private=True)
    raise Cant("generic", ctx.language)

@register(group=Groups.GLOBAL, main=halloween)
async def leaderboard(ctx: Context, user: User=None, limit: int=10) -> Embed:
    '''
    Shows Event leaderboard based on amount of turns
    Params
    ------
    user:
        Shows stats of another user
    limit:
        How many scores to show
    '''
    s = ctx.db.sql.session()
    total_turned = s.query(sa.func.count(HalloweenLog.user_id), HalloweenLog.user_id).filter(HalloweenLog.server_id == ctx.guild_id).group_by(HalloweenLog.user_id).order_by(sa.func.count(HalloweenLog.user_id).desc()).limit(limit).all()
    #top_race_turns = s.query(sa.func.count(HalloweenLog.race), HalloweenLog.race).filter(HalloweenLog.server_id == ctx.guild_id).group_by(HalloweenLog.race).all()
    #turned_by_user = s.query(sa.func.count(HalloweenLog.race), HalloweenLog.race, HalloweenLog.user_id).filter(HalloweenLog.server_id == ctx.guild_id).group_by(HalloweenLog.user_id, HalloweenLog.race).all()
    if not any(user.id == i.user_id for i in total_turned):
        _user = s.query(sa.func.count(HalloweenLog.user_id), HalloweenLog.user_id).filter(HalloweenLog.server_id == ctx.guild_id, HalloweenLog.user_id == user.id).group_by(HalloweenLog.user_id).first()
        if _user:
            total_turned.append(_user)
    from MFramework.utils.leaderboards import Leaderboard, Leaderboard_Entry
    entries = []
    for row in total_turned:
        entries.append(Leaderboard_Entry(ctx, row[1], row[0]))
    return [Leaderboard(ctx, user.id, entries, limit).as_embed()]

@register(group=Groups.GLOBAL, main=halloween)
async def history(ctx: Context, user: User = None, limit: int = 10) -> Embed:
    '''
    Shows turn history
    Params
    ------
    user:
        User's history to show
    limit:
        How many turns to show
    '''
    s = ctx.db.sql.session()
    from MFramework import Guild_Member

    turns = []
    turn_history = s.query(HalloweenLog).filter(HalloweenLog.server_id == ctx.guild_id, HalloweenLog.target_id == user.id).order_by(HalloweenLog.timestamp.desc()).limit(limit).all()
    for entry in turn_history[:int(limit)]:
        _u = entry.user_id
        _u = ctx.cache.members.get(int(_u), Guild_Member(user=User(username=_u))).user.username
        if entry.previous == entry.race:
            line = "Defended"
        elif entry.previous is Race.Human and _u == entry.target_id:
            if entry.race in IMMUNE_TABLE:
                line = f"Drank potion and became `{entry.race}`"
            else:
                line = f"Enlisted as `{entry.race}`"
        else:
            line = f"`{entry.previous}` into `{entry.race}`"
        turns.append(f"[<t:{int(entry.timestamp.timestamp())}:d>] {line} by `{_u}`")

    targets = []
    targets_history = s.query(HalloweenLog).filter(HalloweenLog.server_id == ctx.guild_id, HalloweenLog.user_id == user.id).order_by(HalloweenLog.timestamp.desc()).limit(limit).all()
    for entry in targets_history[:int(limit)]:
        _u = entry.target_id
        _u = ctx.cache.members.get(int(_u), Guild_Member(user=User(username=_u))).user.username
        if entry.previous == entry.race:
            line = "was protected from being turned"
        elif _u == entry.user_id:
            if entry.race in IMMUNE_TABLE:
                line = f"drank potion and became `{entry.race}`"
            else:
                line = f"enlisted as `{entry.race}`"
        else:
            line = f"from `{entry.previous}` into `{entry.race}`"
        targets.append(f"[<t:{int(entry.timestamp.timestamp())}:d>] `{_u}` {line}")

    e = Embed().setTitle(f"{user.username}'s History")
    if turns:
        e.addField("Turns", "\n".join(turns))
    if targets:
        e.addField("Targets", "\n".join(targets))
    e.addField("Statistics", f"Total Turns: `{len(turn_history)}`\nTotal Targets: `{len(targets_history)}`")
    return [e]

from MFramework import onDispatch, Bot, Guild_Member_Add

@onDispatch
async def guild_member_add(self: Bot, data: Guild_Member_Add):
    s = self.db.sql.session()
    r = s.query(Halloween).filter(Halloween.user_id == data.user.id).first()
    if r and ROLES.get(data.guild_id, None):
        if type(r.race) is Race:
            race = r.race.name
        else:
            race = r.race
        role = ROLES.get(data.guild_id, {}).get(race, None)
        if role:
            await self.add_guild_member_role(data.guild_id, data.user.id, role, "Halloween Minigame")
