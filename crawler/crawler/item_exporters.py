"""item_exporters.py contains Scrapy item exporters.

Once you have scraped your items, you often want to persist or export those items, to use the data in some other
application. That is, after all, the whole purpose of the scraping process.

For this purpose Scrapy provides a collection of Item Exporters for different output formats, such as XML, CSV or JSON.

More Info:
    https://doc.scrapy.org/en/latest/topics/exporters.html

"""

import os

from scrapy.utils.serialize import ScrapyJSONEncoder
from scrapy.exporters import BaseItemExporter
from scrapy.utils.python import to_bytes


class JsonLinesItemSplitFileExporter(BaseItemExporter):

    """An item exporter to organize json lines into separate folders.

    Attributes:
        _configure (func): Uses to configure the Item Exporter by setting the options dictionary.
        encoder (ScrapyJSONEncoder): Encoder used to convert scrapy items into a json format line.

    """

    def __init__(self, **kwargs):
        """Initialize the configuration dictionary and encoder.

        Args:
            **kwargs: Arbitrary keyword arguments for the options dictionary.
        """
        # If dont_fail is set, it won't raise an exception on unexpected options
        self._configure(kwargs, dont_fail=True)
        kwargs.setdefault('ensure_ascii', not self.encoding)
        self.encoder = ScrapyJSONEncoder()
        super(JsonLinesItemSplitFileExporter, self).__init__()

    def export_item(self, spider, item=None):
        """Export Scrapy items to specific files based on the article_type

        Args:
            spider (scrapy.spider.Spiders): Scrapy spider that is used to crawl the item.
            item (scrapy.Item): A Scrapy item that contains a complete scraped information for an article/product.

        """
        # Serialize the item, and perform encoding to create a python dictionary
        item_dict = dict(self._get_serialized_fields(item))
        data = self.encoder.encode(item_dict) + os.linesep

        # If there is only one item in article_type, then the path (folders) would just be
        # scraped_data/spider.name/article_type. Otherwise we would combine all the article_type list except the last
        # item into a path, such as scraped_data/spider.name/article_type[0]/article_type[1], then the item would be
        # a json line placed in scraped_data/spider.name/article_type[0]/article_type[1]/article_type[2].jl.
        if len(item['article_type']) == 1:
            path = os.path.join("scraped_data", spider.name)
            item_path = os.path.join(path, item['article_type'][0]) + ".jl"
        else:
            path = os.path.join(os.path.join("scraped_data", spider.name), (os.path.join(*item['article_type'][:-1])))
            item_path = os.path.join(path, item['article_type'][-1]) + ".jl"
        if not os.path.exists(path):
            os.makedirs(path)

        # Write in append and byte mode
        open(item_path, 'a+b').write(to_bytes(data, self.encoding))
