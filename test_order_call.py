import os
import argparse
import grpc
import order_pb2_grpc, order_pb2, common_pb2

parser = argparse.ArgumentParser()
parser.add_argument('--target', default=os.getenv('ERP_TARGET', 'localhost:50056'))
args = parser.parse_args()

channel = grpc.insecure_channel(args.target)
stub = order_pb2_grpc.OrderStub(channel)
req = order_pb2.G_SyncBillListRequest()  # type: ignore[attr-defined]
item = order_pb2.G_SyncBillRequest()  # type: ignore[attr-defined]
item.BillKey = 'BILL-XYZ'
item.BillType = common_pb2.G_BillType.SalesOrder  # type: ignore[attr-defined]
req.Data.append(item)
try:
    resp = stub.SynchroSaleOrderList(req, timeout=5)
    print('resp data count=', len(resp.Data))
    if resp.Data:
        print(resp.Data[0].BillKey, resp.Data[0].SyncState, resp.Data[0].SyncMsg)
except Exception as e:
    print('RPC error:', e)
