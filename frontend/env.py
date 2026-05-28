import os
from dotenv import load_dotenv

load_dotenv()

import socket

# For DEV
def get_local_ipv4():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

ip = get_local_ipv4()

TRIAL_LENGTH = 7

FRONTEND_URL = f'http://{ip}:5000'
API_BASE = f'http://{ip}:8000/api'

DATABASE_URL = os.getenv("DATABASE_URL")

SECRET_KEY = "CHANGE_THIS_TO_LONG_RANDOM_SECRET"
ALGORITHM = "HS256"
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")

S3_URL = os.getenv("S3_URL")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")
PROFILE_PICTURE_PREFIX = os.getenv("PROFILE_PICTURE_PREFIX")
WAIVER_PREFIX = os.getenv("WAIVER_PREFIX")

STRIPE_KEY = os.getenv("STRIPE_KEY_DEV")
STRIPE_WEBHOOK_KEY = os.getenv("STRIPE_WEBHOOK_KEY")

def print_env_var():
    for key, value in globals().items():
        print(f"{key} = {value}")
if __name__ == '__main__':
    print_env_var()