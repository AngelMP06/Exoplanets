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

## 2026-08-05
### Hice

- Realizé los test para que corran cada vez que la carpeta api/ sufre cambios, estos test comprueban que la data enviada por la API sea correcta, ahora que tengo todos los tests listos, queda subirlo a render

## 2026-08-06
### Decidí

- Render en vez de un entorno serverless (ej. Cloudflare Workers) para el backend: mi API usa un proceso persistente (lifespan + conexión DuckDB reutilizada), y Workers no soporta paquetes con binarios nativos como duckdb.

- Backend propio (FastAPI) en vez de un servicio gestionado tipo Supabase: el objetivo del proyecto es demostrar que puedo construir y desplegar esa capa yo mismo, no delegarla a un servicio de terceros.

- FreeTier de Render (no el plan de pago) para hostear: mi .duckdb pesa 9MB así que la RAM del free tier (512 MB) es más que suficiente. El trade-off es el spin-down tras 15 min de inactividad - el primer request después de eso tarda 30-60 s en responder (el contenedor entero tiene que levantar, no solo la descarga del archivo, que es rápida por el tamaño chico). Aceptable para portafolio de bajo tráfico; una opción futura es pagar el plan Starter ($7/mes) para eliminar el spin-down.

## 2026-08-09
### Decidí

- Voy a crear el siguiente diseño para mi frontend, todo estará en una sola página scrolleable, las 9 marts se agruparán según categoría (habitability, discovery, size, distance, system) y se mostrará cada categoría con su ranking, gráfica de distribución y una descripción que se obtuvo del EDA.

## 2026-08-13

- Decidí que voy a crear un mart extra, llamado position el cual tendra RA, Decl, distance_pc, planet_name y star_name  este me servirá para 2 cosas, una para hacer la distribución de distance_pc y otra para crear un mapa en 3d de las posiciones de todos los planetas.