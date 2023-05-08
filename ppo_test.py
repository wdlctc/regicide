import gym
from gym import spaces
import numpy as np
import torch


from sb3_contrib.common.maskable.policies import MaskableActorCriticPolicy
from sb3_contrib.common.wrappers import ActionMasker
from sb3_contrib.ppo_mask import MaskablePPO
from sb3_contrib.common.maskable.utils import get_action_masks


from ppo_mask_recurrent import RecurrentMaskablePPO
from common.evaluation import evaluate_policy

# Import Hanabi environment
from regicide_env import RegicideEnv
from regicide import RegicideGame
from regicide_desk import RegicideDisacrdDesk, RegicideDrawDesk, RegicideEnemyDesk
from regicide_hand import RegicideHand
import unittest
import argparse
parser = argparse.ArgumentParser(description='PyTorch ImageNet Example',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--regicide_name', default="Regicide-Single")
args = parser.parse_args()

class RegicideCustomEnv(gym.Env):
    def __init__(self, args):
        self.env = RegicideEnv(args, seed = 1000)
        self.action_space = spaces.Discrete(self.env.num_moves())
        self.possible_actions = np.arange(self.action_space.n)
        self.invalid_actions = []
        self.observation_space = self.env.observation_space[0]

    def reset(self):
        obs, share_obs, available_actions = self.env.reset()
        return obs

    def step(self, action):

        legal_moves = self.env.state.legal_moves()
        legal_moves_as_int = self.env.state.legal_moves_as_int()
        # print(legal_moves)
        # for move in legal_moves:
        #     legal_moves_as_int.append(self.env.game.get_move_uid(move))
        # print(legal_moves_as_int, action, legal_moves)
        if action in legal_moves_as_int:
            # observation, reward, done, info = self.env.step([int(action)])
            observation, share_obs, reward, done, info, available_actions = \
                self.env.step([int(action)])
            # print(observation, reward, done, info)
            return observation, reward, done, info
        else:
            observation = self.env.make_observation()
            return observation, -1, False, {}

    def action_masks(self):
        legal_moves = self.env.state.legal_moves()
        legal_moves_as_int = self.env.state.legal_moves_as_int()
        return [action in legal_moves_as_int for action in self.possible_actions]

    def render(self, mode='human'):
        self.env.render(mode=mode)

    def close(self):
        self.env.close()
        
env = RegicideCustomEnv(args)

# Load the trained model
model = RecurrentMaskablePPO.load("./saved_models/5000000")

# Test the trained model
obs = env.reset()
for _ in range(1000000):
    # Retrieve current action mask
    action_masks = get_action_masks(env)
    # print(action_masks)
    action, _states = model.predict(obs, action_masks=action_masks)
    # print(action)
    # env.env.show()
    obs, rewards, dones, info = env.step(action)
    # if dones == True:
    # print(rewards, dones)
    # env.render()
    if dones:
        env.env.show()
        print(rewards, dones)
        obs = env.reset()
        if env.env.state.is_win():
            user_input = input("Enter action: ")