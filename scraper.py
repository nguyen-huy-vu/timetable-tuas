from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
# import time
import json
import os

# a function to parse timetable from lukkari
def parse_timetable_from_html(html_content):
    """
    Parse timetable HTML and return structured dict with dates and events
    """
    soup = BeautifulSoup(html_content, "html.parser")

    results = []

    # get headers
    day_columns = soup.select(".fc-col, .fc-timegrid-col")

    for col in day_columns:
        # get day name + date (Mon 3.2)
        header = col.select_one(".fc-col-header, .fc-daygrid-day-top, .fc-daygrid-day-number")
        if header:
            day_text = header.get_text(" ", strip=True)
        else:
            day_text = None

        # all event entries inside the column
        events = col.select(".fc-event, .event, .fc-timegrid-event")
        for e in events:
            text = e.get_text("\n", strip=True).split("\n")

            start_time, end_time = None, None
            title, course_code, room, location = None, None, None, None

            if len(text) > 0 and "-" in text[0]:
                time_part = text[0]
                parts = [t.strip() for t in time_part.split("-")]
                if len(parts) == 2:
                    start_time, end_time = parts

            if len(text) > 1:
                line = text[1]
                parts = line.rsplit(" ", 1)
                if len(parts) == 2 and parts[1].replace("-", "").isalnum():
                    title = parts[0].strip()
                    course_code = parts[1].strip()
                else:
                    title = line.strip()

            if len(text) > 2:
                loc_parts = [p.strip() for p in text[2].split(",")]
                if len(loc_parts) >= 1:
                    room = loc_parts[0]
                if len(loc_parts) >= 2:
                    location = ", ".join(loc_parts[1:])

            results.append({
                "day": day_text,
                "start_time": start_time,
                "end_time": end_time,
                "title": title,
                "course_code": course_code,
                "room": room,
                "location": location,
            })

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
    # time.sleep(2)  # wait to ensure page loaded

    # click to login
    # driver.find_element(By.XPATH, "/html/body/app-root/mat-sidenav-container/mat-sidenav-content/mat-toolbar/mat-toolbar-row/button[2]").click()
    # time.sleep(2)  # wait to ensure page loaded
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/app-root/mat-sidenav-container/mat-sidenav-content/mat-toolbar/mat-toolbar-row/button[2]"))).click()
    
    # login
    # driver.find_element(By.XPATH, "/html/body/div/div/div/div[1]/form/div[1]/input").send_keys(username)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "/html/body/div/div/div/div[1]/form/div[1]/input"))).send_keys(username)
    driver.find_element(By.XPATH, "/html/body/div/div/div/div[1]/form/div[2]/input").send_keys(password)
    driver.find_element(By.XPATH, "/html/body/div/div/div/div[1]/form/div[4]/button").click()
    # time.sleep(5)  # wait to ensure calendar loaded

    # xpath for timetable
    xpath = "/html/body/app-root/mat-sidenav-container/mat-sidenav-content/mat-drawer-container/mat-drawer-content/div[2]/ng-component/div/div[2]/ng-fullcalendar"
    
    # get html content of current week
    # table_element_this = driver.find_element(By.XPATH, xpath)
    table_element_this = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
    html_content_this = table_element_this.get_attribute("outerHTML")
    # time.sleep(1)

    # parse and save timetable of current week to json
    result_this = parse_timetable_from_html(html_content_this)
    write_to_json(result_this,"result_this") 

    # move on next week
    # driver.find_element(By.XPATH, "/html/body/app-root/mat-sidenav-container/mat-sidenav-content/mat-drawer-container/mat-drawer-content/div[2]/ng-component/div/div[2]/ng-fullcalendar/div[1]/div[1]/div/button[2]").click()
    # time.sleep(3)
    WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/app-root/mat-sidenav-container/mat-sidenav-content/mat-drawer-container/mat-drawer-content/div[2]/ng-component/div/div[2]/ng-fullcalendar/div[1]/div[1]/div/button[2]"))).click()

    # get html content of next week
    table_element_next = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
    html_content_next = table_element_next.get_attribute("outerHTML")
    # time.sleep(1)

    # parse and save timetable of next week to json
    result_next = parse_timetable_from_html(html_content_next)
    write_to_json(result_next,"result_next")
    
    driver.quit()

if __name__ == "__main__":
    main()