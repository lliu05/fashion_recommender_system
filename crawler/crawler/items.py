"""items.py contains Scrapy items to store scraped data.

The main goal in scraping is to extract structured data from unstructured sources, typically, web pages. Scrapy spiders
can return the extracted data as Python dicts. While convenient and familiar, Python dicts lack structure: it is easy to
 make a typo in a field name or return inconsistent data, especially in a larger project with many spiders.

To define common output data format Scrapy provides the Item class. Item objects are simple containers used to collect
the scraped data. They provide a dictionary-like API with a convenient syntax for declaring their available fields.

More Info:
    https://doc.scrapy.org/en/latest/topics/items.html

"""

import scrapy
from scrapy.loader.processors import TakeFirst
from scrapy.loader.processors import MapCompose
from w3lib.url import url_query_cleaner
from .processors import RemoveSaleHome


class NordstromItem(scrapy.Item):

    """Scrapy item to store scraped data from Nordstrom.com.

    Attributes:
        article_type (scrapy.Field): List of the associated article type, for example: ['women', 'sports'].
        product_name (scrapy.Field): Str of the product name, for example: Cage Strap Tank.
        product_url (scrapy.Field): Str of the url of the product.
        brand_name (scrapy.Field): Str of associated brand of the product, for example: Zella.
        price (scrapy.Field): String of the price of the product.
        fit (scrapy.Field): List of the different sizes for the product.
        width (scrapy.Field): List of different width for the product, this is sometimes used in shoes.
        colors (scrapy.Field): List of colros for the product.
        size_info (scrapy.Field): List of information given for the size.
        details_and_care_info (scrapy.Field): List of care information for the product.
        details_and_care_list (scrapy.Field): List of care and details information.
        image_urls (scrapy.Field): List of urls of the images.
        images (scrapy.Field): List of hashes for corresponding image_urls.

    """

    article_type = scrapy.Field(output_processor=RemoveSaleHome())
    product_name = scrapy.Field(output_processor=TakeFirst())
    product_url = scrapy.Field(output_processor=TakeFirst())
    brand_name = scrapy.Field(output_processor=TakeFirst())
    price = scrapy.Field(output_processor=MapCompose(lambda x: x[1:]))
    fit = scrapy.Field()
    width = scrapy.Field()
    colors = scrapy.Field()
    size_info = scrapy.Field()
    details_and_care_info = scrapy.Field()
    details_and_care_list = scrapy.Field()
    image_urls = scrapy.Field(output_processor=MapCompose(lambda x: url_query_cleaner(x)))
    images = scrapy.Field()
