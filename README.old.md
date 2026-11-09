
# Automating working hour submission with Selenium

## Overview
This Python script uses Selenium WebDriver to automate working hour report for internal use. it uses cred saved in cred manager

## Features
- Logs into a specified website using stored credentials from the Windows Credential Manager.
- Navigates to a login page, inputs username and password, and clicks the login button.
- Waits for the login process to complete and captures a screenshot for debugging.
- Prompts the user to input lunch time and a specific day of the month to update data fields on the webpage.
- Clears existing text in a specified text field and inputs new data.
- Captures another screenshot after updating the data field.
- Closes the browser window after a delay to ensure changes take effect.

## Requirements
- Python 3.x
- `selenium` Python package
- `chromedriver` (automatically installed by `chromedriver-autoinstaller` package)
- `pywin32` Python package for Windows Credential Manager access

## Installation
1. Clone the repository or download the script.
2. Install dependencies using pip:

```
pip install -r requirements.txt
```

## Usage
1. Ensure that the script is configured with the correct target URL.
2. Store your website login credentials in the Windows Credential Manager under a specific target name.
3. Run the script:

```
python workinghour.py
```

4. Follow the prompts to input lunch time and a specific day of the month for updating data.
5. Check the generated screenshots (`after_input.png`) for debugging purposes.

## Notes
- Adjust the script according to your specific website's HTML structure (e.g., XPath selectors).
- Ensure proper error handling and validation of user inputs.
