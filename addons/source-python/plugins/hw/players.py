# ======================================================================
# >> IMPORTS
# ======================================================================

# Hero-Wars
from hw.database import load_player_data
from hw.database import save_player_data
from hw.database import save_hero_data

from hw.entities import Hero

from hw.tools import find_element

from hw.configs import database_path
from hw.configs import starting_heroes

# Xtend
from xtend.players import PlayerEntity

# Source.Python
from players.helpers import index_from_userid


# ======================================================================
# >> ALL DECLARATION
# ======================================================================

__all__ = (
    'player_list',
    'get_player',
    'create_player',
    'remove_player'
)


# ======================================================================
# >> GLOBALS
# ======================================================================

player_list = []


# ======================================================================
# >> FUNCTIONS
# ======================================================================

def get_player(value, key='userid'):
    """Gets a player with matching key.

    Loops through the player list and returns a player with matching
    key to the provided parameter value.

    Args:
        value: Value of the player's key to look for
        key: Key to compare the value to

    Returns:
        Player with matching key or None
    """

    return find_element(player_list, key, value)


def create_player(userid):
    """Creates a new player, fetching his data from the database.

    Creates a new player object, loads any saved data from the database
    based on SteamID, makes sure the player gets the starting heroes
    and has a current hero set. Finally returns the player after adding
    him to the global player list.

    Args:
        userid: Userid of the player to create

    Returns:
        New player who's been added to the player list
    """

    # Create a new player and load his data from the database (if any)
    player = _Player(index_from_userid(userid))
    load_player_data(database_path, player)

    # Make sure player gets the starting hero(es)
    heroes = Hero.get_subclasses()
    for cls_id in starting_heroes:
        hero_cls = find_element(heroes, 'cls_id', cls_id)
        if hero_cls and not find_element(player.heroes, 'cls_id', cls_id):
            player.heroes.append(hero_cls())

    # Make sure the player has a current hero
    if not player.hero and player.heroes:
        player.hero = player.heroes[0]

    # Add the player to the global list and return the player
    player_list.append(player)
    return player


def remove_player(player):
    """Removes a player, inserting his data into the database.

    Finds a player with given userid, saving his data into the database
    and removing him from the global player list.

    Args:
        userid: Userid of the player to remove
    """

    # Save player's data and remove him
    save_player_data(database_path, player)
    player_list.remove(player)
    del PlayerEntity._instances[player.index]


# ======================================================================
# >> CLASSES
# ======================================================================

class _Player(PlayerEntity):
    """Player class for Hero-Wars related activity.

    Player extends Source.Python's PlayerEntity, implementing player
    sided properties for Hero-Wars related information.
    Adds methods such as burn, freeze and push.

    Attributes:
        gold: Player's Hero-Wars gold, used to purchase heroes and items
        hero: Player's hero currently in use
        heroes: List of owned heroes
        lang_key: Language key used to display messages and menus
    """

    def __init__(self, index):
        """Creates a new Hero-Wars player.

        Args:
            index: Player's index
        """

        self._gold = 0
        self._hero = None
        self.heroes = []

    @property
    def gold(self):
        """Getter for player's Hero-Wars gold.

        Returns:
            Player's gold
        """

        return self._gold

    @gold.setter
    def gold(self, gold):
        """Setter for player's Hero-Wars gold.

        Raises:
            ValueError: If gold is set to a negative value
        """

        if gold < 0:
            raise ValueError('Attempt to set negative gold for a player.')
        self._gold = gold

    @property
    def hero(self):
        """Getter for player's current hero.

        Returns:
            Player's hero
        """

        return self._hero

    @hero.setter
    def hero(self, hero):
        """Setter for player's current hero.

        Makes sure player owns the hero and saves his current hero to
        the database before switching to the new one.

        Args:
            hero: Hero to switch to

        Raises:
            ValueError: Hero not owned by the player
        """

        # Make sure player owns the hero
        if hero not in self.heroes:
            raise ValueError('Hero {cls_id} not owned by {steamid}.'.format(
                cls_id=hero.cls_id, steamid=self.steamid
            ))

        # If player has a current hero
        if self.hero:

            # Save current hero's data
            save_hero_data(database_path, self.steamid, self.hero)

            # Destroy current hero's items
            for item in self.hero.items:
                if not item.permanent:
                    self.hero.items.remove(item)

        # Change to the new hero
        self._hero = hero

    @property
    def cs_team(self):
        """Returns player's Counter-Strike team."""

        return ['un', 'spec', 't', 'ct'][self.team]

    @cs_team.setter
    def cs_team(self, value):
        """Sets player's Counter-Strike team."""

        self.team = ['un', 'spec', 't', 'ct'].index(value)
