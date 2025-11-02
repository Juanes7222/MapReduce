# MapReduce Visual - Distributed Computing Dashboard

Proyecto educativo que demuestra la arquitectura MapReduce con engines distribuidos, gRPC, balanceo de carga y modelo cliente-servidor.

## ARQUITECTURA

### Cliente-Servidor

- **Cliente (Frontend React)**: Navegador que se comunica únicamente con el Coordinator via REST
- **Servidor (Coordinator)**: Punto central que coordina jobs y engines
  - REST API (puerto 8000) para clientes
  - gRPC server (puerto 50051) para engines
- **Engines (Workers)**: Procesos backend que se registran y procesan tareas via gRPC

### FLUJO MAPREDUCE

1. **Cliente** envía texto al **Coordinator** (POST /api/jobs)
2. **Coordinator** particiona el texto en shards y los encola
3. **Mappers** (engines) piden tareas, cuentan palabras y reportan resultados
4. **Coordinator** hace shuffle (agrupa palabras)
5. **Reducers** (engines) suman conteos finales
6. **Cliente** consulta resultados (GET /api/jobs/{id})

## REQUISITOS

- Python >= 3.10
- Node.js >= 16
- MongoDB (local)

## INSTALACIÓN

### 1. Configuración del Backend

```bash
# Accede al directorio
cd backend

# Crea tu entorno virtual
# Cambia .venv por el nombre de tu entorno virtual
python -m venv .venv

# Activa el entorno virtual
# Cambia .venv por el nombre de tu entorno virtual
.\.venv\Scripts\Activate.ps1

# Instala dependencias
pip install -r requirements.txt

# Genera stubs de gRPC
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. jobs.proto

# Verifica que se generaron jobs_pb2.py y jobs_pb2_grpc.py
ls -la jobs_pb2*
```
Esto generará los archivos **jobs_pb2.py** y **jobs_pb2_grpc.py** en el directorio **backend/.**
Son necesarios para ejecutar **scripts/run_server.py** y **scripts/engine.py**, pero no forman parte del repositorio.

### 2. Configuración del Frontend

```bash
# Accede al directorio
cd frontend

# Instala dependencias (si es necesario)
yarn install
```

### 3. Verificar de MongoDB

```bash
# MongoDB debe estar corriendo en localhost:27017
# Ingresa este comando en PowerShell para verificar:
mongosh --eval "db.version()"
```

## EJECUCIÓN
### Opción 1: Usar Supervisor (Recomendado en producción)

```bash
# Reinicia el backend (incluye coordinator)
sudo supervisorctl restart backend

# Reinicia el frontend
sudo supervisorctl restart frontend

# Visualiza los logs
tail -f /var/log/supervisor/backend.*.log
tail -f /var/log/supervisor/frontend.*.log
```

### Opción 2: Ejecución Manual (Desarrollo)

#### Terminal 1: Coordinator
```bash
# Accede al directorio
cd backend

# Activa el entorno virtual si no lo haz hecho
# Cambia .venv por el nombre de tu entorno virtual
.\.venv\Scripts\Activate.ps1

# Inicia el servidor
python -m scripts.run_server
```

#### Terminal 2-N: Engines (Mappers)
```bash
# Accede al directorio
cd backend

# Mapper 1
python -m scripts.engine --engine-id mapper-1 --role mapper --capacity 5
# Opcional: --coordinator localhost:50051

# Mapper 2
python -m scripts.engine --engine-id mapper-2 --role mapper --capacity 5
# Opcional: --coordinator localhost:50051
```
No olvides que cada **Mapper** debe ser ejecutado en su propia terminal.

#### Terminal N+1-M: Engines (Reducers)
```bash
# Accede al directorio
cd backend

# Reducer 1
python -m scripts.engine --engine-id reducer-1 --role reducer --capacity 5
# Opcional: --coordinator localhost:50051

# Reducer 2
python -m scripts.engine --engine-id reducer-2 --role reducer --capacity 5
# Opcional: --coordinator localhost:50051
```
No olvides que cada **Reducer** debe ser ejecutado en su propia terminal.

#### Frontend
```bash
# Accede al directorio
cd frontend

# Inicia el servidor
yarn start
```

## PRUEBAS

### 1. Interfaz Web

Abre el navegador en la URL del frontend y:

1. Carga el texto de ejemplo o pega tu propio texto
2. Selecciona la estrategia de balanceo (Round Robin / Least Loaded)
3. Haz clic en "Iniciar Trabajo"
4. Observa el Panel de Control y los Registros en tiempo real
5. Observa los resultados (10 palabras más frecuentes) en la pestaña de Trabajos

### 2. Cliente CLI

```bash
# Accede al directorio
cd backend

# Con texto directo
python -m scripts.client_demo --text "El veloz murciélago hindú comía feliz cardillo y kiwi. La cigüeña tocaba el saxofón detrás del palenque de paja."

# Con archivo
echo "MapReduce es un modelo de programación distribuida..." > test.txt
python -m scripts.client_demo --file test.txt --strategy round_robin

# Listar engines
python -m scripts.client_demo --list-engines
```

