import boto3
import os
from pathlib import Path
from dotenv import load_dotenv
from botocore.exceptions import ClientError

load_dotenv()

OUTPUT_DIR = Path("export/output")
S3_BUCKET = os.getenv("AWS_BUCKET_NAME")
S3_PREFIX = "web"  # carpeta pública, separada de raw/ y warehouse/

if not S3_BUCKET: 
    raise SystemExit("AWS_BUCKET_NAME no está seteado")

def get_s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION"),
    )

def main():
    s3 = get_s3_client()
    json_files = list(OUTPUT_DIR.glob("*.json"))

    if not json_files:
        raise SystemExit(f"No se encontraron JSON en {OUTPUT_DIR}")

    for file_path in json_files:
        s3_key = f"{S3_PREFIX}/{file_path.name}"
        try:
            s3.upload_file(
                str(file_path),
                S3_BUCKET,
                s3_key,
                ExtraArgs={"ContentType": "application/json"},
            )
            print(f"Subido: {s3_key}")
        except ClientError as e:
            print(f"Error subiendo {file_path.name}: {e}")
            raise

if __name__ == "__main__":
    main()