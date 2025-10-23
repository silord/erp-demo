import os
from grpc_tools import protoc

# 遍历所有proto文件
for file in os.listdir('.'):
    if file.endswith('.proto'):
        protoc.main([
            'grpc_tools.protoc',
            f'--python_out=.',
            f'--grpc_python_out=.',
            file
        ])