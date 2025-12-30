from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import os
import sys

def get_driver(headless=False): # ADD PARAMETER
    options = Options()
    if headless:
        options.add_argument("--headless")
        # Recommended flags for headless stability
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)

def scrape_all(headless_mode=False): # ADD PARAMETER
    driver = get_driver(headless=headless_mode)
    base_url = "https://web-scraping.dev"
    
    products_data = []
    reviews_data = []
    testimonials_data = []

    try:
        # --- 1. PRODUCTS (pid) ---
        print(f"--- Scraping Products (Headless={headless_mode}) ---")
        p_id_counter = 1
        for page_num in range(1, 7):
            driver.get(f"{base_url}/products?page={page_num}")
            time.sleep(2)
            cards = driver.find_elements(By.CLASS_NAME, "product")
            for card in cards:
                try:
                    products_data.append({
                        "pid": p_id_counter,
                        "Title": card.find_element(By.TAG_NAME, "h3").text,
                        "Description": card.find_element(By.CLASS_NAME, "short-description").text,
                        "Price": f"${card.find_element(By.CLASS_NAME, 'price').text}"
                    })
                    p_id_counter += 1
                except: continue

        # --- 2. REVIEWS (rid) ---
        print("--- Scraping Reviews ---")
        r_id_counter = 1
        driver.get(f"{base_url}/reviews")
        for i in range(5):
            try:
                load_more = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "page-load-more")))
                driver.execute_script("arguments[0].scrollIntoView();", load_more)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", load_more)
                time.sleep(2)
            except: break

        review_elements = driver.find_elements(By.CSS_SELECTOR, '[data-testid="review"]')
        for rev in review_elements:
            try:
                star_container = rev.find_element(By.CSS_SELECTOR, '[data-testid="review-stars"]')
                reviews_data.append({
                    "rid": r_id_counter,
                    "Date": rev.find_element(By.CSS_SELECTOR, '[data-testid="review-date"]').text,
                    "Review_Text": rev.find_element(By.CSS_SELECTOR, '[data-testid="review-text"]').text,
                    "Stars": len(star_container.find_elements(By.TAG_NAME, "svg"))
                })
                r_id_counter += 1
            except: continue

        # --- 3. TESTIMONIALS (tid) ---
        print("--- Scraping Testimonials ---")
        t_id_counter = 1
        driver.get(f"{base_url}/testimonials")
        for _ in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
        testimonial_elements = driver.find_elements(By.CLASS_NAME, "testimonial")
        for test in testimonial_elements:
            try:
                rating_span = test.find_element(By.CLASS_NAME, "rating")
                testimonials_data.append({
                    "tid": t_id_counter,
                    "Testimonial_Text": test.find_element(By.CLASS_NAME, "text").text,
                    "Stars": len(rating_span.find_elements(By.TAG_NAME, "svg"))
                })
                t_id_counter += 1
            except: continue

        # --- SAVE SEPARATE FILES ---
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_folder = os.path.join(script_dir, "..", "data")

        if not os.path.exists(data_folder):
            os.makedirs(data_folder)

        products_path = os.path.join(data_folder, "products.csv")
        testimonials_path = os.path.join(data_folder, "testimonials.csv")
        reviews_path = os.path.join(data_folder, "reviews.csv")
        
        pd.DataFrame(products_data).to_csv(products_path, index=False)
        pd.DataFrame(testimonials_data).to_csv(testimonials_path, index=False)
        
        df_rev = pd.DataFrame(reviews_data)
        df_rev['Date'] = pd.to_datetime(df_rev['Date'], errors='coerce').fillna(pd.Timestamp('2023-01-01'))
        df_rev.to_csv(reviews_path, index=False)

        print(f"Success! Saved to: {data_folder}")

    finally:
        driver.quit()

if __name__ == "__main__":
    # Check if "--headless" was passed as a command line argument
    is_headless = "--headless" in sys.argv
    scrape_all(headless_mode=is_headless)