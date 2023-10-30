from scraper_class import DepopScraper
import pandas as pd

base_url = 'https://www.depop.com/gb/category/mens/shoes/sneakers/?categories=6&subcategories=54&sort=popular' # Link to Deopop product search you want to scrape
max_scroll_count = 50 # Each page scroll translates to an additional 24 products/sellers scraped (24 scraped by default), scraping an additional scroll takes ~2-3 minutes 
csv_save_location = 'c:\\Users\\alexw\\Git projects\\Depop scraper\\Depop-scraper\\Output\\seller_list_1.csv' # Change file path
scraper = DepopScraper(base_url, max_scroll_count)
scraper.scrape()

def cleanse_follower_count(value):
    if 'K' in value:
        return float(value.replace('K','')) * 1000
    else:
        return float(value)

df = pd.DataFrame(scraper.seller_list, columns=['Seller Name', 'Seller Rating', '# Items Sold', '# Depop Followers', 'Social Media Link', 'Depop Store Link'])
df = df.drop_duplicates(subset=['Seller Name'], keep='first')

df['# Depop Followers'] = df['# Depop Followers'].apply(cleanse_follower_count)

pattern = r'(\d+) Shop Reviews\. Rated (\d+(?:\.\d+)?) out of 5 stars\.'
pattern2 = r'(\d+)'
df[['# Reviews', 'Star Rating']] = df['Seller Rating'].str.extract(pattern)
df['# Reviews'] = df['# Reviews'].astype(int)
df['Star Rating'] = df['Star Rating'].astype(float)
df['# Items Sold'] = df['# Items Sold'].str.extract(pattern2)

df = df.drop(columns='Seller Rating')
df = df[['Seller Name', '# Depop Followers','# Items Sold', '# Reviews', 'Star Rating', 'Social Media Link', 'Depop Store Link']]
df.to_csv(csv_save_location, index=False)

