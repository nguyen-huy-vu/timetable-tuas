from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import json
import os

def main():

    username = os.environ.get("LOGIN_USER")
    password = os.environ.get("LOGIN_PASS")

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu") 

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # open lukkari
    driver.get("https://lukkari.turkuamk.fi/#/schedule")
    time.sleep(2)  # wait to ensure page loads

    # click on Login
    driver.find_element(By.XPATH, "/html/body/app-root/mat-sidenav-container/mat-sidenav-content/mat-toolbar/mat-toolbar-row/button[2]").click()
    time.sleep(2)  # wait to ensure page loads

    # login
    driver.find_element(By.XPATH, "/html/body/div/div/div/div[1]/form/div[1]/input").send_keys(username)
    driver.find_element(By.XPATH, "/html/body/div/div/div/div[1]/form/div[2]/input").send_keys(password)
    driver.find_element(By.XPATH, "/html/body/div/div/div/div[1]/form/div[4]/button").click()
    time.sleep(5)  # wait to ensure page loads

    # get html content of calendar
    xpath = "/html/body/app-root/mat-sidenav-container/mat-sidenav-content/mat-drawer-container/mat-drawer-content/div[2]/ng-component/div/div[2]/ng-fullcalendar"
    table_element = driver.find_element(By.XPATH, xpath)
    html_content = table_element.get_attribute("outerHTML")

    time.sleep(2)
    driver.quit()

    # parse html with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    # get headers
    headers = soup.select('th.fc-day-header')
    header_dates = [th['data-date'] for th in headers]
    header_names = [th.get_text(strip=True) for th in headers]

    # get data of each columns
    content_cols = soup.select('div.fc-content-skeleton td')

    print("header_dates:", header_dates)
    print("len(header_dates):", len(header_dates))
    print("len(cols):", len(content_cols))
    print("HTML snippet:", content_cols[:500])

    # initial an empty dict to store the result
    result = {
        date: {"label": name, "events": []}
        for date, name in zip(header_dates, header_names)
    }

    print(result)

    # parse content into result
    for idx, td in enumerate(content_cols):
        # Map cell to date
        date_key = header_dates[idx]

        # Find all events in this cell
        events = td.select("a.fc-time-grid-event")

        for ev in events:
            # Extract time
            time_span = ev.select_one(".fc-time span")
            time_text = time_span.get_text(strip=True) if time_span else ""

            # Extract title  (weight 500)
            title_div = ev.select_one("div[style*='font-weight:500']")
            title_text = title_div.get_text(strip=True) if title_div else ""

            # Extract location (weight 300)
            loc_div = ev.select_one("div[style*='font-weight:300']")
            location_text = loc_div.get_text("\n", strip=True) if loc_div else ""

            # Add to schedule
            result[date_key]["events"].append({
                "time": time_text,
                "title": title_text,
                "location": location_text
            })

    with open("result.json", "w") as f:
        json.dump(result, f)
    print("Saved:", result)

if __name__ == "__main__":
    main()