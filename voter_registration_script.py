from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time
import random

# Path to ChromeDriver
chrome_driver_path = '/usr/bin/chromedriver'  # Adjust if necessary

# Function to simulate human-like delays
def human_delay(min_seconds=1, max_seconds=3):
    time.sleep(random.uniform(min_seconds, max_seconds))

# Function to read input from a text file
def read_input_from_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
        data = []
        for line in lines:
            county, zip_code, first_name, last_name, dob = line.strip().split(',')
            # Ensure the county name is in uppercase
            county = county.upper()
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
        human_delay()

        # Wait for the County dropdown to be present
        county_dropdown = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'ctl00_ContentPlaceHolder1_CountyCombo'))
        )

        # Fill in the County dropdown
        Select(county_dropdown).select_by_visible_text(input_data['county'])
        human_delay()

        # Fill in the Zip Code
        zip_code_field = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_txtVRSzip')
        zip_code_field.clear()
        for char in input_data['zip_code']:
            zip_code_field.send_keys(char)
            human_delay(min_seconds=0.1, max_seconds=0.3)
        human_delay()

        # Fill in the First Name
        first_name_field = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_txtVRSOpt2Item2')
        first_name_field.clear()
        for char in input_data['first_name']:
            first_name_field.send_keys(char)
            human_delay(min_seconds=0.1, max_seconds=0.3)
        human_delay()

        # Fill in the Last Name
        last_name_field = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_txtVRSOpt2Item3')
        last_name_field.clear()
        for char in input_data['last_name']:
            last_name_field.send_keys(char)
            human_delay(min_seconds=0.1, max_seconds=0.3)
        human_delay()

        # Fill in the Date of Birth
        dob_field = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_txtVRSOpt2Item4')
        dob_field.clear()
        for char in input_data['dob']:
            dob_field.send_keys(char)
            human_delay(min_seconds=0.1, max_seconds=0.3)
        human_delay()

        # Submit the form
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'ctl00_ContentPlaceHolder1_btnContinue'))
        )
        submit_button.click()
        human_delay()

        # Wait for the results to load
        time.sleep(5)

        # Check if the "not found" message is displayed
        try:
            not_found_message = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_lblNotFound')
            if not_found_message.is_displayed():
                print(f"No results found for {input_data['first_name']} {input_data['last_name']}.")
                return None
        except:
            pass

        # Capture the results
        results = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_UpdatePanel1').text
        return results

    except Exception as e:
        print(f"An error occurred during the search: {e}")
        return None

# Main script
def main():
    try:
        # Ask the user if they want to read input from a file
        use_file = input("Do you want to read input from a file? (yes/no): ").strip().lower()
        if use_file == 'yes':
            file_path = input("Enter the path to the input file: ").strip()
            input_data_list = read_input_from_file(file_path)
        else:
            # Manual input for a single inquiry
            county = input("County: ").upper()  # Ensure county is uppercase
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
        driver = webdriver.Chrome(service=service)

        # Maximize the browser window
        driver.maximize_window()

        # Open the target website
        driver.get('https://www.pavoterservices.pa.gov/pages/voterregistrationstatus.aspx')
        human_delay()

        # Process each inquiry
        for i, input_data in enumerate(input_data_list):
            if i >= 16:
                print("Reached the limit of 16 searches. Restart the script to continue.")
                break

            print(f"Processing inquiry {i + 1} for {input_data['first_name']} {input_data['last_name']}...")
            results = perform_search(input_data, driver)

            if results:
                # Save the results to a text file
                with open(f"results_{input_data['first_name']}_{input_data['last_name']}.txt", 'w', encoding='utf-8') as f:
                    f.write(results)
                print(f"Results saved to 'results_{input_data['first_name']}_{input_data['last_name']}.txt'.")

            # Refresh the page for the next inquiry
            driver.refresh()
            human_delay()

            # Take a break after every 10 inquiries
            if (i + 1) % 10 == 0:
                print("Taking a break to avoid CAPTCHA...")
                time.sleep(random.randint(60, 120))  # Wait 1-2 minutes

    except Exception as e:
        # Print the error message
        print(f"An error occurred: {e}")

        # Save the page source to a file
        with open('page_source.txt', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)

        # Take a screenshot
        driver.save_screenshot('error_screenshot.png')

    finally:
        # Close the browser
        driver.quit()

if __name__ == "__main__":
    main()
