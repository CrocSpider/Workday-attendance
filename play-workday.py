import argparse
import os
import re
from datetime import date, datetime
from pathlib import Path

import keyring
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


WORKDAY_URL = "https://wd3.myworkday.com/springernature/d/task/2998$10895.htmld"
STATE_FILE = Path.home() / ".workday-playwright-state.json"
WORKDAY_TIME_TYPE = "Working from Home (Japan)"


def parse_time(value):
    value = value.strip().upper().replace(".", "")
    for time_format in ("%H:%M", "%I:%M %p", "%I:%M%p", "%I %p"):
        try:
            parsed = datetime.strptime(value, time_format)
            hour = parsed.hour
            suffix = "AM" if hour < 12 else "PM"
            display_hour = hour % 12 or 12
            return hour + parsed.minute / 60, f"{display_hour}:{parsed.minute:02d} {suffix}"
        except ValueError:
            continue
    raise ValueError(f"Invalid time '{value}'. Use HH:MM, e.g. 9:00 or 17:30.")


def get_day_cells(page):
    return page.locator('[data-automation-id^="dayCell-"]').evaluate_all(
        """cells => cells.map((cell, index) => ({
            index,
            id: cell.getAttribute('data-automation-id'),
            text: (cell.textContent || '').trim()
        }))"""
    )


def parse_day_label(text):
    match = re.search(r"(\d{1,2})\s*/\s*(\d{1,2})", text)
    return (int(match.group(1)), int(match.group(2))) if match else None


def select_date(page, target_date):
    target = (target_date.month, target_date.day)

    for _ in range(54):
        cells = get_day_cells(page)
        for cell in cells:
            if parse_day_label(cell["text"]) == target:
                page.locator('[data-automation-id^="dayCell-"]').nth(cell["index"]).click()
                return cell["index"]

        visible_dates = [parse_day_label(cell["text"]) for cell in cells]
        visible_dates = [value for value in visible_dates if value]
        if not visible_dates:
            raise RuntimeError("Workday day cells were found, but their dates could not be read.")

        first_visible = visible_dates[0]
        direction = "Previous Week" if target < first_visible else "Next Week"
        page.get_by_role("button", name=direction, exact=True).click()
        page.wait_for_timeout(500)

    raise RuntimeError(f"Could not find {target_date:%Y-%m-%d} in Workday week view.")


def open_time_dialog(page, day_index, start_hour):
    panel = page.locator(".gwt-appointment-panel").first
    panel.scroll_into_view_if_needed()
    box = panel.bounding_box()
    if not box:
        raise RuntimeError("Workday time grid is not visible.")

    day_width = box["width"] / 7
    x = box["x"] + day_width * (day_index + 0.5)
    y = box["y"] + box["height"] * (start_hour / 24) + 2
    page.mouse.click(x, y)

    dialog = page.get_by_role("dialog", name="Enter Time")
    dialog.wait_for(timeout=10000)
    return dialog


def fill_time_dialog(page, dialog, start_time, end_time, notes):
    dialog.get_by_role("textbox", name="Time Type", exact=True).click()
    page.get_by_role("menuitemradio", name=WORKDAY_TIME_TYPE, exact=True).click()
    dialog.get_by_role("textbox", name="In", exact=True).fill(start_time)
    dialog.get_by_role("textbox", name="Out", exact=True).fill(end_time)
    if notes:
        dialog.get_by_role("textbox", name="Comment", exact=True).fill(notes)
    dialog.get_by_role("button", name="OK", exact=True).click()


def get_keyring_credentials():
    username = keyring.get_password("oasis", "username")
    password = keyring.get_password("oasis", "password")
    if not username or not password:
        raise RuntimeError(
            "Missing keychain credentials for service 'oasis' "
            "(accounts 'username' and 'password')."
        )
    return username, password


def authenticate_with_okta(page):
    username, password = get_keyring_credentials()

    username_box = page.get_by_role("textbox", name=re.compile("Username", re.I))
    if username_box.count():
        username_box.fill(username)
        page.get_by_role("button", name="Next", exact=True).click()

    password_box = page.locator('input[type="password"]')
    if password_box.count():
        password_box.fill(password)
        page.get_by_role(
            "button", name=re.compile("Next|Sign in|Verify", re.I)
        ).first.click()

    fastpass = page.get_by_text("Use Okta FastPass", exact=True)
    if fastpass.count():
        fastpass.locator(
            "xpath=ancestor::div[contains(@class, 'authenticator-row')][1]"
        ).get_by_text("Select", exact=True).click()
        print("Approve the Okta FastPass request on your device.")


def ensure_authenticated(page):
    weekly_body = page.locator('[data-automation-id="weeklyBody"]')
    try:
        weekly_body.wait_for(timeout=5000)
        return
    except PlaywrightTimeoutError:
        pass

    authenticate_with_okta(page)
    weekly_body.wait_for(timeout=180000)


def main():
    parser = argparse.ArgumentParser(description="Enter a time block in Workday.")
    parser.add_argument(
        "--draft",
        action="store_true",
        help="Prepare the entry without clicking Workday's Save button.",
    )
    args = parser.parse_args()

    submission_day = input(
        "Enter the day of the current month (leave empty for today): "
    ).strip()
    day = int(submission_day) if submission_day else datetime.now().day
    target_date = date(datetime.now().year, datetime.now().month, day)

    start_value = input("Enter start time (default 9:00): ").strip() or "9:00"
    end_value = input("Enter end time (default 17:30): ").strip() or "17:30"
    notes = input("Enter a comment if needed: ").strip()
    start_hour, start_time = parse_time(start_value)
    end_hour, end_time = parse_time(end_value)
    if end_hour <= start_hour:
        raise ValueError("End time must be later than start time.")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context(
            storage_state=str(STATE_FILE) if STATE_FILE.exists() else None,
            viewport={"width": 1440, "height": 1000},
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(WORKDAY_URL, timeout=60000, wait_until="domcontentloaded")

        ensure_authenticated(page)

        context.storage_state(path=str(STATE_FILE))
        os.chmod(STATE_FILE, 0o600)

        day_index = select_date(page, target_date)
        dialog = open_time_dialog(page, day_index, start_hour)
        fill_time_dialog(page, dialog, start_time, end_time, notes)

        if args.draft:
            print("Draft prepared but not saved.")
            browser.close()
            return

        page.get_by_role("button", name="Save", exact=True).click()
        print("Workday time entry saved.")
        browser.close()


if __name__ == "__main__":
    main()
