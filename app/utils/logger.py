from datetime import datetime

def log(msg):
    print("[", datetime.now().strftime("%H:%M:%S"), "]", msg)