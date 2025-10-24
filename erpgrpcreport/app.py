from flask import Flask, jsonify
from .grpc_client import call_synchro_sample
from .config import cfg

app = Flask(__name__)


@app.route('/health')
def health():
    return jsonify({'status': 'ok'})


@app.route('/report')
def report():
    success, data = call_synchro_sample()
    if success:
        # convert proto to dict in a simple way
        try:
            # Some responses are proto messages; use their string repr
            return jsonify({'ok': True, 'response': str(data)})
        except Exception:
            return jsonify({'ok': True, 'response': repr(data)})
    else:
        return jsonify({'ok': False, 'error': data}), 500


def run():
    app.run(host=cfg.FLASK_HOST, port=cfg.FLASK_PORT)


if __name__ == '__main__':
    run()
