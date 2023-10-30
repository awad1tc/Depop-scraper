import requests
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
import time

#Depop product search (mens trainers sorted by most popular) to be scraped - could turn this into a list for other categories
base_url='https://www.depop.com/gb/category/mens/shoes/sneakers/?categories=6&subcategories=54&sort=popular'
base_href ='https://www.depop.com'
max_scroll_count = 1
scroll_count = 0
product_links = []
seller_list = []
seller_links=[]

driver = webdriver.Chrome()
wait = WebDriverWait(driver,5)
driver.get(base_url)
wait.until(ec.visibility_of_element_located((By.CSS_SELECTOR, '#__next > div > div.sc-cZhdbk.lyxqn > div.sc-jQXnze.jbEdTw > button.sc-gFWTza.kCPnvT.sc-HjLFp.izavHH'))).click()
current_url = driver.current_url
time.sleep(1)
prev_height = driver.execute_script('return document.body.scollHeight')


while max_scroll_count > scroll_count:
    scroll_count += 1
    driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
    time.sleep(1)
    new_height = driver.execute_script('return document.body.scrollHeight')
    if new_height == prev_height:
        break
    prev_height = new_height
    
soup = BeautifulSoup(driver.page_source, 'lxml')
product_list = soup.find_all('div', class_="styles__ProductImageContainer-sc-369aefb3-3 eiGCuM")


for item in product_list:
    for link in item.find_all('a', href=True):
        product_links.append(base_href+link.get('href'))
        

for link in product_links:
    cur_page = requests.get(link)
    temp_soup = BeautifulSoup(cur_page.content, 'lxml')
    temp_soup = temp_soup.find('div', class_='styles__BioUserDetails-sc-46110958-2 dovOWV').find('a').get('href')
    seller_links.append(base_href+temp_soup)
    

for link in seller_links:
    cur_seller=[]
    cur_seller = requests.get(link)
    temp_soup = BeautifulSoup(cur_seller.content, 'lxml')
    temp_soup = temp_soup.find('div', class_='Container-sc-21c8a640-0 fagice')
    seller_name = temp_soup.find('p', class_='sc-eDnWTT styles__UserName-sc-e36d061d-4 ePldeT hlLCGy').text
    seller_rating = temp_soup.find('button', class_='styles__FeedbackContainer-sc-770a596e-0 hzjaRy').get('aria-label')
    items_sold = temp_soup.find('p', class_='sc-eDnWTT Signal-style__StyledText-sc-8ba3dbcb-2 kcKICQ denCzF').text
    followers = temp_soup.find('p', class_='sc-eDnWTT styles__StatsValue-sc-c1872ee6-0 fRxqiS lhsWNI').text
    description = temp_soup.find('p', class_='sc-eDnWTT kcKICQ').text if temp_soup.find('p', class_='sc-eDnWTT kcKICQ') is not None else None
    social = temp_soup.find('a', class_='sc-eDnWTT kcKICQ').get('href') if temp_soup.find('a', class_='sc-eDnWTT kcKICQ') is not None else None
    seller_list.append([seller_name, seller_rating, items_sold, followers, description, social, link])
        
