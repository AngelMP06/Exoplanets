import os
os.environ["SKIP_S3_DOWNLOAD"] = "true"
os.environ["DUCKDB_PATH"] = "tests/fixtures/test_exoplanets.duckdb"

from fastapi.testclient import TestClient
from main import app # pyright: ignore[reportAttributeAccessIssue]

# Esto hace que el lifespan se active al iniciar el test
with TestClient(app) as client:

    # Test para verificar si health responde correctamente
    def test_health_ok():
        response = client.get("/health")
        assert response.status_code == 200

    # Test pra verificar si health responde correctamente cuando db_ready es False
    def test_health_not_ok(monkeypatch):
        # Temporalmente db_ready se pone en False solo para este test
        monkeypatch.setattr("main.db_ready", False)
        response = client.get("/health")
        assert response.status_code == 503

    # Test para endpoint sin categoría
    def test_habitability():
        response = client.get("/habitability")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) > 0

    # Test para endpoint con categoría que no existe
    def test_size_categoria_invalida_devuelve_vacio():
        response = client.get("/size", params={"categoria": "no_existe"})
        assert response.status_code == 200
        assert response.json() == []

    # Test para endpoint con categoría que sí existe
    def test_size_categoria_valida_devuelve_datos():
        response = client.get("/size", params={"categoria": "mas grande"})
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) > 0
        
    # Test para endpoint con injection, verificar que nadie pueda poner un string malicioso que haga que la query devuelva o haga algo que no debería 
    def test_size_injection_no_rompe():
        response = client.get("/size", params={"categoria": "'; DROP TABLE mart_size; --"})
        assert response.status_code == 200
        assert response.json() == []

        # Confirma que la tabla sigue existiendo después del intento
        response_valido = client.get("/size", params={"categoria": "mas grande"})
        assert response_valido.status_code == 200
        assert len(response_valido.json()) > 0