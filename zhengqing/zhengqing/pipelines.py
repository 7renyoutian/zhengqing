# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import redis
from scrapy.exceptions import DropItem
import json
# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class ZhengqingPipeline:
    def _safe_convert(self, value):
        """
        处理任意输入值，确保返回 Redis 支持的基础类型（优先字符串）
        :param value: 原始值（可能是 None、列表、Selector、str 等）
        :return: 合法的 str/int/float
        """
        # 1. 先处理 None 直接返回空字符串
        if value is None:
            return ""

        # 2. 处理可迭代对象（列表、元组等，比如 extract() 返回的列表）
        if isinstance(value, (list, tuple)):
            # 拼接成字符串，或取第一个非空元素，按需选择
            # 这里选择：拼接所有非空元素，用逗号分隔
            return ",".join([self._safe_convert(v) for v in value if v])

        # 3. 处理数字类型（int/float），直接转为字符串（方便统一存储）
        if isinstance(value, (int, float)):
            return str(value)

        # 4. 处理字符串类型（包括 str 和 bytes）
        if isinstance(value, str):
            return value.strip()  # 去除首尾空格，更整洁
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="ignore").strip()

        # 5. 其他未知类型，转为字符串表示
        try:
            return str(value).strip()
        except:
            return ""

    def open_spider(self,spider):
        self.red=redis.Redis(host='localhost',port=6379,db=1)


    def close_spider(self,spider):
        self.red.close()


    def process_item(self, item, spider):
        print(item['title'])

        # 先提取原始值，再通过自定义函数处理，确保无 None、无特殊类型
        link = self._safe_convert(item["link"])
        title = self._safe_convert(item.get("title"))
        text = self._safe_convert(item.get("text"))
        jpg = self._safe_convert(item.get("jpg"))

        #  把三个字段打包成一个字典，再转成 JSON 字符串
        full_data = json.dumps({
            "link": link,
            "title": title,
            "text": text,
            "jpg": jpg
        }, ensure_ascii=False)  # ensure_ascii=False 保留中文
        if not title and not text and not jpg:
            raise DropItem("所有字段均为空，丢弃该条数据")
        self.red.lpush('content:zeng',full_data)

        return item
