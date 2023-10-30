import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
import time

class DepopScraper:
    def __init__(self, base_url, max_scroll_count=1):
        self.base_url = base_url
        self.base_href = 'https://www.depop.com'
        self.max_scroll_count = max_scroll_count
        self.driver = webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, 5)
        self.product_links = []
        self.seller_list = []
        self.seller_links = []
        self.saved_scroll_pos = None
        self.scroll_count = 0
        self.products_scraped = 0
        
    def scrape(self):
        self.driver.get(self.base_url)
        self.wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, '#__next > div > div.sc-cZhdbk.lyxqn > div.sc-jQXnze.jbEdTw > button.sc-gFWTza.kCPnvT.sc-HjLFp.izavHH'))).click()
        time.sleep(1)
        prev_height = self.driver.execute_script('return document.body.scollHeight')
        global_start = time.time()

        while self.max_scroll_count > self.scroll_count:
            if self.max_scroll_count == 0:
                self.saved_scroll_pos = self.driver.page_source
                self.find_sellers(self.saved_scroll_pos)
            self.scroll_count += 1
            print("Scroll {}".format(self.scroll_count))
            self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
            time.sleep(1)
            new_height = self.driver.execute_script('return document.body.scrollHeight')
            if self.max_scroll_count == self.scroll_count:
                self.saved_scroll_pos = self.driver.page_source
                self.find_sellers(self.saved_scroll_pos)
            if new_height == prev_height:
                print("Scroll limit reached at {} scrolls\n".format(self.scroll_count))
                self.saved_scroll_pos = self.driver.page_source
                #self.find_sellers(self.saved_scroll_pos)
            prev_height = new_height
        global_end = time.time()
        global_elapsed = global_end - global_start
        print("{} out of {} scrolls completed and scraped. Total time elapsed: {} seconds".format(self.scroll_count,self.max_scroll_count, global_elapsed))

    def find_sellers(self, page_source):
        soup = BeautifulSoup(page_source, 'lxml')
        product_list = soup.find_all('div', class_="styles__ProductImageContainer-sc-369aefb3-3 eiGCuM")

        product_link_temp = []
        for item in product_list:
            for link in item.find_all('a', href=True):
                product_link_temp.append(self.base_href + link.get('href'))
        self.product_links.extend(product_link_temp)

        product_batches = len(product_link_temp)//24
        batches_processed = 0
        seller_link_temp = []
        print("Scraping product pages to amass seller links...\n")
        for link in product_link_temp:
            self.products_scraped += 1
            start = time.time()
            cur_page = requests.get(link)
            temp_soup = BeautifulSoup(cur_page.content, 'lxml')
            temp_soup = temp_soup.find('div', class_='styles__BioUserDetails-sc-46110958-2 dovOWV').find('a').get('href')
            seller_link_temp.append(self.base_href + temp_soup)
            if self.products_scraped % 24 == 0:
                batches_processed += 1
                end = time.time()
                time_elapsed = end - start
                print("Batch {} out of {} scraped, appoximately {} minutes remaining\n".format(batches_processed, product_batches, time_elapsed * (product_batches - batches_processed)))
        self.seller_links.extend(seller_link_temp)
        print("{} seller links scraped in total\n".format(self.products_scraped))

        batch_processed = 0
        total_batches = len(seller_link_temp)//24
        sellers_processed = 0
        seller_list_temp = []
        print("Scraping seller pages for data capture...\n")
        for link in seller_link_temp:
            start = time.time()
            cur_seller = requests.get(link)
            temp_soup = BeautifulSoup(cur_seller.content, 'lxml')
            temp_soup = temp_soup.find('div', class_='Container-sc-21c8a640-0 fagice')
            seller_name = temp_soup.find('p', class_='sc-eDnWTT styles__UserName-sc-e36d061d-4 ePldeT hlLCGy').text
            seller_rating = temp_soup.find('button', class_='styles__FeedbackContainer-sc-770a596e-0 hzjaRy').get('aria-label')
            items_sold = temp_soup.find('p', class_='sc-eDnWTT Signal-style__StyledText-sc-8ba3dbcb-2 kcKICQ denCzF').text
            followers = temp_soup.find('p', class_='sc-eDnWTT styles__StatsValue-sc-c1872ee6-0 fRxqiS lhsWNI').text
            social = temp_soup.find('a', class_='sc-eDnWTT kcKICQ')
            social = social.get('href') if social is not None else None
            seller_list_temp.append([seller_name, seller_rating, items_sold, followers, social, link])
            if(len(seller_list_temp)) % 24 == 0:
                end = time.time()
                time_elapsed = end - start
                batch_processed += 1
                mins_remaining = (time_elapsed * (total_batches - batch_processed))
                print("Scraped batch {} of {}. Approximately {} minutes remaining".format(batch_processed, total_batches,mins_remaining))
        self.seller_list.extend(seller_list_temp)
        print("Sellers succesfully added to database")

