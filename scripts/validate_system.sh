#!/bin/bash

# MapReduce Visual - System Validation
# Verifica que todos los componentes estén funcionando

echo "========================================"
echo "MapReduce Visual - System Validation"
echo "========================================"
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BACKEND_URL="localhost:8000"
ERRORS=0

# Función para verificar
check() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2"
        ERRORS=$((ERRORS + 1))
    fi
}

# 1. Verificar que el backend esté corriendo
echo "1. Backend Coordinator (REST API)"
curl -s "$BACKEND_URL/" -o /dev/null
check $? "REST API responding on port 8000"

# 2. Verificar gRPC server
echo ""
echo "2. gRPC Server"
netstat -tlnp | grep ":50051" > /dev/null 2>&1
check $? "gRPC server listening on port 50051"

# 3. Verificar frontend
echo ""
echo "3. Frontend"
curl -s "http://localhost:3000" -o /dev/null
check $? "React frontend accessible"

# 4. Verificar engines
echo ""
echo "4. Engines (Workers)"
STATS=$(curl -s "$BACKEND_URL/stats")
TOTAL_ENGINES=$(echo $STATS | python3 -c "import sys, json; print(json.load(sys.stdin)['total_engines'])" 2>/dev/null)
MAPPERS=$(echo $STATS | python3 -c "import sys, json; print(json.load(sys.stdin)['mappers'])" 2>/dev/null)
REDUCERS=$(echo $STATS | python3 -c "import sys, json; print(json.load(sys.stdin)['reducers'])" 2>/dev/null)

if [ "$TOTAL_ENGINES" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} $TOTAL_ENGINES engines connected ($MAPPERS mappers, $REDUCERS reducers)"
else
    echo -e "${YELLOW}⚠${NC} No engines connected. Run: /app/start_engines.sh"
fi

# 5. Verificar archivos críticos
echo ""
echo "5. Critical Files"
[ -f ../backend/server.py ] && check 0 "server.py exists" || check 1 "server.py missing"
[ -f ../backend/engine.py ] && check 0 "engine.py exists" || check 1 "engine.py missing"
[ -f ../backend/jobs_pb2.py ] && check 0 "gRPC stubs generated" || check 1 "gRPC stubs missing"
[ -f ../frontend/src/App.js ] && check 0 "Frontend App.js exists" || check 1 "Frontend missing"

# 6. Test job creation (opcional)
echo ""
echo "6. End-to-End Test (Optional)"
if [ "$TOTAL_ENGINES" -gt 0 ]; then
    echo "Creating test job..."
    JOB_RESPONSE=$(curl -s -X POST "$BACKEND_URL/jobs" \
        -H "Content-Type: application/json" \
        -d '{"text":"test job validation quick brown fox lazy dog", "balancing_strategy":"round_robin"}')
    
    JOB_ID=$(echo $JOB_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['job_id'])" 2>/dev/null)
    
    if [ -n "$JOB_ID" ]; then
        check 0 "Test job created: $JOB_ID"
        echo "  Waiting for completion..."
        
        for i in {1..15}; do
            sleep 1
            STATUS=$(curl -s "$BACKEND_URL/jobs/$JOB_ID" | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null)
            echo -n "."
            if [ "$STATUS" = "completada" ]; then
                echo ""
                check 0 "Job completed successfully"
                break
            fi
        done
        
        if [ "$STATUS" != "completada" ]; then
            echo ""
            echo -e "${YELLOW}⚠${NC} Job still processing (status: $STATUS)"
        fi
    else
        check 1 "Failed to create test job"
    fi
else
    echo -e "${YELLOW}⚠${NC} Skipping (no engines available)"
fi

# Resumen
echo ""
echo "========================================"
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "System is ready to use:"
    echo "  Frontend: https://visual-map-reduce.preview.emergentagent.com"
    echo "  API Docs: $BACKEND_URL/docs"
else
    echo -e "${RED}✗ $ERRORS checks failed${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Restart backend: sudo supervisorctl restart backend"
    echo "  2. Start engines: ./scripts/start_engines.sh"
    echo "  3. Check logs: tail -f /var/log/supervisor/backend.*.log"
fi
echo "========================================"
