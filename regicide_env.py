from regicide import RegicideGame, RegicideStateType
from gym import spaces
import numpy as np
from gym.spaces import Discrete

class Environment(object):
    """Abstract Environment interface.

    All concrete implementations of an environment should derive from this
    interface and implement the method stubs.
    """

    def seed(self, seed):
        raise NotImplementedError("Not implemented in Abstract Base class")

    def reset(self, config):
        r"""Reset the environment with a new config.

        Signals environment handlers to reset and restart the environment using
        a config dict.

        Args:
          config: dict, specifying the parameters of the environment to be
            generated.

        Returns:
          observation: A dict containing the full observation state.
        """
        raise NotImplementedError("Not implemented in Abstract Base class")

    def step(self, action):
        """Take one step in the game.

        Args:
          action: dict, mapping to an action taken by an agent.

        Returns:
          observation: dict, Containing full observation state.
          reward: float, Reward obtained from taking the action.
          done: bool, Whether the game is done.
          info: dict, Optional debugging information.

        Raises:
          AssertionError: When an illegal action is provided.
        """
        raise NotImplementedError("Not implemented in Abstract Base class")

    def close(self):
        """Take one step in the game.

        Raises:
          AssertionError: abnormal close.
        """
        raise NotImplementedError("Not implemented in Abstract Base class")

