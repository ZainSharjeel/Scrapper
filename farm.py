from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException

import time
from datetime import datetime, timedelta
import logging
import json
import os
import csv
import random
import threading
import queue
from concurrent.futures import ThreadPoolExecutor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='flight_scraper_farm.log'
)

# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logging.getLogger().addHandler(console_handler)

# Ensure output directories exist
os.makedirs('data/json', exist_ok=True)
os.makedirs('data/csv', exist_ok=True)
os.makedirs('logs', exist_ok=True)

# Define popular routes to scrape
ROUTES = [
    {"origin": "Jeddah", "destination": "Dubai"},
    {"origin": "Jeddah", "destination": "Riyadh"},
    {"origin": "Dubai", "destination": "London"},
    {"origin": "Riyadh", "destination": "Cairo"},
    {"origin": "Jeddah", "destination": "Istanbul"}
    # Add more routes as needed
]

# User agent list for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
]

# Format the date properly for Kayak's date picker
def get_formatted_date(days_from_now=0):
    target_date = datetime.now() + timedelta(days=days_from_now)
    formatted_date = target_date.strftime("%B %d %Y")  # %B = full month name
    array = formatted_date.split(" ")
    
    # Remove leading zero from day if present and add comma
    if array[1][0] == "0":
        array[1] = array[1][1] + ","
    else:
        array[1] = array[1] + ","
        
    formatted_date = ' '.join(array)
    return formatted_date

def setup_driver(headless=True, proxy=None):
    chrome_options = Options()
    chrome_options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.popups": 0,  # 0 = block
        "profile.default_content_setting_values.notifications": 2  # block notifications
    })
    
    # Rotate user agents
    chrome_options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
    
    if headless:
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920,1080")
    
    # Add proxy if provided
    if proxy:
        chrome_options.add_argument(f'--proxy-server={proxy}')
    
    # Additional options to make headless Chrome more stable
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-features=NetworkService")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.maximize_window()  # Maximize window to ensure all elements are visible
    return driver

def select_from_dropdown(driver, input_xpath, input_text, list_id, max_retries=3):
    """Generic function to handle input and dropdown selection with retries"""
    for attempt in range(max_retries):
        try:
            # Clear any existing input and enter new text
            input_element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, input_xpath))
            )
            input_element.clear()
            input_element.send_keys(input_text)
            time.sleep(1)  # Give time for dropdown to populate
            
            # Wait for and select the first dropdown item
            ul_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, f'//ul[@id="{list_id}"]'))
            )
            
            # Get all list items
            li_elements = ul_element.find_elements(By.TAG_NAME, 'li')
            
            if li_elements:
                logging.info(f"Found {len(li_elements)} options for {input_text}")
                li_elements[0].click()
                time.sleep(1)  # Wait for selection to register
                return True
            else:
                logging.warning(f"No dropdown items found for {input_text}, attempt {attempt+1}")
                time.sleep(2)  # Wait before retrying
        except (TimeoutException, NoSuchElementException) as e:
            logging.warning(f"Error selecting from dropdown: {e}, attempt {attempt+1}")
            time.sleep(2)  # Wait before retrying
    
    logging.error(f"Failed to select {input_text} after {max_retries} attempts")
    return False

def handle_popups(driver):
    """Handle common popups that might appear on Kayak"""
    try:
        # Try to close cookie consent popup if it appears
        cookie_buttons = driver.find_elements(By.XPATH, '//button[contains(text(), "Accept") or contains(text(), "Got it") or contains(text(), "Close")]')
        for button in cookie_buttons:
            if button.is_displayed():
                button.click()
                logging.info("Closed cookie consent popup")
                time.sleep(1)
                break
                
        # Try to close any other random popups
        close_buttons = driver.find_elements(By.XPATH, '//button[@aria-label="Close" or contains(@class, "close")]')
        for button in close_buttons:
            if button.is_displayed():
                button.click()
                logging.info("Closed a popup")
                time.sleep(1)
                
    except Exception as e:
        logging.warning(f"Error handling popups: {e}")

def save_to_json(data, origin, destination, date_str):
    """Save scraped data to JSON file"""
    filename = f"data/json/{origin}_{destination}_{date_str.replace(' ', '_')}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    logging.info(f"Saved JSON data to {filename}")
    return filename

