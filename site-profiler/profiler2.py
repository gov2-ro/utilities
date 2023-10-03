import os
import csv
import sqlite3
import requests
import chardet
from bs4 import BeautifulSoup
from tqdm import tqdm

# Define input and output file paths
# url_list_file = '../data/domainlist.csv'
# db_file = '../data/sites2.db'
url_list_file = '../../data/site-profiles/domainlist2.csv'
db_file = '../../data/site-profiles/sites-profiles2.db'

# Create SQLite database and table if it doesn't exist
conn = sqlite3.connect(db_file)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS sites (
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
                )''')
conn.commit()

# Function to fetch a URL and handle redirects
def fetch_url(url):
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()

        # Check if the URL was redirected and update the final URL
        final_url = response.url

        # Fetch page encoding
        encoding = chardet.detect(response.content)['encoding']
        
        return final_url, response.text, encoding

    except requests.exceptions.RequestException as e:
        return None, str(e), None

# Function to extract page title
def extract_title(html):
    soup = BeautifulSoup(html, 'html.parser')
    title_tag = soup.find('title')
    return title_tag.text if title_tag else None

# Function to extract page description
def extract_description(html):
    soup = BeautifulSoup(html, 'html.parser')
    meta_description = soup.find('meta', attrs={'name': 'description'})
    og_description = soup.find('meta', attrs={'property': 'og:description'})
    description = []

    if meta_description:
        description.append(meta_description['content'])
    
    if og_description:
        description.append(og_description['content'])

    return ' || '.join(description) if description else None

# Function to check if a URL exists
def url_exists(url):
    try:
        response = requests.head(url, headers={"User-Agent": "Mozilla/5.0"})
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

# Read domains from the CSV file and process them
with open(url_list_file, 'r') as csvfile:
    csvreader = csv.reader(csvfile)
    next(csvreader)  # Skip the header row

    for row in tqdm(csvreader, desc="Processing URLs"):
        domain = row[0]
        url = f"https://{domain}"
        if not url_exists(url) and not domain.startswith('www.'):
            url = f"https://www.{domain}"

        final_url, page_content, encoding = fetch_url(url)

        title = extract_title(page_content) if final_url else "Fetch Error"
        description = extract_description(page_content) if final_url else "Fetch Error"
        is_wp = 1 if "/wp-content/" in page_content or "/wp-includes/" in page_content else 0
        wp_json_url = f"{final_url}/wp-json/"
        wp_json_exists = 1 if url_exists(wp_json_url) else 0
        sitemap_url = f"{final_url}sitemap.xml"
        sitemap_exists = 1 if url_exists(sitemap_url) else 0
        response_time = None if not final_url else requests.get(final_url).elapsed.total_seconds()
        page_size_html = len(page_content) / (1024 * 1024) if final_url else -1
        page_size_text = len(' '.join(BeautifulSoup(page_content, 'html.parser').stripped_strings)) / (1024 * 1024) if final_url else -1
        ssl = 1 if final_url.startswith("https://") else 0
        etag = None  # You can implement this if needed
        fetch_date = None  # You can implement this if needed
        ip = None  # You can implement this if needed

        cursor.execute('''INSERT INTO sites (domain, url, title, description, is_wp, wp_json, sitemap, 
                        response_time, page_size_html, page_size_text, ssl, etag, fetch_date, ip) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                       (domain, final_url, title, description, is_wp, wp_json_exists, sitemap_exists,
                        response_time, page_size_html, page_size_text, ssl, etag, fetch_date, ip))
        conn.commit()

conn.close()
print("Data processing completed and saved to the database.")
