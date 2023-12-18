import asyncio
import math
import httpx
from typing import TypedDict, List, Literal
import time
from urllib.parse import urlencode

from parsel import Selector
import pandas as pd



session = httpx.AsyncClient(
    # for our HTTP headers we want to use a real browser's default headers to prevent being blocked
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.35",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
    },
    # Enable HTTP2 version of the protocol to prevent being blocked
    http2=True,
    # enable automatic follow of redirects
    follow_redirects=True
)

# this is scrape result we'll receive
class ProductPreviewResult(TypedDict):
    """type hint for search scrape results for product preview data"""

    url: str  # url to full product page

def parse_search(response: httpx.Response) -> List[ProductPreviewResult]:
    previews = []
    sel = Selector(response.text)
    listing_boxes = sel.css('.srp-results li.s-item')
    for box in listing_boxes:
        # quick helpers to extract first element and all elements
        css = lambda css: box.css(css).get("").strip()
        previews.append(
            {
                "url": css("a.s-item__link::attr(href)").split("?")[0]
            }
        )
    return previews

SORTING_MAP = {
    "best_match": 12,
    "ending_soonest": 1,
    "newly_listed": 10,
}

async def scrape_search(
    query,
    max_page=1,
    category=0,
    items_per_page=120,
    location=1,
    with_store=1,
    sort: Literal['best_match', 'ending_soonest', 'newly_lsited'] = 'best_match'
) -> List[ProductPreviewResult]:
    def make_request(page):
        return  'https://www.ebay.co.uk/sch/i.html?'+ urlencode({
            "_nkw" : query,
            "_sacat" : category,
            "_ipg" : items_per_page,
            "_sop" : SORTING_MAP[sort],
            "_pgn" : page,
            "_PrefLoc" : location,
            "_SellerWithStore" : with_store,
            
            
        })
        

    first_page = await session.get(make_request(page=1))
    results = parse_search(first_page)
    if max_page == 1:
        return results
    # find total amount of results for concurrent pagination
    total_results = first_page.selector.css(".srp-controls__count-heading>span::text").get()
    total_results = int(total_results.replace(",", ""))
    total_pages = math.ceil(total_results / items_per_page)
    if total_pages > max_page:
        total_pages = max_page
    other_pages = [session.get(make_request(page=i)) for i in range(2, total_pages + 1)]
    for response in asyncio.as_completed(other_pages):
        response = await response
        try:
            results.extend(parse_search(response))
        except Exception as e:
            print(f"failed to scrape search page {response.url}")
    return results

def parse_product(response: httpx.Response) -> dict:
    sel = Selector(response.text)
    css = lambda css: sel.css(css).get("").strip()
    item = {}
    item["seller_url"] = css("[data-testid=str-title] a::attr(href)").split("?")[0]
    return item


product_links = asyncio.run(scrape_search("sneakers"))
product_links = [dict(t) for t in {tuple(d.items()) for d in product_links}]

session = httpx.Client(
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.35",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
    },
    http2=True,
    follow_redirects=True
)

seller_links = []

status_freq = 10
num_products = len(product_links)
num_batches = num_products // 10
completed_batches = 0

for pair in product_links[0:len(product_links)//2]:
    start = time.time()
    for key, value in pair.items():
        response = session.get(value)
        seller_links.append(parse_product(response))
    if len(seller_links) % status_freq == 0:
        end = time.time()
        time_elapsed = end - start
        completed_batches += 1
        print('Scraping seller links.... Batch {} of {} complete. Approximately {} minutes remaining'.format(completed_batches, num_batches, (num_batches-completed_batches)*time_elapsed))
        


def parse_sellers(response, link: httpx.Response) -> dict:
    sel = Selector(response.text)
    css_join = lambda css: sel.css(css).get("").strip()
    item = {}
    item['store_link'] = link
    item['store_name'] = sel.css('h1 a::text').getall()[0]
    item['feedback_percent'] = css_join('.str-seller-card__feedback-link>span::text')
    item['items_sold'] = sel.xpath('//div/div/div/div/span/text()').getall()[4]
    return item

session = httpx.Client(
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.35",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
    },
    http2=True,
    follow_redirects=True
)

seller_links = [dict(t) for t in {tuple(d.items()) for d in seller_links}]
seller_data = []
status_freq = 10
num_sellers = len(seller_links)
num_batches = num_sellers // 10
completed_batches = 0

for pair in seller_links:
    start = time.time()
    for key, value in pair.items():
        response = session.get(value)
        seller_data.append(parse_sellers(response, value))
    if len(seller_data) % status_freq == 0:
        end = time.time()
        time_elapsed = end - start
        completed_batches += 1
        print('Scraping seller data.... Batch {} of {} complete. Approximately {} minutes remaining'.format(completed_batches, num_batches, (num_batches-completed_batches)*time_elapsed))

def cleanse_sales_count(value):
    if 'M' in value:
        return int(value.replace('K','')) * 100000
    elif 'K' in value:
        return int(value.replace('K','')) * 1000
    else:
        return int(value)

df = pd.DataFrame(seller_data)

df['items_sold'] = df['items_sold'].apply(cleanse_sales_count)
print(df)