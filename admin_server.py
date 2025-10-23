from flask import Flask, jsonify, render_template_string, request
import sync_store
import os
import sync_config
import requests
import grpc
import order_pb2
import order_pb2_grpc
from concurrent.futures import ThreadPoolExecutor
import uuid
import time

# Simple in-memory task store: {task_id: {status, result, error, started_at, finished_at}}
TASKS = {}
EXECUTOR = ThreadPoolExecutor(max_workers=4)

app = Flask(__name__)


HTML_TEMPLATE = """
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>Sync Results</title>
    <style>
      body{font-family:Segoe UI, Roboto, Helvetica, Arial, sans-serif;margin:24px}
      table{border-collapse:collapse;width:100%}
      th,td{border:1px solid #ddd;padding:8px}
      th{background:#f4f4f4;text-align:left}
      .meta{color:#666;margin-bottom:12px}
    </style>
    <script>
      async function load(){
        const res = await fetch('/api/sync-results');
        const data = await res.json();
        const tbody = document.getElementById('tbody');
        tbody.innerHTML = '';
        data.forEach(r=>{
          const tr = document.createElement('tr');
          ['id','bill_key','erp_key','sync_state','sync_msg','error_code','created_at'].forEach(k=>{
            const td = document.createElement('td');
            td.textContent = r[k];
            tr.appendChild(td);
          });
          tbody.appendChild(tr);
        });
        document.getElementById('count').textContent = data.length;
      }

      async function trigger(){
        const action = document.getElementById('action').value;
        const real = document.getElementById('realrun').checked;
        const target = document.getElementById('target').value;
        const body = { action: action, dry_run: !real, target: target };
        const resp = await fetch('/admin/trigger', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body)});
        const data = await resp.json();
        if(data.task_id){
          document.getElementById('result').textContent = '任务已提交: ' + data.task_id + '\n轮询中...';
          pollTask(data.task_id);
        } else {
          document.getElementById('result').textContent = JSON.stringify(data, null, 2);
        }
      }

      async function pollTask(taskId){
        try{
          const r = await fetch('/admin/task/' + taskId);
          const j = await r.json();
          document.getElementById('result').textContent = JSON.stringify(j, null, 2);
          if(j.status === 'queued' || j.status === 'running'){
            setTimeout(()=>pollTask(taskId), 1500);
          } else {
            // finished or error
            load(); // refresh table
          }
        } catch(e){
          document.getElementById('result').textContent = '轮询出错: ' + e;
        }
      }

      window.onload = ()=>{ load(); setInterval(load, 5000); };
    </script>
  </head>
  <body>
    <h1>Sync Results</h1>
    <div style="margin-bottom:12px">
      <label for="action">操作:</label>
      <select id="action">
        <option value="get-token">获取 token</option>
        <option value="call-order">触发样例同步（Order.SynchroSaleOrderList）</option>
      </select>
      <label style="margin-left:8px"><input type="checkbox" id="realrun" /> 真实调用</label>
      <label style="margin-left:8px">gRPC目标: <input id="target" value="localhost:50051" style="width:160px"/></label>
      <button onclick="trigger()" style="margin-left:8px">触发联调</button>
    </div>
    <div class="meta">Total: <span id="count">0</span> — 数据每 5s 刷新一次</div>
    <table>
    <h2>联调结果</h2>
    <pre id="result" style="background:#f8f8f8;border:1px solid #eee;padding:8px;min-height:80px;white-space:pre-wrap"></pre>
      <thead>
        <tr>
          <th>id</th><th>bill_key</th><th>erp_key</th><th>sync_state</th><th>sync_msg</th><th>error_code</th><th>created_at</th>
        </tr>
      </thead>
      <tbody id="tbody"></tbody>
    </table>
  </body>
</html>
"""


