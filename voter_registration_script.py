from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import os
import csv
import calendar

# Path to ChromeDriver
chrome_driver_path = '/usr/bin/chromedriver'  # Adjust if necessary

# Dictionaries to cache mappings
MUNICIPALITY_TO_COUNTIES = {}
ZIP_TO_COUNTY = {}
ZIP_TO_CITY = {}

# Function to ensure results directory exists
def ensure_results_dir():
    if not os.path.exists('results'):
        os.makedirs('results')

# Function to check if results contain junk content
def is_junk_content(content):
    if not content:
        return True
    junk_phrases = [
        "FIND VOTER REGISTRATION STATUS",
        "Your search did not return any results",
        "Please correct the errors below and try again"
    ]
    return any(phrase in content for phrase in junk_phrases)

# Function to load municipality to counties mapping from CSV files in csv-dataset folder
def load_municipality_mapping(csv_folder='csv-dataset'):
    # Clear existing mapping
    MUNICIPALITY_TO_COUNTIES.clear()
    
    # Get all CSV files in the folder
    csv_files = [f for f in os.listdir(csv_folder) if f.endswith('.csv')]
    
    for filename in csv_files:
        with open(os.path.join(csv_folder, filename), mode='r') as csv_file:
            # Try different delimiters and header formats
            try:
                # First try tab-delimited with expected headers
                csv_reader = csv.DictReader(csv_file, delimiter='\t')
                row = next(csv_reader)  # Try reading first row to check columns
                
                # Check for required columns (case insensitive)
                required_columns = {'municipality', 'county'}
                actual_columns = {col.lower() for col in row.keys()}
                
                if not required_columns.issubset(actual_columns):
                    # Try comma-delimited if tab fails
                    csv_file.seek(0)
                    csv_reader = csv.DictReader(csv_file, delimiter=',')
                    row = next(csv_reader)
                    actual_columns = {col.lower() for col in row.keys()}
                    if not required_columns.issubset(actual_columns):
                        log_message(f"Skipping {filename}: Missing required columns")
                        continue
                
                # Determine column names (case insensitive)
                col_map = {}
                for col in csv_reader.fieldnames:
                    lower_col = col.lower()
                    if lower_col == 'municipality':
                        col_map['municipality'] = col
                    elif lower_col == 'county':
                        col_map['county'] = col
                
                # Process all rows
                csv_file.seek(0)
                next(csv_reader)  # Skip header
                for row in csv_reader:
                    try:
                        municipality = row[col_map['municipality']].lower().strip()
                        county = row[col_map['county']].upper().strip()
                        
                        # Initialize list if municipality not in dictionary
                        if municipality not in MUNICIPALITY_TO_COUNTIES:
                            MUNICIPALITY_TO_COUNTIES[municipality] = []
                        
                        # Add county if not already in list
                        if county not in MUNICIPALITY_TO_COUNTIES[municipality]:
                            MUNICIPALITY_TO_COUNTIES[municipality].append(county)
                        
                        # Add common variations
                        variations = []
                        if "borough" in municipality:
                            variations.append(municipality.replace(" borough", ""))
                        elif "township" in municipality:
                            variations.append(municipality.replace(" township", ""))
                        elif "city" in municipality:
                            variations.append(municipality.replace(" city", ""))
                        
                        for variation in variations:
                            if variation not in MUNICIPALITY_TO_COUNTIES:
                                MUNICIPALITY_TO_COUNTIES[variation] = []
                            if county not in MUNICIPALITY_TO_COUNTIES[variation]:
                                MUNICIPALITY_TO_COUNTIES[variation].append(county)
                    except KeyError as e:
                        log_message(f"Skipping row in {filename}: Missing column {e}")
                        continue
                        
            except Exception as e:
                log_message(f"Error processing {filename}: {str(e)}")
                continue

def load_zip_mapping(zip_file='zip-database/zip-codes.txt'):
    ZIP_TO_COUNTY.clear()
    ZIP_TO_CITY.clear()
    with open(zip_file, 'r') as file:
        for line in file:
            if line.strip() and line.startswith("ZIP Code"):
                parts = line.strip().split('\t')
                if len(parts) >= 3:
                    zip_code = parts[0].replace("ZIP Code ", "").strip()
                    city = parts[1].strip().lower()
                    county = parts[2].strip().upper()
                    ZIP_TO_COUNTY[zip_code] = county
                    ZIP_TO_CITY[zip_code] = city

