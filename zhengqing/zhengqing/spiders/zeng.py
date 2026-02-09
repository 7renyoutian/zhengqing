import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.http import Request
import redis
from scrapy import signals
from scrapy.exceptions import CloseSpider
import time
from twisted.internet import reactor
import hashlib
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


class ZengSpider(scrapy.Spider):
    name = "zeng"
    allowed_domains = ["zzuli.edu.cn"]
    # 仅起始URL用的去重Hash的Redis key
    DUPLICATE_KEY = "spider:duplicate:fingerprints"
    FINGERPRINT_EXPIRE = 60 * 60 * 24 * 7  # 起始URL指纹过期7天
    # SPIDER_TIMEOUT = 1200  # 全局超时（秒）
    # specific_timeout = 180  # 特定监控超时（秒）
    # check_interval = 1  # 监控检测间隔（秒）

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.red = redis.Redis(host="127.0.0.1", port=6379, db=1, decode_responses=True)
        # self.timeout_call = None  # Twisted定时器引用（全局超时）
        # self.specific_check_call = None  # Twisted定时器引用（特定监控）
        # self.last_specific_time = time.time()  # 最后一次有效响应时间

    # def check_specific_timeout(self):
    #     """Twisted异步版：检查特定超时"""
    #     try:
    #         if time.time() - self.last_specific_time > self.specific_timeout:
    #             self.logger.error(f"[{self.specific_timeout}秒无有效响应] 触发爬虫关闭")
    #             self.stop_all_timers()
    #             self.force_stop_spider(reason="no_new_list_htm_url")
    #             return
    #
    #         if reactor.running:
    #             self.specific_check_call = reactor.callLater(
    #                 self.check_interval, self.check_specific_timeout
    #             )
    #     except Exception as e:
    #         self.logger.error(f"监控检测异常：{e}", exc_info=True)
    #         self.stop_all_timers()

    # def timeout_close(self):
    #     """全局超时回调：强制终止程序"""
    #     self.logger.info(f"[{self.SPIDER_TIMEOUT}秒全局超时] 触发程序终止")
    #     self.force_stop_spider(reason="global_timeout")
    #
    # def force_stop_spider(self, reason):
    #     """强制停止爬虫+终止反应器"""
    #     self.stop_all_timers()
    #     if hasattr(self.crawler, 'engine') and self.crawler.engine.running:
    #         self.crawler.engine.close()
    #     if reactor.running:
    #         reactor.stop()
    #     if hasattr(self.crawler, 'engine') and not self.crawler.engine.stopped:
    #         raise CloseSpider(reason=reason)
    #
    # def stop_all_timers(self):
    #     """停止所有Twisted定时器"""
    #     if self.timeout_call and self.timeout_call.active():
    #         self.timeout_call.cancel()
    #         self.timeout_call = None
    #     if self.specific_check_call and self.specific_check_call.active():
    #         self.specific_check_call.cancel()
    #         self.specific_check_call = None
    #     self.logger.info("所有定时器已停止")

    def normalize_url(self, url):
        """URL归一化：仅用于起始URL的指纹生成"""
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        sorted_query = urlencode(sorted(query.items()), doseq=True)
        normalized = urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path.rstrip('/'),
            parsed.params,
            sorted_query,
            parsed.fragment
        ))
        return normalized

    def generate_request_fingerprint(self, url, method='GET', body=None):
        """生成起始URL的唯一指纹"""
        normalized_url = self.normalize_url(url)
        request_features = [
            normalized_url,
            method.upper(),
            body if body else ''
        ]
        fingerprint = hashlib.md5('|'.join(request_features).encode('utf-8')).hexdigest()
        return fingerprint

    def clean_expired_fingerprints(self):
        """清理过期的起始URL指纹（可选）"""
        current_time = time.time()
        fingerprints = self.red.hgetall(self.DUPLICATE_KEY)
        if not fingerprints:
            return
        expired = [fp for fp, expire_ts in fingerprints.items() if float(expire_ts) < current_time]
        if expired:
            self.red.hdel(self.DUPLICATE_KEY, *expired)
            self.logger.debug(f"清理了{len(expired)}个过期的起始URL指纹")

    def is_request_duplicate(self, url, method='GET', body=None):
        """仅校验起始URL是否重复"""
        fingerprint = self.generate_request_fingerprint(url, method, body)
        if self.red.hexists(self.DUPLICATE_KEY, fingerprint):
            return True
        expire_ts = time.time() + self.FINGERPRINT_EXPIRE
        self.red.hset(self.DUPLICATE_KEY, fingerprint, str(expire_ts))
        self.clean_expired_fingerprints()
        return False

    def start_requests(self):
        """初始化：仅起始URL走自定义指纹去重"""
        # 启动定时器
        # self.specific_check_call = reactor.callLater(0, self.check_specific_timeout)
        # self.timeout_call = reactor.callLater(self.SPIDER_TIMEOUT, self.timeout_close)

        # 读取初始URL
        self.logger.info("开始读取Redis中的初始URL...")
        urls = self.red.lrange("tongzhi:linklist", 0, -1)
        urls = [url.decode('utf-8') if isinstance(url, bytes) else url for url in urls]
        self.logger.info(f"Redis读取到URL列表：{urls}，长度：{len(urls)}")

        request_count = 0
        for url_str in urls:
            # 仅起始URL走自定义指纹去重
            if self.is_request_duplicate(url_str):
                self.logger.debug(f"起始URL {url_str} 已重复，跳过")
                continue

            self.logger.info(f"生成初始请求：{url_str}")
            yield Request(url=url_str, callback=self.parse)
            request_count += 1

        self.logger.info(f"共生成{request_count}个初始请求")
        if request_count == 0:
            self.logger.error("未生成任何初始请求！请检查Redis数据或去重逻辑")
            # self.stop_all_timers()
            raise CloseSpider(reason="no_initial_requests")

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_closed(self, reason):
        """爬虫关闭时清理资源"""
        self.logger.info(f"爬虫关闭，原因：{reason}")
        # self.stop_all_timers()
        if self.red:
            try:
                self.red.connection_pool.disconnect()
                self.logger.info("Redis连接已优雅关闭")
            except Exception as e:
                self.logger.error(f"关闭Redis连接失败：{e}", exc_info=True)

    def parse(self, resp, **kwargs):
        """解析列表页：分页/详情页交给Scrapy内置去重"""
        try:
            link_extractor = LinkExtractor()
            links = link_extractor.extract_links(resp)
            for link in links:
                if not link.url.endswith(('page.htm', '.html')):
                    continue
                # 关键：移除page:link校验，详情页交给Scrapy内置去重
                if link.url.endswith('page.htm') and not self.red.sismember("pagelink", link.url):
                    self.red.sadd("pagelink", link.url)
                    #self.last_specific_time = time.time()  # 重置超时计时
                    self.logger.info(f"生成详情页请求：{link.url}")
                    yield Request(
                        url=link.url,
                        callback=self.parse_page,
                        priority=10,
                    )

            # 提取分页链接：移除is_request_duplicate校验，交给Scrapy内置去重
            hrefs_fenye = resp.xpath("//li[@class='page_nav']/a/@href").extract()
            for href in hrefs_fenye:
                if href.startswith("javascript:void(0)"):
                    continue
                href = resp.urljoin(href)
                self.logger.info(f"生成分页请求：{href}")
                yield Request(
                    url=href,
                    callback=self.parse,
                )
        except Exception as e:
            self.logger.error(f"解析列表页 {resp.url} 失败：{e}", exc_info=True)

    def parse_page(self, resp, **kwargs):
        """解析详情页：提取数据"""
        try:
            title = resp.xpath("//div[@class='article']/h1/text()").extract_first()
            # 提取纯文本
            texts = resp.xpath(
                "//body//text()[not(ancestor::script) and not(ancestor::style) and not(ancestor::svg) and not (ancestor::iframe)]").extract()
            filtered_texts = [text.strip() for text in texts if text.strip()]
            full_page_text = "\n".join(filtered_texts)

            # 提取图片链接
            jpgs = resp.xpath("//img/@src").extract()
            jpg_urls = []
            for jpg in jpgs:
                jpg_url = resp.urljoin(jpg)
                if jpg_url.lower().endswith((".jpg", ".jpeg", ".png")):
                    jpg_urls.append(jpg_url)

            item = {
                "link": resp.url,
                "title": title,
                "text": full_page_text,
                "jpg": jpg_urls
            }
            yield item
        except Exception as e:
            self.logger.error(f"解析详情页 {resp.url} 失败：{e}", exc_info=True)