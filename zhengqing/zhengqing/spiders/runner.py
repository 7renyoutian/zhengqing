# 第一步：最顶部安装反应器
# import sys
# import os
# from scrapy.utils.reactor import install_reactor
#
# # 安装 AsyncioSelectorReactor
# install_reactor('twisted.internet.asyncioreactor.AsyncioSelectorReactor')
#
# # 第二步：导入Scrapy模块
# import scrapy
# from scrapy.crawler import CrawlerProcess
#
# # 添加路径
# sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
#
# # 导入爬虫（确保qing.py在当前路径）
# from qing import QingSpider
#
# # 配置
# settings = {
#     'BOT_NAME': 'qing_spider',
#     'ROBOTSTXT_OBEY': False,
#     'LOG_LEVEL': 'INFO',
#     'DOWNLOAD_TIMEOUT': 30,
#     'CONCURRENT_REQUESTS': 16,
#     'DEPTH_LIMIT': 0,
#     'TWISTED_REACTOR': 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'
# }
#
# # 启动爬虫
# process = CrawlerProcess(settings)
# process.crawl(QingSpider)
# # 关键：stop_after_crawl=False 确保爬虫不提前关闭
# process.start(stop_after_crawl=False)


import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.reactor import install_reactor
import os
import sys

# 强制安装AsyncioSelectorReactor（与Twisted兼容）
install_reactor('twisted.internet.asyncioreactor.AsyncioSelectorReactor')

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入修复后的爬虫类
from qing import QingSpider

# 配置爬虫进程
process = CrawlerProcess({
    'BOT_NAME': 'qing_spider',
    'ROBOTSTXT_OBEY': False,
    'LOG_LEVEL': 'INFO',
    # 禁用内置的超时处理，使用爬虫内的自定义超时
    'DOWNLOAD_TIMEOUT': 30,
    'CONCURRENT_REQUESTS' : 16,
    'CONCURRENT_REQUESTS_PER_DOMAIN' : 8,
})

# 启动爬虫
process.crawl(QingSpider)
process.start(stop_after_crawl=True)  # 关键：爬虫结束后自动停止反应器