from enum import Enum


class SearchType(Enum):
    # 综合
    DEFAULT = "general"

    # 用户
    PEOPLE = "people"

    # 热门
    TOPIC = "topic"

    # 视频
    VIDEO = "zvideo"