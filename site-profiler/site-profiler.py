import csv
import requests
import sqlite3
import os
import json
import time
import socket
import ssl
import urllib.parse
from bs4 import BeautifulSoup
from tqdm import tqdm
import xml.etree.ElementTree as ET
import feedparser

# Define the input CSV file and SQLite database file
# url_list_file = '../data/domainlist.csv'
# db_file = '../data/sites.db'
url_list_file = '../../data/site-profiles/domainlist2.csv'
db_file = '../../data/site-profiles/sites-profiles22.db'
# TODO: use If-None-Match / Etag 'If-None-Match': '"848f2-6067ebcfc4f9f-gzip"',
timeout = 6
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Brave";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-GB,en;q=0.8',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
}

# Initialize SQLite database and create the 'sites' table if it doesn't exist
conn = sqlite3.connect(db_file)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS sites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        domain TEXT,
        url TEXT,
        title TEXT,
        description TEXT,
        rss TEXT,
        is_wp INTEGER,
        wp_json INTEGER,
        sitemap TEXT,
        response_time REAL,
        page_size_html REAL,
        page_size_text REAL,
        ssl INTEGER,
        etag TEXT,
        fetch_date TEXT,
        ip TEXT
    )
''')
conn.commit()

# Function to check if a URL is valid
def is_valid_url(url):
    try:
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
        return True, response.url
    except (requests.exceptions.RequestException, requests.exceptions.HTTPError):
        return False, None

def validate_response(response_text, format):
    if format.lower() == "json":
        try:
            json_data = json.loads(response_text)
            return "JSON"
        except ValueError:
            pass

    elif format.lower() == "xml":
        try:
            xml_data = ET.fromstring(response_text)
            return "XML"
        except ET.ParseError:
            pass

    elif format.lower() == "rss":
        try:
            rss_data = feedparser.parse(response_text)
            if rss_data.get('feed', None):
                return "RSS"
        except Exception:
            pass

    # If the specified format is not recognized or parsing fails, return None
    return None

def get_content(url):
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
        return response.text

# Function to fetch data from a URL and extract required information
def fetch_data(domain):
    domain = domain.strip('/')
    http_url = f"http://{domain}"
    https_url = f"https://{domain}"
    www_url = f"http://www.{domain}"
    www_https_url = f"https://www.{domain}"

    valid, url = is_valid_url(https_url)
    if not valid:
        valid, url = is_valid_url(http_url)
    if not valid and not domain.startswith('www.'):
        valid, url = is_valid_url(www_url)
    if not valid and not domain.startswith('www.'):
        valid, url = is_valid_url(www_https_url)

    try:
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = soup.title.string if soup.title else None
        
        description = ""
        meta_description = soup.find("meta", {"name": "description"})
        og_description = soup.find("meta", {"property": "og:description"})
        if meta_description:
            description += meta_description.get('content')
        if og_description:
            description += ' ' + og_description.get('content')
        
        rss_links = []
        for link in soup.find_all("link", rel="alternate"):
            if link.get("type") == "application/rss+xml":
                rss_links.append(link.get("href"))

        is_wp = int('/wp-content/' in response.text or '/wp-includes/' in response.text)
        
        wp_json_url = f"{url}/wp-json/"
        wp_json_valid, _ = is_valid_url(wp_json_url)
        if wp_json_valid:
            if validate_response(get_content(wp_json_url), 'json') is not None:
                wp_json_valid = wp_json_url
            else: 
                wp_json_valid = 0
    

        sitemap_link = soup.find("link", rel="sitemap")
        sitemap_url = sitemap_link.get("href") if sitemap_link else url + 'sitemap.xml'
        if validate_response(get_content(sitemap_url), 'xml') is None:
                # tqdm.write('sitemap ok')
                # continue()
                sitemap_url = 0
        # else: 
        #     sitemap_url = 0        
        
        response_time = response.elapsed.total_seconds()
        page_size_html = len(response.text) / (1024 * 1024)  # MB
        page_size_text = len(soup.get_text()) / (1024 * 1024)  # MB
        
        ssl_enabled = bool(response.url.startswith('https'))
        
        etag = response.headers.get('etag')
        
        fetch_date = time.strftime('%Y-%m-%d %H:%M:%S')
        
        ip = socket.gethostbyname(urllib.parse.urlparse(url).netloc)

        return (
            domain,
            url,
            title,
            description,
            json.dumps(rss_links),
            is_wp,
            wp_json_valid,
            sitemap_url,
            response_time,
            page_size_html,
            page_size_text,
            ssl_enabled,
            etag,
            fetch_date,
            ip,
        )
    except Exception as e:
        return (domain, str(e), None, None, None, None, None, None, None, None, None, None, None, None, None)

# Read the CSV file and process each domain
with open(url_list_file, 'r') as csvfile:
    reader = csv.reader(csvfile)
    next(reader)  # Skip header row
    
    # Initialize counters
    total_errors = 0
    total_is_wp = 0
    total_rss = 0
    
    for row in tqdm(reader):
        domain = row[0]
        data = fetch_data(domain)
        cursor.execute('INSERT INTO sites VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', data)
        conn.commit()
        tqdm.write(domain)
        # Update counters
        if data[2] is None:  # Title is None (error)
            total_errors += 1
        if data[5] == 1:  # is_wp is 1
            total_is_wp += 1
        if data[4] is not None:  # RSS is not None
            rss_links = json.loads(data[4])
            total_rss += len(rss_links)

# Close the database connection
conn.close()

# Print the total counts
print(f"Total Fetch Errors: {total_errors}")
print(f"Total is_wp: {total_is_wp}")
print(f"Total RSS Links: {total_rss}")
