import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

 

# Function to open a URL, collect data, and save it to the output CSV file
def process_domain(domain, driver, output_csv):
    try:
        start_time = time.time()
        driver.get(domain)

        # Wait for the page to fully load (you can customize the wait time)
        time.sleep(5)

        response_time_1 = time.time() - start_time

        # Get the initial response header
        initial_response_header = str(driver.execute_script("return JSON.stringify(performance.timing)"))

        # Wait for the page to fully load (you can customize the wait time)
        time.sleep(5)

        response_time_final = time.time() - start_time

        # Get the page size
        page_size = driver.execute_script("return document.documentElement.outerHTML.length")
        page_size_words = len(driver.execute_script("return document.body.innerText.split(' ')"))

        # Get the last updated timestamp (if available)
        last_updated = driver.execute_script("return document.lastModified")

        # Save data to the output CSV file
        with open(output_csv, mode='a', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow([domain, driver.current_url, response_time_1, initial_response_header, response_time_final, page_size, page_size_words, last_updated, ''])
            print(domain + ' / ' + driver.current_url + ' / ' + str(response_time_1) + ' / ' + initial_response_header + ' / ' + str(response_time_final) + ' / ' + str(page_size) + ' / ' + str(page_size_words) + ' / ' + str(last_updated))

    except Exception as e:
        # If there is an error, save the error message
        with open(output_csv, mode='a', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow([domain, '', '', '', '', '', '', '', str(e)])

# Main function
def main():
    input_csv =  '../../data/site-profiles/domainlist2.csv'
    output_csv =  '../../data/site-profiles/out-x.csv'

    # Initialize Selenium webdriver (you may need to specify the path to your webdriver executable)
    driver = webdriver.Chrome()

    # Write CSV header
    with open(output_csv, mode='w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['Domain', 'Final_URL', 'Response_Time_1', 'Initial_Response_Header', 'Response_Time_Load', 'Page_Size', 'Page_Size_Words', 'Last_Updated', 'Fetch_Error'])

    # Read domains from input CSV and process each one
    with open(input_csv, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            domain = row['Hostname']
            process_domain(domain, driver, output_csv)

    # Close the Selenium webdriver
    driver.quit()

if __name__ == "__main__":
    main()
