import os
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import time
from datetime import datetime

DOWNLOAD_FOLDER = "nse_quarterly_results_pdfs"
NSE_ANNOUNCEMENTS_URL = "https://www.nseindia.com/companies-listing/corporate-filings-announcements"
NSE_BASE_URL = "https://www.nseindia.com"
NSE_PDF_BASE_URL = "https://nsearchives.nseindia.com" 


if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)
    print(f"Created download folder: {DOWNLOAD_FOLDER}")
else:
    print(f"Download folder already exists: {DOWNLOAD_FOLDER}")

HEADERS_FOR_REQUESTS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': '*/*',
    'Referer': NSE_ANNOUNCEMENTS_URL,
    'X-Requested-With': 'XMLHttpRequest',
}

def get_chrome_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    
    options.page_load_timeout = 90 
    
    driver = webdriver.Chrome(options=options)

    driver.implicitly_wait(10)
    return driver

def fetch_and_download_quarterly_results_selenium():
    driver = None
    downloaded_count = 0
    
    try:
        driver = get_chrome_driver()
        print(f"Navigating to {NSE_ANNOUNCEMENTS_URL} using Selenium...")
        driver.get(NSE_ANNOUNCEMENTS_URL)

        
        print("Waiting for announcements table to load (max 45 seconds)...")
        WebDriverWait(driver, 120).until( 
            EC.presence_of_element_located((By.CSS_SELECTOR, "table.table-striped tbody tr"))
        )
        print("Announcements table loaded successfully.")

        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')

        announcements_table = soup.find('table', class_='table-striped')
        if not announcements_table:
            print("Error: Could not find the announcements table with class 'table-striped'.")
            return

        print("Parsing table for quarterly results...")
        for row in announcements_table.find_all('tr'):
            columns = row.find_all('td')
            
            if len(columns) >= 7:
                subject_text = columns[3].get_text(strip=True).lower()
                company_name = columns[2].get_text(strip=True).replace(' ', '_').replace('.', '')
                broadcast_date_time_str = columns[6].get_text(strip=True)
                
                attachment_link_tag = columns[5].find('a', href=True)
                
                pdf_full_url = None
                if attachment_link_tag:
                    relative_path = attachment_link_tag['href']
                    if '.pdf' in relative_path.lower():
                        if relative_path.startswith('/corporate/'):
                             pdf_full_url = f"{NSE_PDF_BASE_URL}{relative_path}"
                        elif not relative_path.startswith('http'):
                            pdf_full_url = f"{NSE_BASE_URL}{relative_path}"
                        else:
                            pdf_full_url = relative_path

                if pdf_full_url and \
                   ("quarterly result" in subject_text or \
                    "financial result" in subject_text or \
                    "audited financial result" in subject_text or \
                    "un-audited financial result" in subject_text or \
                    "unaudited financial result" in subject_text):
                    
                    try:
                        date_part = broadcast_date_time_str.split(' ')[0] 
                        date_obj = datetime.strptime(date_part, '%d-%b-%Y')
                        formatted_date = date_obj.strftime('%Y-%m-%d')
                    except ValueError:
                        formatted_date = date_part.replace('/', '-').replace(' ', '_').replace(':', '')

                    filename = f"{company_name}_{formatted_date}_QuarterlyResult.pdf"
                    filepath = os.path.join(DOWNLOAD_FOLDER, filename)

                    if not os.path.exists(filepath):
                        print(f"Found new result: {filename}. Attempting download from: {pdf_full_url}")
                        try:
                            pdf_response = requests.get(pdf_full_url, stream=True, headers=HEADERS_FOR_REQUESTS, timeout=30)
                            pdf_response.raise_for_status()

                            with open(filepath, 'wb') as f:
                                for chunk in pdf_response.iter_content(chunk_size=8192):
                                    f.write(chunk)
                            print(f"Successfully downloaded: {filename}")
                            downloaded_count += 1
                        except requests.exceptions.RequestException as req_err:
                            print(f"Error downloading {filename} from {pdf_full_url}: {req_err}")
                    else:
                        print(f"Skipping {filename}: Already exists.")

        print(f"\nProcessing complete. Total new PDFs downloaded: {downloaded_count}")

    except TimeoutException:
        print("Error: Selenium timed out. The page or required elements did not load within the expected time.")
        print("This could be due to slow internet, heavy website load, or aggressive anti-bot measures.")
    except WebDriverException as e:
        print(f"Error: Selenium WebDriver encountered an issue: {e}")
        print("Ensure 'chromedriver' is installed and its version matches your Chrome browser. Also check system PATH.")
    except Exception as e:
        print(f"An unexpected error occurred during script execution: {e}")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    fetch_and_download_quarterly_results_selenium()