def get_county(municipality_name, zip_code=None):
    # Clean inputs
    lower_municipality = municipality_name.lower().strip()
    
    # Try ZIP code first if available
    if zip_code:
        # First try exact ZIP code match
        if zip_code in ZIP_TO_COUNTY:
            return ZIP_TO_COUNTY[zip_code]
        
        # Then try matching city name from ZIP database
        if zip_code in ZIP_TO_CITY:
            zip_city = ZIP_TO_CITY[zip_code]
            if zip_city in MUNICIPALITY_TO_COUNTIES:
                counties = MUNICIPALITY_TO_COUNTIES[zip_city]
                if len(counties) == 1:
                    return counties[0]
    
    # Then try municipality mapping
    if lower_municipality in MUNICIPALITY_TO_COUNTIES:
        counties = MUNICIPALITY_TO_COUNTIES[lower_municipality]
        if len(counties) == 1:
            return counties[0]
        
        # If multiple counties, try to match with ZIP city
        if zip_code and zip_code in ZIP_TO_CITY:
            zip_city = ZIP_TO_CITY[zip_code]
            if zip_city.lower() == lower_municipality:
                return ZIP_TO_COUNTY.get(zip_code, counties[0])
    
    # Try common variations (remove "township", "borough", etc.)
    variations = [
        lower_municipality.replace(" township", ""),
        lower_municipality.replace(" borough", ""),
        lower_municipality.replace(" city", ""),
        lower_municipality.replace(" town", ""),
        lower_municipality.split("(")[0].strip(),
    ]
    
    for variation in variations:
        if variation in MUNICIPALITY_TO_COUNTIES:
            counties = MUNICIPALITY_TO_COUNTIES[variation]
            if len(counties) == 1:
                return counties[0]
    
    # If we get here and have multiple counties, log warning
    if lower_municipality in MUNICIPALITY_TO_COUNTIES:
        counties = MUNICIPALITY_TO_COUNTIES[lower_municipality]
        if len(counties) > 1:
            log_message(f"Warning: Municipality '{municipality_name}' exists in multiple counties: {', '.join(counties)}")
            if zip_code:
                log_message(f"Using first county in list for zip code {zip_code} (no exact match found)")
            return counties[0]
    
    # If not found, return the original input in uppercase
    log_message(f"Warning: Municipality '{municipality_name}' not found in mapping. Using as county name.")
    return municipality_name.upper()

# Function to simulate minimal delays (optional)
def minimal_delay():
    time.sleep(0.01)

# Update the read_input_from_file function to pass zip_code to get_county
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
            # Convert city to proper county, passing zip_code for disambiguation
            county = get_county(city, zip_code)
            
            # Parse the input date
            month, day, year = dob.split('/')
            start_day = int(day)
            
            # Generate dates starting from the input day, then wrap around the month
            for offset in range(0, 31):  # Check all 31 possible days
                day_to_try = (start_day + offset - 1) % 31 + 1  # Wrap around after day 31
                formatted_day = f"{day_to_try:02d}"
                new_dob = f"{month}/{formatted_day}/{year}"
                data.append({
                    'county': county,
                    'zip_code': zip_code,
                    'first_name': first_name,
                    'last_name': last_name,
                    'dob': new_dob
                })
    return data

