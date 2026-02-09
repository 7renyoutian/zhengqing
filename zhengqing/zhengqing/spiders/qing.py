# import scrapy
# import time
# from scrapy.exceptions import CloseSpider
# from twisted.internet import reactor
# from scrapy.linkextractors import LinkExtractor
# import redis
#
#
# class QingSpider(scrapy.Spider):
#     name = 'qing'
#     allowed_domains = ["zzuli.edu.cn"]
#     start_urls = ["https://www.zzuli.edu.cn/"]
#     # 超时配置（根据你的需求调整）
#     SPIDER_TIMEOUT = 300  # 全局超时（秒）
#     specific_timeout = 120  # 特定链接超时（秒）
#     check_interval = 10  # 检查间隔（秒）
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # 初始化Redis（如果使用），这里先注释，避免依赖问题
#         self.red = redis.Redis(host='localhost', port=6379, db=1)
#         self.last_specific_time = time.time()  # 初始化最后响应时间
#         self.specific_check_call = None  # 定时器句柄
#         self.timeout_call = None  # 全局超时句柄
#
#     async def start(self):
#         """
#         Scrapy 2.13+ 规范的 start 方法（异步生成器）
#         1. 启动定时器
#         2. 生成初始请求
#         """
#         # 1. 启动定时器（Twisted reactor 定时器）
#         self.start_timers()
#
#         # 2. 生成初始请求（异步生成器方式，符合框架要求）
#         for url in self.start_urls:
#             yield scrapy.Request(url, callback=self.parse)
#
#     def start_timers(self):
#         """启动所有定时器"""
#         # 启动特定链接检查定时器（立即执行第一次）
#         self.specific_check_call = reactor.callLater(0, self.check_specific_timeout)
#         # 启动全局超时定时器
#         self.timeout_call = reactor.callLater(self.SPIDER_TIMEOUT, self.timeout_close)
#
#     def stop_all_timers(self):
#         """停止所有定时器"""
#         if self.specific_check_call and self.specific_check_call.active():
#             self.specific_check_call.cancel()
#         if self.timeout_call and self.timeout_call.active():
#             self.timeout_call.cancel()
#
#     def check_specific_timeout(self):
#         """检查特定链接超时"""
#         try:
#             if time.time() - self.last_specific_time > self.specific_timeout:
#                 self.logger.error(f"[{self.specific_timeout}秒无有效响应] 触发爬虫关闭")
#                 self.force_stop_spider(reason="no_new_list_htm_url")
#                 return
#             # 循环调用（继续监控）
#             self.specific_check_call = reactor.callLater(self.check_interval, self.check_specific_timeout)
#         except Exception as e:
#             self.logger.error(f"监控检测异常：{e}")
#             self.stop_all_timers()
#             self.force_stop_spider(reason=f"monitor_error: {e}")
#
#     def timeout_close(self):
#         """全局超时关闭爬虫"""
#         self.logger.error(f"[{self.SPIDER_TIMEOUT}秒全局超时] 触发爬虫关闭")
#         self.force_stop_spider(reason="global_timeout")
#
#     def force_stop_spider(self, reason):
#         """强制停止爬虫"""
#         self.stop_all_timers()
#         # 抛出 CloseSpider 异常，让Scrapy优雅关闭
#         raise CloseSpider(reason=reason)
#
#     def parse(self, resp, **kwargs):
#         # 提取所有链接（示例逻辑，根据你的需求修改）
#         link_extractor = LinkExtractor()
#         links = link_extractor.extract_links(resp)
#
#         has_new_request = False
#         for link in links:
#             # 示例：过滤list.htm链接（根据你的业务逻辑调整）
#             if link.url.endswith('list.htm') and not self.red.sismember("tongzhi:link", link.url):
#                 self.logger.info(f"发现list.htm链接：{link.url}")
#                 self.last_specific_time = time.time()
#                 self.red.sadd("tongzhi:link", link.url)
#                 self.red.rpush("tongzhi:linklist", link.url)
#                 yield scrapy.Request(link.url, callback=self.parse)
#                 has_new_request = True
#
#             if not self.red.sismember("zhengqing:link", link.url):
#                 self.red.sadd("zhengqing:link", link.url)
#                 yield scrapy.Request(link.url, callback=self.parse)
#
#
#         # 提取分页链接（示例）
#         hrefs_fenye = resp.xpath("//li[@class='page_nav']/a/@href").extract()
#         for href in hrefs_fenye:
#             if href.startswith("javascript:void(0)"):
#                 continue
#             full_url = resp.urljoin(href)
#             self.logger.info(f"分页链接：{full_url}")
#             yield scrapy.Request(full_url, callback=self.parse)
#             has_new_request = True
#
#
#         # 若无新请求，生成空请求保持爬虫运行
#     #     if not has_new_request:
#     #         yield scrapy.Request(
#     #             url=resp.url,
#     #             callback=self.parse_empty,
#     #             dont_filter=True,
#     #             priority=-100
#     #         )
#     #
#     # def parse_empty(self, response):
#     #     """空请求解析：保持爬虫运行"""
#     #     # 每10秒提交一次空请求（避免爬虫提前关闭）
#     #     yield scrapy.Request(
#     #         url=response.url,
#     #         callback=self.parse_empty,
#     #         dont_filter=True,
#     #         priority=-100,
#     #         meta={'delay': 10}
#     #     )
#
#     def closed(self, reason):
#         """爬虫关闭时的清理操作"""
#         self.logger.info(f"爬虫关闭，原因：{reason}")
#         self.stop_all_timers()
#         self.logger.info("所有定时器已停止")



