#!/bin/sh
set -e
# start admin in background
echo "Starting admin_server on ${FLASK_ADMIN_HOST:-127.0.0.1}:${FLASK_ADMIN_PORT:-8080}"
python admin_server.py &
ADMIN_PID=$!
echo "admin pid=${ADMIN_PID}"

# start grpc server in foreground
echo "Starting erp_service"
python erp_service.py

# when erp_service exits, kill admin
kill $ADMIN_PID || true