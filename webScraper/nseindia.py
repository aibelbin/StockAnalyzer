import datetime
import requests
import os
import time
import json
import asyncio


DOWNLOAD_FOLDER = './corporate_filings_pdfs'
PROCESSED_IDS_FILE = './processed_nse_announcements.json'
CHECK_INTERVAL_SECONDS = 30


os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


def load_processed_ids():
    if os.path.exists(PROCESSED_IDS_FILE):
        with open(PROCESSED_IDS_FILE, 'r') as f:
            return set(json.load(f))
    return set()


def save_processed_ids(processed_ids):
    with open(PROCESSED_IDS_FILE, 'w') as f:
        json.dump(list(processed_ids), f)


processed_nse_ids = load_processed_ids()
print(f"Loaded {len(processed_nse_ids)} previously processed NSE announcement IDs.")


headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Connection': 'keep-alive',
}


max_retries = 3
download_timeout_per_attempt = 90

print(f" {CHECK_INTERVAL_SECONDS} interval seconds ")

while True:
    current_check_time = datetime.datetime.now()
    print(f"\ upd {current_check_time.strftime('%Y-%m-%d %H:%M:%S')} ")


    try:
        from bse import BSE
        pass
    except ImportError:
        pass
    except Exception as e:
        print(f"Skipping BSE check due to error: {e}")


    try:
        from nse import NSE
        with NSE(download_folder='./') as nse_api:
            announcements_nse = nse_api.announcements()

            new_announcements_count = 0

            for ann in reversed(announcements_nse):
                seq_id = ann.get('seq_id')
                if not seq_id:
                    print(f" {ann.get('desc', 'N/A')}")
                    continue

                if seq_id in processed_nse_ids:
                    continue

                new_announcements_count += 1
                symbol = ann.get('symbol', 'N/A')
                description = ann.get('desc', 'No Description')
                attachment_file_url = ann.get('attchmntFile')
                announcement_datetime_str = ann.get('an_dt')

                is_todays_announcement = False
                if announcement_datetime_str:
                    try:
                        ann_date = datetime.datetime.strptime(announcement_datetime_str, '%d-%b-%Y %H:%M:%S').date()
                        if ann_date == current_check_time.date():
                            is_todays_announcement = True
                    except ValueError:
                        print(f"Could not parse date '{announcement_datetime_str}' for announcement: {ann.get('desc', 'N/A')}. Assuming not today's.")

                if not is_todays_announcement:
                    print(f"New Seq ID {seq_id} found but not for today's date ({announcement_datetime_str}). Skipping download/alert.")
                    processed_nse_ids.add(seq_id)
                    continue

                print(f"\nNEW NSE Announcement: Symbol: {symbol}, Description: {description}")
                print(f"Date/Time: {announcement_datetime_str}, Seq ID: {seq_id}")
                print(f"Attachment URL: {attachment_file_url}")

                downloaded_file_path = None
                if attachment_file_url and attachment_file_url.endswith('.pdf'):
                    base_filename = os.path.basename(attachment_file_url).split('?')[0]
                    file_name_prefix = f"{symbol}_{current_check_time.strftime('%Y%m%d')}"
                    final_file_name = os.path.join(DOWNLOAD_FOLDER, f"{file_name_prefix}_{base_filename}")

                    print(f"Attempting to download: {final_file_name}")

                    for attempt in range(max_retries):
                        try:
                            print(f"Download attempt {attempt + 1}/{max_retries}...")
                            with requests.get(attachment_file_url, stream=True, timeout=download_timeout_per_attempt, headers=headers) as response:
                                response.raise_for_status()

                                total_size = int(response.headers.get('content-length', 0))
                                downloaded_size = 0

                                with open(final_file_name, 'wb') as f:
                                    for chunk in response.iter_content(chunk_size=8192):
                                        if chunk:
                                            f.write(chunk)
                                            downloaded_size += len(chunk)

                                print(f"Downloaded: {final_file_name} ({round(downloaded_size / 1024, 2)} KB)")
                                downloaded_file_path = final_file_name
                                break

                        except requests.exceptions.Timeout:
                            print(f"Download timed out after {download_timeout_per_attempt} seconds. Retrying...")
                            time.sleep(5 * (attempt + 1))
                        except requests.exceptions.ConnectionError as ce:
                            print(f"Connection error: {ce}. Retrying...")
                            time.sleep(5 * (attempt + 1))
                        except requests.exceptions.RequestException as e:
                            print(f"HTTP or other Request error: {e}. Not retrying this specific error for now.")
                            break
                        except Exception as e:
                            print(f"An unexpected error occurred during PDF download: {e}. Not retrying.")
                            break
                    else:
                        print(f"Failed to download {final_file_name} after {max_retries} attempts.")
                elif attachment_file_url:
                    print(f"Attachment is not a PDF: {attachment_file_url}. Not downloading.")
                else:
                    print(f"No attachment URL found for this announcement.")

                alert_message = (
                    f"<b>New NSE Announcement:</b>\n"
                    f"Symbol: {symbol}\n"
                    f"Description: {description}\n"
                    f"Time: {announcement_datetime_str}\n"
                    f"<a href='{attachment_file_url}'>View Document</a>"
                )

                processed_nse_ids.add(seq_id)
                save_processed_ids(processed_nse_ids)

            time.sleep(3)

        print(f"Checked. Found {new_announcements_count} new NSE announcements.")

    except ImportError:
        print("NSE library not found. Please install: pip install nse")
    except Exception as e:
        print(f"Error during NSE processing: {e}")
        print("Please check the NSE library or network connection.")

    print(f"Waiting {CHECK_INTERVAL_SECONDS} seconds before next check...")
    time.sleep(CHECK_INTERVAL_SECONDS)