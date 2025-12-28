from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
import time

def get_driver():
    options = Options()
    # options.add_argument("--headless") 
    return webdriver.Chrome(options=options)

def scrape_mapping():
    driver = get_driver()
    base_url = "https://web-scraping.dev/products"
    mapping_data = []
    
    # Track pid to stay in sync with your products.csv
    pid_counter = 1

    try:
        # Loop through the product listing pages
        for page_num in range(1, 7):
            print(f"Accessing Product Page {page_num}...")
            driver.get(f"{base_url}?page={page_num}")
            time.sleep(2)

            # Get links for all products on this page
            # Based on your previous HTML, the link is inside h3 > a
            links = [a.get_attribute('href') for a in driver.find_elements(By.CSS_SELECTOR, "h3 a")]

            for link in links:
                print(f"  Mapping pid {pid_counter} from {link}")
                driver.get(link)
                time.sleep(2)

                # Look for the reviews container you provided
                try:
                    # Find all div elements that have 'review' in their class name
                    # We then grab the <p> tag inside each one
                    reviews = driver.find_elements(By.CSS_SELECTOR, "div.review")
                    
                    if not reviews:
                        mapping_data.append({
                            "pid": pid_counter,
                            "Review_Text": "No reviews found for this product."
                        })
                    else:
                        for rev in reviews:
                            # Extract text from the <p> tag inside the review div
                            text = rev.find_element(By.TAG_NAME, "p").text
                            mapping_data.append({
                                "pid": pid_counter,
                                "Review_Text": text
                            })
                except Exception as e:
                    print(f"    Error on pid {pid_counter}: {e}")
                    mapping_data.append({
                        "pid": pid_counter,
                        "Review_Text": "Error extracting reviews."
                    })
                
                pid_counter += 1
        
        # Save to CSV
        df = pd.DataFrame(mapping_data)
        df.to_csv("product_reviews.csv", index=False)
        print(f"SUCCESS: Saved mapping to product_reviews.csv")

    finally:
        driver.quit()
def link_reviews_to_ids():
    print("--- Linking Product Reviews to Global Review IDs (rid) ---")
    
    # 1. Load the data
    try:
        product_reviews_df = pd.read_csv("product_reviews.csv")
        global_reviews_df = pd.read_csv("reviews.csv")
    except FileNotFoundError:
        print("Error: Make sure both product_reviews.csv and reviews.csv exist.")
        return

    # 2. Create a mapping dictionary for fast lookup
    # We map the Review_Text to the rid
    # Note: We strip whitespace to ensure matches are accurate
    text_to_id_map = dict(zip(
        global_reviews_df['Review_Text'].str.strip(), 
        global_reviews_df['rid']
    ))

    # 3. Apply the mapping
    # If the text matches, it gets the rid; otherwise, it gets None
    product_reviews_df['rid'] = product_reviews_df['Review_Text'].str.strip().map(text_to_id_map)

    # 4. Save the updated file
    product_reviews_df.to_csv("../data/product_reviews.csv", index=False)
    
    # Check how many matches we found
    matches = product_reviews_df['rid'].notna().sum()
    print(f"SUCCESS: Linked {matches} reviews to their global IDs (rid).")
    
if __name__ == "__main__":
    scrape_mapping()
    link_reviews_to_ids()