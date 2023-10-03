with python, having a csv file (url_list_file = '../data/domainlist.csv') containing a list of domains (the list of domains doesn't contain the protocol, http:// or https://)

loop each domain, and save the following fields in a sqlite database db_file = '../data/sites.db', table 'sites'

- domain: given domain url from csvfile
- url: check if url works with https:// or http:// and use that, also check if page redirects (with any method, including javascript). If fetch fails and domain name doesn't contain www., also try with www. Use the resulting url in the following queries:
- title: title of the frontpage,
- description: look for page description meta tag, and og:description field. If both found, save both, separated by '|| '.
- rss: list of rss feed urls, if found in the source
- is_wp: check if '/wp-content/' or '/wp-includes/' strings are found in front page source code,
- wp_json: true if {url}/wp-json/ exists and the response is a valid json,
- sitemap: url - check for <link rel="sitemap" .. > in head, or if {url}sitemap.xml exists,
- response_time: front page response time,
- page_size_html: character count of front page raw html (Mb), -1 if error fetching 
- page_size_text: character count of front page text (with header, scripts, tags, comments etc striped) (Mb), -1 if error fetching 
- ssl: if front page is encrypted,
- etag: if found in the request headers,
- fetch_date,
- ip 

use headers to simulate a browser request 
if domain fails to be fetched, save the error in the title column
use try / except so the script doesn't break on any failures
use tqdm to create a progress bar
use tqdm to show the currently fetched url, also a counter with total number of fetch errors, is_wp, rss
detect page encoding and save data accordingly 
