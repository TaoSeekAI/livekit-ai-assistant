"""
Vision Processor Module
处理视频帧，执行物体检测和场景理解
"""

import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple
from ultralytics import YOLO
from loguru import logger
import asyncio
from PIL import Image
import io


class VisionProcessor:
    """视频处理器，支持物体检测和场景分析"""

    def __init__(self, model_name: str = "yolov8n.pt"):
        """
        初始化视觉处理器

        Args:
            model_name: YOLO模型名称
        """
        self.model_name = model_name
        self.model: Optional[YOLO] = None
        self._initialized = False

    async def initialize(self):
        """异步初始化模型"""
        if self._initialized:
            return

        logger.info(f"Loading vision model: {self.model_name}")
        try:
            # 在线程池中加载模型，避免阻塞事件循环
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None,
                YOLO,
                self.model_name
            )
            self._initialized = True
            logger.info("Vision model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load vision model: {e}")
            raise

    async def process_frame(
        self,
        frame: np.ndarray,
        confidence_threshold: float = 0.5
    ) -> Dict:
        """
        处理单个视频帧

        Args:
            frame: BGR格式的视频帧
            confidence_threshold: 检测置信度阈值

        Returns:
            包含检测结果的字典
        """
        if not self._initialized:
            await self.initialize()

        try:
            # 在线程池中运行推理
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                self._run_inference,
                frame,
                confidence_threshold
            )

            return results

        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            return {
                "error": str(e),
                "detections": [],
                "description": "Error processing image"
            }

    def _run_inference(
        self,
        frame: np.ndarray,
        confidence_threshold: float
    ) -> Dict:
        """
        执行模型推理（同步方法）

        Args:
            frame: 视频帧
            confidence_threshold: 置信度阈值

        Returns:
            检测结果字典
        """
        results = self.model(frame, conf=confidence_threshold)

        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # 获取边界框坐标
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()

                # 获取置信度和类别
                confidence = float(box.conf[0].cpu().numpy())
                class_id = int(box.cls[0].cpu().numpy())
                class_name = self.model.names[class_id]

                detections.append({
                    "class": class_name,
                    "confidence": confidence,
                    "bbox": {
                        "x1": float(x1),
                        "y1": float(y1),
                        "x2": float(x2),
                        "y2": float(y2)
                    }
                })

        # 生成场景描述
        description = self._generate_description(detections)

        return {
            "detections": detections,
            "description": description,
            "num_objects": len(detections)
        }

    def _generate_description(self, detections: List[Dict]) -> str:
        """
        根据检测结果生成自然语言描述

        Args:
            detections: 检测结果列表

        Returns:
            场景描述文本
        """
        if not detections:
            return "未检测到任何物体"

        # 统计各类物体数量
        object_counts = {}
        for det in detections:
            class_name = det["class"]
            object_counts[class_name] = object_counts.get(class_name, 0) + 1

        # 构建描述
        parts = []
        for obj, count in object_counts.items():
            if count == 1:
                parts.append(f"一个{obj}")
            else:
                parts.append(f"{count}个{obj}")

        description = "我看到了" + "、".join(parts)
        return description

    async def process_image_bytes(
        self,
        image_bytes: bytes,
        confidence_threshold: float = 0.5
    ) -> Dict:
        """
        处理图片字节数据

        Args:
            image_bytes: 图片字节数据
            confidence_threshold: 检测置信度阈值

        Returns:
            检测结果字典
        """
        try:
            # 将字节转换为numpy数组
            nparr = np.frombuffer(image_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is None:
                return {
                    "error": "Invalid image data",
                    "detections": [],
                    "description": "无法解析图片"
                }

            return await self.process_frame(frame, confidence_threshold)

        except Exception as e:
            logger.error(f"Error processing image bytes: {e}")
            return {
                "error": str(e),
                "detections": [],
                "description": "图片处理出错"
            }

    def draw_detections(
        self,
        frame: np.ndarray,
        detections: List[Dict]
    ) -> np.ndarray:
        """
        在帧上绘制检测结果

        Args:
            frame: 原始帧
            detections: 检测结果列表

        Returns:
            标注后的帧
        """
        annotated_frame = frame.copy()

        for det in detections:
            bbox = det["bbox"]
            class_name = det["class"]
            confidence = det["confidence"]

            # 绘制边界框
            x1, y1 = int(bbox["x1"]), int(bbox["y1"])
            x2, y2 = int(bbox["x2"]), int(bbox["y2"])

            cv2.rectangle(
                annotated_frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            # 绘制标签
            label = f"{class_name}: {confidence:.2f}"
            (text_width, text_height), _ = cv2.getTextSize(
                label,
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                2
            )

            cv2.rectangle(
                annotated_frame,
                (x1, y1 - text_height - 10),
                (x1 + text_width, y1),
                (0, 255, 0),
                -1
            )

            cv2.putText(
                annotated_frame,
                label,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 0),
                2
            )

        return annotated_frame

    async def cleanup(self):
        """清理资源"""
        self.model = None
        self._initialized = False
        logger.info("Vision processor cleaned up")


# 便捷的全局实例
_global_processor: Optional[VisionProcessor] = None


async def get_vision_processor(model_name: str = "yolov8n.pt") -> VisionProcessor:
    """
    获取全局视觉处理器实例

    Args:
        model_name: 模型名称

    Returns:
        VisionProcessor实例
    """
    global _global_processor

    if _global_processor is None:
        _global_processor = VisionProcessor(model_name)
        await _global_processor.initialize()

    return _global_processor
