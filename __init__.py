"""
ComfyUI Threads API 节点
基于 Meta 官方 Threads API 文档开发
支持文本、图片、视频发布到 Threads
"""

# 尝试从不同的可能文件名导入
try:
    from .threads_api import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
    print("✅ 从 threads_uploader.py 加载成功")
except ImportError:
    NODE_CLASS_MAPPINGS = {}
    NODE_DISPLAY_NAME_MAPPINGS = {}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']