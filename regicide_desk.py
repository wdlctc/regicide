import random
from abc import ABC
from regicide_card import RegicideCard, RegicideEnemy

class RegicideDesk(ABC):
    def __init__(self, game):
        """Creates a RegicideDesk object.

        Args:
            game: A game instance, containing information about the game configuration.
        """
        self._index = 0
        self._game = game
        self._desk = [] # Initialize an empty desk
        self._num_ranks = game.num_start_ranks() # Get the number of ranks from the game instance
        self._num_colors = game.num_colors()  # Get the number of colors from the game instance

    def card(self, index):
        """Returns the card at the given index in the desk.
        """
        return self._desk[index]

    def setup(self):
        """Sets up the desk. This method should be implemented by subclasses."""
        pass

    def empty(self):
        """Checks if the desk is empty."""
        return len(self._desk) == 0

    def dealCard(self):
        """Deals a card from the top of desk."""
        if not self.empty():
            return self._desk.pop(0)
        else:
            return None

    def placecard(self, card):
        """Places a card at the end of the desk."""
        if isinstance(card, RegicideCard):
            self._desk.append(card)
        else:
            raise AssertionError

    def insertcard(self, card):
        """Inserts a card at the beginning of the desk."""
        if isinstance(card, RegicideCard):
            self._desk.insert(0, card)
        else:
            raise AssertionError

    def __str__(self):
        return "".join([c.__str__() for c in self._desk])

    def __repr__(self):
        return str(self)

    def __len__(self): return len(self._desk)


class RegicideDrawDesk(RegicideDesk):
    def __init__(self, game):
        """Creates a RegicideDrawDesk object.

        Args:
            game: A game instance, containing information about the game configuration.
        """
        super().__init__(game)
        self._num_ranks = game.num_start_ranks()
        self._num_colors = game.num_colors()
        self.setup()
                    
    def setup(self):
        """Sets up the desk in an shuffle case"""
        for color in range(self._num_colors):
            for rank in range(self._num_ranks):
                card = RegicideCard(color, rank)
                self._desk.append(card)
                random.shuffle(self._desk)

class RegicideDisacrdDesk(RegicideDesk):
    def __init__(self, game):
        """Creates a RegicideDisacrdDesk object.

        Args:
            game: A game instance, containing information about the game configuration.
        """
        super().__init__(game)
        self._num_ranks = game.num_ranks()
        self._num_colors = game.num_colors()
        self.setup()
        
    def random_pop(self):
        random_index = random.randint(0, len(self._desk) - 1)
        random_card = self._desk.pop(random_index)
        return random_card


class RegicideEnemyDesk(RegicideDesk):
    def __init__(self, game):
        """Creates a RegicideEnemyDesk object.

        Args:
            game: A game instance, containing information about the game configuration.
        """
        super().__init__(game)
        self._num_ranks = game.num_ranks()
        self._num_colors = game.num_colors()
        self.setup()

        self.end_enemy = RegicideEnemy(0, 10, 0, 0)
                    
    def setup(self):
        """Sets up the desk in an shuffle case with health and attack setting"""
        for rank in range(10, self._num_ranks):
            health = self._game.enemy_health()[rank - 10]
            attack = self._game.enemy_attack()[rank - 10]
            tmp_desk = []
            for color in range(self._num_colors):
                enemy = RegicideEnemy(color, rank, health, attack)
                tmp_desk.append(enemy)
            random.shuffle(tmp_desk)
            self._desk += tmp_desk

    def total_health(self):
        """ return the all enemy's health"""
        return sum(list(map(lambda x: x.health(), self._desk)))

    def current_enemy(self):
        """ return the enemy from the top of desk"""
        if not self.empty():
            return self._desk[0]
        else:
            print("You win!")
            return self.end_enemy
            raise RuntimeError

    def current_enemy_health(self):
        return self.current_enemy().health()

    def current_enemy_attack(self):
        return self.current_enemy().attack()

    def current_enemy_color(self):
        return self.current_enemy().color()

    def current_enemy_rank(self):
        return self.current_enemy().rank() - 10