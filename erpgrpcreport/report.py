def format_response(proto_resp):
    """Very small helper to format proto responses into plain dicts or strings."""
    try:
        return {'text': str(proto_resp)}
    except Exception:
        return {'text': repr(proto_resp)}
