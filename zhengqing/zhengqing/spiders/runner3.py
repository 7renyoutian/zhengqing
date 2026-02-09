# runner3.py
# 第一步：优先初始化Reactor，避免与Scrapy冲突
from scrapy.utils.reactor import install_reactor
install_reactor('twisted.internet.asyncioreactor.AsyncioSelectorReactor')

# 第二步：导入其他依赖
from scrapy.crawler import CrawlerProcess
import os
import sys

# 添加当前目录到Python路径（确保能导入zeng.py）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入修复后的爬虫类
from zhengqing.spiders.zeng import ZengSpider

# 配置爬虫进程
process = CrawlerProcess({
    'BOT_NAME': 'zeng_spider',
    'ROBOTSTXT_OBEY': False,
    'LOG_LEVEL': 'INFO',
    'DOWNLOAD_TIMEOUT': 30,
    'CONCURRENT_REQUESTS' : 16,
    'CONCURRENT_REQUESTS_PER_DOMAIN' : 8,
    # 关键：删除/注释这行，恢复Scrapy内置去重（RFPDupeFilter）
    # 'DUPEFILTER_CLASS': 'scrapy.dupefilters.BaseDupeFilter',
    'COOKIES_ENABLED': False,
    'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'ITEM_PIPELINES': {'zhengqing.pipelines.ZhengqingPipeline': 300}
})

# 启动爬虫
process.crawl(ZengSpider)
process.start(stop_after_crawl=True)