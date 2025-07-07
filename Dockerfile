# 使用官方Python 3.9 slim镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p uploads results

# 设置环境变量
ENV FLASK_ENV=production
ENV PORT=5001

# 暴露端口
EXPOSE $PORT

# 启动应用
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--timeout", "300", "--workers", "2", "app:app"] 