import duckdb
import os
from dotenv import load_dotenv

load_dotenv()

aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
region_name=os.getenv("AWS_REGION")

con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs;")
con.execute(f"""
    SET s3_region='{region_name}';
    SET s3_access_key_id='{aws_access_key_id}';
    SET s3_secret_access_key='{aws_secret_access_key}';
""")

df = con.execute("SELECT * FROM read_parquet('s3://exoplanetas-pipeline-datos/raw/planets.parquet') LIMIT 5").df()
print(df)
