from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import sys

# Path to ChromeDriver
chrome_driver_path = '/usr/bin/chromedriver'  # Adjust if necessary

# Function to simulate minimal delays (optional)
def minimal_delay():
    time.sleep(0.01)

# Function to read input from a text file
def read_input_from_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
        data = []
        for line in lines:
            # Skip the header row if it exists
            if line.startswith("City") or line.startswith("county"):
                continue
            # Skip empty lines
            if not line.strip():
                continue
            # Detect delimiter (tab or comma)
            if '\t' in line:
                delimiter = '\t'  # Tab-separated
            else:
                delimiter = ','   # Comma-separated
            # Split by the detected delimiter
            parts = line.strip().split(delimiter)
            if len(parts) != 5:
                print(f"Skipping invalid line: {line.strip()}")
                continue
            city, zip_code, first_name, last_name, dob = parts
            # Ensure the county name is in uppercase
            county = city.upper()
            data.append({
                'county': county,
                'zip_code': zip_code,
                'first_name': first_name,
                'last_name': last_name,
                'dob': dob
            })
    return data

# Function to perform a single search
def perform_search(input_data, driver):
    try:
        # Wait for the "Find your Voter Registration Status by Name" radio button to be clickable
        radio_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'ctl00_ContentPlaceHolder1_rdoSearchByName'))
        )
        radio_button.click()
        minimal_delay()

        # Wait for the County dropdown to be present
        county_dropdown = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'ctl00_ContentPlaceHolder1_CountyCombo'))
        )

        # Fill in the County dropdown
        Select(county_dropdown).select_by_visible_text(input_data['county'])
        minimal_delay()

        # Fill in the Zip Code
        zip_code_field = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_txtVRSzip')
        zip_code_field.clear()
        zip_code_field.send_keys(input_data['zip_code'])
        minimal_delay()

        # Fill in the First Name
        first_name_field = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_txtVRSOpt2Item2')
        first_name_field.clear()
        first_name_field.send_keys(input_data['first_name'])
        minimal_delay()

        # Fill in the Last Name
        last_name_field = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_txtVRSOpt2Item3')
        last_name_field.clear()
        last_name_field.send_keys(input_data['last_name'])
        minimal_delay()

        # Fill in the Date of Birth
        dob_field = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_txtVRSOpt2Item4')
        dob_field.clear()
        dob_field.send_keys(input_data['dob'])
        minimal_delay()

        # Submit the form
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'ctl00_ContentPlaceHolder1_btnContinue'))
        )
        submit_button.click()
        minimal_delay()

        # Wait for the results to load
        time.sleep(5)

        # Check if the "not found" message is displayed
        try:
            not_found_message = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_lblNotFound')
            if not_found_message.is_displayed():
                print(f"No results found for {input_data['first_name']} {input_data['last_name']}.")
                return None  # No results found
        except:
            pass

        # Capture the results
        results = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_UpdatePanel1').text
        print(f"Results found for {input_data['first_name']} {input_data['last_name']}.")
        return results  # Return the results as a string

    except Exception as e:
        print(f"An error occurred during the search: {e}")
        return None

# Function to restart the browser and reload the page
def restart_browser(service):
    driver = webdriver.Chrome(service=service)
    driver.minimize_window()
    driver.get('https://www.pavoterservices.pa.gov/pages/voterregistrationstatus.aspx')
    minimal_delay()
    return driver

# Main script
def main():
    driver = None
    try:
        # Ask the user if they want to read input from a file
        use_file = input("Do you want to read input from a file? (yes/no): ").strip().lower()
        if use_file == 'yes':
            file_path = input("Enter the path to the input file: ").strip()
            input_data_list = read_input_from_file(file_path)
        else:
            # Manual input for a single inquiry
            county = input("County: ").upper()
            zip_code = input("Zip Code: ")
            first_name = input("First Name: ")
            last_name = input("Last Name: ")
            dob = input("Date of Birth (mm/dd/yyyy): ")
            input_data_list = [{
                'county': county,
                'zip_code': zip_code,
                'first_name': first_name,
                'last_name': last_name,
                'dob': dob
            }]

        # Initialize the WebDriver using the Service class
        service = Service(chrome_driver_path)
        driver = restart_browser(service)

        # Track names that have already been processed
        processed_names = set()

        # Process each inquiry
        for i, input_data in enumerate(input_data_list):
            # Skip if the name has already been processed
            name_key = f"{input_data['first_name']} {input_data['last_name']}"
            if name_key in processed_names:
                print(f"Skipping already processed name: {name_key}")
                continue

            if i > 0 and i % 15 == 0:
                print("Restarting the browser to prevent CAPTCHA...")
                driver.quit()
                time.sleep(random.randint(60, 120))  # Wait 1-2 minutes
                driver = restart_browser(service)

            print(f"Processing inquiry {i + 1} for {input_data['first_name']} {input_data['last_name']}...")
            results = perform_search(input_data, driver)

            if results:
                # Save the results to a text file
                with open(f"results_{input_data['first_name']}_{input_data['last_name']}.txt", 'w', encoding='utf-8') as f:
                    f.write(results)  # Write the results as a string
                print(f"Results saved to 'results_{input_data['first_name']}_{input_data['last_name']}.txt'.")
                # Add the name to the processed set
                processed_names.add(name_key)

            # Refresh the page for the next inquiry
            driver.refresh()
            minimal_delay()

    except Exception as e:
        print(f"An error occurred: {e}")
        if driver:
            with open('page_source.txt', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            driver.save_screenshot('error_screenshot.png')

    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
