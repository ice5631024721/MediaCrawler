import asyncio
import json
import os
import pathlib
from typing import Dict
import aiofiles

from base.base_crawler import AbstractStore
from tools import utils
from var import crawler_type_var


def calculate_number_of_files(file_store_path: str) -> int:
    """计算数据保存文件的前部分排序数字，支持每次运行代码不写到同一个文件中
    Args:
        file_store_path;
    Returns:
        file nums
    """
    if not os.path.exists(file_store_path):
        return 1
    try:
        return max([int(file_name.split("_")[0]) for file_name in os.listdir(file_store_path)]) + 1
    except ValueError:
        return 1


class TouriaoMdStoreImplement(AbstractStore):
    async def store_creator(self, creator: Dict):
        pass

    store_path: str = "data/toutiao"
    file_count: int = calculate_number_of_files(store_path)

    def make_save_file_name(self, store_type: str, note_id: str) -> str:
        """
        make save file name by store type
        Args:
            store_type: contents or comments

        Returns: eg: data/bilibili/search_comments_20240114.csv ...
        :param note_id:

        """

        return f"{self.store_path}/{crawler_type_var.get()}_{store_type}_{utils.get_current_date()}_{note_id}.md"

    async def save_data_to_md(self, save_item: Dict, store_type: str):
        """
        Below is a simple way to save it in CSV format.
        Args:
            save_item:  save content dict info
            store_type: Save type contains content and comments（contents | comments）

        Returns: no returns

        """
        pathlib.Path(self.store_path).mkdir(parents=True, exist_ok=True)
        note_id = save_item["note_id"]
        if note_id is None:
            return
        save_file_name = self.make_save_file_name(store_type=store_type, note_id=note_id)
        async with aiofiles.open(save_file_name, mode='w', encoding="utf-8-sig", newline="") as file:
            content = save_item.get("content")
            await file.write(content)

    async def store_content(self, content_item: Dict):
        """
        Weibo content CSV storage implementation
        Args:
            content_item: note item dict

        Returns:

        """
        await self.save_data_to_md(save_item=content_item, store_type="contents")

    async def store_comment(self, comment_item: Dict):
        """
        Weibo comment CSV storage implementation
        Args:
            comment_item: comment item dict

        Returns:

        """
        pass
        # await self.save_data_to_md(save_item=comment_item, store_type="comments")


class ToutiaoJsonStoreImplement(AbstractStore):
    async def store_creator(self, creator: Dict):
        pass

    json_store_path: str = "data/toutiao/json"
    words_store_path: str = "data/weibo/words"
    lock = asyncio.Lock()
    file_count: int = calculate_number_of_files(json_store_path)

    def make_save_file_name(self, store_type: str) -> (str, str):
        """
        make save file name by store type
        Args:
            store_type: Save type contains content and comments（contents | comments）

        Returns:

        """

        return (
            f"{self.json_store_path}/{crawler_type_var.get()}_{store_type}_{utils.get_current_date()}.json",
        )

    async def save_data_to_json(self, save_item: Dict, store_type: str):
        """
        Below is a simple way to save it in json format.
        Args:
            save_item: save content dict info
            store_type: Save type contains content and comments（contents | comments）

        Returns:

        """
        pathlib.Path(self.json_store_path).mkdir(parents=True, exist_ok=True)
        pathlib.Path(self.words_store_path).mkdir(parents=True, exist_ok=True)
        save_file_name, words_file_name_prefix = self.make_save_file_name(store_type=store_type)
        save_data = []

        async with self.lock:
            if os.path.exists(save_file_name):
                async with aiofiles.open(save_file_name, 'r', encoding='utf-8') as file:
                    save_data = json.loads(await file.read())

            save_data.append(save_item)
            async with aiofiles.open(save_file_name, 'w', encoding='utf-8') as file:
                await file.write(json.dumps(save_data, ensure_ascii=False))

    async def store_content(self, content_item: Dict):
        """
        content JSON storage implementation
        Args:
            content_item:

        Returns:

        """
        await self.save_data_to_json(content_item, "contents")

    async def store_comment(self, comment_item: Dict):
        """
        comment JSON storage implementatio
        Args:
            comment_item:

        Returns:

        """
        await self.save_data_to_json(comment_item, "comments")
