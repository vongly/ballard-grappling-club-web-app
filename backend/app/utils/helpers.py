class CheckS3Bucket:
    def __init__(self, client: object, bucket_name: str):
        self.client = client
        self.bucket_name = bucket_name

    def ensure_bucket(self):
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
        except Exception:
            self.client.create_bucket(Bucket=self.bucket_name)

    def ensure_key(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except self.client.exceptions.ClientError:
            return False