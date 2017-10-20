"""Spider used to scrape asos.com products/articles."""

import scrapy
import json
import logging
import os
import re
from w3lib.url import url_query_cleaner
from logging.handlers import RotatingFileHandler
from scrapy.loader import ItemLoader
from ..items import AsosItem


class AsosSpider(scrapy.Spider):

    """Scrapy spider to crawl asos.com website.

    Crawls asos by first going to the main webpage, and then looking at the top tabs, such as women and men, then
    get all the links under tabs. If inside the link contains the grid of products, then we would go into each of the
    products, and get all the information including the images.

    Attributes:
        name (str): The name of the spider.
        start_urls (list): The urls to crawl from the start.

    """

    name = "asos"
    start_urls = ['http://us.asos.com/']

    def __init__(self):
        """Initialize the spider by setting up the logger and make sure the directory exists for the logger."""
        super(AsosSpider, self).__init__()
        if not os.path.exists("logs"):
            os.makedirs("logs")
        logging.getLogger().addHandler(RotatingFileHandler(f"logs/{self.name}.txt", maxBytes=1024000, backupCount=100))

    def parse(self, response):
        """Parse the website located in the start_urls list.

        The parse function is a function that is automatically executed on the start_urls when the spider starts.

        Args:
            response (scrapy.http.Response): A scrapy response after a webpage is parsed.

        """
        # Collect all article types on asos homepage, such as women->shoes, which are placed in an li html tag,
        # inside li tags have an attribute href that allow us to move to the next page
        for article in response.css("div[class=sub-floor-menu] li a::attr(href)").extract():
            request = scrapy.Request(article, callback=self.parse_article, meta={'item': item})
            yield request

    def parse_article(self, response):
        """Parse the each product/article that is shown.

        Args:
            response (scrapy.http.Response): A scrapy response after a webpage is parsed.

        """
        # After reach in each article, start collecting all product links to each product under the articles
        # that have href tag, meaning it leads to a product link, such as women->shoes->New Look Satin Twist Slider.
        for product_url in response.css("a.product.product-link::attr(href)").extract():
            request = scrapy.Request(product_url, callback=self.parse_item, meta={'item': item})
            request.meta["product_url"] = product_url
            yield request

    def parse_item(self, response):
        """Parse the each item's details.

        Args:
            response (scrapy.http.Response): A scrapy response after a webpage is parsed.

        """

        # Prepare data for json loads, because price, color, and size need to be extracted from json
        data = response.xpath('//script[contains(., "Pages/FullProduct")]/text()').re_first("view\('(\{.*\})',")

        # Avoid set products pages, which would give error when doing re.sub() afterwards
        if not data:
            return

        # Avoid backslash bugs, which would give error when loading json files
        data_cleaned = re.sub(r'[\\]+"', r'\"', data)
        data_cleaned = re.sub(r"[\\]+'", r"'", data_cleaned)

        # Load json files for the purpose to extract price, color and size
        data_json = json.loads(data_cleaned)

        # Create size_list as a list and color_set as a set to avoid repetition
        size_list = []

        # Iterate through variants to collect sizes and colors
        for variant in data_json['variants']:
            size_list.append(variant['size'])

        # Create an item loader in order to add data into our Scrapy items.
        loader = ItemLoader(item=AsosItem(), response=response)

        # Get the article type from the last page through meta
        loader.add_css("article_type", "div.asos-product div.bread-crumb ul li a::text")

        # Get the product name, such as Adidas Originals Velvet Vibes Hooded Track Top
        loader.add_css("product_name", "h1::text")

        # Get the product url
        loader.add_value("product_url", response.url)

        # Get the brand name for the product, such as Adidas
        loader.add_css("brand_name", "div.product-description span a strong::text")

        # Get the price from the website
        loader.add_value("price", data_json['price']['current'])

        # Get the size of the product, this could be sizes like numbers
        loader.add_value("fit", size_list)

        # Get the color of the article
        loader.add_value("colors", data_json['variants']['colour'])

        # Get the details and care information
        loader.add_css("details_and_care_info", "div.about-me span::text")
        loader.add_css("details_and_care_list", "div.care-info span::text")

        # image_urls and images are used for the download pipeline
        loader.add_css("image_urls", "li aa img::attr(src)")
        loader.add_value("images", None)

        # Add the spider name so we can use it to organize our json lines files
        loader.add_value("spider_name", self.name)
        yield loader.load_item()
