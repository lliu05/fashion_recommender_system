"""Pipelines.py contains Scrapy pipelines.

After an item has been scraped by a spider, it is sent to the Item Pipeline which processes it through several
components that are executed sequentially.

More Info:
    https://doc.scrapy.org/en/latest/topics/item-pipeline.html

"""

from scrapy import signals
from .item_exporters import JsonLinesItemSplitFileExporter


class FashionSiteExportPipeline(object):

    """A pipeline that is used to organize json lines files.

    The pipeline is used in order to use an item exporter called JsonLinesItemSplitFileExporter to organize scraped
    output files. Otherwise all output files are aggregated into one file using default feed exports.

    """

    @classmethod
    def from_crawler(cls, crawler):
        """Creates a pipeline instance from a crawler.

        If present, this classmethod is called to create a pipeline instance from a Crawler. It must return a new
        instance of the pipeline. Crawler object provides access to all Scrapy core components like settings and
        signals; it is a way for pipeline to access them and hook its functionality into Scrapy.

        Args:
            crawler (scrapy.crawler.Crawler): A Scrapy crawler instance.

        Returns:
            pipeline (FashionSiteExportPipeline): A pipeline instance.

        """
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        """Sets up the JsonLinesItemSplitFileExporter exporter.

        This method is called when the spider is opened. We want to setup the exporter with our custom json lines item
        exporter.

        Args:
            spider (scrapy.spiders.Spider): A Scrapy spider instance.

        """
        spider.logger.info(f"{self.__class__.__name__} spider_opened")
        self.exporter = JsonLinesItemSplitFileExporter()
        self.exporter.start_exporting()

    def spider_closed(self, spider):
        """When the spider is closed, we need to tell the exporter to finish exporting.

        Args:
            spider (scrapy.spiders.Spider): A Scrapy spider instance.

        """
        spider.logger.info(f"{self.__class__.__name__} spider_closed")
        self.exporter.finish_exporting()

    def process_item(self, item, spider):
        """Process the item sent from the a spider.

        When a spider finishes crawling a website and yield an item, then this item will be sent to the process_item
        function. Then we will need to use the exporter to export the item given from the spider.

        Args:
            item (list or str): A list or str depending on if there's a list of item or only one item (then it is only
                a string).

        """
        spider.logger.info(f"{self.__class__.__name__} process_item {item}")
        self.exporter.export_item(spider, item)
        return item