@app.route('/api/sync-results')
def api_sync_results():
    """Return latest sync results as JSON. Query param `limit` optional."""
    try:
        limit = int(request.args.get('limit', '100'))
    except Exception:
        limit = 100
    rows = sync_store.list_results(limit)
    # list_results returns list of tuples; convert to dicts
    keys = ['id', 'bill_key', 'erp_key', 'sync_state', 'sync_msg', 'error_code', 'created_at']
    data = [dict(zip(keys, row)) for row in rows]
    return jsonify(data)


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/admin/trigger', methods=['POST'])
def admin_trigger():
  """Submit a trigger job to background executor and return task id."""
  body = request.get_json(force=True, silent=True) or {}
  action = body.get('action', 'get-token')
  dry_run = body.get('dry_run', True)
  target = body.get('target') or request.args.get('target')

  task_id = str(uuid.uuid4())
  TASKS[task_id] = {'status': 'queued', 'result': None, 'error': None, 'started_at': None, 'finished_at': None}

  def run_trigger_job(body):
    TASKS[task_id]['status'] = 'running'
    TASKS[task_id]['started_at'] = time.time()
    try:
      action = body.get('action', 'get-token')
      dry_run = body.get('dry_run', True)
      target = body.get('target')

      if action == 'get-token':
        cfg = sync_config.load_config()
        payload = {'corpId': cfg.corp_id, 'appId': cfg.app_id, 'appSecret': cfg.app_secret}
        if dry_run:
          TASKS[task_id]['result'] = {'mode': 'dry-run', 'payload': payload}
        else:
          r = requests.post(cfg.token_url, json=payload, timeout=10)
          TASKS[task_id]['result'] = {'mode': 'live', 'http_status': r.status_code, 'body': r.text}

      elif action == 'call-order':
        sample = order_pb2.G_SyncBillListRequest()
        item = order_pb2.G_SyncBillRequest()
        item.BillKey = 'BILL-UI-1'
        item.BillCode = 'BILL-UI-1'
        item.TotalPrice = 100.0
        d = order_pb2.G_SyncBillDetailInfo()
        d.ProductKey = 'PROD-UI-1'
        d.ProductName = '示例商品UI'
        d.Qty = 1
        d.Price = 100
        item.Details.extend([d])
        sample.Data.extend([item])

        if dry_run:
          TASKS[task_id]['result'] = {'mode': 'dry-run', 'proto': str(sample)}
        else:
          tgt = target or os.environ.get('ERP_TARGET', 'localhost:50051')
          with grpc.insecure_channel(tgt) as ch:
            stub = order_pb2_grpc.OrderStub(ch)
            resp = stub.SynchroSaleOrderList(sample, timeout=30)
            TASKS[task_id]['result'] = {'mode': 'live', 'response': str(resp)}
      else:
        TASKS[task_id]['error'] = 'unknown action'
        TASKS[task_id]['status'] = 'error'
        return

      TASKS[task_id]['status'] = 'finished'
    except Exception as e:
      TASKS[task_id]['error'] = str(e)
      TASKS[task_id]['status'] = 'error'
    finally:
      TASKS[task_id]['finished_at'] = time.time()

  EXECUTOR.submit(run_trigger_job, body)
  return jsonify({'task_id': task_id, 'status': 'queued'})


@app.route('/admin/task/<task_id>')
def admin_task_status(task_id):
  t = TASKS.get(task_id)
  if not t:
    return jsonify({'status': 'error', 'error': 'not found'}), 404
  # shallow copy to avoid exposing internal
  return jsonify({
    'status': t['status'],
    'result': t['result'],
    'error': t['error'],
    'started_at': t['started_at'],
    'finished_at': t['finished_at'],
  })


def ensure_deps():
    # simple runtime hint: Flask should already be importable; this file is safe to import without extra checks
    pass


if __name__ == '__main__':
    # Default host/port; allow override with env FLASK_ADMIN_HOST/FLASK_ADMIN_PORT
    host = os.environ.get('FLASK_ADMIN_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_ADMIN_PORT', '8080'))
    print(f"Starting admin HTTP interface on http://{host}:{port}/")
    app.run(host=host, port=port)
