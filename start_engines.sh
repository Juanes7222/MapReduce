#!/bin/bash

# MapReduce Visual - Start Engines Script
# Este script inicia múltiples engines (mappers y reducers)

echo "=================================="
echo "MapReduce Visual - Starting Engines"
echo "=================================="

# Configuración
NUM_MAPPERS=${1:-2}
NUM_REDUCERS=${2:-2}

cd /app/backend

# Detener engines existentes
echo "Stopping existing engines..."
pkill -f "engine.py" 2>/dev/null
sleep 2

# Iniciar mappers
echo "Starting $NUM_MAPPERS mappers..."
for i in $(seq 1 $NUM_MAPPERS); do
    python engine.py --engine-id mapper-$i --role mapper --capacity 5 > /tmp/mapper$i.log 2>&1 &
    echo "  - mapper-$i started (PID: $!)"
done

# Iniciar reducers
echo "Starting $NUM_REDUCERS reducers..."
for i in $(seq 1 $NUM_REDUCERS); do
    python engine.py --engine-id reducer-$i --role reducer --capacity 5 > /tmp/reducer$i.log 2>&1 &
    echo "  - reducer-$i started (PID: $!)"
done

# Esperar a que se registren
echo ""
echo "Waiting for engines to register..."
sleep 4

# Verificar engines registrados
echo ""
echo "Registered engines:"
curl -s "https://visual-map-reduce.preview.emergentagent.com/api/engines" | python3 -c "
import sys, json
try:
    engines = json.load(sys.stdin)
    print(f'  Total: {len(engines)} engines')
    mappers = [e for e in engines if e['role'] == 'mapper']
    reducers = [e for e in engines if e['role'] == 'reducer']
    print(f'  - Mappers: {len(mappers)}')
    print(f'  - Reducers: {len(reducers)}')
    for e in engines:
        print(f'    {e[\"engine_id\"]} ({e[\"role\"]}): {e[\"status\"]}')
except:
    print('  Error checking engines')
"

echo ""
echo "=================================="
echo "✓ Engines started successfully!"
echo ""
echo "View logs:"
echo "  tail -f /tmp/mapper*.log"
echo "  tail -f /tmp/reducer*.log"
echo ""
echo "Stop engines:"
echo "  pkill -f engine.py"
echo "=================================="
