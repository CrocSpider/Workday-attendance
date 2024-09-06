from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from datetime import datetime
import getpass
import win32cred
import time

# Replace this with your target URL
target_url = "https://oasis.springernature.com/oasis3/login.aspx"

# Function to retrieve credentials from Windows Credential Manager
def get_credentials(target_name):
    try:
        creds = win32cred.CredRead(target_name, win32cred.CRED_TYPE_GENERIC)
        return creds['UserName'], creds['CredentialBlob'].decode('utf-16')
    except Exception as e:
        print(f"Failed to retrieve credentials: {e}")
        return None, None
    
# Set up the WebDriver options
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Run in headless mode
options.add_argument('--disable-gpu')  # Disable GPU
options.add_argument('--window-size=1920x1080')  # Set window size
options.add_argument('--log-level=1')  # Set log level to 1
options.add_argument('--no-sandbox')  # Bypass OS security model
options.add_argument('--disable-dev-shm-usage')  # Overcome limited resource problems
# Set up the WebDriver (assuming you have Chrome and ChromeDriver installed)
driver = webdriver.Chrome(options=options)

# Function to take a screenshot for debugging
def take_screenshot(driver, file_name):
    driver.save_screenshot(file_name)

try:
    # Navigate to the login page
    driver.get(target_url)
    # Retrieve credentials from Windows Credential Manager
    target_name = 'oasis'  # Replace with the actual target name used in Credential Manager

    username, password = get_credentials(target_name)
    if not username or not password:
        raise ValueError("Credentials not found or incomplete.")
    
    # Prompt the user for username and password inputs
    #username = input("Enter your username: ")
    #password = getpass.getpass("Enter your password: ")
    submission_day = input("Enter the day of the month you want to submit the data for (e.g., 20 for June 20th. leave empty for today): ")
    start_time = input("Enter start time (leave empty for default 9:00): ")
    start_time = start_time if start_time else "9:00"
    end_time = input("Enter end time (leave empty for default 17:30): ")
    end_time = end_time if end_time else "17:30"
    # Prompt the user for the lunch time and the day of the month they want to submit the data for
    lunch_time = "1:00"
    notes = input("Enter Note if needed:")
    # Find the username and password input fields, and login button
    username_input = driver.find_element("id", "txtLoginID")
    password_input = driver.find_element("id", "txtPassword")
    login_button = driver.find_element("id", "btnLogin")

    # Input the user credentials and click the login button
    username_input.send_keys(username)
    password_input.send_keys(password)
    login_button.click()

    # Wait for the login process to complete (you might need to adjust the time based on the actual loading time)
    driver.implicitly_wait(5)

    working_hour_tab = driver.find_element("xpath", f"/html/body/form/div[3]/div[5]/div/div/ul/li[6]/a")
    working_hour_tab.click()
    today_date = datetime
    # If the user did not input anything, use today's date
    if not submission_day:
        current_day = datetime.now().day
    else:
        current_day = submission_day

    #next button
    next_element = driver.find_element("xpath", f"/html/body/form/div[3]/div[2]/div[1]/table/tbody/tr[3]/td[2]/input[2]")
    next_element.click()

    # Find the "edit" element for the current day and click on it
    edit_element = driver.find_element("xpath", f"/html/body/form/div[4]/div[1]/div/table/tbody/tr[{current_day}]/td[17]/div/a")
    edit_element.click()

    # Find the text field for the current day, clear it, and input new text
    start_field = driver.find_element("xpath", f"/html/body/form/div[4]/div[1]/div/table/tbody/tr[{current_day}]/td[5]/div/input")
    start_field.clear()  # Clear the existing text
    start_field.send_keys(start_time)

    end_field = driver.find_element("xpath", f"/html/body/form/div[4]/div[1]/div/table/tbody/tr[{current_day}]/td[6]/div/input")
    end_field.clear()
    end_field.send_keys(end_time)

    lunch_field = driver.find_element("xpath", f"/html/body/form/div[4]/div[1]/div/table/tbody/tr[{current_day}]/td[8]/div/input")
    lunch_field.clear()
    lunch_field.send_keys(lunch_time)

    note_field = driver.find_element("xpath", f"/html/body/form/div[4]/div[1]/div/table/tbody/tr[{current_day}]/td[16]/div/input")
    note_field.clear()
    note_field.send_keys(notes)

    update_button = driver.find_element("xpath", f"/html/body/form/div[4]/div[1]/div/table/tbody/tr[{current_day}]/td[17]/div/a[1]")
    update_button.click()

    # Add a delay before quitting the browser to ensure changes take effect
    time.sleep(3)

    # Take a screenshot after inputting the lunch time
    take_screenshot(driver, f'after_input-{today_date}.png')


finally:
    # Close the browser window
    driver.quit()