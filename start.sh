#!/bin/bash

# 设置默认端口
if [ -z "$PORT" ]; then
    export PORT=5001
fi

echo "Starting application on port $PORT"

# 启动应用
exec gunicorn app:app --bind 0.0.0.0:$PORT --timeout 300 --workers 2 