import subprocess
import os
import sys
import time

def main():
    print("Запуск FastAPI (бэкенд)...")
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.api:app", "--reload", "--port", "8000"], 
        cwd=os.getcwd()
    )
    
    print("Запуск Vite (фронтенд)...")
    frontend = subprocess.Popen(
        ["npm", "run", "dev"], 
        cwd=os.path.join(os.getcwd(), "web"), 
        shell=True
    )
    
    print("\n" + "="*50)
    print("✅ СЕРВЕРИ ЗАПУЩЕНО!")
    print("👉 Бэкенд API: http://127.0.0.1:8000")
    print("👉 Фронтенд:  http://localhost:5173")
    print("="*50 + "\n")

    try:
        backend.wait()
        frontend.wait()
    except KeyboardInterrupt:
        print("\nЗупинка серверів...")
        backend.terminate()
        frontend.terminate()

if __name__ == "__main__":
    main()
