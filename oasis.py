import getpass
import win32cred
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime

# --- Helper for WinCred ---
def get_credentials(target_name):
    try:
        creds = win32cred.CredRead(target_name, win32cred.CRED_TYPE_GENERIC)
        return creds['UserName'], creds['CredentialBlob'].decode('utf-16')
    except Exception as e:
        print(f"Failed to retrieve credentials: {e}")
        return None, None

def take_screenshot(driver, file_name):
    driver.save_screenshot(file_name)

# --- Chrome options: Headless+No Images+Speedy ---
chrome_options = Options()
chrome_options.add_argument("--headless=new")  # 'new' is best headless as of Chrome 112+
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument('--window-size=1920,1080')
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument('--blink-settings=imagesEnabled=false')  # disables image loading (faster)

# --- Main Automation ---
try:
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)
    url = "https://oasis.springernature.com/oasis3/login.aspx"

    driver.get(url)

    # --- Credentials ---
    target_name = 'oasis'  # <-- Use your Windows Credential Manager key
    username, password = get_credentials(target_name)
    if not username or not password:
        raise ValueError("Credentials not found or incomplete.")

    # --- User Data ---
    submission_day = input("Enter the day of the month you want to submit the data for (e.g., 20 for June 20th. leave empty for today): ")
    start_time = input("Enter start time (leave empty for default 9:00): ") or "9:00"
    end_time = input("Enter end time (leave empty for default 17:30): ") or "17:30"
    lunch_time = "1:00"
    notes = input("Enter Note if needed:")

    # --- Login ---
    username_input = wait.until(EC.presence_of_element_located((By.ID, "txtLoginID")))
    password_input = driver.find_element(By.ID, "txtPassword")
    login_button = driver.find_element(By.ID, "btnLogin")
    username_input.send_keys(username)
    password_input.send_keys(password)
    login_button.click()

    # --- Wait for Working Hours tab ---
    working_hour_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/div[3]/div[5]/div/div/ul/li[6]/a")))
    working_hour_tab.click()

    # --- Day logic ---
    if not submission_day:
        current_day = datetime.now().day
    else:
        try:
            current_day = int(submission_day)
            assert 1 <= current_day <= 31
        except Exception:
            raise ValueError("Invalid day number.")

    # --- Next button ---
    next_element = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/div[3]/div[2]/div[1]/table/tbody/tr[3]/td[2]/input[2]")))
    next_element.click()

    # --- Edit the row for this day ---
    edit_xpath = f"/html/body/form/div[4]/div[1]/div/table/tbody/tr[{current_day}]/td[17]/div/a"
    edit_element = wait.until(EC.element_to_be_clickable((By.XPATH, edit_xpath)))
    edit_element.click()

    # --- Fill fields ---
    def fill(xpath, value):
        el = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        el.clear()
        el.send_keys(value)

    fill(f"/html/body/form/div[4]/div[1]/div/table/tbody/tr[{current_day}]/td[5]/div/input", start_time)
    fill(f"/html/body/form/div[4]/div[1]/div/table/tbody/tr[{current_day}]/td[6]/div/input", end_time)
    fill(f"/html/body/form/div[4]/div[1]/div/table/tbody/tr[{current_day}]/td[8]/div/input", lunch_time)
    fill(f"/html/body/form/div[4]/div[1]/div/table/tbody/tr[{current_day}]/td[16]/div/input", notes)

    # --- Submit/Update ---
    update_button = wait.until(EC.element_to_be_clickable((By.XPATH,
        f"/html/body/form/div[4]/div[1]/div/table/tbody/tr[{current_day}]/td[17]/div/a[1]")))
    update_button.click()

    # --- Screenshot for proof/debugging ---
    take_screenshot(driver, f'after_input-{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')

    print("✔ Done! Working hours submitted.")

finally:
    try:
        driver.quit()
    except:
        pass