# 部署指南

## 目录
1. [环境要求](#环境要求)
2. [本地开发部署](#本地开发部署)
3. [生产环境部署](#生产环境部署)
4. [配置说明](#配置说明)
5. [故障排除](#故障排除)

## 环境要求

### 最小要求
- **CPU**: 4核心
- **内存**: 8GB RAM
- **存储**: 20GB可用空间
- **网络**: 10Mbps上行/下行

### 推荐配置
- **CPU**: 8核心+
- **内存**: 16GB+ RAM
- **GPU**: NVIDIA GPU (用于视觉处理)
- **存储**: 50GB+ SSD
- **网络**: 100Mbps+

### 软件要求
- Docker 20.10+
- Docker Compose 2.0+
- Python 3.10+ (本地开发)
- Android Studio (Android开发)
- Node.js 18+ (可选，用于管理工具)

## 本地开发部署

### 1. 克隆项目

```bash
git clone https://github.com/YOUR_USERNAME/livekit-ai-assistant.git
cd livekit-ai-assistant
```

### 2. 配置环境变量

创建 `.env` 文件:

```bash
cp backend/.env.example backend/.env
```

编辑 `backend/.env`:

```env
# LiveKit配置
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret

# OpenAI配置
OPENAI_API_KEY=sk-your-api-key-here

# 可选: DeepGram (更快的STT)
# DEEPGRAM_API_KEY=your-deepgram-key

# 可选: ElevenLabs (更好的TTS)
# ELEVENLABS_API_KEY=your-elevenlabs-key
```

### 3. 启动LiveKit Server

使用Docker Compose:

```bash
docker-compose up -d livekit
```

验证服务运行:

```bash
docker-compose logs -f livekit
```

应该看到:
```
livekit_1 | INF starting LiveKit server version=...
livekit_1 | INF server listening addr=:7880
```

### 4. 启动Python Agent

#### 方式1: 使用Docker (推荐)

```bash
docker-compose up -d agent
docker-compose logs -f agent
```

#### 方式2: 本地运行

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 下载YOLO模型
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

# 运行Agent
python agent.py
```

### 5. 构建Android客户端

```bash
cd android-client

# 配置LiveKit服务器地址
# 如果使用模拟器，使用 10.0.2.2 代替 localhost
# 如果使用真机，使用电脑的局域网IP
echo "LIVEKIT_URL=ws://10.0.2.2:7880" > local.properties

# 构建应用
./gradlew assembleDebug

# 安装到设备
./gradlew installDebug
```

### 6. 测试系统

1. 打开Android应用
2. 点击"连接"按钮
3. 允许麦克风和摄像头权限
4. 开始对话测试

## 生产环境部署

### 1. 服务器准备

#### 1.1 系统要求

- Ubuntu 22.04 LTS (推荐)
- Docker和Docker Compose已安装
- 防火墙配置:
  ```bash
  # LiveKit端口
  sudo ufw allow 7880/tcp   # HTTP/WebSocket
  sudo ufw allow 7881/tcp   # TURN
  sudo ufw allow 7882/udp   # WebRTC
  sudo ufw allow 50000:50100/udp  # RTC端口范围
  ```

#### 1.2 域名和SSL证书

LiveKit需要HTTPS/WSS才能在生产环境工作:

```bash
# 使用certbot获取Let's Encrypt证书
sudo apt install certbot
sudo certbot certonly --standalone -d your-domain.com
```

### 2. 配置生产环境

#### 2.1 更新 livekit.yaml

```yaml
port: 7880
bind_addresses:
  - "0.0.0.0"

rtc:
  port_range_start: 50000
  port_range_end: 50100
  use_external_ip: true
  # 配置TURN服务器
  turn_servers:
    - host: turn.your-domain.com
      port: 3478
      protocol: udp

keys:
  # 使用强密钥！
  production_key: your-strong-secret-key-here

# 启用TLS
cert_file: /path/to/cert.pem
key_file: /path/to/key.pem

logging:
  level: info
  json: true

room:
  auto_create: true
  empty_timeout: 300
  max_participants: 100

# 限速配置
limit:
  bytes_per_sec: 10_000_000  # 10MB/s
```

#### 2.2 生产环境 Docker Compose

创建 `docker-compose.prod.yml`:

```yaml
version: '3.9'

services:
  livekit:
    image: livekit/livekit-server:latest
    command: --config /etc/livekit.yaml
    ports:
      - "7880:7880"
      - "7881:7881"
      - "7882:7882/udp"
      - "50000-50100:50000-50100/udp"
    volumes:
      - ./livekit.yaml:/etc/livekit.yaml
      - /path/to/certs:/certs:ro
    restart: always
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G

  agent:
    build:
      context: ./backend
    environment:
      - LIVEKIT_URL=wss://your-domain.com
      - LIVEKIT_API_KEY=${LIVEKIT_API_KEY}
      - LIVEKIT_API_SECRET=${LIVEKIT_API_SECRET}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - LOG_LEVEL=INFO
    volumes:
      - ./backend:/app
      - agent-logs:/app/logs
    restart: always
    deploy:
      replicas: 2  # 运行2个agent实例
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  # 可选: Redis用于会话共享
  redis:
    image: redis:7-alpine
    restart: always
    volumes:
      - redis-data:/data

volumes:
  agent-logs:
  redis-data:
```

### 3. 使用Kubernetes部署 (高级)

#### 3.1 LiveKit Helm Chart

```bash
# 添加LiveKit Helm仓库
helm repo add livekit https://helm.livekit.io
helm repo update

# 创建命名空间
kubectl create namespace livekit

# 安装LiveKit
helm install livekit livekit/livekit-server \
  --namespace livekit \
  --set livekit.config.keys.your_key=your_secret \
  --set service.type=LoadBalancer
```

#### 3.2 Agent Deployment

创建 `k8s/agent-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: livekit-agent
  namespace: livekit
spec:
  replicas: 3
  selector:
    matchLabels:
      app: livekit-agent
  template:
    metadata:
      labels:
        app: livekit-agent
    spec:
      containers:
      - name: agent
        image: your-registry/livekit-agent:latest
        env:
        - name: LIVEKIT_URL
          value: "ws://livekit-server:7880"
        - name: LIVEKIT_API_KEY
          valueFrom:
            secretKeyRef:
              name: livekit-keys
              key: api-key
        - name: LIVEKIT_API_SECRET
          valueFrom:
            secretKeyRef:
              name: livekit-keys
              key: api-secret
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: openai-keys
              key: api-key
        resources:
          limits:
            nvidia.com/gpu: 1
            memory: "4Gi"
            cpu: "2"
          requests:
            memory: "2Gi"
            cpu: "1"
---
apiVersion: v1
kind: Secret
metadata:
  name: livekit-keys
  namespace: livekit
type: Opaque
stringData:
  api-key: your-api-key
  api-secret: your-api-secret
---
apiVersion: v1
kind: Secret
metadata:
  name: openai-keys
  namespace: livekit
type: Opaque
stringData:
  api-key: sk-your-openai-key
```

部署:

```bash
kubectl apply -f k8s/agent-deployment.yaml
```

### 4. Android生产构建

#### 4.1 配置生产服务器

编辑 `android-client/app/src/main/res/values/config.xml`:

```xml
<resources>
    <string name="livekit_url">wss://your-domain.com</string>
    <string name="api_endpoint">https://your-api-server.com</string>
</resources>
```

#### 4.2 生成签名密钥

```bash
keytool -genkey -v -keystore release.keystore \
  -alias your-app-alias \
  -keyalg RSA -keysize 2048 \
  -validity 10000
```

#### 4.3 配置签名

编辑 `android-client/app/build.gradle`:

```gradle
android {
    signingConfigs {
        release {
            storeFile file("../release.keystore")
            storePassword System.getenv("KEYSTORE_PASSWORD")
            keyAlias System.getenv("KEY_ALIAS")
            keyPassword System.getenv("KEY_PASSWORD")
        }
    }

    buildTypes {
        release {
            signingConfig signingConfigs.release
            minifyEnabled true
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
}
```

#### 4.4 构建发布版本

```bash
export KEYSTORE_PASSWORD=your-password
export KEY_ALIAS=your-alias
export KEY_PASSWORD=your-key-password

./gradlew assembleRelease
```

APK位于: `app/build/outputs/apk/release/app-release.apk`

## 配置说明

### LiveKit Server配置

| 参数 | 说明 | 默认值 |
|------|------|--------|
| port | HTTP/WebSocket端口 | 7880 |
| rtc.port_range_start | RTC端口范围起始 | 50000 |
| rtc.port_range_end | RTC端口范围结束 | 50100 |
| room.max_participants | 最大参与者数 | 100 |
| room.empty_timeout | 空房间超时(秒) | 300 |

### Agent配置

| 环境变量 | 说明 | 必需 |
|----------|------|------|
| LIVEKIT_URL | LiveKit服务器地址 | 是 |
| LIVEKIT_API_KEY | API密钥 | 是 |
| LIVEKIT_API_SECRET | API密钥 | 是 |
| OPENAI_API_KEY | OpenAI API密钥 | 是 |
| VISION_ENABLED | 启用视觉处理 | 否 (默认true) |
| VISION_SAMPLE_RATE | 视频采样率(FPS) | 否 (默认1.0) |
| LOG_LEVEL | 日志级别 | 否 (默认INFO) |

## 监控和维护

### 1. 日志查看

```bash
# Docker Compose
docker-compose logs -f livekit
docker-compose logs -f agent

# Kubernetes
kubectl logs -f deployment/livekit-agent -n livekit
```

### 2. 健康检查

```bash
# LiveKit Server健康检查
curl http://localhost:7880/

# Agent状态检查
docker-compose ps agent
```

### 3. 性能监控

推荐使用Prometheus + Grafana:

```bash
# 安装Prometheus
docker run -d -p 9090:9090 \
  -v ./prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus

# 安装Grafana
docker run -d -p 3000:3000 grafana/grafana
```

## 故障排除

### 问题1: Agent无法连接到LiveKit Server

**症状**: Agent日志显示连接错误

**解决方案**:
1. 检查LIVEKIT_URL配置
2. 确认LiveKit Server正在运行
3. 检查网络连接和防火墙

```bash
# 测试连接
curl -v ws://localhost:7880
```

### 问题2: Android客户端无法连接

**症状**: 连接超时或失败

**解决方案**:
1. 确认使用正确的URL (模拟器用10.0.2.2)
2. 检查网络权限
3. 确认LiveKit Server可访问

### 问题3: 视频识别不工作

**症状**: 无法识别视频内容

**解决方案**:
1. 检查VISION_ENABLED配置
2. 确认YOLO模型已下载
3. 查看Agent日志错误信息
4. 确认GPU可用 (如果使用GPU)

```bash
# 测试GPU
nvidia-smi

# 重新下载模型
docker-compose exec agent python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

### 问题4: 音频延迟高

**症状**: 语音响应延迟

**解决方案**:
1. 检查网络延迟
2. 使用DeepGram替代Whisper (更快)
3. 调整视频采样率
4. 使用更快的TTS模型

## 性能优化

### 1. 网络优化

```yaml
# livekit.yaml
rtc:
  # 启用TURN
  turn_servers:
    - host: turn.your-domain.com
      port: 3478

  # 带宽限制
  subscriber_bandwidth_limit: 5000000  # 5Mbps
```

### 2. Agent优化

```python
# 减少视频处理频率
VISION_SAMPLE_RATE=0.5  # 每2秒一次

# 使用轻量模型
VISION_MODEL=yolov8n.pt  # nano模型
```

### 3. 扩展Agent实例

```bash
# Docker Compose
docker-compose up -d --scale agent=3

# Kubernetes
kubectl scale deployment livekit-agent --replicas=5 -n livekit
```

## 备份和恢复

### 备份配置

```bash
# 备份配置文件
tar -czf backup-$(date +%Y%m%d).tar.gz \
  livekit.yaml \
  backend/.env \
  docker-compose.yml
```

### 恢复

```bash
# 解压备份
tar -xzf backup-20250127.tar.gz

# 重启服务
docker-compose down
docker-compose up -d
```

## 安全最佳实践

1. **使用强密钥**: 定期更换API密钥
2. **启用HTTPS**: 生产环境必须使用TLS
3. **限制访问**: 使用防火墙限制端口访问
4. **监控日志**: 定期检查异常访问
5. **更新依赖**: 及时更新Docker镜像和依赖包

## 成本估算

### AWS部署示例

- **EC2实例** (t3.xlarge): $150/月
- **带宽** (1TB): $90/月
- **存储** (100GB SSD): $10/月
- **OpenAI API**: 按使用量计费

**总计**: ~$250/月起

### 优化建议

- 使用Spot实例节省成本
- 配置自动扩缩容
- 使用CDN减少带宽成本
- 缓存常用AI响应
