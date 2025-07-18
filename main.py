import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from datetime import datetime
import json
from datetime import datetime

def scrape_kayak_flights(origin, destination):
    date = datetime.now()  # Current date and time
    formatted_day = str(date.day)
    formatted_date = date.strftime("%B") + f" {formatted_day}, {date.year}"
    

    # Configure Chrome options
    chrome_options = Options()
    chrome_options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.popups": 0,
        "profile.default_content_setting_values.notifications": 2
    })
    # chrome_options.add_argument("--headless=new") 

    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://www.kayak.com/")

    flight_data = []
    
    try:
        original_window = driver.current_window_handle

        # Select one-way
        dropdown = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "Uqct-title")))
        dropdown.click()
        dropdown.click()

        onway = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="oneway"]')))
        onway.click()

        # Clear origin field
        clear_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//div[@aria-label="Remove value"]')))
        clear_btn.click()

        # Origin
        origin_input = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//input[@aria-label="Flight origin input"]')))
        origin_input.send_keys(origin)

        ul_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//ul[@id="flight-origin-smarty-input-list"]')))
        li_elements = ul_element.find_elements(By.TAG_NAME, 'li')
        if li_elements:
            li_elements[0].click()

        # Destination
        destination_input = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//input[@aria-label="Flight destination input"]')))
        destination_input.send_keys(destination)

        ul_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//ul[@id="flight-destination-smarty-input-list"]')))
        li_elements = ul_element.find_elements(By.TAG_NAME, 'li')
        if li_elements:
            li_elements[0].click()

        # Select Date
        depart_date = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, f'//div[@role="button" and contains(@aria-label, "{formatted_date}")]')))
        depart_date.click()
        

        # Click search
        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Search"]')))
        button.click()

        # Wait for possible tab switch
        print("🪟 Waiting for new tab or popup to open...")
        initial_windows = driver.window_handles

        try:
            WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > len(initial_windows))
            print("✅ New window opened.")
        except:
            print("⚠️ No new window opened — continuing in same tab.")
        time.sleep(2)  # Adjust this time (in seconds) to wait a little longer

        all_windows = driver.window_handles
        matched_window = None

        for handle in all_windows:
            driver.switch_to.window(handle)
            current_url = driver.current_url
            if "kayak.com/flights" in current_url:
                matched_window = handle
                print(f"🔗 Found a Kayak tab: {current_url}")
                break

        if matched_window:
            # Close other tabs
            for handle in all_windows:
                if handle != matched_window:
                    driver.switch_to.window(handle)
                    driver.close()
            driver.switch_to.window(matched_window)
        else:
            print("⚠️ No Kayak tab found — falling back to original.")
            driver.switch_to.window(original_window)
        # Extract results
        all_results = WebDriverWait(driver, 120).until(
            EC.presence_of_all_elements_located((By.XPATH, '//div[@class="Fxw9-result-item-container"]'))
        )

        for result in all_results:
            try:
                timeFlighttag = result.find_element(By.XPATH, './/div[@class="vmXl vmXl-mod-variant-large"]')
                timeFlight = timeFlighttag.find_element(By.TAG_NAME, 'span')
                price = result.find_element(By.XPATH, './/div[@class="e2GB-price-text"]')

                flight_data.append({
                    "Origin":origin,
                    "Destination":destination,
                    "departure_time": timeFlight.text,
                    "price": price.text,
                    "date":formatted_date
                })

            except Exception:
                continue

    except Exception as e:
        print("Error occurred:", e)

    finally:
        driver.quit()

    import json
    import os

    # Define the folder and filename
    folder_name = "kayak_flights_data_EU"
    base_name = "kayak_flights_EU"
    ext = ".json"
    counter = 1

    # Create the folder if it doesn't exist
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        print(f"✅ Folder '{folder_name}' created.")

    # Find an available filename
    while os.path.exists(f"{folder_name}/{base_name}_{counter}{ext}"):
        counter += 1

    filename = f"{folder_name}/{base_name}_{counter}{ext}"

    # Save the flight data to the JSON file
    with open(filename, "w", encoding='utf-8') as f:
        json.dump(flight_data, f, indent=4)

    print(f"✅ Flight data saved to {filename}")

    return flight_data