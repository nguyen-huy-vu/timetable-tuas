import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def main():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    driver.get("https://www.gigantti.fi/")
    title = driver.title
    driver.quit()

    result = {"title": title}

    with open("result.json", "w") as f:
        json.dump(result, f)
    print("Saved:", result)

if __name__ == "__main__":
    main()