
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

# Paths
domainlist_csv = '../../data/site-profiles/domenii-institutii-centrale.csv'
domain_column = 'clean'
results_csv = '../../data/site-profiles/selenium-ping.csv'

# Define the number of rows to write to CSV at once
batch_size = 20

gecko_driver_path = '/usr/local/bin/geckodriver'
# Function to fetch the webpage and collect data
def fetch_website_data(driver, domain, row):
    try:
        # Start the timer for response_time_1
        start_time_1 = time.time()

        # Open the URL
        driver.get(f'http://{domain}')

        # Wait for the page to load completely
        driver.execute_script("return window.performance.timing.loadEventEnd > 0")
        end_time_load = time.time()

        # Collect required data
        final_url = driver.current_url
        response_time_1 = end_time_load - start_time_1
        # response_code = driver.execute_script("return JSON.stringify(window.performance.timing)")
        response_code = driver.execute_script("return window.performance.timing.responseEnd")

        response_time_load = end_time_load - start_time_1
        page_size = driver.execute_script("return document.body.scrollHeight")
        page_size_words = len(driver.page_source.split())
        last_updated = time.strftime('%Y-%m-%d %H:%M:%S')
        fetch_error = None  # No error if page loaded successfully

    except Exception as e:
        # Handle errors
        final_url = None
        response_time_1 = None
        response_code = None
        response_time_load = None
        page_size = None
        page_size_words = None
        last_updated = None
        fetch_error = str(e)

    return [domain, final_url, response_time_1, response_code, response_time_load, page_size, page_size_words, last_updated, fetch_error]

# Create a Firefox WebDriver with visible browser
options = Options()
options.headless = False
options.binary_location = '/usr/bin/firefox'  # Replace with your Firefox binary location
# driver = webdriver.Firefox(options=options, executable_path='/usr/local/bin/geckodriver')  # Replace with your geckodriver path
firefox_options = Options()
driver = webdriver.Firefox(service=FirefoxService(executable_path=gecko_driver_path), options=firefox_options)


# Read domain list from CSV
with open(domainlist_csv, 'r') as infile:
    reader = csv.DictReader(infile)
    rows = list(reader)



# Initialize progress bar
total_rows = len(rows)
pbar = tqdm(total=total_rows)

# Write header to results_csv
header = ["domain", "final_url", "response_time_1", "response_code", "response_time_load", "page_size", "page_size_words", "last_updated", "fetch_error"]
with open(results_csv, 'w', newline='') as outfile:
    csv_writer = csv.writer(outfile)
    csv_writer.writerow(header)

# Loop through the domain list, fetch data, and write to CSV
results_data = []
for i, row in enumerate(rows):
    domain = row[domain_column]
    result_row = fetch_website_data(driver, domain, row)
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