def save_to_csv(data, origin, destination, date_str):
    """Save scraped data to CSV file"""
    if not data:
        logging.warning("No data to save to CSV")
        return None
        
    filename = f"data/csv/{origin}_{destination}_{date_str.replace(' ', '_')}.csv"
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        fieldnames = data[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)
    logging.info(f"Saved CSV data to {filename}")
    return filename

def scrape_flight_data(origin, destination, date_str, headless=True, proxy=None, max_retries=2):
    """
    Scrape flight data for a specific route and date
    Returns a list of flight data dictionaries
    """
    retry_count = 0
    while retry_count <= max_retries:
        driver = None
        try:
            driver = setup_driver(headless=headless, proxy=proxy)
            logging.info(f"Starting scrape: {origin} to {destination} on {date_str}")
            
            # Navigate to Kayak
            driver.get("https://www.kayak.com/")
            logging.info("Navigated to Kayak homepage")
            
            # Wait for initial page load
            time.sleep(3 + random.uniform(1, 3))  # Add randomness to avoid detection
            
            # Handle potential popups or overlays
            handle_popups(driver)
            
            # Click on flight type dropdown
            dropdown = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "Uqct-title"))
            )   
            dropdown.click()
            logging.info("Clicked flight type dropdown")
            time.sleep(1)
            
            # Select one-way flight
            oneway = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="oneway"]'))
            )
            oneway.click()
            logging.info("Selected one-way flight")
            time.sleep(1)
            
            # Clear origin if needed
            try:
                clear_buttons = driver.find_elements(By.XPATH, '//div[@aria-label="Remove value"]')
                for btn in clear_buttons:
                    if btn.is_displayed():
                        btn.click()
                        logging.info("Cleared a field")
                        time.sleep(1)
            except Exception:
                logging.info("No clear buttons found or accessible")
            
            # Enter origin
            if not select_from_dropdown(
                driver, 
                '//input[@aria-label="Flight origin input"]', 
                origin, 
                "flight-origin-smarty-input-list"
            ):
                raise Exception(f"Failed to select origin location: {origin}")
            
            time.sleep(1 + random.uniform(0.5, 1.5))  # Add randomness
            
            # Enter destination
            if not select_from_dropdown(
                driver, 
                '//input[@aria-label="Flight destination input"]', 
                destination, 
                "flight-destination-smarty-input-list"
            ):
                raise Exception(f"Failed to select destination location: {destination}")
            
            time.sleep(1 + random.uniform(0.5, 1.5))  # Add randomness
            
            # Select departure date
            try:
                wait = WebDriverWait(driver, 15)
                depart_date = wait.until(EC.element_to_be_clickable((
                    By.XPATH,
                    f'//div[@role="button" and contains(@aria-label, "{date_str}")]'
                )))
                depart_date.click()
                logging.info(f"Selected departure date: {date_str}")
            except TimeoutException:
                logging.warning(f"Could not find exact date {date_str}, trying alternative date selection")
                # Try clicking on a date input field first (site might have changed)
                try:
                    date_input = driver.find_element(By.XPATH, '//input[contains(@placeholder, "Date")]')
                    date_input.click()
                    time.sleep(1)
                    
                    # Try finding a date by its number only
                    day_number = date_str.split()[1].replace(',', '')
                    day_element = driver.find_element(By.XPATH, f'//div[contains(@aria-label, "{day_number}") and @role="button"]')
                    day_element.click()
                except Exception as e:
                    logging.error(f"Alternative date selection failed: {e}")
                    raise
            
            time.sleep(1 + random.uniform(0.5, 1.5))  # Add randomness
            
            # Click search button
            button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Search"]'))
            )
            button.click()
            logging.info("Clicked search button")
            
            # Handle window/tab switching
            time.sleep(5)  # Wait for new tab to open
            
            # Make sure we have window handles before trying to access them
            if len(driver.window_handles) > 1:
                original_window = driver.current_window_handle
                
                # Find the new tab/window
                for window_handle in driver.window_handles:
                    if window_handle != original_window:
                        driver.switch_to.window(window_handle)
                        break
            
            # Just make sure we're on the results page by checking the URL
            current_url = driver.current_url
            if "kayak" not in current_url or "flights" not in current_url:
                logging.warning(f"Unexpected URL after search: {current_url}")
                # We might still be on the right page, so continue
            
            logging.info("Waiting for results to load (this may take up to 2 minutes)...")
            
            # Set a longer timeout for results page
            result_wait = WebDriverWait(driver, 120)
            
            # First try to wait for the loading indicator to disappear
            try:
                result_wait.until(EC.invisibility_of_element_located(
                    (By.XPATH, '//div[contains(@class, "Spinner") or contains(@class, "loader")]')
                ))
            except:
                logging.info("Loading indicator method failed or timed out, continuing anyway")
            
            # Then wait for actual results
            try:
                all_results = result_wait.until(
                    EC.presence_of_all_elements_located((By.XPATH, '//div[@class="Fxw9-result-item-container"]'))
                )
            except TimeoutException:
                # Try alternative selectors if the original one doesn't work
                try:
                    all_results = result_wait.until(
                        EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@class, "result-item")]'))
                    )
                except TimeoutException:
                    # One more attempt with a very generic selector
                    all_results = result_wait.until(
                        EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@class, "flight-result")]'))
                    )
            
            # If we still have no results, take a screenshot for debugging
            if not all_results:
                screenshot_path = f"logs/error_screenshot_{origin}_{destination}_{int(time.time())}.png"
                driver.save_screenshot(screenshot_path)
                logging.warning(f"No results found. Screenshot saved to {screenshot_path}")
                if retry_count < max_retries:
                    retry_count += 1
                    logging.info(f"Retrying ({retry_count}/{max_retries})...")
                    if driver:
                        driver.quit()
                    time.sleep(5 + random.uniform(2, 5))  # Wait before retrying
                    continue
                else:
                    return []
            
            logging.info(f"Found {len(all_results)} flight results")
            
            # Process flight results
            flight_data = []
            for i, result in enumerate(all_results):
                try:
                    flight_info = {
                        "origin": origin,
                        "destination": destination,
                        "date": date_str,
                        "flight_number": i + 1,
                        "scrape_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    # Try multiple ways to extract flight time
                    try:
                        time_element = result.find_element(By.XPATH, './/div[contains(@class, "vmXl")]//span')
                        flight_info["time"] = time_element.text
                    except:
                        try:
                            time_element = result.find_element(By.XPATH, './/div[contains(@class, "time")]')
                            flight_info["time"] = time_element.text
                        except:
                            flight_info["time"] = "Not available"
                    
                    # Try to extract airline
                    try:
                        airline = result.find_element(By.XPATH, './/div[contains(@class, "c_cgF")]')
                        flight_info["airline"] = airline.text
                    except:
                        try:
                            airline = result.find_element(By.XPATH, './/div[contains(@class, "carrier")]')
                            flight_info["airline"] = airline.text
                        except:
                            flight_info["airline"] = "Unknown"
                    
                    # Try to extract price
                    try:
                        price = result.find_element(By.XPATH, './/div[contains(@class, "price-text")]')
                        flight_info["price"] = price.text
                    except:
                        try:
                            price = result.find_element(By.XPATH, './/div[contains(@class, "price")]')
                            flight_info["price"] = price.text
                        except:
                            flight_info["price"] = "Price not available"
                    
                    # Try to extract flight duration
                    try:
                        duration = result.find_element(By.XPATH, './/div[contains(@class, "duration")]')
                        flight_info["duration"] = duration.text
                    except:
                        flight_info["duration"] = "Not available"
                    
                    # Try to extract stops information
                    try:
                        stops = result.find_element(By.XPATH, './/div[contains(@class, "stops")]')
                        flight_info["stops"] = stops.text
                    except:
                        flight_info["stops"] = "Not available"
                    
                    flight_data.append(flight_info)
                    logging.info(f"Processed flight {i+1}/{len(all_results)}")
                    
                except (NoSuchElementException, StaleElementReferenceException) as e:
                    logging.warning(f"Issue processing flight {i+1}: {e}")
                    continue
            
            # Successfully scraped data, return it
            return flight_data
            
        except Exception as e:
            logging.error(f"Error during scraping: {e}", exc_info=True)
            if retry_count < max_retries:
                retry_count += 1
                logging.info(f"Retrying ({retry_count}/{max_retries})...")
                time.sleep(5 + random.uniform(2, 5))  # Wait before retrying
            else:
                logging.error(f"Failed to scrape {origin} to {destination} on {date_str} after {max_retries} attempts")
                return []
                
        finally:
            if driver:
                driver.quit()
                logging.info("Browser closed")
    
    return []  # Return empty list if all retries failed

def worker(task_queue, results, max_workers):
    """Worker function for thread pool"""
    while not task_queue.empty():
        try:
            task = task_queue.get()
            origin = task["origin"]
            destination = task["destination"]
            date_str = task["date"]
            
            # Random delay between scrapes to avoid being blocked
            delay = random.uniform(1, 5)
            logging.info(f"Worker waiting {delay:.2f} seconds before starting task")
            time.sleep(delay)
            
            # Perform the scraping
            flight_data = scrape_flight_data(origin, destination, date_str, headless=True)
            
            if flight_data:
                # Save results to files
                json_file = save_to_json(flight_data, origin, destination, date_str)
                csv_file = save_to_csv(flight_data, origin, destination, date_str)
                
                # Add summary to results
                results.append({
                    "origin": origin,
                    "destination": destination,
                    "date": date_str,
                    "flights_found": len(flight_data),
                    "json_file": json_file,
                    "csv_file": csv_file
                })
            else:
                logging.warning(f"No flight data found for {origin} to {destination} on {date_str}")
                results.append({
                    "origin": origin,
                    "destination": destination,
                    "date": date_str,
                    "flights_found": 0,
                    "json_file": None,
                    "csv_file": None
                })
                
        except Exception as e:
            logging.error(f"Worker error: {e}", exc_info=True)
        finally:
            task_queue.task_done()

def run_scraper_farm(routes=None, days_ahead=None, max_workers=3):
    """
    Run the scraper farm with multiple threads
    
    Args:
        routes: List of origin-destination pairs to scrape. Default is ROUTES.
        days_ahead: List of days to look ahead for each route. Default is [0, 7, 14].
        max_workers: Maximum number of concurrent workers. Default is 3.
    """
    if routes is None:
        routes = ROUTES
        
    if days_ahead is None:
        days_ahead = [0, 7, 14]  # Today, next week, two weeks
    
    # Create task queue
    task_queue = queue.Queue()
    results = []
    
    # Add tasks to queue
    for route in routes:
        for days in days_ahead:
            date_str = get_formatted_date(days)
            task_queue.put({
                "origin": route["origin"],
                "destination": route["destination"],
                "date": date_str
            })
            
    # Create and start worker threads
    threads = []
    
    for _ in range(min(max_workers, task_queue.qsize())):
        thread = threading.Thread(
            target=worker, 
            args=(task_queue, results, max_workers)
        )
        threads.append(thread)
        thread.start()
    
    # Wait for all tasks to complete
    task_queue.join()
    
    # Log summary
    logging.info(f"Scraping completed for {len(results)} route-date combinations")
    for result in results:
        status = "SUCCESS" if result["flights_found"] > 0 else "FAILED"
        logging.info(f"{status}: {result['origin']} to {result['destination']} on {result['date']}: {result['flights_found']} flights")
    
    return results

if __name__ == "__main__":
    try:
        # Example usage
        logging.info("Starting Flight Scraper Farm")
        
        # Option 1: Scrape predefined routes
        results = run_scraper_farm(max_workers=2)
        
        # Option 2: Scrape custom routes
        # custom_routes = [
        #     {"origin": "New York", "destination": "Los Angeles"},
        #     {"origin": "Chicago", "destination": "Miami"}
        # ]
        # custom_days = [1, 3, 5]  # Tomorrow, 3 days from now, 5 days from now
        # results = run_scraper_farm(routes=custom_routes, days_ahead=custom_days, max_workers=2)
        
        # Save summary
        summary_file = f"data/summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=4)
        logging.info(f"Summary saved to {summary_file}")
        
    except Exception as e:
        logging.error(f"Main program error: {e}", exc_info=True)
