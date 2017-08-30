"""Processors that are used with Scrapy items.

The processors are used to either process the input before or after new data is received for a Scrapy item.

More Info:
    https://doc.scrapy.org/en/latest/topics/loaders.html#input-and-output-processors

"""


class RemoveSaleHome(object):

    """Removes Home or Sale keyword from the first or second item in the article_type array.

    Tries to remove the keyword home or sale from the article_type array if it appears in the first or second item.
    Since for all articles must start with home, so we can remove it due to redundancy. Sale keyword are also removed.

    """

    def __call__(self, values):
        """Function to remove Home or Sale keyword.

        Args:
            values (list): A list from a Scrapy's item with key 'article_type'.

        Returns:
            values (list): A list of Scrapy's item with key 'article_type' with removed items.

        """
        # Note that we must check for sale first, otherwise a pop(0) will let sale keyword become the 0th index, and
        # we would not be able to remove it.
        if "sale" in values[1].lower():
            values.pop(1)
        if "home" in values[0].lower():
            values.pop(0)
        return values
