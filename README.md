# 📊 Data Mining & Sentiment Intelligence Dashboard

An end-to-end data science application that scrapes e-commerce data and applies **Natural Language Processing (NLP)** to extract actionable product insights. The dashboard identifies customer sentiment trends, highlights top-performing products, and detects anomalies between star ratings and written text.



## 🚀 Key Features

* **Automated Web Scraping**: Integrated controls to trigger Selenium scrapers directly from the UI. Supports both **Visible** (debug) and **Headless** (background) modes.
* **Multi-Model Sentiment Analysis**: Toggle between different transformer models:
    * **DistilBERT**: High speed for quick summaries.
    * **RoBERTa**: Fine-tuned for social media/review nuance.
    * **BERT**: Robust standard for multilingual sentiment.
* **Time-Series Filtering**: Interactive slider to explore review data month-by-month for the year 2023.
* **Product Intelligence**: 
    * **Top Rated**: Automatic identification of products with high positive ratios (less than 40% negative).
    * **Needs Improvement**: Flags products with $\ge 40\%$ negative sentiment.
* **Anomaly Detection**: Automatically catches "Review Mismatches" (e.g., a 1-star rating paired with a positive written review).
* **Visual Analytics**: Dynamic Word Clouds and distribution bar charts that update based on filters.

## 🛠️ Technical Stack

* **Frontend**: Streamlit
* **NLP Engine**: HuggingFace Transformers (Pipeline API)
* **Automation**: Selenium WebDriver (Chrome)
* **Data Processing**: Pandas, NumPy
* **Visualization**: Matplotlib, WordCloud

## 📂 Project Structure

```text
├── app.py                      # Main Streamlit dashboard application
├── data/                       # CSV storage for scraped datasets
│   ├── products.csv
│   ├── reviews.csv
│   ├── testimonials.csv
│   └── product_reviews.csv     # Mapping between products and reviews
├── web_scraping_scripts/       # Selenium automation scripts
│   ├── scraper_all.py          # Primary data harvester
│   └── scraper_product_reviews.py # Detailed mapping script
└── requirements.txt            # Python dependencies
└── README.md                   # Setup Information
```

## ⚙️ Installation & Setup

### 1. Clone the Repository
Open your terminal and run:
```bash
git clone <your-repository-link>
cd <your-project-folder-name>
```

### 2. Create a Virtual Environment (Optional but Recommended)
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
streamlit run app.py
```

## 🔍 How to Use
* Step 1: **Data Acquisition**
    * Navigate to the Sidebar.
    * Click **Visible** if you want to see the Chrome browser perform the scraping.
    * Click **Headless** to run the scrapers in the background without a browser window.
    * Wait for the **🎉 Data Updated!** message.

* Step 2: **Product & Review Exploration**
    * Use the Navigation radio buttons to view the raw **Product Catalog** or **Customer Testimonials**.
    * Switch to the **Reviews** page to see the 2023 intelligence report.

* Step 3: **Sentiment Intelligence**
    * Adjust the **Month Slider** to filter reviews by a specific time period.
    * Select a **Sentiment Model** (DistilBERT, RoBERTa, or BERT) from the dropdown.
    * Click **🔍 Run Full Intelligence Report**.

* Step 4: **Analyzing Results**
    * **Word Cloud:** See the most frequent terms used by customers that month.
    * **Performance Lists:** Check which products are flagged for "Needs Improvement" (≥40% negative).
    * **Anomaly Detection:** Scroll to the bottom to find "Low Stars but Positive Text" or "High Stars but Negative Text" to identify sarcasm or data errors.