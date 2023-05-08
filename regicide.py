# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Python interface to regicide code."""
import os
import math
import enum

from regicide_desk import RegicideDisacrdDesk, RegicideDrawDesk, RegicideEnemyDesk
from regicide_hand import RegicideHand
from regicide_move import RegicideMoveType, RegicideMove, RegicideMoveGenerator

COMBO_LIST = [1, 4, 6, 4, 1]
# COMBO_LIST_color = [[], \
#                     [0], [1], [2], [3], \
#                     [0,1], [0,2], [0,3], [1, 2], [1, 3], [2, 3],
#                     [0,1,2], [0,1,3], [0,2,3], [1,2,3],
#                     [0,1,2,3]]

class RegicideStateType(enum.IntEnum):
    """Move types."""
    INVALID = 0
    PLAY = 1
    DISCARD = 2
    WIN = 3
    LOSS = 4

class RegicideState(object):
    """Current environment state for an active Regicide game.

    The game is turn-based, with only one active agent at a time. Chance events
    are explicitly included, so the active agent may be "nature" (represented
    by cur_player() returning CHANCE_PLAYER_ID).
    """

    def __init__(self, game):
        self._game = game
        self._desk = RegicideDrawDesk(game)
        self._discard_desk = RegicideDisacrdDesk(game)
        self._enemy_desk = RegicideEnemyDesk(game)
        self._hands = [RegicideHand(game, self._desk, self._discard_desk) 
                       for _ in range(game.num_players())]
        for hand in self._hands:
            hand.sort()
        self._RegicideMoveGenerator = RegicideMoveGenerator(self._game.num_colors(), self._game.num_ranks())

        self._cur_player = 0
        self._demage = 0
        self._cur_state = RegicideStateType.PLAY
        self._num_players = game.num_players()
        self._moves = self.all_moves()
        self._maximum_score = self._enemy_desk.total_health()
        self._enemy_encoding = [1 for _ in range(self._game.enemy_size())]
        self._reward = 0

    def is_terminal(self):
        """Returns false if game is still active, true otherwise."""
        return self._cur_state == RegicideStateType.WIN or self._cur_state == RegicideStateType.LOSS

    def is_win(self):
        """Returns false if game is still active, true otherwise."""
        return self._cur_state == RegicideStateType.WIN 

    def observation(self, player):
        """Returns player's observed view of current environment state."""
        return None#HanabiObservation(self._state, self._game, player)

    def cur_state(self):
        return self._cur_state

    def cur_player(self):
        """Returns index of next player to act.

        Index will be CHANCE_PLAYER_ID if a chance event needs to be resolved.
        """
        return self._cur_player

    def deck_size(self):
        """Returns number of cards left in the deck."""
        return len(self._desk)
   
    def enemy_desk_size(self):
        """Returns number of cards left in the deck."""
        return len(self._enemy_desk)

    def discard_desk_size(self):
        """Returns number of cards left in the deck."""
        return len(self._discard_desk)

    def discard_size(self):
        """Returns a list of all discarded cards, in order they were discarded."""
        return len(self._discard_desk)

    def current_enemy_health(self):
        return self._enemy_desk.current_enemy_health()

    def current_enemy_attack(self):
        return self._enemy_desk.current_enemy_attack()

    def current_enemy_color(self):
        return self._enemy_desk.current_enemy_color()

    def current_enemy_rank(self):
        return self._enemy_desk.current_enemy_rank()

    def current_enemy(self):
        return self._enemy_desk.current_enemy()

    def player_hand_size(self, index):
        return len(self._hands[index])

    def all_hands_size(self):
        return [len(self._hands[i]) for i in range(self.num_players())]

    def cur_player_hand_size(self):
        return len(self.cur_player_hand())

    def cur_player_hand(self):
        return self._hands[self._cur_player]

    def enemy_encoding(self):
        return self._enemy_encoding

    def player_hands(self):
        """Returns a list of all hands, with cards ordered oldest to newest."""
        hand_list = []
        for player in range(self.num_players()):
            player_hand = self._hands[self._cur_player]
            for i in range(len(player_hand)):
                card = player_hand.card(i)
                hand_list.append(card.to_dict())
        return hand_list

    def player_hands_full(self):
        for hand in self._hands:
            if not hand.full():
                return False
        return True

    def end_of_game_status(self):
        """Returns the end of game status, NOT_FINISHED if game is still active."""
        return None

    def get_move(self, move_id):
        move = self._RegicideMoveGenerator.generate(move_id)
        # move = RegicideMove(move_id, self._game.hand_size())
        return move
    
    def apply_move(self, move):
        assert self.move_is_legal(move)
        self._reward = 0
        if move.type() == RegicideMoveType.PLAY:

            card = self.cur_player_hand().pop_card_in_hand(move.info())
            color_list = [False for _ in range(self._game.num_colors())]
            color = card.color()
            color_list[color] = True
            value = card.value()
            self.apply_to_enemy(color_list, value)
            self._discard_desk.placecard(card)
        elif move.type() == RegicideMoveType.DISCARD:
            
            card = self.cur_player_hand().pop_card_in_hand(move.info())
            value = card.value()
            self._demage -= value
            self._discard_desk.placecard(card)
            if self._demage <= 0:
                self._demage = 0
                self._cur_state = RegicideStateType.PLAY
        elif move.type() == RegicideMoveType.ACE:
            combo_list = []
            card_list = []
            color_list = [False for _ in range(self._game.num_colors())]
            value = 0
            
            card = self.cur_player_hand().pop_card_in_hand(move.ace_info())
            card_list.append(card)

            card = self.cur_player_hand().pop_card_in_hand(move.info())
            card_list.append(card)
            for card in card_list:
                value += card.value()
                color_list[card.color()] = True
            self.apply_to_enemy(color_list, value)
            for card in card_list:
                self._discard_desk.placecard(card)
        elif move.type() == RegicideMoveType.COMBO:
            combo_list = move.combo_list()
            card_list = []
            value = 0
            color_list = [False for _ in range(self._game.num_colors())]
            for v, c in combo_list:
                card = self.cur_player_hand().pop_card_in_hand((v, c))
                card_list.append(card)
                value += card.value()
                color_list[card.color()] = True
            self.apply_to_enemy(color_list, value)
            for card in card_list:
                self._discard_desk.placecard(card)
            
        self.cur_player_hand().sort()
        if self.cur_player_hand_size() == 0 and not self._enemy_desk.empty():
            self._cur_state = RegicideStateType.LOSS
            self._reward -= self.score()

    def apply_to_enemy(self, color_list, value):
        enemy = self.current_enemy()
        attack = value
        for i in range(self._game.num_colors()):
            if color_list[i] and i != enemy.color():
                if i == 0:
                    # Heart
                    self.apply_heart_effect(value)
                elif i == 1:
                    # diamonds 
                    self.apply_diamonds_effect(value)
                elif i == 2:
                    # spades 
                    self.apply_spades_effect(value)
                elif i == 3:
                    # clubs 
                    attack = self.apply_clubs_effect(value)
                else:
                    raise RuntimeError
            if color_list[i] and i == enemy.color():
                self._reward -= value / 20
        self.apply_attack_enemy(attack)

    def apply_heart_effect(self, value):
        count = 0
        for _ in range(value):
            if self._discard_desk.empty():
                self._reward += count / 20
                return
            else:
                count += 1
                card = self._discard_desk.random_pop()
                self._desk.placecard(card)

    def apply_diamonds_effect(self, value):
        draw_player = self.cur_player()
        count = 0
        for _ in range(value):
            if self.player_hands_full():
                self._reward += count / 20
                return
            else:
                count += 1
                while(self._hands[draw_player].full()):
                    draw_player = (draw_player + 1) % self.num_players()
                self._hands[draw_player].drawcard()
                draw_player = (draw_player + 1) % self.num_players()

    def apply_spades_effect(self, value):
        enemy = self.current_enemy()
        self._reward += min(enemy.attack(), value) / 20
        enemy.reduce_attack(value)

    def apply_clubs_effect(self, value):
        self._reward += min(self.current_enemy().health() - value, value) / 20
        return value * 2

    def apply_attack_enemy(self, attach):
        enemy = self.current_enemy()
        enemy.reduce_health(attach)
        if enemy.health() <= 0:
            self._enemy_desk.dealCard()
            if enemy.health() == 0:
                self._desk.insertcard(enemy)
                self._enemy_encoding[enemy.enemy_encoding()] = 0
                # print(self._reward)
                self._reward += 1 
                self._reward += enemy._value / 100
            else:
                self._discard_desk.placecard(enemy)
                self._enemy_encoding[enemy.enemy_encoding()] = 0
                self._reward += 1 
            if self._enemy_desk.empty():
                self._cur_state = RegicideStateType.WIN
                self._reward = 12
        elif enemy.attack() != 0:
            self._cur_state = RegicideStateType.DISCARD
            self._demage = enemy.attack()

    def all_moves(self):
        moves = []
        max_moves = self._game.max_moves()
        for move_id in range(max_moves):
            move = self._RegicideMoveGenerator.generate(move_id)
            moves.append(move)
        return moves

    def legal_moves(self):
        """Returns list of legal moves for currently acting player."""
        legal_moves = []
        for move in self._moves:
            if self.move_is_legal(move):
                legal_moves.append(move)
        return legal_moves
    
    def legal_moves_as_dict(self):
        return list(map(lambda x: x.to_dict(), self.legal_moves()))

    def legal_moves_as_int(self):
        return list(map(lambda x: x.move(), self.legal_moves()))

    def move_is_legal(self, move):
        """Returns true if and only if move is legal for active agent."""
        if move.type() == RegicideMoveType.PLAY:
            card_info = move.info()#(move.rank(), move.color())
            if not self.cur_player_hand().card_in_hand(card_info):
                return False
            if (self.cur_state() == RegicideStateType.PLAY):
                return True
            else:
                return False
        elif move.type() == RegicideMoveType.DISCARD:
            card_info = move.info()
            if not self.cur_player_hand().card_in_hand(card_info):
                return False
            if (self.cur_state() == RegicideStateType.DISCARD):
                return True
            else:
                return False
        elif move.type() == RegicideMoveType.ACE:
            ace_card_info = move.ace_info()
            card_info = move.info()
            if ace_card_info == card_info:
                return False
            if not self.cur_player_hand().card_in_hand(ace_card_info):
                return False
            if not self.cur_player_hand().card_in_hand(card_info):
                return False
            if self.cur_state() == RegicideStateType.PLAY:
                return True
            else:
                return False
        elif move.type() == RegicideMoveType.COMBO:
            combo_list = move.combo_list()
            for combo in combo_list:
                if not self.cur_player_hand().card_in_hand(combo):
                    return False
            if self.cur_state() == RegicideStateType.PLAY:
                return True
            else:
                return False
        else:
            return False

    def num_players(self):
        """Returns the number of players in the game."""
        return self._num_players

    def reward(self):
        return self.reward

    def score(self):
        """Returns the co-operative game score at a terminal state."""
        # return self._maximum_score - self._enemy_desk.total_health()
        return self.enemy_desk_size()

    def hand_score(self):
        """Returns the co-operative game score at a terminal state."""
        # return self._maximum_score - self._enemy_desk.total_health()
        return self.cur_player_hand().total_value()

    def move_history(self):
        """Returns list of moves made, from oldest to most recent."""
        return None

    def show(self):
        print("-------------------------------------------")
        print("current_player_id: %d" % (self.cur_player()))
        print("cur_player_hand:   %s" % (self.cur_player_hand()))
        print("current_enemy:     %s" % (self.current_enemy()))
        print("deck_size:         %d" % (self.deck_size()))
        print("discard_desk_size: %d" % (self.discard_desk_size()))
        print("enemy_desk_size:   %d" % (self.enemy_desk_size()))
        print("current_enemy:     %s" % (self.enemy_desk_size()))
        print("cur_state:         %s" % (self.cur_state()))
        print("enemy_encoding:    " + str(self.enemy_encoding()))
        if self.cur_state() == RegicideStateType.DISCARD:
            print("damage take:       %d" % (self._demage))
        # obs_dict["current_player"] = self.state.cur_player()
        # obs_dict["num_players"] = self.state.num_players()
        # obs_dict["deck_size"] = self.state.deck_size()
        # obs_dict["enemy_deck_size"] = self.state.enemy_desk_size()
        # obs_dict["discard_desk_size"] = self.state.discard_desk_size()
        # obs_dict["all_hand_size"] = self.state.all_hands_size()

        # obs_dict["enemy_health"] = self.state.current_enemy_health()
        # obs_dict["enemy_attack"] = self.state.current_enemy_attack()
        # obs_dict["enemy_color"] = self.state.current_enemy_color()

        # obs_dict["legal_moves"] = self.state.legal_moves_as_dict()
        # obs_dict["legal_moves_as_int"] = self.state.legal_moves_as_int()

        # obs_dict["observed_hands"] = self.state.player_hands()

        # obs_dict["vectorized"] = self.observation_encoder.encode(self.state)


