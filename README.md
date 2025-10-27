# LiveKit AI Assistant - 实时音视频AI助手

一个基于LiveKit的实时音视频AI助手系统，支持Android客户端与Python后端的实时交互。

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Android 客户端                             │
│  - 实时语音对话                                                    │
│  - 视频通话                                                        │
│  - 图片上传/拍照                                                   │
│  - 语音记录                                                        │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ WebRTC (LiveKit Protocol)
                 │
┌────────────────▼────────────────────────────────────────────────┐
│                     LiveKit Server (SFU)                        │
│  - 媒体路由                                                        │
│  - 房间管理                                                        │
│  - 信令处理                                                        │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 │ Agent Worker Protocol
                 │
┌────────────────▼────────────────────────────────────────────────┐
│                    Python Backend Agent                         │
│  - 语音识别 (STT)                                                 │
│  - 视频内容识别 (Computer Vision)                                 │
│  - AI模型处理 (LLM)                                               │
│  - 语音合成 (TTS)                                                 │
│  - 文字转录与回显                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 核心功能

### Android客户端
- ✅ 实时语音对话
- ✅ 视频通话
- ✅ 拍照上传
- ✅ 图片上传
- ✅ 语音记录
- ✅ 实时文字转录显示

### Python后端
- ✅ 视频帧捕获与处理
- ✅ 计算机视觉模型集成
- ✅ 语音转文字 (STT)
- ✅ 文字转语音 (TTS)
- ✅ LLM对话处理
- ✅ 实时结果回显

## 技术栈

### 前端 (Android)
- **语言**: Kotlin
- **最低SDK**: Android 7.0 (API 24)
- **核心库**:
  - LiveKit Android SDK 2.21.0+
  - Jetpack Compose (UI)
  - CameraX (相机)
  - Coroutines (异步)

### 后端 (Python)
- **语言**: Python 3.10+
- **核心库**:
  - livekit-agents
  - OpenCV (视频处理)
  - ultralytics (YOLOv8)
  - openai-whisper (STT)
  - elevenlabs/openai (TTS)

### 基础设施
- **LiveKit Server**: 自托管或LiveKit Cloud
- **AI模型**: OpenAI GPT-4/Claude
- **部署**: Docker + Kubernetes (可选)

## 快速开始

### 1. 环境准备

#### LiveKit Server
```bash
# 使用Docker运行LiveKit Server
docker run -d \
  -p 7880:7880 \
  -p 7881:7881 \
  -p 7882:7882/udp \
  -e LIVEKIT_KEYS="devkey: secret" \
  livekit/livekit-server:latest
```

#### 后端服务
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 配置环境变量
export LIVEKIT_URL=ws://localhost:7880
export LIVEKIT_API_KEY=devkey
export LIVEKIT_API_SECRET=secret
export OPENAI_API_KEY=your_openai_key

# 运行Agent
python agent.py
```

#### Android客户端
```bash
cd android-client
./gradlew build
./gradlew installDebug
```

### 2. 配置说明

在 `backend/.env` 文件中配置:
```env
LIVEKIT_URL=ws://your-server:7880
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
OPENAI_API_KEY=your_openai_key
```

在Android `app/src/main/res/values/config.xml`:
```xml
<resources>
    <string name="livekit_url">wss://your-server</string>
</resources>
```

## 使用方法

### 启动流程

1. **启动LiveKit Server**
   ```bash
   docker-compose up -d
   ```

2. **启动Python Agent**
   ```bash
   cd backend
   python agent.py
   ```

3. **启动Android应用**
   - 在Android Studio中打开项目
   - 运行应用到设备或模拟器

### 功能使用

#### 语音对话
1. 点击"连接"按钮加入房间
2. 点击麦克风图标开始说话
3. AI Agent会自动识别并回复

#### 视频识别
1. 点击摄像头图标开启视频
2. 对准需要识别的物体
3. AI会实时分析并显示识别结果

#### 图片上传
1. 点击"上传图片"按钮
2. 选择图片或拍照
3. AI分析图片内容并给出描述

## 项目结构

```
livekit-ai-assistant/
├── android-client/          # Android客户端
│   ├── app/
│   │   ├── src/
│   │   │   ├── main/
│   │   │   │   ├── java/com/livekit/assistant/
│   │   │   │   │   ├── MainActivity.kt
│   │   │   │   │   ├── LiveKitManager.kt
│   │   │   │   │   └── ui/
│   │   │   │   └── res/
│   │   └── build.gradle
│   └── build.gradle
├── backend/                 # Python后端
│   ├── agent.py            # 主Agent程序
│   ├── vision_processor.py # 视频处理
│   ├── requirements.txt    # 依赖
│   └── .env.example        # 环境变量示例
├── docs/                    # 文档
│   ├── ARCHITECTURE.md     # 架构设计
│   ├── API.md              # API文档
│   ├── DEPLOYMENT.md       # 部署指南
│   └── TESTING.md          # 测试文档
├── docker-compose.yml      # Docker编排
└── README.md               # 本文件
```

## 开发指南

### Android开发
详见 [android-client/README.md](android-client/README.md)

### 后端开发
详见 [backend/README.md](backend/README.md)

### 部署指南
详见 [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

## 测试

### 单元测试
```bash
# Android
cd android-client
./gradlew test

# Python
cd backend
pytest
```

### 集成测试
详见 [docs/TESTING.md](docs/TESTING.md)

## 故障排除

### 常见问题

1. **无法连接到LiveKit Server**
   - 检查服务器地址配置
   - 确认防火墙端口开放
   - 验证API密钥正确

2. **视频无法显示**
   - 检查摄像头权限
   - 确认网络带宽
   - 查看日志错误信息

3. **AI识别不准确**
   - 确保光线充足
   - 保持物体在画面中心
   - 检查模型配置

详细故障排除见 [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

## 性能优化

- 网络优化：根据带宽调整视频质量
- 模型优化：使用量化模型减少延迟
- 缓存策略：缓存常用AI响应

## 安全性

- 使用HTTPS/WSS加密通信
- Token基于时间过期
- 服务端验证所有请求
- 敏感数据不存储

## 贡献指南

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md)

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 联系方式

- 问题反馈: GitHub Issues
- 邮件: support@example.com

## 致谢

- [LiveKit](https://livekit.io/) - 实时音视频基础设施
- [OpenAI](https://openai.com/) - AI模型
- [Ultralytics](https://ultralytics.com/) - YOLO模型

## 版本历史

### v0.1.0 (2025-10-27)
- 初始版本发布
- 基础功能实现
- Android客户端
- Python后端Agent
- 视频识别功能
