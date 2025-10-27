# 快速开始指南 🚀

只需5分钟即可运行LiveKit AI Assistant！

## 前置要求

✅ Docker 和 Docker Compose 已安装
✅ Android设备或模拟器
✅ OpenAI API密钥

## 第一步: 获取代码

```bash
git clone https://github.com/TaoSeekAI/livekit-ai-assistant.git
cd livekit-ai-assistant
```

## 第二步: 配置API密钥

```bash
# 复制环境变量模板
cp backend/.env.example backend/.env

# 编辑配置文件
nano backend/.env  # 或使用你喜欢的编辑器
```

最小配置（仅需修改这一项）:
```env
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
```

💡 **获取OpenAI API Key**: https://platform.openai.com/api-keys

## 第三步: 启动后端服务

```bash
# 启动LiveKit Server和AI Agent
docker-compose up -d

# 查看服务状态
docker-compose ps

# 应该看到两个服务都是 "Up"
```

查看日志确认启动成功:
```bash
docker-compose logs -f agent
```

看到 "Agent started successfully" 表示成功！

## 第四步: 构建Android应用

### 方式1: 使用Android Studio (推荐)

1. 打开Android Studio
2. File → Open → 选择 `android-client` 目录
3. 等待Gradle同步完成
4. 点击 Run 按钮 ▶️

### 方式2: 命令行构建

```bash
cd android-client

# 构建Debug版本
./gradlew assembleDebug

# 安装到设备
./gradlew installDebug
```

## 第五步: 运行应用

1. 打开手机上的 "LiveKit Assistant" 应用
2. 授予麦克风和摄像头权限
3. 点击 "连接" 按钮

**如果使用模拟器**:
- 应用会自动连接到 `ws://10.0.2.2:7880`

**如果使用真机**:
- 需要修改连接地址为你电脑的局域网IP
- 在 `android-client/app/build.gradle` 中修改:
  ```gradle
  buildConfigField "String", "LIVEKIT_URL", "\"ws://192.168.1.100:7880\""
  ```
- 替换 `192.168.1.100` 为你的实际IP地址

## 测试功能

### 🎤 测试语音对话

1. 点击麦克风图标
2. 说 "你好"
3. AI应该会回复

### 📹 测试视频识别

1. 点击摄像头图标
2. 对准一个物体（如手机、杯子）
3. 问 "你看到了什么？"
4. AI会描述它看到的内容

### 🖼️ 测试图片上传

1. 点击图片图标
2. 选择拍照或从相册选择
3. AI会分析并描述图片

## 故障排除

### 问题1: Docker容器启动失败

```bash
# 检查端口是否被占用
sudo netstat -tlnp | grep 7880

# 如果端口被占用，停止占用的程序或修改端口
```

### 问题2: Android应用连接失败

```bash
# 确认LiveKit Server正在运行
curl http://localhost:7880

# 应该返回LiveKit相关信息
```

如果使用真机:
```bash
# 查看电脑IP
ip addr show  # Linux
ipconfig      # Windows

# 确保手机和电脑在同一WiFi网络
```

### 问题3: AI没有响应

```bash
# 查看Agent日志
docker-compose logs -f agent

# 检查OpenAI API密钥是否正确
cat backend/.env | grep OPENAI_API_KEY
```

### 问题4: 视频识别不工作

```bash
# 重启Agent下载模型
docker-compose restart agent

# 等待模型下载完成（首次启动需要下载YOLOv8模型）
docker-compose logs -f agent
```

## 停止服务

```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v
```

## 下一步

✅ 查看完整文档: [README.md](README.md)
✅ 了解架构: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
✅ 部署到生产: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
✅ 用户指南: [docs/USER_GUIDE.md](docs/USER_GUIDE.md)

## 获取帮助

🐛 遇到问题？[提交Issue](https://github.com/TaoSeekAI/livekit-ai-assistant/issues)
💬 有问题？[讨论区](https://github.com/TaoSeekAI/livekit-ai-assistant/discussions)

## 常用命令速查

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 更新镜像
docker-compose pull
docker-compose up -d

# 清理所有数据
docker-compose down -v
docker system prune -a
```

---

🎉 祝使用愉快！如果觉得项目有用，请给个Star ⭐
