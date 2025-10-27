"""
LiveKit AI Assistant Agent
主Agent程序，处理实时音视频交互
"""

import asyncio
import os
from typing import Optional
from dotenv import load_dotenv
from loguru import logger

from livekit import rtc
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import openai, deepgram, elevenlabs

from vision_processor import get_vision_processor

# 加载环境变量
load_dotenv()

# 配置日志
logger.add(
    "logs/agent_{time}.log",
    rotation="1 day",
    retention="7 days",
    level=os.getenv("LOG_LEVEL", "INFO")
)


class AIAssistant:
    """AI助手核心类"""

    def __init__(self):
        self.vision_enabled = os.getenv("VISION_ENABLED", "true").lower() == "true"
        self.vision_processor = None
        self.current_video_track: Optional[rtc.VideoTrack] = None
        self.last_vision_result = None

    async def initialize(self):
        """初始化组件"""
        if self.vision_enabled:
            logger.info("Initializing vision processor...")
            self.vision_processor = await get_vision_processor(
                os.getenv("VISION_MODEL", "yolov8n.pt")
            )

    async def process_video_frame(self, frame: rtc.VideoFrame) -> Optional[str]:
        """
        处理视频帧

        Args:
            frame: LiveKit视频帧

        Returns:
            视觉分析结果描述
        """
        if not self.vision_processor:
            return None

        try:
            # 将LiveKit VideoFrame转换为numpy数组
            import numpy as np

            # 获取帧数据
            buffer = frame.data
            width = frame.width
            height = frame.height

            # 转换为numpy数组
            arr = np.frombuffer(buffer, dtype=np.uint8)
            arr = arr.reshape((height, width, 3))

            # 处理帧
            result = await self.vision_processor.process_frame(arr)

            self.last_vision_result = result
            return result.get("description", "")

        except Exception as e:
            logger.error(f"Error processing video frame: {e}")
            return None


async def entrypoint(ctx: JobContext):
    """
    Agent入口点
    当用户加入房间时，此函数会被调用

    Args:
        ctx: Job上下文
    """
    logger.info(f"Starting agent for room: {ctx.room.name}")

    # 创建AI助手实例
    assistant = AIAssistant()
    await assistant.initialize()

    # 配置初始对话上下文
    initial_context = llm.ChatContext().append(
        role="system",
        text=(
            "你是一个有帮助的AI助手。你可以：\n"
            "1. 与用户进行自然对话\n"
            "2. 识别和描述用户摄像头中的物体\n"
            "3. 分析用户上传的图片\n"
            "请用简洁、友好的方式回应用户。\n"
            "如果用户询问你看到了什么，请描述视频中的内容。"
        ),
    )

    # 等待房间连接
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # 配置语音管道
    # 使用OpenAI Whisper进行语音识别
    # 使用GPT-4进行对话
    # 使用OpenAI TTS进行语音合成
    agent = VoicePipelineAgent(
        vad=ctx.proc.userdata.get("vad"),
        stt=openai.STT(
            model=os.getenv("STT_MODEL", "whisper-1")
        ),
        llm=openai.LLM(
            model=os.getenv("LLM_MODEL", "gpt-4-turbo-preview")
        ),
        tts=openai.TTS(
            model=os.getenv("TTS_MODEL", "tts-1")
        ),
        chat_ctx=initial_context,
    )

    # 启动agent
    agent.start(ctx.room)

    # 发送欢迎消息
    await agent.say("你好！我是你的AI助手。我可以看到你的摄像头内容。请问有什么可以帮助你的吗？")

    # 监听房间事件
    @ctx.room.on("track_subscribed")
    def on_track_subscribed(
        track: rtc.Track,
        publication: rtc.TrackPublication,
        participant: rtc.RemoteParticipant,
    ):
        """当订阅到新轨道时触发"""
        logger.info(f"Track subscribed: {track.kind} from {participant.identity}")

        if track.kind == rtc.TrackKind.KIND_VIDEO:
            # 保存视频轨道引用
            assistant.current_video_track = track
            logger.info("Video track subscribed, vision processing enabled")

            # 启动视频帧处理任务
            asyncio.create_task(process_video_stream(track, assistant, agent))

    @ctx.room.on("data_received")
    async def on_data_received(data: bytes, participant: rtc.RemoteParticipant):
        """当收到数据消息时触发（用于图片上传）"""
        logger.info(f"Received data from {participant.identity}, size: {len(data)} bytes")

        try:
            # 处理上传的图片
            if assistant.vision_processor:
                result = await assistant.vision_processor.process_image_bytes(data)
                description = result.get("description", "无法识别图片内容")

                # 通过语音回复识别结果
                await agent.say(f"我看到了：{description}")

                # 也通过文本消息发送详细结果
                import json
                await ctx.room.local_participant.publish_data(
                    json.dumps(result, ensure_ascii=False).encode("utf-8"),
                    reliable=True
                )

        except Exception as e:
            logger.error(f"Error processing uploaded image: {e}")
            await agent.say("抱歉，处理图片时出现了错误。")

    # 保持agent运行
    logger.info("Agent started successfully")


async def process_video_stream(
    track: rtc.VideoTrack,
    assistant: AIAssistant,
    agent: VoicePipelineAgent
):
    """
    处理视频流

    Args:
        track: 视频轨道
        assistant: AI助手实例
        agent: 语音管道agent
    """
    logger.info("Starting video stream processing")

    # 视频帧采样率（每秒处理几帧）
    sample_rate = float(os.getenv("VISION_SAMPLE_RATE", "1.0"))
    frame_interval = 1.0 / sample_rate if sample_rate > 0 else 1.0

    last_process_time = 0
    last_description = ""

    try:
        async for event in rtc.VideoStream(track):
            current_time = asyncio.get_event_loop().time()

            # 控制处理频率
            if current_time - last_process_time < frame_interval:
                continue

            last_process_time = current_time

            # 处理视频帧
            frame = event.frame
            description = await assistant.process_video_frame(frame)

            # 如果检测到新内容，主动告知用户
            if description and description != last_description:
                logger.info(f"Vision: {description}")

                # 检查是否有新的物体被检测到
                if "我看到了" in description and description != "我看到了":
                    # 不要每次都说话，只在检测结果显著变化时通知
                    # 这里可以添加更智能的判断逻辑
                    pass

                last_description = description

    except Exception as e:
        logger.error(f"Error in video stream processing: {e}")


async def request_fnc(req: JobRequest) -> None:
    """
    请求处理函数
    决定是否接受新的任务请求

    Args:
        req: 任务请求
    """
    logger.info(f"Received job request for room: {req.room.name}")
    await req.accept(entrypoint)


if __name__ == "__main__":
    # 运行agent worker
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            api_key=os.getenv("LIVEKIT_API_KEY"),
            api_secret=os.getenv("LIVEKIT_API_SECRET"),
            ws_url=os.getenv("LIVEKIT_URL"),
        )
    )
