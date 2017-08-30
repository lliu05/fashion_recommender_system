import scrapy
import logging
import os
from urllib.parse import urlencode, urlunparse, urlparse, parse_qs
from logging.handlers import RotatingFileHandler
from scrapy.loader import ItemLoader
from ..items import NordstromItem


class NordstromSpider(scrapy.Spider):

    """Scrapy spider to crawl nordstrom.com website.

    Crawls Nordstrom by first going to the main webpage, and then looking at the top tabs, such as women and men, then
    get all the links under tabs. If inside the link contains the grid of products, then we would go into each of the
    products, and get all the information including the images.

    Attributes:
        name (str): The name of the spider.
        start_urls (list): The urls to crawl from the start.

    """

    name = "nordstrom"
    start_urls = ["http://shop.nordstrom.com/?origin=tab-logo"]

    def __init__(self):
        """Initialize the spider by setting up the logger and make sure the directory exists for the logger."""
        super(NordstromSpider, self).__init__()
        if not os.path.exists("logs"):
            os.makedirs("logs")
        logging.getLogger().addHandler(RotatingFileHandler(f"logs/{self.name}.txt", maxBytes=1024000, backupCount=100))

    def parse(self, response):
        """Parse the website located in the start_urls list.

        The parse function is a function that is automatically executed on the start_urls when the spider starts.

        Args:
            response (scrapy.http.Response): A scrapy response after a webpage is parsed.

        """
        # Nordstrom's menus such as under men->shoes->boots are placed under an li html tag, we need to find all the
        # li tags that has an attribute href that we can move to the next page
        for product_page in response.css("li a::attr(href)").extract():
            # We only want to get 4 items shown on the page at a time, because if there's more than 4 items, then
            # it is only shown when you scroll down
            url_parts = list(urlparse(response.urljoin(product_page)))
            query = dict(parse_qs(url_parts[4]))
            query.update({"top": 4, "page": 1})
            url_parts[4] = urlencode(query)
            request = scrapy.Request(urlunparse(url_parts), callback=self.parse_article)

            # Remember the page that we are on
            request.meta["page"] = 1
            yield request

    def parse_article(self, response):
        """Parse the each article/product that is shown in the 4xN grid.

        Args:
            response (scrapy.http.Response): A scrapy response after a webpage is parsed.

        """
        # Get the type of clothing this series belongs to, such as
        # Home/Women/Designer Collections/Designer Clothing/Dresses
        article_type = response.css("li a span[itemprop=name]::text").extract()

        # Make sure that we can get the article_type, since there's a lot of web pages that might not have an
        # article type, then we are sure that it doesn't show us any articles
        if article_type:
            # Find each articles (pictures) that has an href of them, they will link us to the product page
            articles = response.css(".product-photo-href::attr(href)").extract()

            # A flag to tell us not to traverse to the next page
            end_of_articles = False

            # If we reached the end of the page, then there are no more articles
            if articles:
                # For each article (or clothing) in each of Nordstrom's product page (the 4x16 grid) contains a class
                # called product-photo-href, we would need to get the class and then get the href attribute so we can
                # enter in the page of the actual product.
                for article in articles:
                    # The next page would be the response joined with the article
                    next_page = response.urljoin(article)
                    # Remember the article_type, which is Home/Women/Designer Collections/Designer Clothing/Dresses
                    # to the next page so that we can add this information
                    request = scrapy.Request(next_page, callback=self.parse_item)
                    request.meta["article_type"] = article_type
                    yield request
            else:
                # If it's the end of articles, then we won't go to the next page
                end_of_articles = True

            # Maybe there are more articles to traverse (next page)
            if not end_of_articles:
                # We want to get the next page, which is basically response's page + 1, then we would also bring this
                # incremented value to the next particle. If the next page doesn't have anymore articles we would then
                # stop going to the next page
                url_parts = list(urlparse(response.url))
                query = dict(parse_qs(url_parts[4]))
                next_page_num = response.meta["page"]+1
                query.update({"top": 4, "page": next_page_num})
                url_parts[4] = urlencode(query)
                request = scrapy.Request(urlunparse(url_parts), callback=self.parse_article)
                request.meta["page"] = next_page_num
                yield request

    def parse_item(self, response):
        """Parse the each item's details.

        Args:
            response (scrapy.http.Response): A scrapy response after a webpage is parsed.

        """
        # Create an item loader in order to add data into our Scrapy items.
        loader = ItemLoader(item=NordstromItem(), response=response)

        # Get the article type from the last page through meta
        loader.add_value("article_type", response.meta["article_type"])

        # Get the product name, such as Coos Long Bomber Jacket
        loader.add_css("product_name", "section[class=np-product-title] h1::text")

        # Get the product url
        loader.add_value("product_url", response.url)

        # Get the brand name for the product, such as ACNE STUDIOS
        loader.add_css("brand_name", "section[class=brand-title] h2 a span::text")

        # Get the price from the webpage
        loader.add_css("price", "div[class=current-price]::text")

        # Get the size of the article, this could be sizes like numbers
        loader.add_css("fit", "section.size-filter div[class=drop-down-options] div[class=option-main-text]::text")

        # Get the width of the article, this happens with shoes
        loader.add_css("width", "section.width-filter div[class=drop-down-options] div[class=option-main-text]::text")

        # Get the color of the article
        loader.add_css("colors", "section.color-filter div[class=color-option-text] div[class=option-main-text]::text")

        # The size info are sentences describing the sizes
        loader.add_css("size_info", "div.extended-product-details div.np-size-info span::text")

        # Get the details and care information
        loader.add_css("details_and_care_info", "div.product-details-and-care div.item-description-body p::text")
        loader.add_css("details_and_care_list", "div.product-details-and-care ul li::text")

        # image_urls and images are used for the download pipeline
        loader.add_css("image_urls", "li.image-thumbnail img::attr(src)")
        loader.add_value("images", None)
        yield loader.load_item()
