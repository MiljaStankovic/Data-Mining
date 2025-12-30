from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time
import os
import sys # ADDED

# Get correct paths globally
script_dir = os.path.dirname(os.path.abspath(__file__))
data_folder = os.path.join(script_dir, "..", "data")

def get_driver(headless=False): # UPDATED
    options = Options()
    if headless:
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)

def scrape_mapping(headless_mode=False): # UPDATED
    driver = get_driver(headless=headless_mode)
    base_url = "https://web-scraping.dev/products"
    mapping_data = []
    pid_counter = 1

    try:
        for page_num in range(1, 7):
            print(f"Accessing Product Page {page_num} (Headless={headless_mode})...")
            driver.get(f"{base_url}?page={page_num}")
            time.sleep(2)

            links = [a.get_attribute('href') for a in driver.find_elements(By.CSS_SELECTOR, "h3 a")]

            for link in links:
                print(f"   Mapping pid {pid_counter} from {link}")
                driver.get(link)
                time.sleep(2)

                try:
                    reviews = driver.find_elements(By.CSS_SELECTOR, "div.review")
                    if not reviews:
                        mapping_data.append({"pid": pid_counter, "Review_Text": "No reviews found for this product."})
                    else:
                        for rev in reviews:
                            text = rev.find_element(By.TAG_NAME, "p").text
                            mapping_data.append({"pid": pid_counter, "Review_Text": text})
                except Exception as e:
                    print(f"    Error on pid {pid_counter}: {e}")
                    mapping_data.append({"pid": pid_counter, "Review_Text": "Error extracting reviews."})
                
                pid_counter += 1
        
        # Save temp file to data folder
        df = pd.DataFrame(mapping_data)
        temp_path = os.path.join(data_folder, "product_reviews.csv")
        df.to_csv(temp_path, index=False)
        print(f"SUCCESS: Saved mapping to {temp_path}")

    finally:
        driver.quit()

def link_reviews_to_ids():
    print("--- Linking Product Reviews to Global Review IDs (rid) ---")
    
    prod_rev_path = os.path.join(data_folder, "product_reviews.csv")
    global_rev_path = os.path.join(data_folder, "reviews.csv")

    try:
        product_reviews_df = pd.read_csv(prod_rev_path)
        global_reviews_df = pd.read_csv(global_rev_path)
    except FileNotFoundError:
        print(f"Error: Make sure {prod_rev_path} and {global_rev_path} exist.")
        return

    text_to_id_map = dict(zip(
        global_reviews_df['Review_Text'].str.strip(), 
        global_reviews_df['rid']
    ))

    product_reviews_df['rid'] = product_reviews_df['Review_Text'].str.strip().map(text_to_id_map)
    
    product_reviews_df.to_csv(prod_rev_path, index=False)
    matches = product_reviews_df['rid'].notna().sum()
    print(f"SUCCESS: Linked {matches} reviews. Saved to: {prod_rev_path}")

if __name__ == "__main__":
    is_headless = "--headless" in sys.argv # CHECK FOR FLAG
    scrape_mapping(headless_mode=is_headless)
    link_reviews_to_ids()