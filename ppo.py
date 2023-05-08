import gym
from gym import spaces
import numpy as np
import torch
import os

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
        self.env = RegicideEnv(args)
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
        # for move in legal_moves:
        #     legal_moves_as_int.append(self.env.game.get_move_uid(move))
        # print(legal_moves_as_int, action, legal_moves)
        if action in legal_moves_as_int:
            # observation, reward, done, info = self.env.step([int(action)])
            observation, share_obs, reward, done, info, available_actions = \
                self.env.step([int(action)])
            # print(action, reward, done, info)
            # self.env.show()
            return observation, reward, done, info
        else:
            observation = self.env.make_observation()
            print(action, legal_moves_as_int)
            print(-1, False)
            self.env.show()
            return observation, -1, False, {}

    def seed(self, seed):
        self.env.seed(seed)

    def action_masks(self):
        legal_moves = self.env.state.legal_moves()
        legal_moves_as_int = self.env.state.legal_moves_as_int()
        return [action in legal_moves_as_int for action in self.possible_actions]

    def render(self, mode='human'):
        self.env.render(mode=mode)

    def close(self):
        self.env.close()

env = RegicideCustomEnv(args)


from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv
from stable_baselines3.common.env_util import make_vec_env
# Number of parallel environments
n_envs = 8

# envs = [lambda: RegicideCustomEnv(args) for _ in range(n_envs)]
# dummy_vec_env = DummyVecEnv(envs)

# Initialize the model
model = RecurrentMaskablePPO("MlpLstmPolicy", env, policy_kwargs={"net_arch": [256, 256, 256]}, gamma=0.4, seed=42, verbose=1,  device='cuda:0' if torch.cuda.is_available() else 'cpu')

from stable_baselines3.common.callbacks import BaseCallback

class SaveOnBestTrainingRewardCallback(BaseCallback):
    """
    Callback for saving a model (the check is done every ``check_freq`` steps)
    based on the training reward (in practice, we recommend using ``EvalCallback``).

    :param check_freq: (int)
    :param log_dir: (str) Path to the folder where the model will be saved.
      It must contains the file created by the ``Monitor`` wrapper.
    :param verbose: (int)
    """
    def __init__(self, check_freq: int, save_path: str, verbose=1):
        super(SaveOnBestTrainingRewardCallback, self).__init__(verbose)
        self.check_freq = check_freq
        self.save_path = save_path
        self.best_mean_reward = -np.inf

    def _init_callback(self) -> None:
        # Create folder if needed
        if self.save_path is not None:
            os.makedirs(self.save_path, exist_ok=True)

    def _on_step(self) -> bool:
        if self.n_calls % self.check_freq == 0:

          # Save the model
          self.model.save(self.save_path + str(self.n_calls))

        return True

        

# Create the callback
callback = SaveOnBestTrainingRewardCallback(check_freq=10000, save_path="./saved_models/")

# Load the trained model
model = RecurrentMaskablePPO.load("./saved_models/3240000", env=env)

# Train the agent
model.learn(total_timesteps=5000000, callback=callback)

# Save the model
model.save("hanabi_ppo")

# Test the trained model
obs = env.reset()
for _ in range(1000):
    # Retrieve current action mask
    action_masks = get_action_masks(env)
    action, _states = model.predict(obs, action_masks=action_masks)
    obs, rewards, dones, info = env.step(action)
    print(action)
    # env.render()
    if dones:
        obs = env.reset()