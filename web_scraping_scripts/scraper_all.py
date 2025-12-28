from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

def get_driver():
    options = Options()
    # options.add_argument("--headless") 
    return webdriver.Chrome(options=options)

def scrape_all():
    driver = get_driver()
    base_url = "https://web-scraping.dev"
    
    products_data = []
    reviews_data = []
    testimonials_data = []

    try:
        # --- 1. PRODUCTS (pid) ---
        print("--- Scraping Products ---")
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
        pd.DataFrame(products_data).to_csv("../data/products.csv", index=False)
        
        df_rev = pd.DataFrame(reviews_data)
        df_rev['Date'] = pd.to_datetime(df_rev['Date'], errors='coerce').fillna(pd.Timestamp('2023-01-01'))
        df_rev.to_csv("../data/reviews.csv", index=False)
        
        pd.DataFrame(testimonials_data).to_csv("../data/testimonials.csv", index=False)

        print(f"DONE! Saved products.csv, reviews.csv, and testimonials.csv with unique IDs.")

    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_all()