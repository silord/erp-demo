import grpc
import order_pb2_grpc, order_pb2, common_pb2

channel = grpc.insecure_channel('localhost:50053')
stub = order_pb2_grpc.OrderStub(channel)
req = order_pb2.G_SyncBillListRequest()
item = order_pb2.G_SyncBillRequest()
item.BillKey = 'BILL-123'
item.BillType = common_pb2.G_BillType.SalesOrder
req.Data.append(item)
resp = stub.SynchroSaleOrderList(req, timeout=5)
print('resp data count=', len(resp.Data))
if resp.Data:
    print(resp.Data[0].BillKey, resp.Data[0].SyncState, resp.Data[0].SyncMsg)