class RegicideEnv(Environment):
    """RL interface to a Regicide environment.

    ```python

    environment = rl_env.make()
    config = { 'players': 5 }
    observation = environment.reset(config)
    while not done:
        # Agent takes action
        action =  ...
        # Environment take a step
        observation, reward, done, info = environment.step(action)
    ```
    """

    def __init__(self, args, seed = 42):
        """Creates an environment with the given game configuration.

        Args:
          config: dict, With parameters for the game. Config takes the following
            keys and values.
              - players: int, Number of players \in [2,4].
              - hand_size: int, Hand size \in [6,8].
              - enemy_health: list, enemy health \in [20,30,40].
              - enemy_attack: list, enemy attack \in [20,30,40].
              - yield_enable: bool, yield_enable \in [True, False].
              - maximum_combo: int, maximum_combo \in 10.
              - observation_type: int.
                0: Minimal observation.
                1: First-order common knowledge observation.
              - seed: int, Random seed.
              - random_start_player: bool, Random start player.
        """
        self._seed = seed
        self._count = 0
        if (args.regicide_name == "Regicide-Single"):
            config = {
                "players": 1,
                "hand_size": 8,
                "enemy_health": [20,30,40],
                "enemy_attack": [10,15,20],
                "yield_enable": True,
                "maximum_combo": 10,
                "seed": self._seed
            }
        elif (args.regicide_name == "Regicide-Double"):
            config = {
                "players": 2,
                "hand_size": 7,
                "enemy_health": [20,30,40],
                "enemy_attack": [10,15,20],
                "yield_enable": True,
                "maximum_combo": 10,
                "seed": self._seed
            }
        else:
            raise ValueError("Unknown environment {}".format(args.regicide_name))

        self.seed(self._seed)
        self.game = RegicideGame(config)

        self.players = self.game.num_players()
        self.action_space = []
        self.observation_space = []
        self.share_observation_space = []
        self.observation_encoder = ObservationEncoder(self.game)

        for i in range(self.players):
            self.action_space.append(Discrete(self.num_moves()))
            self.observation_space.append(
                spaces.Box(low=0, high=1, shape=(self.observation_encoder.shape() + self.players,), dtype=np.float32))
            self.share_observation_space.append(
                spaces.Box(low=0, high=1, shape=(self.observation_encoder.shape() + self.players,), dtype=np.float32))
          
    def seed(self, seed=None):
        if seed is None:
            np.random.seed(1)
        else:
            np.random.seed(seed)

    def reset(self):
        """Resets the environment for a new game.
        """
        self.state = self.game.new_initial_state()
        observation = self._make_observation_all_players()
        current_player = self.state.cur_player()
        observation["current_player"] = current_player
        player_observations = observation['player_observations']

        agent_turn = np.zeros(self.players, dtype=np.int).tolist()
        agent_turn[current_player] = 1

        available_actions = np.zeros(self.num_moves())
        available_actions[player_observations[current_player]['legal_moves_as_int']] = 1.0

        obs = player_observations[current_player]['vectorized'] + agent_turn

        share_obs = [player_observations[i]['vectorized'] for i in range(self.players)]
        concat_obs = np.concatenate(share_obs, axis=0)
        share_obs = np.concatenate((concat_obs, agent_turn), axis=0)

        return obs, share_obs, available_actions

    def step(self, action):
        """Take one step in the game.
        """
        self._count += 1
        action = int(action[0])
        if isinstance(action, int):
            # Convert dict action HanabiMove
            action = self.state.get_move(action)
            if not self.state.move_is_legal(action):
                raise ValueError("In valid move {}".format(action))
        else:
            raise RuntimeError

        # Apply the action to the state.
        last_score = self.state.enemy_desk_size()
        self.state.apply_move(action)

        observation = self._make_observation_all_players()
        current_player = self.state.cur_player()
        observation["current_player"] = current_player
        player_observations = observation['player_observations']

        available_actions = np.zeros(self.num_moves())
        available_actions[player_observations[current_player]['legal_moves_as_int']] = 1.0

        agent_turn = np.zeros(self.players, dtype=np.int).tolist()
        agent_turn[current_player] = 1

        obs = player_observations[current_player]['vectorized'] + agent_turn
        share_obs = [player_observations[i]['vectorized'] for i in range(self.players)]
        concat_obs = np.concatenate(share_obs, axis=0)
        share_obs = np.concatenate((concat_obs, agent_turn), axis=0)

        # if self.state.cur_state() == RegicideStateType.WIN:
        #     reward = 12
        # elif self.state.cur_state() == RegicideStateType.LOSS:
        #     reward = - self.state.score() 
        # else:
        #     reward = last_score - self.state.score() 
        
        reward = self.state._reward

        done = self.state.is_terminal()
        # reward = self.state.score() - last_score
        rewards = [[reward]] * self.players
        infos = {'score': self.state.score()}
        
        return obs, share_obs, reward, done, infos, available_actions

    def make_observation(self):
        observation = self._make_observation_all_players()
        current_player = self.state.cur_player()
        observation["current_player"] = current_player
        player_observations = observation['player_observations']


        agent_turn = np.zeros(self.players, dtype=np.int).tolist()
        agent_turn[current_player] = 1

        obs = player_observations[current_player]['vectorized'] + agent_turn
        share_obs = [player_observations[i]['vectorized'] for i in range(self.players)]
        
        return obs


    def _make_observation_all_players(self):
        """Make observation for all players.

        Returns:
          dict, containing observations for all players.
        """
        obs = {}
        player_observations = [ self._extract_dict_from_backend(
            player_id, self.state.observation(player_id))
            for player_id in range(self.players)
        ]
        obs["player_observations"] = player_observations
        obs["current_player"] = self.state.cur_player()

        return obs

    def show(self):
        self.state.show()
        print("self._count = ", str(self._count))

    def legal_moves(self):
        return self.state.legal_moves_as_dict()

    def _extract_dict_from_backend(self, player_id, observation):
        """Extract a dict of features from an observation from the backend.

        Args:
          player_id: Int, player from whose perspective we generate the observation.
          observation: A `pyhanabi.HanabiObservation` object.

        Returns:
          obs_dict: dict, mapping from HanabiObservation to a dict.
        """
        obs_dict = {}
        obs_dict["current_player"] = self.state.cur_player()
        obs_dict["num_players"] = self.state.num_players()
        obs_dict["deck_size"] = self.state.deck_size()
        obs_dict["enemy_deck_size"] = self.state.enemy_desk_size()
        obs_dict["discard_desk_size"] = self.state.discard_desk_size()
        obs_dict["all_hand_size"] = self.state.all_hands_size()

        obs_dict["enemy_health"] = self.state.current_enemy_health()
        obs_dict["enemy_attack"] = self.state.current_enemy_attack()
        obs_dict["enemy_color"] = self.state.current_enemy_color()
        obs_dict["damage"] = self.state._demage

        obs_dict["legal_moves"] = self.state.legal_moves_as_dict()
        obs_dict["legal_moves_as_int"] = self.state.legal_moves_as_int()

        obs_dict["observed_hands"] = self.state.player_hands()

        obs_dict["vectorized"] = self.observation_encoder.encode(self.state)

        return obs_dict

    def num_moves(self):
        """Returns the total number of moves in this game (legal or not).

        Returns:
          Integer, number of moves.
        """
        return self.game.max_moves()


