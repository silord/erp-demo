"""Small helper to run integration-sync related actions for manual调试.

Usage:
  python sync_runner.py --show       # print effective config
  python sync_runner.py --save-sample  # write sync_config.json sample
  python sync_runner.py --get-token [--dry-run]  # optionally perform token request
"""
import argparse
import requests
from sync_config import load_config, save_sample_config
import os
import json
import grpc
import order_pb2
import order_pb2_grpc


def show_config():
    cfg = load_config()
    print('Effective config:')
    print(json.dumps({
        'token_url': cfg.token_url,
        'corp_id': cfg.corp_id,
        'app_id': cfg.app_id,
        'app_secret': '***' if cfg.app_secret else None,
        'sync_target': cfg.sync_target,
    }, indent=2, ensure_ascii=False))


def get_token(cfg, dry_run=True):
    payload = {
        'corpId': cfg.corp_id,
        'appId': cfg.app_id,
        'appSecret': cfg.app_secret,
    }
    print('Token request payload:')
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    if dry_run:
        print('\nDry run: not sending HTTP request. Use --no-dry-run to actually send it.')
        return None
    try:
        r = requests.post(cfg.token_url, json=payload, timeout=10)
        print('HTTP', r.status_code)
        print(r.text[:2000])
        return r.json()
    except Exception as e:
        print('Request failed:', e)
        return None


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('--show', action='store_true')
    p.add_argument('--save-sample', action='store_true')
    p.add_argument('--get-token', action='store_true')
    p.add_argument('--call-order', action='store_true', help='Build and optionally call Order.SynchroSaleOrderList')
    p.add_argument('--target', default=os.environ.get('ERP_TARGET', 'localhost:50051'), help='gRPC target for Order service')
    p.add_argument('--no-dry-run', action='store_true')
    args = p.parse_args(argv)

    if args.save_sample:
        path = save_sample_config()
        print('Wrote sample config to', path)
        return

    if args.show:
        show_config()
        return

    if args.get_token:
        cfg = load_config()
        get_token(cfg, dry_run=not args.no_dry_run)
        return

    if args.call_order:
        # build a minimal example G_SyncBillListRequest
        sample = order_pb2.G_SyncBillListRequest()
        item = order_pb2.G_SyncBillRequest()
        item.BillKey = 'BILL-TEST-1'
        item.BillCode = 'BILL-TEST-1'
        item.TotalPrice = 123.45
        # add one detail
        d = order_pb2.G_SyncBillDetailInfo()
        d.ProductKey = 'PROD-001'
        d.ProductName = '示例商品'
        d.Qty = 2
        d.Price = 50
        item.Details.extend([d])
        sample.Data.extend([item])
        print('Constructed sample G_SyncBillListRequest:')
        print(sample)

        if not args.no_dry_run:
            print('\nDry run: not calling gRPC. Use --no-dry-run to actually call target', args.target)
            return

        # perform gRPC call
        try:
            with grpc.insecure_channel(args.target) as ch:
                stub = order_pb2_grpc.OrderStub(ch)
                resp = stub.SynchroSaleOrderList(sample, timeout=10)
                print('gRPC response:')
                print(resp)
        except Exception as e:
            print('gRPC call failed:', e)
        return

    p.print_help()


if __name__ == '__main__':
    main()
