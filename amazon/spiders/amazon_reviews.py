import scrapy
from urllib.parse import urljoin
import logging

class AmazonReviewsSpider(scrapy.Spider):

    logging.basicConfig(filename='scraper.log', level=logging.DEBUG,
                        format= '%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    name = "amazon_reviews"

    handle_httpstatus_list = [404]

    custom_settings = {
        'FEEDS': { 'data/%(name)s_%(time)s.csv': { 'format': 'csv',}}
        }

    def start_requests(self):
        asin_list = ['B09RD7XM9X']
        for asin in asin_list:
            amazon_reviews_url = f"https://www.amazon.com/product-reviews/{asin}/ref=cm_cr_getr_d_paging_btm_next_1?pageNumber=1"
            yield scrapy.Request(url=amazon_reviews_url, callback=self.parse_reviews, meta={'asin': asin, 'retry_count': 0, 'page_count': 1})


    def parse_reviews(self, response):
        
        asin = response.meta['asin']
        retry_count = response.meta['retry_count']
        page_count = response.meta['page_count']

        review_elements = response.css("#cm_cr-review_list div.review")
        if len(review_elements) > 0 and page_count <= 19:
            print(f"sussecsfull: {response.url}")
            retry_count = 0
            page_count += 1
            if page_count <= 10:
                next_page = f"https://www.amazon.com/product-reviews/{asin}/ref=cm_cr_getr_d_paging_btm_next_{page_count}?pageNumber={page_count}"
            else:
                next_page = f"https://www.amazon.com/product-reviews/{asin}/ref=cm_cr_getr_d_paging_btm_next_{page_count-10}?pageNumber={page_count-10}&sortBy=recent"
            yield scrapy.Request(url=next_page, callback=self.parse_reviews, meta={'asin': asin, 'retry_count': retry_count, 'page_count': page_count})

        elif retry_count < 3 and page_count <= 20:
            print(f"retrying {response.url} {retry_count+1}/3")
            if response.status != 404:
                with open(f"responses/{asin}_page_{page_count}_retry_{retry_count}.html", "w", encoding='utf-8') as file:
                    file.write(response.text)
            retry_count = retry_count+1
            yield scrapy.Request(url=response.url, callback=self.parse_reviews, dont_filter=True, meta={'asin': asin, 'retry_count': retry_count, 'page_count': page_count})

        for review_element in review_elements:
            yield {
                    "asin": asin,
                    "text": "".join(review_element.css("span[data-hook=review-body] ::text").getall()).strip(),
                    "title": review_element.css("*[data-hook=review-title]>span::text").get(),
                    "location_and_date": review_element.css("span[data-hook=review-date] ::text").get(),
                    "verified": bool(review_element.css("span[data-hook=avp-badge] ::text").get()),
                    "rating": review_element.css("*[data-hook*=review-star-rating] ::text").re(r"(\d+\.*\d*) out")[0],
                    }
    

