import ai2thor.controller
import time
import math

# [1] 커스텀 플래너 함수: 목표를 달성하기 위한 액션 시퀀스를 실시간으로 계산합니다.
def generate_plan(current_objects, target_object_type):
    print(f"\n🧠 [플래너 가동] 목표: '{target_object_type}'를 찾아내서 집어라!")
    
    # 1. 타겟 물체 찾기
    target_obj = None
    for obj in current_objects:
        if obj['objectType'] == target_object_type:
            target_obj = obj
            break
            
    if not target_obj:
        print(f"❌ 플랜 실패: 방 안에 {target_object_type}이(가) 존재하지 않습니다.")
        return []

    target_id = target_obj['objectId']
    print(f"🎯 타겟 발견: {target_id} (현재 상태: 보이는가? {target_obj['visible']})")
    
    plan = []
    
    # ff_planner가 수행하는 논리적 조건(Precondition) 탐색 과정의 축소판입니다.
    # 2. 물체가 시야에 없으면 회전하거나 다가가야 함 (여기서는 단순화하여 시야에 들어올 때까지 탐색한다고 가정)
    if not target_obj['visible']:
        print("   -> 물체가 시야에 없습니다. 탐색(회전) 액션을 계획에 추가합니다.")
        # 실제 ff_planner는 내비게이션 메시를 계산하지만, 여기서는 단순 탐색 로직 추가
        plan.append({"action": "RotateRight"})
        plan.append({"action": "RotateRight"})
    
    # 3. 물체를 집기 위한 조건 확인
    if not target_obj['pickupable']:
        print(f"❌ 플랜 실패: {target_object_type}은(는) 집을 수 없는 물체입니다.")
        return []
        
    # 4. 물체를 집는 액션 추가
    print("   -> 물체 집기 액션을 계획에 추가합니다.")
    plan.append({
        "action": "PickupObject",
        "objectId": target_id
    })
    
    return plan

# [2] 컨트롤러 생성 및 서버 시동 (우리의 무적 8000번 포트)
print("🚀 AI2-THOR 컨트롤러 생성 중...")
controller = ai2thor.controller.Controller()

try:
    controller.start(port=8000, host='127.0.0.1', start_unity=False)
    print("✅ 파이썬 서버가 127.0.0.1:8000 에서 열렸습니다!")
except TypeError:
    try:
        controller.start(port=8000)
    except Exception as e:
        print(f"❌ 서버 시동 에러: {e}")
        exit()
except Exception as e:
    print(f"❌ 서버 시동 중 알 수 없는 에러: {e}")
    exit()

print("\n" + "="*70)
print("🚨 유니티 실행 명령어:")
print("   /home/choi/.ai2thor/releases/thor-201909061227-Linux64/thor-201909061227-Linux64 -host 127.0.0.1 -port 8000")
print("="*70 + "\n")

# [3] 환경 초기화 및 목표 부여
try:
    # 이번엔 사과(Apple)가 있는 주방(FloorPlan28)을 로드합니다.
    target_scene = "FloorPlan28"
    print(f"🏠 장면 {target_scene} 로딩 대기 중... (유니티를 켜주세요!)")
    
    controller.reset(target_scene)
    print("✨ 유니티 연결 성공!")

    # 환경 기본 세팅
    last_event = controller.step({"action": "Initialize", "gridSize": 0.25})
    
    # [4] 실시간 플래너 구동 및 액션 실행
    # 1. 현재 환경의 모든 오브젝트 상태를 스캔합니다. (State Extraction)
    current_objects = last_event.metadata['objects']
    
    # 2. 목표 부여 (Task)
    task_goal = "Apple"
    
    # 3. 플래너가 경로 계산 (Plan Generation)
    generated_plan = generate_plan(current_objects, task_goal)
    
    if not generated_plan:
        print("🛑 플래너가 유효한 경로를 찾지 못해 실행을 종료합니다.")
    else:
        print("\n🎬 동적 생성된 경로 실행 시작!")
        for i, action_dict in enumerate(generated_plan):
            action_name = action_dict['action']
            print(f"[{i+1}/{len(generated_plan)}] {action_name} 실행 중...", end=" ", flush=True)
            
            # 4. 액션 실행 (Execution)
            last_event = controller.step(action_dict)
            
            if last_event.metadata['lastActionSuccess']:
                print("✅ 성공")
            else:
                print(f"❌ 실패 ({last_event.metadata.get('errorMessage', '원인 불명')})")
                
            time.sleep(0.5)
            
        print("\n🎉 목표 달성! 동적 플래닝 및 실행이 완료되었습니다.")

except Exception as e:
    print(f"\n❌ 실행 중 에러 발생: {e}")

finally:
    input("\n종료하려면 엔터를 누르세요...")
    if 'controller' in locals():
        controller.stop()