def is_valid_date(month, day, year):
    try:
        month = int(month)
        day = int(day)
        year = int(year)
        
        # Check if month is valid (1-12)
        if month < 1 or month > 12:
            return False
            
        # Check if day is valid for the month
        _, last_day = calendar.monthrange(year, month)
        if day < 1 or day > last_day:
            return False
            
        return True
    except ValueError:
        return False

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
            
            # Parse the input date and validate
            try:
                month, day, year = dob.split('/')
                if not is_valid_date(month, day, year):
                    log_message(f"Skipping invalid date {dob} for {first_name} {last_name}")
                    continue
            except ValueError:
                log_message(f"Skipping malformed date {dob} for {first_name} {last_name}")
                continue
            
            # Convert city to proper county, passing zip_code for disambiguation
            county = get_county(city, zip_code)
            start_day = int(day)
            
            # Generate dates starting from the input day, then wrap around the month
            for offset in range(0, 31):  # Check all 31 possible days
                day_to_try = (start_day + offset - 1) % 31 + 1  # Wrap around after day 31
                # Validate the generated date
                if not is_valid_date(month, day_to_try, year):
                    continue
                formatted_day = f"{day_to_try:02d}"
                new_dob = f"{month}/{formatted_day}/{year}"
                data.append({
                    'county': county,
                    'zip_code': zip_code,
                    'first_name': first_name,
                    'last_name': last_name,
                    'dob': new_dob
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
                log_message(f"No results found for {input_data['first_name']} {input_data['last_name']}.")
                return None
        except:
            pass

        # Capture the results
        results = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_UpdatePanel1').text
        return results

    except Exception as e:
        log_message(f"An error occurred during the search: {e}")
        return None

# Function to restart the browser and reload the page
def restart_browser(service):
    # Set up Chrome options for headless
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")  # Important for Linux
    chrome_options.add_argument("--disable-dev-shm-usage")  # Important for Linux
    chrome_options.add_argument("--window-size=1920,1080")  # Set window size
    
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get('https://www.pavoterservices.pa.gov/pages/voterregistrationstatus.aspx')
    minimal_delay()
    return driver

# Function to check if the file size is 1.4 KiB (1,417 bytes)
def is_junk_file(file_path):
    try:
        # Get the file size in bytes
        file_size = os.path.getsize(file_path)
        # Check if the file size is 1,417 bytes
        return file_size == 1417
    except:
        return False

# Function to check and remove junk files
def check_and_remove_junk_files(input_data):
    result_file = os.path.join('results', f"results_{input_data['first_name']}_{input_data['last_name']}.txt")
    if os.path.exists(result_file):
        # Check file size first
        if is_junk_file(result_file):
            log_message(f"Junk file detected for {input_data['first_name']} {input_data['last_name']}. Removing file...")
            os.remove(result_file)
            return True
        
        # Then check content
        with open(result_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if is_junk_content(content):
                log_message(f"Junk content detected for {input_data['first_name']} {input_data['last_name']}. Removing file...")
                os.remove(result_file)
                return True
    return False

# Function to log messages to log.txt
def log_message(message):
    with open('log.txt', 'a') as log_file:
        log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
    print(message)  # Also print to console

# Main script
def main():
    # Ensure results directory exists
    ensure_results_dir()
    
    # Load the mappings at startup
    try:
        load_municipality_mapping()
        load_zip_mapping()
    except Exception as e:
        log_message(f"Warning: Could not load mapping files. Using fallback method. Error: {e}")

    driver = None
    try:
        # Ask the user if they want to read input from a file
        file_path = input("Enter the path to the input file: ").strip()
        input_data_list = read_input_from_file(file_path)
        
        # Initialize the WebDriver using the Service class
        service = Service(chrome_driver_path)
        driver = restart_browser(service)

        # Process each inquiry
        for i, input_data in enumerate(input_data_list):
            # Log the current line being processed
            log_message(f"Processing line {i + 1} in the CSV file: {input_data}")

            # Skip if date is invalid (shouldn't happen since we filtered in read_input_from_file)
            month, day, year = input_data['dob'].split('/')
            if not is_valid_date(month, day, year):
                log_message(f"Skipping invalid date {input_data['dob']} for {input_data['first_name']} {input_data['last_name']}")
                continue

            if i > 0 and i % 15 == 0:
                log_message("Restarting the browser to prevent CAPTCHA...")
                driver.quit()
                time.sleep(random.randint(10, 15))  # Wait 1-2 minutes
                driver = restart_browser(service)

            retry_count = 0
            max_retries = 2  # Maximum number of retries for junk results
            
            while retry_count <= max_retries:
                log_message(f"Processing inquiry {i + 1} for {input_data['first_name']} {input_data['last_name']} (attempt {retry_count + 1})...")
                results = perform_search(input_data, driver)

                if results:
                    # Check if results are junk
                    if not is_junk_content(results):
                        # Save the results to a text file in the results folder
                        with open(result_file, 'w', encoding='utf-8') as f:
                            f.write(results)
                        log_message(f"Valid results saved to '{result_file}'.")
                        break  # Exit retry loop if we got valid results
                    else:
                        log_message(f"Junk results detected for {input_data['first_name']} {input_data['last_name']}")
                        if retry_count < max_retries:
                            log_message("Retrying after browser restart...")
                            driver.quit()
                            time.sleep(random.randint(10, 15))
                            driver = restart_browser(service)
                            retry_count += 1
                        else:
                            log_message(f"Max retries reached for {input_data['first_name']} {input_data['last_name']}. Saving junk results for manual review.")
                            with open(result_file, 'w', encoding='utf-8') as f:
                                f.write(results)
                            break
                else:
                    log_message(f"No results obtained for {input_data['first_name']} {input_data['last_name']}")
                    break

            # Refresh the page for the next inquiry
            driver.refresh()
            minimal_delay()

    except Exception as e:
        log_message(f"An error occurred: {e}")
        if driver:
            with open('page_source.txt', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            driver.save_screenshot('error_screenshot.png')

    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()