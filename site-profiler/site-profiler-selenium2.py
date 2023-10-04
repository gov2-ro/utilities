""" 
add timeout 15s
 """

# Paths
domainlist_csv = '../../data/site-profiles/domainlist-institutii-publice.csv'
domain_column = 'host'
results_csv = '../../data/site-profiles/selenium-pings-institutii-publice.csv'
# Define the number of rows to write to CSV at once
batch_size = 20
timeout = 10
gecko_driver_path = '/usr/local/bin/geckodriver'

import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from tqdm import tqdm
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET


# Function to fetch the webpage and collect data
def fetch_website_data(driver, domain, row):
    try:
        # Start the timer for response_time_1
        start_time_1 = time.time()
        rss_feeds = []
        sitemap_url = None        
        # Open the URL
        driver.get(f'http://{domain}')

        # Wait for the page to load completely
        # driver.execute_script("return window.performance.timing.loadEventEnd > 0")
        
        WebDriverWait(driver, timeout).until(lambda driver: driver.execute_script("return document.readyState === 'complete';"))
        end_time_load = time.time()

        # Collect required data
        final_url = driver.current_url
        response_time_1 = end_time_load - start_time_1
        # response_code = driver.execute_script("return JSON.stringify(window.performance.timing)")
        # response_code = driver.execute_script("return window.performance.timing.responseEnd")
        

        response_time_load = end_time_load - start_time_1
        page_size = driver.execute_script("return document.body.scrollHeight")
        page_size_words = len(driver.page_source.split())
        page_title = driver.title
  
        # Collect RSS feeds from page source (if any)
        page_source = driver.page_source
        
        soup = BeautifulSoup(page_source, 'html.parser')
        link_tags = soup.find_all('link', type='application/rss+xml')
        for link_tag in link_tags:
            rss_feeds.append(link_tag.get('href'))

        # Check for sitemap URL in page source

        try:
            sitemap_tags = soup.find_all('link', rel='sitemap')
            if sitemap_tags:
                sitemap_url = sitemap_tags[0].get('href')
        except:
            sitemap_url = None

        # If no sitemap URL found in page source, check {url}/sitemap.xml
        if not sitemap_url:
            try:
                sitemap_test_url = f'http://{domain}/sitemap.xml'
                sitemap_response = requests.get(sitemap_test_url)
                if sitemap_response.status_code == 200:
                    sitemap_url = sitemap_test_url
            except:
                sitemap_url = None

    except Exception as e:
        # Handle errors
        final_url = None
        response_time_1 = None
        # response_code = None
        response_time_load = None
        page_size = None
        page_size_words = None
 
        page_title = '-ERR: ' + str(e)

    return [domain, final_url, response_time_1, response_time_load, page_size, page_size_words, page_title, rss_feeds, sitemap_url]

# Create a Firefox WebDriver with visible browser
options = Options()
options.headless = False
options.binary_location = '/usr/bin/firefox'  # Replace with your Firefox binary location
# driver = webdriver.Firefox(options=options, executable_path='/usr/local/bin/geckodriver')  # Replace with your geckodriver path
firefox_options = Options()
driver = webdriver.Firefox(service=FirefoxService(executable_path=gecko_driver_path), options=firefox_options)

# driver.set_page_load_timeout(timeout)
driver.implicitly_wait(timeout)
# Read domain list from CSV
with open(domainlist_csv, 'r') as infile:
    reader = csv.DictReader(infile)
    rows = list(reader)



# Initialize progress bar
total_rows = len(rows)
pbar = tqdm(total=total_rows)

# Write header to results_csv
header = ["domain", "final_url", "response_time_1", "response_time_load", "page_size", "page_size_words",   "page_title", "rss_feeds", "sitemap_url"]
with open(results_csv, 'w', newline='') as outfile:
    csv_writer = csv.writer(outfile)
    csv_writer.writerow(header)

# Loop through the domain list, fetch data, and write to CSV
results_data = []
for i, row in enumerate(rows):
    domain = row[domain_column]
    result_row = fetch_website_data(driver, domain, row)
    tqdm.write('> ' + domain + ' --> ' + result_row[-3])
    results_data.append(result_row)
    pbar.update(1)

    if i % batch_size == 0 or i == total_rows - 1:
        with open(results_csv, 'a', newline='') as outfile:
            csv_writer = csv.writer(outfile)
            csv_writer.writerows(results_data)
        results_data = []

# Close the progress bar
pbar.close()

# Close the WebDriver
driver.quit()
