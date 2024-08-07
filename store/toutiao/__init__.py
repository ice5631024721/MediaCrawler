import re
from typing import List, Dict

import config
from base.base_crawler import AbstractStore
from tools import utils
from .toutiao_store_impl import ToutiaoJsonStoreImplement
from .toutiao_store_impl import TouriaoMdStoreImplement


class ToutiaostoreFactory:
    STORES = {
        "json": ToutiaoJsonStoreImplement,
        "md": TouriaoMdStoreImplement,
    }

    @staticmethod
    def create_store() -> AbstractStore:
        # TODO:硬编码
        store_class = ToutiaostoreFactory.STORES.get("md")
        if not store_class:
            raise ValueError(
                "[ToutiaosttoreFactory.create_store] Invalid save option only supported csv or db or json ...")
        return store_class()

async def update_toutiao_note(note_item: Dict):

    note_id  = note_item.get("note_id", None)
    content = note_item.get("content", None)

    if note_id is not None and content is not None:
        save_content_item = {
            # 微博信息
            "note_id": note_id,
            "content": content
        }
        utils.logger.info(
            f"[store.toutiao.update_toutiao_note] weibo note id:{note_id}, title:{save_content_item.get('content')[:24]} ...")
        await ToutiaostoreFactory.create_store().store_content(content_item=save_content_item)