class RegicideGame(object):
    """Game parameters describing a specific instance of Regicide.
    """

    def __init__(self, params = None):
        """Creates a RegicideGame object.

        Args:
            params: is a dictionary of parameters and their values.
        """

        self._params = params
        self._num_players = params['players']
        self._hand_size = params['hand_size']
        self._enemy_health = params['enemy_health']
        self._enemy_attack = params['enemy_attack']
        self._yield_enable = params['yield_enable']
        self._maximum_combo = params['maximum_combo']
        self._seed = params['seed']

        self._max_move = self.max_discard_moves() + self.max_play_moves() + \
                         self.max_combo_moves() + self.max_ace_moves()

    def setup(self):
        return

    def new_initial_state(self):
        return RegicideState(self)
        
    def __del__(self):
        del self

    def num_players(self):
        """Returns the number of players in the game."""
        return self._num_players

    def hand_size(self):
        """Returns the maximum number of cards in each player hand.
        
        The number of cards in a player's hand may be smaller than this maximum
        a) at the beginning of the game before cards are dealt out, b) after
        any Play or Discard action and before the subsequent deal event, and c)
        after the deck is empty and cards can no longer be dealt to a player.
        """
        return self._hand_size

    def enemy_health(self):
        """Returns the enemy health modifier in the game."""
        return self._enemy_health

    def max_enemy_health(self):
        return max(self._enemy_health)

    def enemy_attack(self):
        """Returns the enemy attack modifier in the game."""
        return self._enemy_attack

    def max_enemy_attack(self):
        return max(self._enemy_attack)

    def yield_enable(self):
        """Returns whether the yield option is enable in the game."""
        return self._yield_enable

    def yield_enable(self):
        """Returns the Maximum combo limit in the game."""
        return self._maximum_combo

    def num_cards(self):
        """Returns number of instances of Card(color, rank) in the initial deck."""
        return self.num_colors() * self.num_ranks()

    def num_colors(self):
        """Returns number of instances of Card(color, rank) in the initial deck."""
        return 4

    def num_start_ranks(self):
        """Returns number of instances of Card(color, rank) in the initial deck."""
        return 10

    def num_ranks(self):
        """Returns number of instances of Card(color, rank) in the initial deck."""
        return 13

    def enemy_ranks(self):
        """Returns number of instances of Card(color, rank) in the initial deck."""
        return 3

    # TODO
    def max_moves(self):
        """Returns the number of possible legal moves in the game."""
        return self._max_move

    def max_discard_moves(self):
        return self.num_cards()

    def max_play_moves(self):
        return self.num_cards()

    def max_combo_moves(self):
        max_combo_moves = 0
        self._combo_list = []
        for i in range(2, self._maximum_combo // 2 + 1):
            for j in range(2, 5):
                if i * j <= self._maximum_combo:
                    max_combo_moves += COMBO_LIST[j]
        return max_combo_moves

    def max_ace_moves(self):
        return self.num_cards() * 4

    def enemy_size(self):
        return 12

    def get_move_uid(self, move):
        """Returns a unique ID describing a legal move, or -1 for invalid move."""
        return None

    def get_move(self, move_uid):
        return None

class RegicideObservation(object):
    """Player's observed view of an environment RegicideState.

    The main differences are that 1) aother players' own cards are not visible, and
    2) a player does not know their own player index (seat) so that all player
    indices are described relative to the observing player (or equivalently,
    that from the player's point of view, they are always player index 0).
    """

    def __init__(self, state, game, player):
        """Construct using RegicideState.observation(player)."""
        self._observation = state.observation()

    def observation(self):
        """Returns the RegicideObservation object."""
        return self._observation

    

config = {
    "players": 1,
    "hand_size": 8,
    "enemy_health": [20,30,40],
    "enemy_attack": [10,15,20],
    "yield_enable": True,
    "maximum_combo": 10,
    "seed": 42
}

RegicideGame(config)