class ObservationEncoder(object):
    """ObservationEncoder class.

    The canonical observations wrap an underlying C++ class. To make custom
    observation encoders, create a subclass of this base class and override
    the shape and encode methods.
    """

    def __init__(self, game):
        """Construct using HanabiState.observation(player)."""
        self._game = game

    def cardindex(self, card):
        color = card.color()
        rank = card.rank()
        cardindex = color * self._game.num_ranks() + rank
        return cardindex

    def shape(self):
        return self._game.num_cards() + \
               self._game.num_cards() + self._game.num_cards() + \
               self._game.num_colors() + self._game.enemy_ranks() + \
               self._game.enemy_size() + \
               self._game.max_enemy_health() + 1 + self._game.max_enemy_attack() + 1 + \
               self._game.max_enemy_attack() + 1 +\
               self._game.num_players() * self._game.hand_size() + 1 +\
               len(RegicideStateType.__members__.values())
               

    def encode(self, observation):
        encoding = []
        encoding += self.encodehand(observation)
        encoding += self.encodeboard(observation)

        return encoding

    def encodehand(self, observation):
        encodehand = [0 for _ in range(self._game.num_cards())]
        for i in range(len(observation.cur_player_hand())):
            card = observation.cur_player_hand().card(i)
            cardindex = self.cardindex(card)
            encodehand[cardindex] = 1
        return encodehand

    def encodeboard(self, observation):
        encodeboard = []
        remain_desk_encoding = [0 for _ in range(self._game.num_cards())]
        remain_desk_encoding[observation.deck_size()] = 1

        discard_desk_encoding = [0 for _ in range(self._game.num_cards())]
        discard_desk_encoding[observation.discard_desk_size()] = 1

        enemy_desk_encoding = [0 for _ in range(self._game.enemy_size())]
        enemy_desk_encoding = observation.enemy_encoding()

        enemy_color = [0 for _ in range(self._game.num_colors())]
        enemy_color[observation.current_enemy_color()] = 1

        enemy_rank = [0 for _ in range(self._game.enemy_ranks())]
        enemy_rank[observation.current_enemy_rank()] = 1

        enemy_health = [0 for _ in range(self._game.max_enemy_health() + 1)]
        enemy_health[observation.current_enemy_health()] = 1

        enemy_attack = [0 for _ in range(self._game.max_enemy_attack() + 1)]
        enemy_attack[observation.current_enemy_attack()] = 1

        demage = [0 for _ in range(self._game.max_enemy_attack() + 1)]
        demage[observation._demage] = 1

        state = [1 if observation.cur_state() == state_ else 0 for state_ in RegicideStateType.__members__.values()]

        hand_size = [0 for _ in range(self._game.num_players() * self._game.hand_size() + 1)]
        for i in range(self._game.num_players()):
            hand_size[i * self._game.hand_size() + observation.player_hand_size(i)] = 1

        encodeboard = remain_desk_encoding + discard_desk_encoding + enemy_desk_encoding + \
                      enemy_color + enemy_rank + enemy_health + enemy_attack + \
                      hand_size + demage + state

        return encodeboard
