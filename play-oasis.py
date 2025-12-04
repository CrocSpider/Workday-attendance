from playwright.sync_api import sync_playwright
from datetime import datetime
import time
import platform
import keyring
import getpass

def get_credentials(target_name):
    """
    Cross-platform credential retrieval using keyring library.
    Falls back to manual input if credentials not found.
    """
    try:
        # Try to get username from keyring
        username = keyring.get_password(target_name, "username")
        password = keyring.get_password(target_name, "password")
        
        if username and password:
            return username, password
        else:
            print(f"No stored credentials found for '{target_name}'.")
            username = input("Enter username: ")
            password = getpass.getpass("Enter password: ")
            
            # Optionally save for future use
            save = input("Save credentials? (y/n): ").lower()
            if save == 'y':
                keyring.set_password(target_name, "username", username)
                keyring.set_password(target_name, "password", password)
                print("Credentials saved securely.")
            
            return username, password
    except Exception as e:
        print(f"Failed to retrieve credentials: {e}")
        return None, None

def main():
    url = "https://oasis.springernature.com/oasis3/login.aspx"
    target_name = 'oasis'

    username, password = get_credentials(target_name)
    if not username or not password:
        raise ValueError("Credentials not found or incomplete.")

    submission_day = input("Enter the day of the month you want to submit the data for (e.g., 20 for June 20th. leave empty for today): ")
    start_time = input("Enter start time (leave empty for default 9:00): ") or "9:00"
    end_time = input("Enter end time (leave empty for default 17:30): ") or "17:30"
    lunch_time = "1:00"
    notes = input("Enter Note if needed:")

    if not submission_day:
        current_day = datetime.now().day
    else:
        try:
            current_day = int(submission_day)
            assert 1 <= current_day <= 31
        except Exception:
            raise ValueError("Invalid day number.")

    submission_day = int(submission_day) if submission_day else datetime.now().day
    today = datetime.now()
    target_date = today.replace(day=submission_day)

    # Compose the date string found by codegen:
    row_label = target_date.strftime('/%m/%d %a')
    # e.g., "/06/22 Sat"

    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True,
                                    args=["--disable-blink-features=AutomationControlled"])
        # Block images for speed
        context = browser.new_context(ignore_https_errors=True)
        context.route("**/*", lambda route, request: 
            route.abort() if request.resource_type == "image" else route.continue_())

        page = context.new_page()
        page.goto(url, timeout=60000)

        # Login section
        page.fill("#txtLoginID", username)
        page.fill("#txtPassword", password)
        page.click("#btnLogin")

        # Wait for and click "Working Hours" tab
        #page.wait_for_selector("xpath=/html/body/form/div[3]/div[5]/div/div/ul/li[6]/a", timeout=20000)
        #page.click("xpath=/html/body/form/div[3]/div[5]/div/div/ul/li[6]/a")
        page.get_by_role("link", name="Working Hours Report").click()
        # Click "Next"
        #page.wait_for_selector("xpath=/html/body/form/div[3]/div[2]/div[1]/table/tbody/tr[3]/td[2]/input[2]", timeout=10000)
        #page.click("xpath=/html/body/form/div[3]/div[2]/div[1]/table/tbody/tr[3]/td[2]/input[2]")
        page.get_by_role("button", name="Next").click()
        # Row for current day
        row = f"/html/body/form/div[4]/div[1]/div/table/tbody/tr[{current_day}]"

        # Click edit
        #page.wait_for_selector(f"xpath={row}/td[17]/div/a", timeout=10000)
        #page.click(f"xpath={row}/td[17]/div/a")
        # Click the "Edit" link in that row (partial match!)
        page.get_by_role("row", name=row_label, exact=False).get_by_role("link", name="Edit").click()
        # Fill fields
        page.fill(f"xpath={row}/td[5]/div/input", start_time)
        page.fill(f"xpath={row}/td[6]/div/input", end_time)
        page.fill(f"xpath={row}/td[8]/div/input", lunch_time)
        page.fill(f"xpath={row}/td[16]/div/input", notes)

        # Submit
        page.get_by_role("link", name="Update").click()
        #time.sleep(2)
        page.screenshot(path=f'after_input-{datetime.now().strftime("%Y%m%d_%H%M%S")}.png', full_page=True)

        print("✔ Done! Working hours submitted.")
        time.sleep(2)
        browser.close()

if __name__ == '__main__':
    main()