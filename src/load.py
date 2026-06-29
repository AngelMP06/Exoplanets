import boto3
import os
from dotenv import load_dotenv

load_dotenv()

def load_to_s3(df, key: str):
    """Guarda el DataFrame como Parquet en S3."""
    local_path = f"data/{key}"
    
    # guardar local primero
    df.to_parquet(local_path, index=False)
    print(f"Guardado local: {local_path}")
    
    # subir a S3
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION"),
    )
    
    bucket = os.getenv("AWS_BUCKET_NAME")
    s3.upload_file(local_path, bucket, f"raw/{key}")
    print(f"Subido a S3: s3://{bucket}/raw/{key}")