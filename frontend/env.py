import os

TRIAL_LENGTH = 7

FRONTEND_URL = os.getenv("FRONTEND_URL")
API_BASE = os.getenv("API_BASE")

DATABASE_URL = os.getenv("DATABASE_URL")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

S3_URL = os.getenv("S3_URL")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
S3_REGION = os.getenv("S3_REGION")
BUCKET_NAME = os.getenv("BUCKET_NAME")
PROFILE_PICTURE_PREFIX = os.getenv("PROFILE_PICTURE_PREFIX")
WAIVER_PREFIX = os.getenv("WAIVER_PREFIX")

STRIPE_KEY = os.getenv("STRIPE_KEY")
STRIPE_WEBHOOK_KEY = os.getenv("STRIPE_WEBHOOK_KEY")

def print_env_var():
    for key, value in globals().items():
        print(f"{key} = {value}")

if __name__ == '__main__':
    print_env_var()