
COLOR_CHAR = ["Heart", "Diamonds", "Spades", "Clubs"] 

def color_idx_to_char(color_idx):
  """Helper function for converting color index to a character.

  Args:
    color_idx: int, index into color char vector.

  Returns:
    color_char: str, A single character representing a color.

  Raises:
    AssertionError: If index is not in range.
  """
  assert isinstance(color_idx, int)
  if color_idx == -1:
    return None
  else:
    return COLOR_CHAR[color_idx]

class RegicideCard(object):
    """Regicide card, with color and rank.

    Python implementation of RegicideCard class.
    """

    def __init__(self, color, rank):
        """A simple RegicideCard object.

        Args:
            color: an integer, starting at 0. Colors are in this order Hearts, Diamonds, Spades, Clubs
            rank: an integer, starting at 0 (representing a Ace card) In the standard
            game, the largest value is 13 (representing a King card).
            value: an integer represeting card value
        """
        self._color = color
        self._rank = rank
        self._value = self._rank + 1

    def color(self):
        return self._color

    def rank(self):
        return self._rank

    def key(self):
        return self._color * 13 + self._rank 

    def value(self):
        return self._value

    def __str__(self):
        if self.valid():
            return str(self.value()) + ' ' + COLOR_CHAR[self._color]
        else:
            return "XX"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self._color == other.color() and self._rank == other.rank()

    def valid(self):
        return self._color >= 0 and self._color <=3 and\
               self._rank >= 0 and self._rank <= 12
    
    def info(self):
        return (self.rank(), self.color())

    def to_dict(self):
        """Serialize to dict.

        Returns:
            d:dict, containing color and rank of card.
        """
        return {"color": color_idx_to_char(self.color()), "rank": self.rank()}


class RegicideEnemy(RegicideCard):
    """Regicide card, with a color and a rank.

    Python implementation of RegicideCard class.
    """

    def __init__(self, color, rank, health, attack):
        """A simple RegicideCard object.

        Args:
            color: an integer, starting at 0. Colors are in this order Hearts, Tiles, Clovers, Pikes
            rank: an integer, starting at 0 (representing a Ace card) In the standard
            game, the largest value is 13 (representing a King card).
            health: an integer, represent the enemy's health
            attack: an integer, represent the enemy's attack
        """
        super().__init__(color, rank)
        self._health = health
        self._attack = attack
        self._value = self._attack

        self._level = rank - 10 + 1

        self._enemy_encoding = (rank - 10) * 4 + color
        
    def health(self):
        return self._health

    def attack(self):
        return self._attack

    def level(self):
        return self._level

    def enemy_encoding(self):
        return self._enemy_encoding

    def reduce_attack(self, sheild):
        self._attack = max(0, self._attack - sheild)

    def reduce_health(self, attack):
        self._health = self._health - attack

    def __str__(self):
        if self.valid():
            return "E" + str(self._rank + 1) + ' ' + COLOR_CHAR[self._color] + ' H' + str(self._health) + ' A' +str(self._attack)
        else:
            return "XX"