import json
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("log-level=3")
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    return driver

def scrape_thumbnails(driver, url, num_thumbnails):
    thumbnail_data = set()
    
    driver.get(url)
    
    last_scroll_height = driver.execute_script("return document.body.scrollHeight;")
    while len(thumbnail_data) < num_thumbnails:
        initial_len = len(thumbnail_data)
        
        driver.execute_script("window.scrollBy(0, 200);")
        time.sleep(1)

        new_scroll_height = driver.execute_script("return document.body.scrollHeight;")
        if new_scroll_height == last_scroll_height:
            time.sleep(2)
            driver.execute_script("window.scrollBy(0, 200);")
        
        last_scroll_height = new_scroll_height
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        game_grid_items = soup.find_all("div", class_="game-grid-item")
        
        for item in game_grid_items:
            anchor = item.find("a", class_="game-thumbnail")
            if anchor:
                game_url = "https://gamejolt.com" + anchor["href"]
                game_title = anchor.find("div", class_="-title")
                if game_title:
                    game_title = game_title.get_text(strip=True)
                thumbnail = item.find("img", class_=lambda x: x in ["img-responsive -img", "-media"])
                if thumbnail:
                    thumbnail_url = thumbnail["src"]
                    thumbnail_data.add(f"{thumbnail_url}B2B--B2B{game_title}B2B--B2B{game_url}")
                
            if len(thumbnail_data) >= num_thumbnails:
                break
        
        print(f"Current number of thumbnails: {len(thumbnail_data)}")
    
    return list(thumbnail_data)[:num_thumbnails]

if __name__ == "__main__":
    url = "https://gamejolt.com/games/best/tag-fnaf"
    num_thumbnails = 35
    
    driver = init_driver()
    thumbnail_urls = scrape_thumbnails(driver, url, num_thumbnails)
    driver.quit()
    
    with open("thumbnail_data.json", "w") as f:
        json.dump(thumbnail_urls, f)
