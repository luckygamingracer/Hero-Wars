# ======================================================================
# >> IMPORTS
# ======================================================================

# Hero-Wars
from hw.entities import Hero

from hw.tools import find_element

# Python
import sqlite3


# ======================================================================
# >> ALL DECLARATION
# ======================================================================

__all__ = (
    'setup_database',
    'load_player_data',
    'save_player_data',
    'save_hero_data',
    'load_hero_data'
)


# ======================================================================
# >> FUNCTIONS
# ======================================================================

def setup_database(database_file):
    """Creates the HW tables into the database if they don't exist.

    Args:
        database_file: Path to the database file
    """

    with sqlite3.connect(database_file) as connection:
        cursor = connection.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS players (
            steamid TEXT PRIMARY KEY,
            gold INTEGER,
            hero_cls_id TEXT
        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS heroes (
            steamid TEXT,
            cls_id TEXT,
            level INTEGER,
            exp INTEGER,
            PRIMARY KEY (steamid, cls_id)
        )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS skills (
            steamid TEXT,
            hero_cls_id TEXT,
            cls_id TEXT,
            level INTEGER,
            PRIMARY KEY (steamid, hero_cls_id, cls_id)
        )""")


def save_player_data(database_file, player):
    """Saves player's data into the database.

    Args:
        database_file: Path to the database file
        player: Player whose data to save
    """

    with sqlite3.connect(database_file) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO players VALUES (?, ?, ?)",
            (player.steamid, player.gold, player.hero.cls_id)
        )
    save_hero_data(database_file, player.steamid, player.hero)


def save_hero_data(database_file, steamid, hero):
    """Saves hero's data into the database.

    Args:
        database_file: Path to the database file
        steamid: Steamid of the hero's owner
        hero: Hero whose data to save
    """

    with sqlite3.connect(database_file) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO heroes VALUES (?, ?, ?, ?)",
            (steamid, hero.cls_id, hero.level, hero.exp)
        )
        for skill in hero.skills:
            cursor.execute(
                "INSERT OR REPLACE INTO skills VALUES (?, ?, ?, ?)",
                (steamid, hero.cls_id, skill.cls_id, skill.level)
            )


def load_player_data(database_file, player):
    """Loads player's data from the database.

    Args:
        database_file: Path to the database file
        player: Player whose data to load
    """

    heroes = Hero.get_subclasses()
    with sqlite3.connect(database_file) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT gold, hero_cls_id FROM players WHERE steamid=?",
            (player.steamid, )
        )
        gold, current_hero_cls_id = cursor.fetchone() or (0, None)
        player.gold = gold

        # Load player's heroes
        cursor.execute(
            "SELECT cls_id, level, exp FROM heroes WHERE steamid=?",
            (player.steamid, )
        )
        for cls_id, level, exp in cursor.fetchall():
            hero_cls = find_element(heroes, 'cls_id', cls_id)
            if hero_cls:
                hero = hero_cls(level, exp)
                load_hero_data(database_file, player.steamid, hero)
                player.heroes.append(hero)
                if cls_id == current_hero_cls_id:
                    player.hero = hero


def load_hero_data(database_file, steamid, hero):
    """Loads hero's data from the database.

    Args:
        database_file: Path to the database file
        steamid: Steamid of the hero's owner
        hero: Hero whose data to load
    """

    with sqlite3.connect(database_file) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT level, exp FROM heroes WHERE steamid=? AND cls_id=?",
            (steamid, hero.cls_id)
        )
        level, exp = cursor.fetchone() or (0, 0)
        if level > hero.max_level:
            hero.level = hero.max._level
        else:
            hero.level = level
        hero.exp = exp

        # Load hero's skills
        for skill in hero.skills:
            cursor.execute(
                "SELECT level FROM skills "
                "WHERE steamid=? AND hero_cls_id=? AND cls_id=?",
                (steamid, hero.cls_id, skill.cls_id)
            )
            data = cursor.fetchone()
            if data:
                skill.level = data[0]