import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.http import Request
import redis
from scrapy import signals
from scrapy.exceptions import CloseSpider
import time
from twisted.internet import reactor  # 导入Twisted反应器

class QingSpider(scrapy.Spider):
    name = "qing"
    allowed_domains = ["zzuli.edu.cn"]
    start_urls = ["https://jwc.zzuli.edu.cn/"]
    SPIDER_TIMEOUT = 1200  # 全局超时（秒）
    specific_timeout = 180  # 特定监控超时（秒）
    check_interval = 1     # 监控检测间隔（秒）

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.red = redis.Redis(host="127.0.0.1", port=6379, db=1, decode_responses=True)
        self.timeout_call = None  # Twisted定时器引用（全局超时）
        self.specific_check_call = None  # Twisted定时器引用（特定监控）
        self.last_specific_time = time.time()  # 最后一次有效响应时间

    def check_specific_timeout(self):
        """Twisted异步版：检查特定超时"""
        try:
            # 判断是否超时
            if time.time() - self.last_specific_time > self.specific_timeout:
                self.logger.error(f"[{self.specific_timeout}秒无有效响应] 触发爬虫关闭")
                # 1. 停止所有定时器
                self.stop_all_timers()
                # 2. 强制关闭爬虫+终止反应器
                self.force_stop_spider(reason="no_new_list_htm_url")
                return  # 终止后续循环

            # 循环调用：用Twisted的callLater替代线程定时器
            self.specific_check_call = reactor.callLater(
                self.check_interval, self.check_specific_timeout
            )
        except Exception as e:
            self.logger.error(f"监控检测异常：{e}")
            self.stop_all_timers()

    def timeout_close(self):
        """全局超时回调：强制终止程序"""
        self.logger.info(f"[{self.SPIDER_TIMEOUT}秒全局超时] 触发程序终止")
        self.force_stop_spider(reason="global_timeout")

    def force_stop_spider(self, reason):
        """强制停止爬虫+终止反应器（核心：彻底退出程序）"""
        # 1. 停止所有定时器
        self.stop_all_timers()
        # 2. 关闭爬虫引擎
        if hasattr(self.crawler, 'engine') and self.crawler.engine.running:
            self.crawler.engine.close()
        # 3. 强制终止Twisted反应器（关键：终止程序）
        if reactor.running:
            reactor.stop()
        # 4. 抛出CloseSpider确保爬虫逻辑终止
        raise CloseSpider(reason=reason)

    def stop_all_timers(self):
        """停止所有Twisted定时器"""
        # 停止全局超时定时器
        if self.timeout_call and self.timeout_call.active():
            self.timeout_call.cancel()
            self.timeout_call = None
        # 停止特定监控定时器
        if self.specific_check_call and self.specific_check_call.active():
            self.specific_check_call.cancel()
            self.specific_check_call = None
        self.logger.info("所有定时器已停止")

    def start_requests(self):
        """初始化：启动Twisted定时器（替代线程定时器）"""
        # 启动特定监控定时器（立即执行）
        self.specific_check_call = reactor.callLater(0, self.check_specific_timeout)
        # 启动全局超时定时器
        self.timeout_call = reactor.callLater(self.SPIDER_TIMEOUT, self.timeout_close)
        yield Request(self.start_urls[0], callback=self.parse)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)

        return spider

    def spider_closed(self, reason):
        """爬虫关闭时清理资源"""
        self.logger.info(f"爬虫关闭，原因：{reason}")
        self.stop_all_timers()  # 清理定时器
        if self.red:
            self.red.close()  # 关闭Redis连接



    def parse(self, resp,**kwargs):
        """解析逻辑（保持原有逻辑，仅补充更新最后响应时间）"""
        link_extractor = LinkExtractor()
        links = link_extractor.extract_links(resp)

        for link in links:

            # 命中list.htm时，更新最后响应时间（重置特定超时）
            if link.url.endswith('list.htm') and not self.red.sismember("tongzhi:link", link.url):
                self.last_specific_time = time.time()  # 关键：重置超时计时
                self.red.sadd("tongzhi:link", link.url)
                self.red.rpush("tongzhi:linklist", link.url)
                self.logger.info(f"已存入tongzhi: {link.url}")
                yield Request(url=link.url, callback=self.parse)

            if not self.red.sismember("zhengqing:link", link.url):
                self.red.sadd("zhengqing:link", link.url)
                self.logger.info(f"已存入zhengqing: {link.url}")
                yield Request(url=link.url, callback=self.parse)



        # 分页逻辑
        hrefs_fenye = resp.xpath("//li[@class='page_nav']/a/@href").extract()
        for href in hrefs_fenye:
            if href.startswith("javascript:void(0)"):
                continue
            href = resp.urljoin(href)
            self.logger.info(f"分页链接：{href}")
            yield Request(url=href, callback=self.parse)

