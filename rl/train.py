import random
import os
import sys
import time

# 경로 설정 (중요)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../gen')))

from rl.env_wrapper import AlfredRLEnv
from rl.agent import RandomAgent
from rl.utils import render
from env.thor_env import ThorEnv  


def main():
    # 1️⃣ env 생성
    thor = ThorEnv()
    env = AlfredRLEnv(thor)

    scene = "FloorPlan1"

    # 2️⃣ agent
    agent = RandomAgent(len(env.action_space))

    trajectory = []

    NUM_EPISODES = 5
    MAX_STEPS = 200

    for episode in range(NUM_EPISODES):
        print(f"\n===== Episode {episode} =====")

        # 🔥 task 없이 reset
        state = env.reset(scene, traj=None, args=None)

        for step in range(MAX_STEPS):

            # 1. action 선택
            action = agent.act(state)

            # 2. step 실행
            next_state, reward, done, info = env.step(action)

            # 3. trajectory 저장 (skill discovery 핵심)
            trajectory.append({
                "episode": episode,
                "step": step,
                "state": state,
                "action": action,
                "reward": reward
            })

            # 4. 시각화
            try:
                render(next_state)
            except:
                pass  # xvfb 환경에서는 무시

            # 5. 상태 업데이트
            state = next_state

            print(f"[Episode {episode}] Step {step} | Action: {action} | Reward: {reward:.3f}")

            # ❗ task 없으니까 done 의미 없음
            if done:
                print("Done triggered (ignored in exploration mode)")
                break

            # optional: 속도 조절 (너무 빠르면 주석)
            time.sleep(0.02)

    print("\n🔥 Collected trajectories:", len(trajectory))


if __name__ == "__main__":
    main()