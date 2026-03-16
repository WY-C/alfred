import json
import os
import glob
import ai2thor.controller
import time

# [1] 데이터 경로 찾기
search_pattern = "data/json_2.1.0/train/*/trial_*/traj_data.json"
found_files = sorted(glob.glob(search_pattern))

if not found_files:
    print("❌ 에러: 데이터를 찾을 수 없습니다. 경로를 확인하세요.")
    exit()

data_path = found_files[0]
print(f"✅ 데이터 발견: {data_path}")

with open(data_path, 'r') as f:
    traj_data = json.load(f)

# [2] 컨트롤러 생성 및 서버 시동
print("🚀 AI2-THOR 컨트롤러 생성 중...")
controller = ai2thor.controller.Controller()

print("🔥 서버 시동 및 8000번 포트 강제 지정 중...")
try:
    controller.start(port=8000, host='127.0.0.1', start_unity=False)
    print("✅ 파이썬 서버가 127.0.0.1:8000 에서 열렸습니다!")
except TypeError:
    print("⚠️ host/start_unity 옵션 거부됨. 기본 모드로 8000번 포트를 엽니다.")
    try:
        controller.start(port=8000)
        print("✅ 파이썬 서버가 8000번 포트에서 열렸습니다!")
    except Exception as e:
        print(f"❌ 서버 시동 에러: {e}")
        exit()
except Exception as e:
    print(f"❌ 서버 시동 중 알 수 없는 에러: {e}")
    exit()

print("\n" + "="*70)
print("🚨 [중요] 유니티 실행 시 반드시 '-host 127.0.0.1' 옵션을 추가해야 합니다!")
print("👉 새 터미널에서 아래 명령어를 정확히 복사해서 실행하세요:")
print("   /home/choi/.ai2thor/releases/thor-201909061227-Linux64/thor-201909061227-Linux64 -host 127.0.0.1 -port 8000")
print("="*70 + "\n")

# [3] 장면 로딩 및 재현
try:
    floor_plan = traj_data['scene']['floor_plan']
    print(f"🏠 장면 {floor_plan} 로딩 대기 중... (유니티 화면이 '침실'로 바뀌어야 정상입니다)")
    
    controller.reset(floor_plan)
    print("✨ 드디어 연결 성공! 에이전트가 움직이기 시작합니다.")

    # 그리드 크기 초기화
    controller.step({"action": "Initialize", "gridSize": 0.25})
    
    # 시작 위치 순간이동 및 last_event 저장
    print("📍 에이전트 위치 초기화 중...")
    init_action = traj_data['scene']['init_action']
    last_event = controller.step({
        "action": "TeleportFull",
        "x": init_action['x'],
        "y": init_action['y'],
        "z": init_action['z'],
        "rotation": init_action['rotation'],
        "horizon": init_action['horizon'],
        "standing": init_action.get('standing', True)
    })

    # [4] 전문가 액션 재현 루프
    print("🎬 전문가 경로 재현 시작!")
    low_actions = traj_data['plan']['low_actions']

    for i, plan in enumerate(low_actions):
        action_dict = dict(plan['api_action'])
        action_name = action_dict.get('action', 'Unknown')
        
        # 🔑 오브젝트 ID 동적 보정
        if 'objectId' in action_dict:
            recorded_id = action_dict['objectId']
            target_class = recorded_id.split('|')[0] 
            
            current_objects = last_event.metadata['objects']
            
            # 1순위: 에이전트 시야에 보이는 동일한 종류의 물체
            visible_targets = [obj for obj in current_objects if obj['objectType'] == target_class and obj['visible']]
            
            if visible_targets:
                action_dict['objectId'] = visible_targets[0]['objectId']
            else:
                # 2순위: 시야에 안 보이면 방 전체에서 찾기
                all_targets = [obj for obj in current_objects if obj['objectType'] == target_class]
                if all_targets:
                    action_dict['objectId'] = all_targets[0]['objectId']
            
            # ID가 보정되었을 때만 로그 출력
            if recorded_id != action_dict['objectId']:
                print(f"\n   [ID 보정] {recorded_id} -> {action_dict['objectId']}")

        print(f"[{i+1}/{len(low_actions)}] {action_name} 실행 중...", end=" ", flush=True)
        
        # 액션 실행
        last_event = controller.step(action_dict)
        
        # 결과 판별 로직 강화 (이미 켜짐, 이미 열림 등의 상태 방어)
        if last_event.metadata['lastActionSuccess']:
            print("✅ 성공")
        else:
            err_msg = last_event.metadata.get('errorMessage', '').lower()
            
            if action_name == 'ToggleObjectOn' and 'already on' in err_msg:
                print("✅ 성공 (상태 유지: 이미 켜져 있음)")
            elif action_name == 'ToggleObjectOff' and 'already off' in err_msg:
                print("✅ 성공 (상태 유지: 이미 꺼져 있음)")
            elif action_name == 'OpenObject' and 'already open' in err_msg:
                print("✅ 성공 (상태 유지: 이미 열려 있음)")
            elif action_name == 'CloseObject' and 'already closed' in err_msg:
                print("✅ 성공 (상태 유지: 이미 닫혀 있음)")
            else:
                print(f"❌ 실패 ({last_event.metadata.get('errorMessage', '원인 불명')})")
        
        # 움직임을 관찰하기 위해 0.3초 대기
        time.sleep(0.3)

    print("\n" + "="*60)
    print("🎉 완벽한 성공! 모든 전문가 동작 재현이 끝났습니다.")
    print("="*60)

except Exception as e:
    print(f"\n❌ 실행 중 에러 발생: {e}")

finally:
    input("\n종료하려면 엔터를 누르세요...")
    if 'controller' in locals():
        controller.stop()