# start_server.py
import subprocess
import time
import requests
import os

def is_comfyui_running(url: str = "http://127.0.0.1:8188") -> bool:
    """ComfyUI 서버가 켜져서 응답하는지 확인합니다."""
    try:
        response = requests.get(url, timeout=2)
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False

def launch_comfyui_server(comfy_folder_path: str, url: str = "http://127.0.0.1:8188") -> bool:
    """
    Git으로 설치된 ComfyUI를 python main.py 명령어로 실행하고 대기합니다.
    """
    if is_comfyui_running(url):
        print("ComfyUI 서버가 이미 실행 중입니다.")
        return True
        
    print(f"ComfyUI 서버 부팅 시작: [{comfy_folder_path}]")
    
    # 1. Git 설치 버전의 핵심 실행 파일인 main.py 경로 확인
    main_py_path = os.path.join(comfy_folder_path, "main.py")
    
    if not os.path.exists(main_py_path):
        print(f"오류: 실행 파일({main_py_path})을 찾을 수 없습니다. 경로를 다시 확인하세요.")
        return False

    try:
        # 2. 실행 명령어 세팅
        # 기본적으로 시스템 환경변수에 등록된 python을 사용합니다.
        # 만약 venv 가상환경을 사용 중이라면 아래 주석을 해제하고 경로를 수정하세요.
        python_executable = os.path.join(comfy_folder_path, "venv", "Scripts", "python.exe")
        command = [python_executable, "main.py"]
        
        command = ["python", "main.py"]
        
        # 3. 독립된 콘솔 창에서 ComfyUI 실행
        subprocess.Popen(
            command, 
            cwd=comfy_folder_path, 
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        
        # 4. 서버 부팅 대기 (최대 60초)
        max_retries = 30
        for i in range(max_retries):
            time.sleep(2)
            print(f"서버 부팅 대기 중... ({i+1}/{max_retries})")
            
            if is_comfyui_running(url):
                print("ComfyUI 서버 연결 완료!")
                return True
                
        print("오류: 지정된 시간 내에 ComfyUI 서버가 응답하지 않습니다.")
        return False
        
    except Exception as e:
        print(f"ComfyUI 실행 중 오류 발생: {e}")
        return False