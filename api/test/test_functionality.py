import boto3
import os
from dotenv import load_dotenv
from botocore.exceptions import ClientError

load_dotenv()  # busca .env en el directorio desde donde corrés el script

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)

bucket = os.getenv("AWS_BUCKET_NAME", "exoplanetas-pipeline-datos")

 # Test 1: debería funcionar (list)
try:
    response = s3.list_objects_v2(Bucket=bucket)
    print("✅ ListBucket OK - Archivos encontrados:", response.get("KeyCount"))
except ClientError as e:
    print(f"Test 1: List Objects - Failed: {e}")

# Test 2: debería funcionar (get) — ajustá el key a un archivo real que exista
try:
    s3.download_file(bucket, "warehouse/exoplanets.duckdb", "test_download.duckdb")
    print("✅ GetObject OK. Archivo descargado.")
except ClientError as e:
    print(f"Test 2: Get Object - Failed: {e}")

# Test 3: NO debería funcionar (put) — esto tiene que fallar
try:
    s3.put_object(Bucket=bucket, Key="test_no_deberia_existir.txt", Body=b"esto no deberia subir")
    print("🚨 PutObject funcionó — MAL, la policy tiene un permiso que no debería tener")
except ClientError as e:
    print("✅ PutObject falló como se esperaba:", e.response["Error"]["Code"])