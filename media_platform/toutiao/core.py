# -*- coding: utf-8 -*-
# @Author  : relakkes@gmail.com
# @Time    : 2023/12/23 15:41
# @Desc    : 微博爬虫主流程代码


import asyncio
import os
import random
from asyncio import Task
from typing import Dict, List, Optional, Tuple

from playwright.async_api import (BrowserContext, BrowserType, Page,
                                  async_playwright)

import config
from base.base_crawler import AbstractCrawler
from proxy.proxy_ip_pool import IpInfoModel, create_ip_pool
from store import toutiao as toutiao_store
from store import weibo as weibo_store
from tools import utils
from var import crawler_type_var
from .client import ToutiaoClient
from .exception import DataFetchError
from .field import SearchType
from .help import get_toutiao_help


# from .help import filter_search_result_card


class ToutiaoCrawler(AbstractCrawler):
    context_page: Page
    toutiao_client: ToutiaoClient
    browser_context: BrowserContext

    def __init__(self):
        self.index_url = "https://so.toutiao.com"
        self.mobile_index_url = "https://so.toutiao.com"
        self.user_agent = utils.get_user_agent()
        self.mobile_user_agent = utils.get_mobile_user_agent()

    async def start(self):
        playwright_proxy_format, httpx_proxy_format = None, None
        if config.ENABLE_IP_PROXY:
            ip_proxy_pool = await create_ip_pool(config.IP_PROXY_POOL_COUNT, enable_validate_ip=True)
            ip_proxy_info: IpInfoModel = await ip_proxy_pool.get_proxy()
            playwright_proxy_format, httpx_proxy_format = self.format_proxy_info(ip_proxy_info)

        async with async_playwright() as playwright:
            # Launch a browser context.
            chromium = playwright.chromium
            self.browser_context = await self.launch_browser(
                chromium,
                None,
                self.user_agent,
                headless=config.HEADLESS
            )
            # # stealth.min.js is a js script to prevent the website from detecting the crawler.
            await self.browser_context.add_init_script(path="libs/stealth.min.js")
            self.context_page = await self.browser_context.new_page()
            await self.context_page.goto(self.mobile_index_url)

            # Create a client to interact with the xiaohongshu website.
            self.toutiao_client = await self.create_toutiao_client(httpx_proxy_format)
            # if not await self.toutiao_client.pong():
            #     login_obj = ToutiaoLogin(
            #         login_type=config.LOGIN_TYPE,
            #         login_phone="",  # your phone number
            #         browser_context=self.browser_context,
            #         context_page=self.context_page,
            #         cookie_str=config.COOKIES
            #     )
            await self.context_page.goto(self.index_url)
            #     await asyncio.sleep(1)
            # await login_obj.begin()
            #
            #     # 登录成功后重定向到手机端的网站，再更新手机端登录成功的cookie
            #     utils.logger.info(
            #         "[WeiboCrawler.start] redirect weibo mobile homepage and update cookies on mobile platform")
            current_cookie = await self.browser_context.cookies()
            _, cookie_dict = utils.convert_cookies(current_cookie)
            await self.context_page.goto(self.mobile_index_url)
            await asyncio.sleep(2)
            await self.toutiao_client.update_cookies(browser_context=self.browser_context)

            crawler_type_var.set(config.CRAWLER_TYPE)
            if config.CRAWLER_TYPE == "search":
                # Search for video and retrieve their comment information.
                await self.search()
            elif config.CRAWLER_TYPE == "detail":
                # Get the information and comments of the specified post
                await self.get_specified_notes()
            else:
                pass
            utils.logger.info("[ToutiaoCrawler.start] toutiao Crawler finished ...")

    async def search(self):
        """
        search weibo note with keywords
        :return:
        """
        utils.logger.info("[ToutiaoCrawler.search] Begin search toutiao keywords")
        toutiao_limit_count = 10  # weibo limit page fixed value
        if config.CRAWLER_MAX_NOTES_COUNT < toutiao_limit_count:
            config.CRAWLER_MAX_NOTES_COUNT = toutiao_limit_count
        start_page = config.START_PAGE
        for keyword in config.KEYWORDS.split(","):
            utils.logger.info(f"[ToutiaoCrawler.search] Current search keyword: {keyword}")
            page = 0
            while (page - start_page + 1) * toutiao_limit_count <= config.CRAWLER_MAX_NOTES_COUNT:
                if page < start_page:
                    utils.logger.info(f"[ToutiaoCrawler.search] Skip page: {page}")
                    page += 1
                    continue
                utils.logger.info(f"[ToutiaoCrawler.search] search toutiao keyword: {keyword}, page: {page}")
                search_res = await self.toutiao_client.get_note_by_keyword(
                    keyword=keyword,
                    page=page,
                    search_type=SearchType.DEFAULT
                )
                note_list = get_toutiao_help(search_res.get('data'))


                semaphore = asyncio.Semaphore(config.MAX_CONCURRENCY_NUM)
                task_list = [self.get_note_detail(ele, semaphore) for ele in note_list if ele is not None]
                note_details = await asyncio.gather(*task_list)
                for every_note in note_details:
                    await toutiao_store.update_toutiao_note(every_note)
                    # print(json.dumps(every_note,ensure_ascii=False))


                page += 1
                # await self.batch_get_notes_comments(note_id_list)

    async def get_specified_notes(self):
        """
        get specified notes info
        :return:
        """
        semaphore = asyncio.Semaphore(config.MAX_CONCURRENCY_NUM)
        task_list = [
            self.get_note_info_task(note_id=note_id, semaphore=semaphore) for note_id in
            config.WEIBO_SPECIFIED_ID_LIST
        ]
        video_details = await asyncio.gather(*task_list)
        for note_item in video_details:
            if note_item:
                await weibo_store.update_weibo_note(note_item)
        await self.batch_get_notes_comments(config.WEIBO_SPECIFIED_ID_LIST)

    async def get_note_info_task(self, note_id: str, semaphore: asyncio.Semaphore) -> Optional[Dict]:
        """
        Get note detail task
        :param note_id:
        :param semaphore:
        :return:
        """
        async with semaphore:
            try:
                result = await self.toutiao_client.get_note_info_by_id(note_id)
                return result
            except DataFetchError as ex:
                utils.logger.error(f"[WeiboCrawler.get_note_info_task] Get note detail error: {ex}")
                return None
            except KeyError as ex:
                utils.logger.error(
                    f"[WeiboCrawler.get_note_info_task] have not fund note detail note_id:{note_id}, err: {ex}")
                return None

    async def batch_get_notes_comments(self, note_id_list: List[str]):
        """
        batch get notes comments
        :param note_id_list:
        :return:
        """
        if not config.ENABLE_GET_COMMENTS:
            utils.logger.info(f"[WeiboCrawler.batch_get_note_comments] Crawling comment mode is not enabled")
            return

        utils.logger.info(f"[WeiboCrawler.batch_get_notes_comments] note ids:{note_id_list}")
        semaphore = asyncio.Semaphore(config.MAX_CONCURRENCY_NUM)
        task_list: List[Task] = []
        for note_id in note_id_list:
            task = asyncio.create_task(self.get_note_comments(note_id, semaphore), name=note_id)
            task_list.append(task)
        await asyncio.gather(*task_list)

    async def get_note_comments(self, note_id: str, semaphore: asyncio.Semaphore):
        """
        get comment for note id
        :param note_id:
        :param semaphore:
        :return:
        """
        async with semaphore:
            try:
                utils.logger.info(f"[WeiboCrawler.get_note_comments] begin get note_id: {note_id} comments ...")
                await self.toutiao_client.get_note_all_comments(
                    note_id=note_id,
                    crawl_interval=random.randint(1, 10),  # 微博对API的限流比较严重，所以延时提高一些
                    callback=weibo_store.batch_update_weibo_note_comments
                )
            except DataFetchError as ex:
                utils.logger.error(f"[WeiboCrawler.get_note_comments] get note_id: {note_id} comment error: {ex}")
            except Exception as e:
                utils.logger.error(f"[WeiboCrawler.get_note_comments] may be been blocked, err:{e}")

    async def get_note_images(self, mblog: Dict):
        """
        get note images
        :param mblog:
        :return:
        """
        if not config.ENABLE_GET_IMAGES:
            utils.logger.info(f"[WeiboCrawler.get_note_images] Crawling image mode is not enabled")
            return

        pics: Dict = mblog.get("pics")
        if not pics:
            return
        for pic in pics:
            url = pic.get("url")
            if not url:
                continue
            content = await self.toutiao_client.get_note_image(url)
            if content != None:
                extension_file_name = url.split(".")[-1]
                await weibo_store.update_weibo_note_image(pic["pid"], content, extension_file_name)

    async def create_toutiao_client(self, httpx_proxy: Optional[str]) -> ToutiaoClient:
        """Create xhs client"""
        utils.logger.info("[WeiboCrawler.create_toutiao_client] Begin create weibo API client ...")
        cookie_str, cookie_dict = utils.convert_cookies(await self.browser_context.cookies())
        toutiao_client_obj = ToutiaoClient(
            proxies=httpx_proxy,
            headers={
                "User-Agent": utils.get_mobile_user_agent(),
                "Cookie": cookie_str,
                "Origin": "https://so.toutiao.com",
                "Referer": "https://so.toutiao.com",
                "Content-Type": "application/json;charset=UTF-8"
            },
            playwright_page=self.context_page,
            cookie_dict=cookie_dict,
        )
        return toutiao_client_obj

    @staticmethod
    def format_proxy_info(ip_proxy_info: IpInfoModel) -> Tuple[Optional[Dict], Optional[Dict]]:
        """format proxy info for playwright and httpx"""
        playwright_proxy = {
            "server": f"{ip_proxy_info.protocol}{ip_proxy_info.ip}:{ip_proxy_info.port}",
            "username": ip_proxy_info.user,
            "password": ip_proxy_info.password,
        }
        httpx_proxy = {
            f"{ip_proxy_info.protocol}": f"http://{ip_proxy_info.user}:{ip_proxy_info.password}@{ip_proxy_info.ip}:{ip_proxy_info.port}"
        }
        return playwright_proxy, httpx_proxy

    async def launch_browser(
            self,
            chromium: BrowserType,
            playwright_proxy: Optional[Dict],
            user_agent: Optional[str],
            headless: bool = True
    ) -> BrowserContext:
        """Launch browser and create browser context"""
        utils.logger.info("[ToutiaoCrawler.launch_browser] Begin create browser context ...")
        if config.SAVE_LOGIN_STATE:
            user_data_dir = os.path.join(os.getcwd(), "browser_data",
                                         config.USER_DATA_DIR % config.PLATFORM)  # type: ignore
            browser_context = await chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                accept_downloads=True,
                headless=headless,
                proxy=playwright_proxy,  # type: ignore
                viewport={"width": 1920, "height": 1080},
                user_agent=user_agent
            )
            return browser_context
        else:
            browser = await chromium.launch(headless=headless, proxy=playwright_proxy)  # type: ignore
            browser_context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=user_agent
            )
            return browser_context

    async def get_note_detail(self, article_url: str, semaphore: asyncio.Semaphore) -> \
            Optional[Dict]:
        """Get note detail"""
        async with semaphore:
            try:
                return await self.toutiao_client.get_note_by_id(article_url)
            except DataFetchError as ex:
                utils.logger.error(f"[ToutiaoCrawler.get_note_detail] Get note detail error: {ex}")
                return None
            except KeyError as ex:
                utils.logger.error(
                    f"[ToutiaoCrawler.get_note_detail] have not fund note detail note_id:{article_url}, err: {ex}")
                return None
