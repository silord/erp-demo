import grpc
import order_pb2
import order_pb2_grpc
from google.protobuf import empty_pb2
from .config import cfg
from .auth import get_handday_token
import logging

logger = logging.getLogger(__name__)

def call_synchro_sample(target: str = None, timeout: float = None):
    """Call Order.SynchroSaleOrderList on target with a small sample request.

    Returns tuple (success: bool, response or error str)
    """
    tgt = target or cfg.ERP_TARGET
    to = timeout or cfg.GRPC_TIMEOUT
    # build sample request
    sample = order_pb2.G_SyncBillListRequest()
    item = order_pb2.G_SyncBillRequest()
    item.BillKey = 'ERPGRPC-REPORT-1'
    item.BillCode = 'ERPGRPC-REPORT-1'
    item.TotalPrice = 1.23
    d = order_pb2.G_SyncBillDetailInfo()
    d.ProductKey = 'REPORT-PROD'
    d.ProductName = '报告样例商品'
    d.Qty = 1
    d.Price = 1.23
    item.Details.extend([d])
    sample.Data.extend([item])

    try:
        # Obtain token (if available) and attach as metadata
        ok, token_or_err = get_handday_token()
        metadata = None
        if ok:
            token = token_or_err
            metadata = [("authorization", f"Bearer {token}")]
            logger.debug('Using Handday token for gRPC call')
        else:
            logger.warning('Failed to get Handday token: %s. Proceeding without token.', token_or_err)

        with grpc.insecure_channel(tgt) as ch:
            stub = order_pb2_grpc.OrderStub(ch)
            try:
                resp = stub.SynchroSaleOrderList(sample, timeout=to, metadata=metadata)
                return True, resp
            except grpc.RpcError as e:
                # If unauthenticated, try once to refresh token and retry
                if e.code() in (grpc.StatusCode.UNAUTHENTICATED, grpc.StatusCode.PERMISSION_DENIED):
                    logger.info('RPC unauthenticated; attempting to refresh token and retry')
                    ok2, token_or_err2 = get_handday_token()
                    if ok2:
                        metadata2 = [("authorization", f"Bearer {token_or_err2}")]
                        try:
                            resp2 = stub.SynchroSaleOrderList(sample, timeout=to, metadata=metadata2)
                            return True, resp2
                        except Exception as e2:
                            return False, f'RPC retry failed: {e2}'
                    else:
                        return False, f'RPC failed (unauthenticated) and token refresh failed: {token_or_err2}'
                # other RPC errors
                return False, f'RPC failed: {e.code()} {e.details()}'
    except grpc.RpcError as e:
        return False, f'RPC failed: {e.code()} {e.details()}'
    except Exception as e:
        return False, str(e)
