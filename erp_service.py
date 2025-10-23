import grpc
import logging
from concurrent import futures
import initialization_pb2_grpc  # 替换为实际生成的文件名
import initialization_pb2
import order_pb2_grpc
import order_pb2
import common_pb2
import sync_store
from google.protobuf import empty_pb2

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger('erp_service')


class ERPInitializationServicer(initialization_pb2_grpc.InitializationServicer):
    # 必须实现的在线检查接口
    def CheckErpConnection(self, request, context):
        # 记录接收到的请求（Empty 没有字段，但保留日志位于将来扩展）
        logger.info('Received CheckErpConnection request from %s', context.peer())
        # The generated protobuf defines G_CheckErpConnectionResponse with fields Success and Msg
        # G_CheckErpConnectionResponse is generated dynamically by the protobuf
        # runtime via descriptors and may not be visible to static type checkers
        # like Pylance; ignore the attribute access warning here.
        resp = initialization_pb2.G_CheckErpConnectionResponse(  # type: ignore[attr-defined]
            Success=True,  # 模拟ERP在线
            Msg="OK"     # 消息说明
        )
        logger.info('Responding CheckErpConnection: Success=%s, Msg=%s', resp.Success, resp.Msg)
        return resp


class OrderServicer(order_pb2_grpc.OrderServicer):
    """实现部分 Order 服务，示例：实现 SynchroSaleOrderList 来同步订单列表"""
    def SynchroSaleOrderList(self, request, context):
        # request: G_SyncBillListRequest
        logger.info('SynchroSaleOrderList called with %d bills', len(request.Data))
        resp = order_pb2.G_SyncBillListInfoResponse()  # type: ignore[attr-defined]
        for bill in request.Data:
            info = order_pb2.G_SyncBillInfoResponse()  # type: ignore[attr-defined]
            info.ErpKey = getattr(bill, 'BillKey', '') or ''
            info.BillKey = getattr(bill, 'BillKey', '') or ''

            total_details = len(getattr(bill, 'Details', []))
            ok_count = 0
            errors = []

            # 验证每个明细（ProductKey、Qty、Price）
            for d in getattr(bill, 'Details', []):
                prod = getattr(d, 'ProductKey', '')
                qty = getattr(d, 'Qty', 0)
                price = getattr(d, 'Price', 0)
                if not prod:
                    errors.append('missing ProductKey')
                    continue
                if qty is None or qty <= 0:
                    errors.append(f'bad Qty for {prod}')
                    continue
                if price is None or price < 0:
                    errors.append(f'bad Price for {prod}')
                    continue
                ok_count += 1

            # 根据验证结果设置 SyncState/Msg
            if ok_count == total_details and total_details > 0:
                try:
                    info.SyncState = common_pb2.G_SyncStateType.SyncSuccess  # type: ignore[attr-defined]
                except Exception:
                    info.SyncState = 1
                info.SyncMsg = f'Synced {ok_count}/{total_details} details'
                info.ErrorCode = 0
            else:
                try:
                    info.SyncState = common_pb2.G_SyncStateType.SyncFail  # type: ignore[attr-defined]
                except Exception:
                    info.SyncState = 2
                if total_details == 0:
                    info.SyncMsg = 'No details to sync'
                else:
                    info.SyncMsg = 'Errors: ' + ';'.join(errors[:5])
                info.ErrorCode = 1001

            # 复制单据类型（如果有）
            info.BillType = getattr(bill, 'BillType', 0)
            resp.Data.append(info)
            logger.info('Processed bill %s: %s', info.BillKey, info.SyncMsg)
            # persist result
            try:
                sync_store.save_result(info.BillKey, info.ErpKey, info.SyncState, info.SyncMsg, info.ErrorCode)
            except Exception as e:
                logger.warning('Failed to save sync result for %s: %s', info.BillKey, e)

        return resp


def serve(host='[::]:50051', max_workers=10):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    initialization_pb2_grpc.add_InitializationServicer_to_server(ERPInitializationServicer(), server)
    # 注册 Order 服务
    order_pb2_grpc.add_OrderServicer_to_server(OrderServicer(), server)
    # Try multiple addresses to be robust across IPv6/IPv4 system configurations
    # derive port from the requested host so fallbacks use the same port
    try:
        # handle formats like [::]:50051 or 0.0.0.0:50051
        if host.startswith('['):
            port = host.split(']:')[-1]
        else:
            port = host.split(':')[-1]
    except Exception:
        port = '50051'
    bind_candidates = [host, f'0.0.0.0:{port}', f'127.0.0.1:{port}', f'[::]:{port}']
    bound_address = None
    for addr in bind_candidates:
        try:
            added = server.add_insecure_port(addr)
        except Exception:
            added = 0
        if added and added != 0:
            bound_address = addr
            break

    if not bound_address:
        logger.error('Failed to bind to any address from %s', bind_candidates)
        raise RuntimeError(f'Failed to bind to addresses: {bind_candidates}')

    logger.info('Starting gRPC server on %s (workers=%d)', bound_address, max_workers)
    server.start()
    try:
        # block until termination
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info('Server interrupted by user, stopping...')
        server.stop(0)


def parse_host(default='[::]:50051'):
    import os
    import argparse
    parser = argparse.ArgumentParser(description='Start ERP gRPC server')
    parser.add_argument('--host', default=os.getenv('ERP_HOST', default), help='Host:port to bind (e.g. [::]:50051 or 0.0.0.0:50051)')
    parser.add_argument('--workers', type=int, default=int(os.getenv('ERP_WORKERS', '10')),
                        help='Number of worker threads for the gRPC server')
    args = parser.parse_args()
    return args.host, args.workers


if __name__ == '__main__':
    host, workers = parse_host()
    logger.info('Configured host=%s workers=%d', host, workers)
    serve(host=host, max_workers=workers)