from fastapi import FastAPI, HTTPException, Depends
from contextlib import asynccontextmanager
import duckdb

import boto3
import os
from dotenv import load_dotenv
from botocore.exceptions import ClientError

load_dotenv()

DUCKDB_LOCAL_PATH = os.getenv("DUCKDB_PATH", "exoplanets.duckdb")
S3_BUCKET = os.getenv("AWS_BUCKET_NAME")
S3_KEY = "warehouse/exoplanets.duckdb"
SKIP_S3_DOWNLOAD = os.getenv("SKIP_S3_DOWNLOAD")

db_ready = False  # bandera simple para que /health sepa si cargó bien

def get_s3_client():
    return boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- código que corría antes en download_database(), va acá arriba del yield ---
    global db_ready

    if not SKIP_S3_DOWNLOAD:
    
        # TODO 1: crear el cliente s3 (mismo patrón que en test_read_only.py)
        s3 = get_s3_client()

        # TODO 2: descargar S3_KEY a DUCKDB_LOCAL_PATH
        s3.download_file(S3_BUCKET, S3_KEY, DUCKDB_LOCAL_PATH)

    # TODO 3: si falla, ¿qué hacés? (pensá en "fallar ruidoso", no capturar y seguir)
    # No hacer nada, dejar que el fallo se propague, de todas formas si falla aca, quiero que todo se detenga


    # TODO 4: si sale bien, marcar db_ready = True
    db_ready=True
    print("Base de datos cargada completamente")

    yield  # la API corre acá — todo lo de abajo del yield sería código de "shutdown", no lo necesitás todavía

    # (nada por ahora — si algún día necesitás limpiar algo al apagar la API, va acá)


app = FastAPI(lifespan=lifespan)


def get_connection():
    # TODO 5: abrir una conexión NUEVA de solo lectura cada vez que se llama esta función
    con = duckdb.connect(DUCKDB_LOCAL_PATH, read_only=True)
    return con

# Helper para ejecutar la query en cada endpoint
def ejecutar_query(con, query, params = None):
    result = con.execute(query, params or []).fetchall()
    columns = [col[0] for col in con.description]
    return [dict(zip(columns, row)) for row in result]



@app.get("/")
def inicio():
    return {"saludo" : "¡Bienvenido!"}

@app.get("/health")
def health():
    # TODO 6: devolver algo tipo {"status": "ok"} si db_ready y el archivo existe
    if db_ready and os.path.exists(DUCKDB_LOCAL_PATH):
        return {"status": "Funciona correctamente"}
    # TODO 7: si no, devolver un error (pista: FastAPI usa HTTPException para status != 200)
    raise HTTPException(status_code=503, detail="No se cargó la data correctamente")

@app.get("/habitability")
def get_habitability(con = Depends(get_connection)):
    return ejecutar_query(con, "SELECT * FROM mart_habitability")

@app.get("/size")
def get_size(categoria : str, con = Depends(get_connection)):
    return ejecutar_query(con, "SELECT * FROM mart_size WHERE categoria = ?", [categoria])

@app.get("/habitability_by_spectral_type")
def get_habitability_by_spectral_type(con = Depends(get_connection)):
    return ejecutar_query(con, "SELECT * FROM mart_habitability_by_spectral_type")

@app.get("/distance")
def get_distance(categoria : str, con = Depends(get_connection)):
    return ejecutar_query(con, "SELECT * FROM mart_distance WHERE categoria = ?", [categoria])

@app.get("/system")
def get_system(categoria : str, con = Depends(get_connection)):
    return ejecutar_query(con, "SELECT * FROM mart_system WHERE categoria = ?", [categoria])

@app.get("/discovery_distribution")
def get_discovery_distribution(categoria : str, con = Depends(get_connection)):
    return ejecutar_query(con, "SELECT * FROM mart_discovery_distribution WHERE categoria = ?", [categoria])

@app.get("/habitability_distribution")
def get_habitability_distribution(categoria : str, con = Depends(get_connection)):
    return ejecutar_query(con, "SELECT * FROM mart_habitability_distribution WHERE categoria = ?", [categoria])

@app.get("/size_distribution")
def get_size_distribution(categoria : str, con = Depends(get_connection)):
    return ejecutar_query(con, "SELECT * FROM mart_size_distribution WHERE categoria = ?", [categoria])

@app.get("/system_distribution")
def get_system_distribution(categoria : str, con = Depends(get_connection)):
    return ejecutar_query(con, "SELECT * FROM mart_system_distribution WHERE categoria = ?", [categoria])

@app.get("/ping")
def ping():
    return {"message": "pong"}