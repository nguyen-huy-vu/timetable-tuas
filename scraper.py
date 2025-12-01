from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re
import json
import os

# a function to parse timetable from lukkari
def parse_timetable_from_html(html_content):
    """
    Parse timetable HTML and return structured dict with dates and events
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # extract header dates (Mon, Tue, Wed...)
    header_cells = soup.select("th.fc-day-header")

    date_map = []
    for th in header_cells:
        date_str = th.get("data-date")
        if date_str:
            date_map.append(date_str)

    # initialize a dict to store the result
    results = {d: [] for d in date_map}

    # extract ALL event <a> tags in order
    events = soup.select("a.fc-time-grid-event")

    # to be deleted
    print(results)

    for ev in events:

        # extract date column index from parent <td> position
        td = ev.find_parent("td")
        if not td:
            continue

        tr = td.find_parent("tr")
        if not tr:
            continue

        cells = tr.find_all("td", recursive=False)
        try:
            col_index = cells.index(td)
        except ValueError:
            continue

        # col_index 0 = axis, so real dates start at index 1
        date_index = col_index - 1
        if date_index < 0 or date_index >= len(date_map):
            continue

        date_key = date_map[date_index]

        # extract event info

        # time
        time_el = ev.select_one(".fc-time span")
        timeframe = time_el.get_text(strip=True) if time_el else ""

        # Start/End parse
        m = re.match(r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})", timeframe)
        start = m.group(1) if m else ""
        end = m.group(2) if m else ""

        # title + course code
        title_el = ev.select_one("div[style*='font-weight:500']")
        raw_title = title_el.get_text(strip=True) if title_el else ""

        # split title and code
        parts = raw_title.rsplit(" ", 1)
        if len(parts) == 2 and re.match(r".+-\d+", parts[1]):
            title = parts[0]
            course_code = parts[1]
        else:
            title = raw_title
            course_code = ""

        # location
        loc_el = ev.select_one("div[style*='font-weight:300']")
        location = loc_el.get_text("\n", strip=True) if loc_el else ""

        # add record to results
        results[date_key].append({
            "timeframe": timeframe,
            "start": start,
            "end": end,
            "title": title,
            "course_code": course_code,
            "location": location
        })
    # to be deleted
    print(results)

    return results

    
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

    # click to login
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/app-root/mat-sidenav-container/mat-sidenav-content/mat-toolbar/mat-toolbar-row/button[2]"))).click()
    
    # login
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "/html/body/div/div/div/div[1]/form/div[1]/input"))).send_keys(username)
    driver.find_element(By.XPATH, "/html/body/div/div/div/div[1]/form/div[2]/input").send_keys(password)
    driver.find_element(By.XPATH, "/html/body/div/div/div/div[1]/form/div[4]/button").click()

    # xpath for timetable
    xpath = "/html/body/app-root/mat-sidenav-container/mat-sidenav-content/mat-drawer-container/mat-drawer-content/div[2]/ng-component/div/div[2]/ng-fullcalendar/div[2]"
    
    # wait until at least one event is rendered
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "a.fc-time-grid-event"))
    )

    # get html content of current week
    table_element_this = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
    html_content_this = table_element_this.get_attribute("outerHTML")

    # move on next week
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/app-root/mat-sidenav-container/mat-sidenav-content/mat-drawer-container/mat-drawer-content/div[2]/ng-component/div/div[2]/ng-fullcalendar/div[1]/div[1]/div/button[2]"))).click()

    # wait until at least one event is rendered
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "a.fc-time-grid-event"))
    )

    # get html content of next week
    table_element_next = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
    html_content_next = table_element_next.get_attribute("outerHTML")

    # parse and save timetable of current week to json
    result_this = parse_timetable_from_html(html_content_this)
    write_to_json(result_this,"result_this") 

    # parse and save timetable of next week to json
    result_next = parse_timetable_from_html(html_content_next)
    write_to_json(result_next,"result_next")
    
    driver.quit()

if __name__ == "__main__":
    main()