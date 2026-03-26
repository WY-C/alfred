import json
import os
import glob
import ai2thor.controller
import time
from openai import OpenAI

def extract_action_sequence(traj_data):
    actions = traj_data['plan']['low_actions']
    
    action_list = []
    for a in actions:
        act = a['api_action']['action']
        
        # object 정보 추가
        if 'objectId' in a['api_action']:
            obj = a['api_action']['objectId'].split('|')[0]
            act = f"{act}({obj})"
        
        action_list.append(act)
    
    return action_list

def segment_skills(action_list):
    prompt = f"""
You are an expert in robotics task decomposition.

Given the following action sequence, group them into meaningful high-level skills.

Rules:
- Each skill should represent a clear intention
- Group consecutive actions
- Keep order

Actions:
{action_list}

Output format:
Skill 1: skill_name
- action1
- action2

Skill 2: ...
"""
    client = OpenAI(base_url="http://192.168.0.19:8000/v1", api_key="token-any")

    response = client.chat.completions.create(
        model="Qwen/Qwen3-VL-8B-Instruct",
        messages=[{'role': 'user', 'content': prompt}],
        temperature=0
    )
    return response.choices[0].message.content


def generalize_skills(segmented_text):
    prompt = f"""
Generalize the following skills into reusable functions.

Rules:
- Replace specific objects with parameters
- Use function-like naming (e.g., pick(object), navigate_to(object))
- Keep it abstract and reusable

Skills:
{segmented_text}

Output format:
Skill: pick(object)
Description: picks up an object

Skill: navigate_to(object)
Description: moves to target object
"""

    client = OpenAI(base_url="http://192.168.0.19:8000/v1", api_key="token-any")

    response = client.chat.completions.create(
        model="Qwen/Qwen3-VL-8B-Instruct",
        messages=[{'role': 'user', 'content': prompt}],
        temperature=0
    )

    return response.choices[0].message.content


def process_all_trajectories(file_list, max_files=5):
    all_skills = []
    
    for i, path in enumerate(file_list[:max_files]):
        print(f"\n📂 Processing {i+1}: {path}")
        
        with open(path, 'r') as f:
            traj_data = json.load(f)
        
        action_seq = extract_action_sequence(traj_data)
        
        print("👉 Action sequence:", action_seq[:10], "...")
        
        segmented = segment_skills(action_seq)
        print("\n🧩 Segmented Skills:\n", segmented)
        
        generalized = generalize_skills(segmented)
        print("\n🔧 Generalized Skills:\n", generalized)
        
        all_skills.append(generalized)
    
    return all_skills

def main():
    search_pattern = "data/json_2.1.0/train/*/trial_*/traj_data.json"
    found_files = sorted(glob.glob(search_pattern))

    if not found_files:
        print("❌ 에러: 데이터를 찾을 수 없습니다. 경로를 확인하세요.")
        exit()
    skills = process_all_trajectories(found_files, max_files=3)
    print(skills)

if __name__ == '__main__':
    main()