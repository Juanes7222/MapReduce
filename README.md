# MapReduce Visual - Distributed Computing Dashboard

Proyecto educativo que demuestra la arquitectura MapReduce con engines distribuidos, gRPC, balanceo de carga y modelo cliente-servidor.

## 🏛️ Arquitectura

### Cliente-Servidor

- **Cliente (Frontend React)**: Navegador que se comunica únicamente con el Coordinator via REST
- **Servidor (Coordinator)**: Punto central que coordina jobs y engines
  - REST API (puerto 8000) para clientes
  - gRPC server (puerto 50051) para engines
- **Engines (Workers)**: Procesos backend que se registran y procesan tareas via gRPC

### Flujo MapReduce

1. **Cliente** envía texto al **Coordinator** (POST /api/jobs)
2. **Coordinator** particiona el texto en shards y los encola
3. **Mappers** (engines) piden tareas, cuentan palabras y reportan resultados
4. **Coordinator** hace shuffle (agrupa palabras)
5. **Reducers** (engines) suman conteos finales
6. **Cliente** consulta resultados (GET /api/jobs/{id})

## 🛠️ Requisitos

- Python >= 3.10
- Node.js >= 16
- MongoDB (local)

## 🚀 Instalación

### 1. Backend Setup

```bash
cd backend

# Instalar dependencias
pip install -r requirements.txt

# Generar stubs de gRPC
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. jobs.proto

# Verificar que se generaron jobs_pb2.py y jobs_pb2_grpc.py
ls -la jobs_pb2*
```

### 2. Frontend Setup

```bash
cd frontend

# Instalar dependencias (si es necesario)
yarn install
```

### 3. Verificar MongoDB

```bash
# MongoDB debe estar corriendo en localhost:27017
# Verificar con:
mongosh --eval "db.version()"
```

## ▶️ Ejecución
### Opción 1: Usar Supervisor (Recomendado en producción)

```bash
# Reiniciar backend (incluye coordinator)
sudo supervisorctl restart backend

# Reiniciar frontend
sudo supervisorctl restart frontend

# Ver logs
tail -f /var/log/supervisor/backend.*.log
tail -f /var/log/supervisor/frontend.*.log
```

### Opción 2: Ejecución Manual (Desarrollo)

#### Terminal 1: Coordinator
```bash
cd backend
python -m scripts.run_server
```

#### Terminal 2-N: Engines (Mappers)
```bash
cd backend

# Mapper 1
python -m scripts.engine --engine-id mapper-1 --role mapper --capacity 5 # Opcional: --coordinator localhost:50051

# Mapper 2
python -m scripts.engine --engine-id mapper-2 --role mapper --capacity 5 # Opcional: --coordinator localhost:50051
```

#### Terminal N+1-M: Engines (Reducers)
```bash
cd backend

# Reducer 1
python -m scripts.engine --engine-id reducer-1 --role reducer --capacity 5 # Opcional: --coordinator localhost:50051

# Reducer 2
python -m scripts.engine --engine-id reducer-2 --role reducer --capacity 5 # Opcional: --coordinator localhost:50051
```

#### Frontend
```bash
cd frontend
yarn start
```

## 🧪 Pruebas

### 1. Interfaz Web

Abrir el navegador en la URL del frontend y:

1. Cargar texto de ejemplo o pegar tu propio texto
2. Seleccionar estrategia de balanceo (Round Robin / Least Loaded)
3. Hacer clic en "Start Job"
4. Observar el dashboard de engines y logs en tiempo real
5. Ver resultados (top 10 palabras) cuando el job complete

### 2. Cliente CLI

```bash
cd /app/backend

# Con texto directo
python client_demo.py --text "El rápido zorro marrón salta sobre el perro perezoso. El perro era muy perezoso."

# Con archivo
echo "MapReduce es un modelo de programación distribuida..." > test.txt
python client_demo.py --file test.txt --strategy round_robin

# Listar engines
python client_demo.py --list-engines
```

### 3. Simulación de Performance

```bash
cd /app/backend

# Crear archivo de prueba
echo "Lorem ipsum dolor sit amet..." > large_text.txt

# Ejecutar simulación con diferentes configuraciones
python simulate.py --text-file large_text.txt --configs "1,1;2,2;4,4" --output results.csv

# Ver resultados
cat results.csv
```

Esto generará un CSV con tiempos de ejecución para:
- 1 mapper + 1 reducer
- 2 mappers + 2 reducers  
- 4 mappers + 4 reducers

