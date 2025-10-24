ERPgrpcreport

Lightweight gRPC reporter service that calls ERP Order.SynchroSaleOrderList with a sample request and returns a small report.

Build image (from repo root):

    docker build -f erpgrpcreport/Dockerfile -t erpgrpcreport:latest .

Run:

    docker run -p 8081:8081 --env ERP_TARGET=erp.example.com:50051 erpgrpcreport:latest

Endpoints:
- GET /health
- GET /report -> triggers a sample gRPC call and returns proto text
