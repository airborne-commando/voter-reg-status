Here’s a `README.md` file you can use for your GitHub repository. It provides clear instructions on how to set up and run the voter registration automation script.

---

# Voter Registration Automation Script

This Python script automates the process of checking voter registration status on the [Pennsylvania Voter Services](https://www.pavoterservices.pa.gov/pages/voterregistrationstatus.aspx) website. It uses Selenium to interact with the web page, fill out the form, and retrieve the results.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Usage](#usage)
4. [Input File Format](#input-file-format)
5. [Limitations](#limitations)
6. [Troubleshooting](#troubleshooting)
7. [License](#license)

---

## Prerequisites

Before running the script, ensure you have the following installed:

1. **Python 3.x**: Download and install Python from [python.org](https://www.python.org/downloads/).
2. **ChromeDriver**: Download the version of ChromeDriver that matches your Chrome browser version from [here](https://sites.google.com/chromium.org/driver/).
3. **Google Chrome**: Ensure you have the latest version of Google Chrome installed.

---

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/airborne-commando/voter-reg-status.git
   cd voter-reg-status
   ```

2. **Set Up a Virtual Environment** (optional but recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. **Install Dependencies**:
   Install the required Python packages using `pip`:
   ```bash
   pip install selenium
   ```

4. **Download ChromeDriver**:
   - Download the appropriate version of ChromeDriver for your system.
   - Place the `chromedriver` executable in the project directory or specify its path in the script.

---

## Usage

### Running the Script

1. **Prepare Input Data**:
   - You can either provide input manually or use a CSV file. See the [Input File Format](#input-file-format) section for details.

2. **Run the Script**:
   ```bash
   python3 voter_registration_script.py
   ```

3. **Follow the Prompts**:
   - The script will ask if you want to read input from a file or enter it manually.
   - If using a file, provide the path to the file.
   - If entering manually, provide the required details (county, zip code, first name, last name, and date of birth).

4. **View Results**:
   - If results are found, they will be saved in a text file named `results_<first_name>_<last_name>.txt`.
   - If no results are found, the script will log the failure.

---

## Input File Format

If using a file for input, it should be formatted as a CSV file with the following columns:
```
county,zip_code,first_name,last_name,dob
```

Example (`input.csv`):
```
ADAMS,12345,John,Doe,01/01/1990
ALLEGHENY,54321,Jane,Smith,02/02/1980
```

- **County**: Must be in uppercase (e.g., `ADAMS`).
- **Zip Code**: A valid 5-digit zip code.
- **First Name**: The voter's first name.
- **Last Name**: The voter's last name.
- **Date of Birth**: In the format `mm/dd/yyyy`.

---

## Limitations

1. **CAPTCHA**:
   - The script is designed to avoid triggering CAPTCHA by introducing random delays and limiting the number of searches per session (16 searches).
   - If CAPTCHA appears, you will need to solve it manually.

2. **Session Limit**:
   - After 16 searches, the script will stop and prompt you to restart it to avoid being flagged as a bot.

3. **Browser Compatibility**:
   - The script is tested with Google Chrome and ChromeDriver. Other browsers are not supported.

---

## Troubleshooting

### Common Issues

1. **ChromeDriver Version Mismatch**:
   - Ensure the version of ChromeDriver matches your Chrome browser version.
   - Download the correct version from [here](https://sites.google.com/chromium.org/driver/).

2. **CAPTCHA Appears**:
   - If CAPTCHA appears, pause the script and solve it manually in the browser.
   - Reduce the number of searches per session or increase delays between actions.

3. **Element Not Found**:
   - Ensure the browser window is maximized.
   - Check the page source (`page_source.txt`) and screenshot (`error_screenshot.png`) for debugging.

4. **File Not Found**:
   - Ensure the input file path is correct and the file is formatted properly.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.

---

## Acknowledgments

- [Selenium](https://www.selenium.dev/) for browser automation.
- [ChromeDriver](https://sites.google.com/chromium.org/driver/) for enabling Chrome automation.

---

Let me know if you need further assistance!