## 📚 API REST (Cliente ↔ Coordinator)

### POST /api/jobs
```json
{
  "text": "texto a procesar",
  "balancing_strategy": "round_robin"  // o "least_loaded"
```
./
├── backend/
│   ├── jobs.proto              # Definición gRPC
│   ├── server.py               # Coordinator (FastAPI + gRPC)
│   ├── engine.py               # Worker (mapper/reducer)
│   ├── client_demo.py          # Cliente CLI
│   ├── simulate.py             # Simulación de performance
│   ├── requirements.txt        # Dependencias Python
│   └── .env                    # Configuración

├── frontend/
│   ├── src/
│   │   ├── App.js              # Componente principal
│   │   ├── App.css             # Estilos dashboard técnico
│   │   └── components/
│   │       ├── JobForm.js       # Form de creación
│   │       ├── JobsList.js      # Lista de jobs
│   │       ├── EnginesDashboard.js  # Visualización engines
│   │       ├── LogsPanel.js     # Logs en tiempo real
│   │       └── StatsPanel.js    # Estadísticas
│   └── package.json

└── README.md                # Este archivo
```

## ⚙️ Configuración

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

## 🐛 Troubleshooting

### Engines no se conectan
```bash
# Verificar que el coordinator esté escuchando en 50051
netstat -tlnp | grep 50051

# Ver logs del coordinator
tail -f /var/log/supervisor/backend.*.log
```

### Jobs se quedan en estado "map" o "reduce"
- Verificar que hay engines del tipo correcto (mappers/reducers)
- Revisar logs de engines para ver errores
- Usar `client_demo.py --list-engines` para ver engines activos

### Frontend no carga datos
- Verificar REACT_APP_BACKEND_URL en frontend/.env
- Abrir DevTools > Network para ver errores de API
- Verificar CORS_ORIGINS en backend/.env

## 📈 Características

✅ Arquitectura cliente-servidor pura  
✅ MapReduce completo (Map → Shuffle → Reduce)  
✅ gRPC para comunicación engines-coordinator  
✅ Balanceo: Round Robin y Least Loaded  
✅ Fault tolerance: heartbeat y requeue  
✅ Dashboard React con polling en tiempo real  
✅ Persistencia en MongoDB  
✅ Cliente CLI y scripts de simulación  
✅ Logs detallados de asignaciones  

## 📦 Estructura de Archivos

```
/app/
├── backend/
│   ├── jobs.proto              # Definición gRPC
│   ├── server.py               # Coordinator (FastAPI + gRPC)
│   ├── engine.py               # Worker (mapper/reducer)
│   ├── client_demo.py          # Cliente CLI
│   ├── simulate.py             # Simulación de performance
│   ├── requirements.txt        # Dependencias Python
│   └── .env                    # Configuración
│
├── frontend/
│   ├── src/
│   │   ├── App.js              # Componente principal
│   │   ├── App.css             # Estilos dashboard técnico
│   │   └── components/
│   │       ├── JobForm.js       # Form de creación
│   │       ├── JobsList.js      # Lista de jobs
│   │       ├── EnginesDashboard.js  # Visualización engines
│   │       ├── LogsPanel.js     # Logs en tiempo real
│   │       └── StatsPanel.js    # Estadísticas
│   └── package.json
│
└── README.md                # Este archivo
```

## 🎯 Validación Cliente-Servidor

### Checklist

- [ ] Coordinator corriendo (verificar puerto 8000 y 50051)
- [ ] Al menos 2 mappers corriendo
- [ ] Al menos 2 reducers corriendo
- [ ] Frontend accesible en navegador
- [ ] Cliente puede crear job desde UI
- [ ] Dashboard muestra engines activos
- [ ] Jobs progresan: map → shuffle → reduce → done
- [ ] Resultados (top-10) se muestran al completar
- [ ] Logs muestran asignaciones en tiempo real
- [ ] Cliente NO se comunica directamente con engines

## 👥 Contribución

Este es un proyecto educativo. Mejoras sugeridas:

- [ ] Persistencia de jobs en MongoDB (actualmente en memoria)
- [ ] WebSocket para notificaciones en lugar de polling
- [ ] Visualización gráfica del flujo MapReduce
- [ ] Soporte para combiners (pre-agregación en mappers)
- [ ] Tests unitarios e integración
- [ ] Docker Compose para fácil deployment

## 📝 Licencia

MIT
