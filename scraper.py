from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import json
import os

# a function to parse timetable from lukkari
def parse_timetable_from_html(html_content):
    """
    Parse timetable HTML and return structured dict with dates and events
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # get headers
    headers = soup.select('th.fc-day-header')
    header_dates = [th['data-date'] for th in headers]
    header_names = [th.get_text(strip=True) for th in headers]

    # initial an empty dict to store the result
    result = {
        date: {"label": name, "events": []}
        for date, name in zip(header_dates, header_names)
    }

    # parse contents to result
    content_cols = soup.select('div.fc-content-skeleton td')

    print(len(header_dates))
    print(len(header_names))
    print(len(content_cols))
    
    for idx, td in enumerate(content_cols[1:]):  # skip first td due to time column
        date_key = header_dates[idx]
        events = td.select("a.fc-time-grid-event")
        for ev in events:
            # extract time
            time_span = ev.select_one(".fc-time span")
            time_text = time_span.get_text(strip=True) if time_span else ""

            # extract title
            title_div = ev.select_one("div[style*='font-weight:500']")
            title_text = title_div.get_text(strip=True) if title_div else ""

            # extract location
            loc_div = ev.select_one("div[style*='font-weight:300']")
            location_text = loc_div.get_text("\n", strip=True) if loc_div else ""

            # append to events
            result[date_key]["events"].append({
                "time": time_text,
                "title": title_text,
                "location": location_text
            })
    return result

    
# a function write result to json
def write_to_json(result,filename):
    with open(f"{filename}.json", "w") as f:
        json.dump(result, f)
    print(f"Saved: {filename}.json")


# main function
def main():
    # prepare username and password
    username = os.environ.get("LOGIN_USER")
    password = os.environ.get("LOGIN_PASS")

    # selenium options
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu") 

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # open lukkari
    driver.get("https://lukkari.turkuamk.fi/#/schedule")
    time.sleep(2)  # wait to ensure page loaded

    # click to login
    driver.find_element(By.XPATH, "/html/body/app-root/mat-sidenav-container/mat-sidenav-content/mat-toolbar/mat-toolbar-row/button[2]").click()
    time.sleep(2)  # wait to ensure page loaded

    # login
    driver.find_element(By.XPATH, "/html/body/div/div/div/div[1]/form/div[1]/input").send_keys(username)
    driver.find_element(By.XPATH, "/html/body/div/div/div/div[1]/form/div[2]/input").send_keys(password)
    driver.find_element(By.XPATH, "/html/body/div/div/div/div[1]/form/div[4]/button").click()
    time.sleep(5)  # wait to ensure calendar loaded

    # xpath for timetable
    xpath = "/html/body/app-root/mat-sidenav-container/mat-sidenav-content/mat-drawer-container/mat-drawer-content/div[2]/ng-component/div/div[2]/ng-fullcalendar"
    
    # get html content of current week
    table_element_this = driver.find_element(By.XPATH, xpath)
    html_content_this = table_element_this.get_attribute("outerHTML")
    time.sleep(1)

    # parse and save timetable of current week to json
    result_this = parse_timetable_from_html(html_content_this)
    write_to_json(result_this,"result_this") 

    # move on next week
    driver.find_element(By.XPATH, "/html/body/app-root/mat-sidenav-container/mat-sidenav-content/mat-drawer-container/mat-drawer-content/div[2]/ng-component/div/div[2]/ng-fullcalendar/div[1]/div[1]/div/button[2]").click()
    time.sleep(3)
    
    # get html content of next week
    table_element_next = driver.find_element(By.XPATH, xpath)
    html_content_next = table_element_next.get_attribute("outerHTML")
    time.sleep(1)

    # parse and save timetable of next week to json
    result_next = parse_timetable_from_html(html_content_next)
    write_to_json(result_next,"result_next")
    
    driver.quit()

if __name__ == "__main__":
    main()