import grpc
import time
import logging
from google.protobuf import empty_pb2
import initialization_pb2_grpc, initialization_pb2

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger('test_client')


def check_erp(max_retries=3, backoff_secs=1.0):
	import os
	import argparse

	# Determine target from environment or default
	default_target = os.getenv('ERP_TARGET', 'localhost:50051')
	parser = argparse.ArgumentParser(description='Test ERP gRPC client')
	parser.add_argument('--target', default=default_target, help='gRPC target (host:port)')
	parser.add_argument('--retries', type=int, default=max_retries, help='Max retry attempts')
	parser.add_argument('--backoff', type=float, default=backoff_secs, help='Backoff base seconds')
	args, _ = parser.parse_known_args()
	target = args.target
	max_retries = args.retries
	backoff_secs = args.backoff
	channel = grpc.insecure_channel(target)
	stub = initialization_pb2_grpc.InitializationStub(channel)

	attempt = 0
	while attempt < max_retries:
		attempt += 1
		try:
			logger.info('Attempt %d: calling CheckErpConnection on %s', attempt, target)
			response = stub.CheckErpConnection(empty_pb2.Empty(), timeout=5)
			logger.info('Received response: Success=%s, Msg=%s', response.Success, response.Msg)
			return response
		except grpc.RpcError as e:
			logger.warning('gRPC error on attempt %d: %s', attempt, e)
			if attempt < max_retries:
				sleep_for = backoff_secs * attempt
				logger.info('Retrying after %.1fs...', sleep_for)
				time.sleep(sleep_for)
			else:
				logger.error('Max retries reached, giving up')
				raise


if __name__ == '__main__':
	try:
		resp = check_erp(max_retries=4, backoff_secs=1.0)
		print(f"ERP在线: {resp.Success}, 消息: {resp.Msg}") # type: ignore
	except Exception as ex:
		logger.error('Final error calling CheckErpConnection: %s', ex)
		print('无法连接到 ERP 服务，请检查服务是否已启动并监听 localhost:50051')