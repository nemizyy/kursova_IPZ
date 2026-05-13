import subprocess
import os
import sys
import time

def main():
    print("Збірка фронтенду (Vite)...")
    subprocess.run(["cmd", "/c", "npm run build"], cwd=os.path.join(os.getcwd(), "web"), check=True)

    print("Запуск FastAPI (бэкенд)...")
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.api:app", "--reload", "--port", "8000"], 
        cwd=os.getcwd()
    )
    
    print("\n" + "="*50)
    print("DONE: SERVER STARTED!")
    print("API: http://127.0.0.1:8000")
    print("="*50 + "\n")

    try:
        backend.wait()
    except KeyboardInterrupt:
        print("\nЗупинка сервера...")
        backend.terminate()

if __name__ == "__main__":
    main()