### 3. Simulación de Rendimiento

```bash
# Accede al directorio
cd backend

# Crea archivo de prueba
echo "Lorem ipsum dolor sit amet..." > large_text.txt

# Ejecuta simulación con diferentes configuraciones
python simulate.py --text-file large_text.txt --configs "1,1;2,2;4,4" --output results.csv

# Visualiza resultados
cat results.csv
```

Esto generará un CSV con tiempos de ejecución para:
- 1 mapper + 1 reducer
- 2 mappers + 2 reducers  
- 4 mappers + 4 reducers

## API REST (CLIENTE ↔ COORDINATOR)

### POST /api/jobs
```json
{
  "text": "texto a procesar",
  "balancing_strategy": "round_robin"  // o "least_loaded"
```

## ESTRUCTURA DE ARCHIVOS
.MAPREDUCE/\
├── backend/\
│ ├─── map_reduce/\
│ ├── api.py # API REST (FastAPI)\
│ ├── coordinator.py # Lógica central del Coordinator\
│ ├── grpc_server.py # Servidor gRPC para comunicación con engines\
│ ├── grpc_service.py # Implementación de servicios gRPC\
│ ├── models.py # Modelos y estructuras de datos\
│ ├── db.py # Conexión MongoDB\
│ ├── utils.py # Utilidades varias\
│ └── init.py\
│ \
│ ├─── scripts/\
│ ├─── client_demo.py # Cliente CLI\
│ ├── engine.py # Engine mapper/reducer\
│ ├── run_server.py # Inicia el Coordinator\
│ ├── simulate.py # Simulador de performance\
│ └── init.py\
│ \
│ ├─── jobs.proto # Definición gRPC\
│ ├── requirements.txt # Dependencias Python\
│ └── .env # Configuración\
│\
├── frontend/\
│   ├─── src/\
│   │   ├── App.js              # Componente principal\
│   │   ├── App.css             # Estilos dashboard técnico\
│   │   └── components/\
│   │       ├── JobForm.js       # Form de creación\
│   │       ├── JobsList.js      # Lista de jobs\
│   │       ├── EnginesDashboard.js  # Visualización engines\
│   │       ├── LogsPanel.js     # Logs en tiempo real\
│   │       └── StatsPanel.js    # Estadísticas\
│   └── package.json\
│\
└── README.md                # Este archivo\
```

## CONFIGURACIÓN

### Backend (.env)
```
MONGO_URL=mongodb://localhost:27017
DB_NAME=mapreduce_db
CORS_ORIGINS=*
```

### Frontend (.env)
```
REACT_APP_BACKEND_URL=https://visual-map-reduce.preview.emergentagent.com
```

## TROUBLESHOOTING

### Los engines no se conectan
```bash
# Verifica que el coordinator esté escuchando en 50051
netstat -tlnp | grep 50051

# Revisa los logs del coordinator
tail -f /var/log/supervisor/backend.*.log
```

### Los Jobs se quedan en estado "map" o "reduce"
- Verifica que haya engines del tipo correcto (mappers/reducers)
- Revisa los logs de los engines para comprobar errores
- Usa `python -m scripts/client_demo --list-engines` para ver los engines activos

### El Frontend no carga datos
- Verifica **REACT_APP_BACKEND_URL** en **frontend/.env**
- Abre DevTools > Network para ver los errores de la API
- Verifica **CORS_ORIGINS** en **backend/.env**

## CARACTERÍSTICAS

* Arquitectura cliente-servidor pura
* MapReduce completo (Map → Shuffle → Reduce)  
* gRPC para comunicación engines-coordinator  
* Balanceo: Round Robin y Least Loaded  
* Tolerancia a Fallas: heartbeat y requeue  
* Dashboard React con polling en tiempo real  
* Persistencia en MongoDB  
* Cliente CLI y scripts de simulación  
* Logs detallados de asignaciones  

## VALIDACIÓN CLIENTE-SERVIDOR (CHECKLIST)

- [✔] Coordinator corriendo (verificar puerto 8000 y 50051)
- [✔] Al menos 2 mappers corriendo
- [✔] Al menos 2 reducers corriendo
- [✔] Frontend accesible en navegador
- [✔] Cliente puede crear job desde UI
- [✔] Dashboard muestra engines activos
- [✔] Jobs progresan: map → shuffle → reduce → done
- [✔] Resultados (top-10) se muestran al completar
- [✔] Logs muestran asignaciones en tiempo real
- [✔] Cliente NO se comunica directamente con engines

## CONTRIBUCIÓN

Este es un proyecto meramente educativo.
Si se desea, las posibles mejoras a implementar son:

- [ ] Persistencia de jobs en MongoDB (actualmente en memoria)
- [ ] WebSocket para notificaciones en lugar de polling
- [ ] Visualización gráfica del flujo MapReduce
- [ ] Soporte para combiners (pre-agregación en mappers)
- [ ] Tests unitarios e integración
- [ ] Docker Compose para fácil deployment

## LICENCIA

MIT
