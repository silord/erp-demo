import os

class Config:
    ERP_TARGET = os.environ.get('ERP_TARGET', 'localhost:50051')
    FLASK_HOST = os.environ.get('ERPGRPCREPORT_HOST', '0.0.0.0')
    FLASK_PORT = int(os.environ.get('ERPGRPCREPORT_PORT', '8081'))
    GRPC_TIMEOUT = float(os.environ.get('ERPGRPCREPORT_GRPC_TIMEOUT', '10'))
    # Handday token endpoint and credentials (read-only from environment for security)
    # Note: do NOT put secrets into source; set these via environment variables.
    HANDDAY_TOKEN_URL = os.environ.get('HANDDAY_TOKEN_URL', 'https://open.handday.cn/grantauth/gettoken')
    HANDDAY_CORP_ID = os.environ.get('HANDDAY_CORP_ID')
    # appType may be numeric; keep as string here and convert where needed
    HANDDAY_APP_TYPE = os.environ.get('HANDDAY_APP_TYPE')
    HANDDAY_APP_ID = os.environ.get('HANDDAY_APP_ID')
    HANDDAY_APP_SECRET = os.environ.get('HANDDAY_APP_SECRET')
    HANDDAY_AUTH_TIMEOUT = float(os.environ.get('HANDDAY_AUTH_TIMEOUT', '5'))
    # Optional: pre-provided token (useful for testing or when token is obtained out-of-band)
    HANDDAY_TOKEN = os.environ.get('HANDDAY_TOKEN')

cfg = Config()
