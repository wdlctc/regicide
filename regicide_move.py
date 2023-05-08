import enum

class RegicideMoveType(enum.IntEnum):
    """Move types."""
    INVALID = 0
    PLAY = 1
    DISCARD = 2
    ACE = 3
    COMBO = 4

class RegicideMoveGenerator(object):

    def __init__(self, num_colors, num_ranks):
        self._num_colors = num_colors 
        self._num_ranks = num_ranks
        self._num_cards = num_colors * num_ranks
    
    def generate(self, move):
        if move < self._num_cards:
            color = move // self._num_ranks
            rank  = move % self._num_ranks
            return RegicideMovePlay(move, color, rank)
        elif move >= self._num_cards and move < self._num_cards * 2:
            color = (move % self._num_cards) // self._num_ranks  
            rank  = move % self._num_ranks
            return RegicideMoveDiscard(move, color, rank)
        elif move >= self._num_cards * 2 and move < self._num_cards * 6:
            ace = move  // self._num_cards - 2
            color = (move % self._num_cards) // self._num_ranks  
            rank  = move % self._num_ranks
            return RegicideMoveAce(move, ace, color, rank)
        elif move >= self._num_cards * 6:
            return RegicideMoveCombo(move, move - self._num_cards * 6)

class RegicideMove(object):
    """Description of an agent move or chance event.

    Python wrapper of C++ HanabiMove class.
    """

    def __init__(self, move):
        assert move is not None
        self._move_type = RegicideMoveType.INVALID

        self._move = move
        self._color = None
        self._rank = None

    def move(self):
        return self._move

    def rank(self):
        return self._rank

    def color(self):
        return self._color

    def type(self):
        return self._move_type

    def info(self):
        return (self._rank, self.color())

    def to_dict(self):
        """Serialize to dict.

        Returns:
        d: dict, Containing type and information of a hanabi move.

        Raises:
        ValueError: If move type is not supported.
        """
        move_dict = {}
        move_type = self.type()
        move_dict["action_type"] = move_type.name
        move_dict["move"] = self._move
        move_dict["color"] = self._color
        move_dict["rank"] = self._rank + 1

        return move_dict

    def __str__(self):
        return str(self.type()) + '.' + str(self.move())

    def __repr__(self):
        return self.__str__()

class RegicideMovePlay(RegicideMove):
    """Description of an agent move or chance event.

    Python wrapper of C++ HanabiMove class.
    """

    def __init__(self, move, color, rank):
        super().__init__(move)
        self._move_type = RegicideMoveType.PLAY
        
        self._color = color
        self._rank = rank

    # def card_index(self):
    #     """Returns 0-based card index for PLAY and DISCARD moves."""
    #     return self.rank()

class RegicideMoveDiscard(RegicideMove):
    """Description of an agent move or chance event.

    Python wrapper of C++ HanabiMove class.
    """

    def __init__(self, move, color, rank):
        super().__init__(move)
        self._move_type = RegicideMoveType.DISCARD

        self._color = color
        self._rank = rank

    # def discard_index(self):
    #     """Returns target player offset for REVEAL_XYZ moves."""
    #     return self.rank()

class RegicideMoveAce(RegicideMove):
    """Description of an agent move or chance event.

    Python wrapper of C++ HanabiMove class.
    """

    def __init__(self, move, ace, color, rank):
        super().__init__(move)
        self._move_type = RegicideMoveType.ACE
        
        self._ace = ace
        self._color = color
        self._rank = rank

    def ace_info(self):
        return (0, self._ace)

    def ace(self):
        return self._ace

    # def ace_index(self):
    #     """Returns target player offset for REVEAL_XYZ moves."""
    #     return self.rank()

    def to_dict(self):
        """Serialize to dict.

        Returns:
        d: dict, Containing type and information of a hanabi move.

        Raises:
        ValueError: If move type is not supported.
        """
        move_dict = {}
        move_type = self.type()
        move_dict["action_type"] = move_type.name
        
        move_dict["move"] = self._move
        move_dict["ace"] = self._ace
        move_dict["color"] = self._color
        move_dict["rank"] = self._rank + 1

        return move_dict

PLAY_LIST_ranks = [
    [(2,0),(2,1)], [(2,0),(2,2)], [(2,0),(2,3)], \
    [(2,1),(2,2)], [(2,1),(2,3)], [(2,2),(2,3)], \
    [(2,0),(2,1),(2,2)], [(2,0),(2,1),(2,3)], \
    [(2,0),(2,2),(2,3)], [(2,1),(2,2),(2,3)], \
    [(2,0),(2,1),(2,2),(2,3)], \
    [(3,0),(3,1)], [(3,0),(3,2)], [(3,0),(3,3)], \
    [(3,1),(3,2)], [(3,1),(3,3)], [(3,2),(3,3)], \
    [(3,0),(3,1),(3,2)], [(3,0),(3,1),(3,3)], \
    [(3,0),(3,2),(3,3)], [(3,1),(3,2),(3,3)], \
    [(4,0),(4,1)], [(4,0),(4,2)], [(4,0),(4,3)], \
    [(4,1),(4,2)], [(4,1),(4,3)], [(4,2),(4,3)], \
    [(5,0),(5,1)], [(5,0),(5,2)], [(5,0),(5,3)], \
    [(5,1),(5,2)], [(5,1),(5,3)], [(5,2),(5,3)]]


COMBO_LIST_ranks = [
    [(1,0),(1,1)], [(1,0),(1,2)], [(1,0),(1,3)], \
    [(1,1),(1,2)], [(1,1),(1,3)], [(1,2),(1,3)], \
    [(1,0),(1,1),(1,2)], [(1,0),(1,1),(1,3)], \
    [(1,0),(1,2),(1,3)], [(1,1),(1,2),(1,3)], \
    [(1,0),(1,1),(1,2),(1,3)], \
    [(2,0),(2,1)], [(2,0),(2,2)], [(2,0),(2,3)], \
    [(2,1),(2,2)], [(2,1),(2,3)], [(2,2),(2,3)], \
    [(2,0),(2,1),(2,2)], [(2,0),(2,1),(2,3)], \
    [(2,0),(2,2),(2,3)], [(2,1),(2,2),(2,3)], \
    [(3,0),(3,1)], [(3,0),(3,2)], [(3,0),(3,3)], \
    [(3,1),(3,2)], [(3,1),(3,3)], [(3,2),(3,3)], \
    [(4,0),(4,1)], [(4,0),(4,2)], [(4,0),(4,3)], \
    [(4,1),(4,2)], [(4,1),(4,3)], [(4,2),(4,3)]]

class RegicideMoveCombo(RegicideMove):
    """Description of an agent move or chance event.

    Python wrapper of C++ HanabiMove class.
    """

    def __init__(self, move, value):
        super().__init__(move)
        self._move_type = RegicideMoveType.COMBO
        self._value = value
        self._combo_list = COMBO_LIST_ranks[self._value]
        self._play_list = PLAY_LIST_ranks[self._value]

    # def combo_index(self):
    #     """Returns target player offset for REVEAL_XYZ moves."""
    #     return self.self._value
    
    def combo_list(self):
        return self._combo_list
        
    def to_dict(self):
        """Serialize to dict.

        Returns:
        d: dict, Containing type and information of a hanabi move.

        Raises:
        ValueError: If move type is not supported.
        """
        move_dict = {}
        move_type = self.type()
        move_dict["action_type"] = move_type.name
        move_dict["move"] = self._move
        move_dict["combo_list"] = self._play_list

        return move_dict