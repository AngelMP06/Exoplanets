# DEVLOG

## 2026-07-15
### Hice
- Diseñé el esquema de mensajes/chats con UUID generado en cliente

### Problemas / cosas raras
- [describe el bug o comportamiento inesperado apenas lo veas]

### Decisiones tomadas
- [decisión corta + por qué, si no amerita un ADR completo]

### Pendiente / dudas para después
- [cosas que quedaron abiertas]

## 2026-07-17
### Hice
- Creé un segundo workflow para github actions, servirá para materializar las tablas de duckdb y subirlas a S3 de nuevo.


## 2026-07-15
### Decidí

- "snapshot: la API descarga el .duckdb al arrancar", no lectura en vivo contra S3. Fue una decisión explícita (priorizar velocidad y resiliencia sobre datos siempre actualizados).


## 2026-07-20
### Hice

- He creado un nuevo usuario en AWS llamado exoplanetas_api que servirá solo para agregar la policy de lectura de mi bucket, pues el anterior usuario tenia lectura y edición.

## 2026-07-27
### Decidí

- Voy a crear funciones sincronas usando sync en vez de async en FastAPI, pues las llamadas a duckdb y S3 no son asíncronas, y haciendolas async habría un bug horrible que hace que un usuario no pueda llamar data de la página hasta que la carga de otro usuario haya acabado.

## 2026-07-28
### Hice

- Al inicio de mi API uso lifespan para verificar que el archivo se descargue correctamente, si no lo hace, dejo que el error se propague en mi workflow y lanze la exception.
- Crear los diccionarios para mandarlos en la API es más fácil con pandas, pero no voy a instalar una librería tan grande solo para una acción. 

## 2026-08-03
### Revisé

- Ya lo había decidido pero lo escribo, al subir la data transformada a S3, hago test, si la data no cumple los test, entonces ese deployment no se termina y los datos servidos serán de antiguos deployments, si fallan me llega al correo, pero en general si algo falla entonces se tendrá data antigua en lugar de data corrupta.