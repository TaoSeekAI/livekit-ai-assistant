FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 下载YOLO模型
RUN python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

# 复制应用代码
COPY . .

# 创建日志目录
RUN mkdir -p logs

# 运行agent
CMD ["python", "agent.py"]
