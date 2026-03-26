import random
import numpy as np

from env.thor_env import ThorEnv

class AlfredRLEnv:
    def __init__(self, thor_env):
        self.env = thor_env

        self.action_space = [
            "MoveAhead",
            "RotateLeft",
            "RotateRight",
            "LookUp",
            "LookDown",
            "PickupObject",
            "OpenObject",
            "CloseObject"
        ]

    def reset(self, scene, traj=None, args=None):
        self.env.reset(scene)

        if traj is not None:
            self.env.set_task(traj, args)

        return self._get_state()

    def step(self, action_idx):
        action_str = self.action_space[action_idx]

        if action_str in ["MoveAhead", "RotateLeft", "RotateRight", "LookUp", "LookDown"]:
            event, _ = self.env.to_thor_api_exec(action_str)
        else:
            obj_id = self._get_nearest_object()
            if obj_id is None:
                return self._get_state(), -0.1, False, {"fail": True}
            event, _ = self.env.to_thor_api_exec(action_str, obj_id)

        # 🔥 task 없으면 reward 0
        if self.env.task is not None:
            reward = self.env.get_transition_reward()
            done = self.env.get_goal_satisfied()
        else:
            reward = 0.0
            done = False

        reward += 0.01  # exploration bonus

        next_state = self._get_state()

        return next_state, reward, done, {}

    def _get_state(self):
        event = self.env.last_event

        return {
            "image": event.frame,
            "inventory": event.metadata['inventoryObjects'],
            "objects": event.metadata['objects']
        }

    def _get_nearest_object(self):
        objs = self.env.last_event.metadata['objects']
        visible = [o for o in objs if o['visible']]

        if len(visible) == 0:
            return None

        return visible[0]['objectId']