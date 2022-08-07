from datetime import datetime, timedelta, timezone

import sqlalchemy as sa
import sqlalchemy.orm as orm
from MFramework import Context, Groups, register
from mlib.database import Base


class Gladiator_History(Base):
    id: int = sa.Column(sa.Integer, primary_key=True)
    user_id: int = sa.Column(sa.ForeignKey("Gladiator.id"))
    boss_id: int = sa.Column(sa.ForeignKey("Gladiator_Boss.id"))
    damage: int = sa.Column(sa.Integer, default=1)
    timestamp: datetime = sa.Column(sa.TIMESTAMP(True), server_default=sa.func.now())


class Gladiator(Base):
    id: int = sa.Column(sa.BigInteger, primary_key=True)
    bonus: int = sa.Column(sa.Integer, default=0)
    history: list[Gladiator_History] = orm.relationship("Gladiator_History")


class Cooldown(Exception):
    pass


class Gladiator_Boss(Base):
    id: int = sa.Column(sa.Integer, primary_key=True)
    health: int = sa.Column(sa.Integer, nullable=False)
    name: str = sa.Column(sa.String, nullable=False)
    start_at: datetime = sa.Column(sa.TIMESTAMP(True), server_default=sa.func.now())
    ends_at: datetime = sa.Column(sa.TIMESTAMP(True), nullable=False)

    def attack(self, session, user_id: int):
        player = Gladiator.by_id(session, user_id)
        if not player:
            player = Gladiator(id=user_id, bonus=0)
            session.add(player)

        if player.history:
            remaining_cooldown = timedelta(minutes=30) - (datetime.now(tz=timezone.utc) - player.history[-1].timestamp)
        else:
            remaining_cooldown = timedelta()
        if remaining_cooldown.total_seconds() > 0:
            raise Cooldown(f"Cooldown remaining: {remaining_cooldown}")

        dmg = 1 + player.bonus
        dmg = dmg if dmg <= self.health else self.health
        self.health -= dmg
        session.add(Gladiator_History(user_id=player.id, boss_id=self.id, damage=dmg))

        return dmg


@register(group=Groups.GLOBAL)
async def arena(ctx: Context):
    """
    Description to use with help command
    Params
    ------
    parameter:
        description
    """
    pass


@register(group=Groups.ADMIN, main=arena)
async def create(ctx: Context, name: str, health: int, duration: timedelta):
    """
    Create new boss
    Params
    ------
    name:
        Name of the boss
    """
    s = ctx.db.sql.session()

    if Gladiator_Boss.by_name(s, name):
        return "Boss already exists"

    s.add(Gladiator_Boss(name=name, health=health, ends_at=ctx.data.id.as_date.astimezone(timezone.utc) + duration))
    s.commit()

    return "Success"


def get_boss(session, ctx: Context, name: str = None):
    if not name:
        boss = (
            session.query(Gladiator_Boss)
            .filter(Gladiator_Boss.ends_at >= ctx.data.id.as_date.astimezone(timezone.utc))
            .filter(Gladiator_Boss.health > 0)
            .first()
        )
    else:
        boss = Gladiator_Boss.by_name(session, name)
        if not boss:
            raise Exception("Couldn't find provided boss")
    return boss


@register(group=Groups.GLOBAL, main=arena)
async def check(ctx: Context, name: str = None):
    """
    Checks remaining boss's health
    Params
    ------
    name:
        Name of the boss to check
    """
    session = ctx.db.sql.session()

    boss = get_boss(session, ctx, name)

    return boss.health


@register(group=Groups.GLOBAL, main=arena)
async def attack(ctx: Context, name: str = None, user_id: int = None, *, session=None):
    """
    Attacks boss
    Params
    ------
    name:
        Boss to attack
    """
    if not session:
        session = ctx.db.sql.session()

    boss = get_boss(session, ctx, name)
    if ctx.data.id.as_date.astimezone(timezone.utc) > boss.ends_at:
        return "Boss is not available anymore!"
    elif boss.health <= 0:
        return "Boss has already been slain!"

    dmg = boss.attack(session, user_id or ctx.user_id)
    session.commit()

    return f"Dealt {dmg} to {boss.name}"


@register(group=Groups.MODERATOR, main=arena)
async def bonus(ctx: Context, bonus: int, user_id: int = None, *, session=None):
    """
    Adds damage bonus
    Params
    ------
    bonus:
        bonus to add
    """
    if not session:
        session = ctx.db.sql.session()

    player = Gladiator.by_id(session, user_id or ctx.user_id)

    if not player:
        player = Gladiator(id=user_id or ctx.user_id, bonus=0)
        session.add(player)

    player.bonus += bonus
    session.commit()

    return player.bonus
