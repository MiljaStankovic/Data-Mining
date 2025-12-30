import streamlit as st
import pandas as pd
from transformers import pipeline
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import subprocess
import sys
import os
import time

MODEL_OPTIONS = {
    "DistilBERT (Fast)": "distilbert-base-uncased-finetuned-sst-2-english",
    "RoBERTa (Accurate)": "cardiffnlp/twitter-roberta-base-sentiment-latest",
    "BERT (Standard)": "nlptown/bert-base-multilingual-uncased-sentiment"
}
# Set page configuration
st.set_page_config(page_title="Data Mining Dashboard", layout="wide")

# --- NLP SETUP ---
# We cache the model so it doesn't reload every time you move the slider
@st.cache_resource
def load_sentiment_model(model_name):
    # This will load the model selected from the dropdown
    return pipeline("sentiment-analysis", model=MODEL_OPTIONS[model_name])

# --- DATA LOADING HELPERS ---
@st.cache_data
def load_data(filename):
    try:
        df = pd.read_csv(filename)
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date']).dt.date
        return df
    except Exception as e:
        return pd.DataFrame()

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", ["Products", "Reviews", "Testimonials"])
# 1. Spacer to push tools to the bottom
st.sidebar.markdown("<br>" * 3, unsafe_allow_html=True) 
# st.sidebar.divider()
st.sidebar.subheader("⚙️ Run Web-Scraper")

# Create two columns for the buttons
col_vis, col_head = st.sidebar.columns(2)

status_placeholder = st.sidebar.empty()

def execute_scrapers(headless):
    scripts = [
        "web_scraping_scripts/scraper_all.py",
        "web_scraping_scripts/scraper_product_reviews.py"
    ]
    try:
        for script in scripts:
            if os.path.exists(script):
                mode_text = "Headless" if headless else "Visible"
                status_placeholder.warning(f"⏳ {mode_text}: {os.path.basename(script)}")
                
                # Build command
                cmd = [sys.executable, script]
                if headless:
                    cmd.append("--headless")
                
                subprocess.run(cmd, check=True)
                st.toast(f"✅ {os.path.basename(script)} done!")
            else:
                st.sidebar.error(f"Missing: {script}")
        
        status_placeholder.success("🎉 Data Updated!")
        st.balloons()
        time.sleep(1)
        st.rerun()
    except Exception as e:
        status_placeholder.error(f"❌ Error: {e}")

# Button logic
if col_vis.button("Visible", use_container_width=True, help="Watch the browser scrape"):
    execute_scrapers(headless=False)

if col_head.button("Headless", use_container_width=True, help="Scrape in the background"):
    execute_scrapers(headless=True)
st.title(f"Scraped Data: {page}")

# --- PAGE LOGIC ---

if page == "Products":
    st.header("🛒 Product Catalog")
    df_products = load_data("data/products.csv")
    st.dataframe(df_products, use_container_width=True, hide_index=True)

elif page == "Testimonials":
    st.header("💬 Customer Testimonials")
    df_test = load_data("data/testimonials.csv")
    st.dataframe(df_test, use_container_width=True, hide_index=True)

elif page == "Reviews":
    st.header("⭐ Review & Product Intelligence (2023)")
    df_reviews = load_data("data/reviews.csv")
    df_products = load_data("data/products.csv")

    if not df_reviews.empty:
        # 1. Slider & Sync Logic
        months_options = ["All", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        col_slider, col_all = st.columns([4, 1])
        
        with col_all:
            st.markdown('<div style="padding-top: 25px;"></div>', unsafe_allow_html=True)
            if st.button("🌐 Show All", use_container_width=True):
                st.session_state.month_slider = "All"
                st.rerun()

        with col_slider:
            selected_period = st.select_slider("Select a month in 2023:", options=months_options, key="month_slider")

        # 2. Filtering Logic
        if selected_period == "All":
            filtered_df = df_reviews.copy()
            show_wordcloud = False
            view_title = "All Reviews (2023)"
        else:
            month_num = months_options.index(selected_period)
            df_reviews['Date'] = pd.to_datetime(df_reviews['Date'])
            filtered_df = df_reviews[
                (df_reviews['Date'].dt.year == 2023) & 
                (df_reviews['Date'].dt.month == month_num)
            ].copy()
            filtered_df['Date'] = filtered_df['Date'].dt.date
            show_wordcloud = True
            view_title = f"Reviews for {selected_period} 2023"

        # --- WORD CLOUD (Only when Month selected) ---
        if show_wordcloud and not filtered_df.empty:
            st.subheader(f"Word Cloud for {selected_period}")
            text = " ".join(review for review in filtered_df.Review_Text.astype(str))
            wordcloud = WordCloud(width=800, height=300, background_color='black').generate(text)
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.imshow(wordcloud, interpolation='bilinear'); ax.axis("off")
            st.pyplot(fig)
            st.divider()

        # 3. Main Display & Analyze Trigger
        st.write(f"Showing **{len(filtered_df)}** reviews ({view_title})")

        if not filtered_df.empty:
            col_drop, col_btn = st.columns([2, 1])
            with col_drop:
                selected_model_key = st.selectbox("Model Selector", list(MODEL_OPTIONS.keys()), label_visibility="collapsed")
            with col_btn:
                analyze_clicked = st.button("🔍 Run Full Intelligence Report", use_container_width=True)

            if analyze_clicked:
                with st.spinner('Processing NLP Analysis...'):
                    # 1. Run Sentiment Analysis
                    current_pipeline = load_sentiment_model(selected_model_key)
                    results = current_pipeline(filtered_df['Review_Text'].tolist())
                    
                    labels, scores = [], []
                    for res in results:
                        label = res['label'].upper()
                        labels.append("POSITIVE" if any(x in label for x in ['POS', '4', '5', 'LABEL_1']) else "NEGATIVE")
                        scores.append(res['score'])

                    filtered_df['Sentiment'] = labels
                    filtered_df['Confidence'] = scores # Kept in background for logic, but hidden in display

                    # --- 2. DETAILED REVIEW LOG ---
                    st.divider()
                    st.subheader("📋 Detailed Review Log")
                    def color_sentiment(val):
                        if val == "POSITIVE": return 'background-color: rgba(0, 255, 0, 0.2);'
                        if val == "NEGATIVE": return 'background-color: rgba(255, 0, 0, 0.2);'
                        return ''
                    
                    # Dropping Confidence here as requested
                    display_df = filtered_df.drop(columns=['Confidence'])
                    st.dataframe(display_df.style.applymap(color_sentiment, subset=['Sentiment']), 
                                 use_container_width=True, hide_index=True)

                    # --- 3. METRICS & BAR CHART ---
                    st.divider()
                    st.subheader(f"Sentiment Distribution ({selected_model_key})")
                    avg_conf = filtered_df['Confidence'].mean()
                    
                    # Only showing Confidence Metric now
                    st.metric("Avg. Model Confidence", f"{avg_conf:.2%}")
                    st.bar_chart(filtered_df['Sentiment'].value_counts())

                    # --- 4. PRODUCT SENTIMENT SUMMARY ---
                    st.divider()
                    st.header("📦 Product Sentiment Summary")
                    df_map = load_data("data/product_reviews.csv")
                    merged_p = pd.merge(df_map, df_products, on="pid", how="left")
                    final_intel_df = pd.merge(filtered_df, merged_p, on="rid", how="left")
                    final_intel_df['Title'] = final_intel_df['Title'].fillna("Unlinked Reviews")
                    
                    product_stats = final_intel_df.groupby(['Title', 'Sentiment']).size().unstack(fill_value=0)
                    if "POSITIVE" not in product_stats: product_stats["POSITIVE"] = 0
                    if "NEGATIVE" not in product_stats: product_stats["NEGATIVE"] = 0
                    
                    st.dataframe(product_stats, use_container_width=True)

                    # --- 5. TOP/BOTTOM LISTS (Logic: Negative Ratio >= 40%) ---
                    st.divider()
                    col_top, col_bot = st.columns(2)
                    
                    # Calculate Ratios
                    product_stats['Total'] = product_stats['POSITIVE'] + product_stats['NEGATIVE']
                    product_stats['Neg_Ratio'] = product_stats['NEGATIVE'] / product_stats['Total']
                    
                    # Filter out the "Unlinked Reviews" placeholder from the rankings
                    rank_df = product_stats.get(product_stats.index != "Unlinked Reviews", product_stats)

                    with col_top:
                        st.success("🏆 Top Rated Products")
                        # High performance: Products where negative reviews are less than 40% 
                        # and they have at least 1 positive review.
                        top_rated = rank_df[rank_df['Neg_Ratio'] < 0.4].sort_values(by='POSITIVE', ascending=False)
                        
                        if not top_rated.empty:
                            for p in top_rated.index[:5]: 
                                ratio = top_rated.loc[p, 'Neg_Ratio']
                                st.write(f"✅ **{p}** ({ratio:.0%} Neg)")
                        else:
                            st.write("No products meet the top-rated criteria.")

                    with col_bot:
                        st.error("🚩 Needs Improvement (≥40% Negative)")
                        # Flagged: Products where negative reviews make up 40% or more of total reviews
                        needs_help = rank_df[rank_df['Neg_Ratio'] >= 0.4].sort_values(by='Neg_Ratio', ascending=False)
                        
                        if not needs_help.empty:
                            for p in needs_help.index[:5]:
                                ratio = needs_help.loc[p, 'Neg_Ratio']
                                st.write(f"❌ **{p}** ({ratio:.0%} Neg)")
                        else:
                            st.write("All products are currently below the 40% negative threshold!")

                    # --- 6. STARS VS SENTIMENT ANOMALIES (NOW AT THE BOTTOM) ---
                    st.divider()
                    st.header("🔍 Anomaly Detection: Stars vs. Sentiment")
                    st.info("These cases represent a mismatch between the customer's rating and the AI's interpretation of their text.")
                    
                    filtered_df['Stars'] = pd.to_numeric(filtered_df['Stars'], errors='coerce')

                    # Case A: Low Stars (1-3) but Positive Sentiment
                    anomalies_pos = filtered_df[(filtered_df['Stars'] <= 3) & (filtered_df['Sentiment'] == "POSITIVE")]
                    
                    # Case B: High Stars (4-5) but Negative Sentiment
                    anomalies_neg = filtered_df[(filtered_df['Stars'] >= 4) & (filtered_df['Sentiment'] == "NEGATIVE")]

                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.warning("⚠️ Low Stars but Positive Text")
                        if not anomalies_pos.empty:
                            st.write(f"Found **{len(anomalies_pos)}** possible errors")
                            # Showing text and stars without confidence
                            st.dataframe(anomalies_pos[['Stars', 'Review_Text']], use_container_width=True, hide_index=True)
                        else:
                            st.write("No anomalies found.")

                    with col_b:
                        st.error("📉 High Stars but Negative Text")
                        if not anomalies_neg.empty:
                            st.write(f"Found **{len(anomalies_neg)}** possible errors")
                            st.dataframe(anomalies_neg[['Stars', 'Review_Text']], use_container_width=True, hide_index=True)
                        else:
                            st.write("No anomalies found.")
            else:
                st.dataframe(filtered_df, use_container_width=True, hide_index=True)
        
        else:
            # This is where your line was incorporated
            st.info(f"No reviews found for {selected_period}.")
            
elif page == "Products with Reviews":
    st.header("🔗 Linked Products & Reviews")
    
    df_p = load_data("data/products.csv")
    df_r = load_data("data/reviews.csv")
    df_map = load_data("data/product_reviews.csv")

    if not df_map.empty and not df_p.empty and not df_r.empty:
        merged_p = pd.merge(df_map, df_p, on="pid", how="inner")
        final_df = pd.merge(merged_p, df_r, on="rid", how="inner", suffixes=('', '_global'))
        
        text_col = "Review_Text" if "Review_Text" in final_df.columns else "Review_Text_global"
        
        # --- NLP IMPLEMENTATION (Optional Toggle) ---
        if st.checkbox("Apply Sentiment Analysis to these reviews"):
            with st.spinner('Processing...'):
                results = sentiment_pipeline(final_df[text_col].tolist())
                final_df['Sentiment'] = [res['label'] for res in results]

        # Define display columns
        possible_cols = ["Title", "Price", "Date", text_col, "Stars", "Sentiment"]
        display_cols = [col for col in possible_cols if col in final_df.columns]
        
        st.write("Displaying product details alongside their matched reviews.")
        st.dataframe(final_df[display_cols], use_container_width=True, hide_index=True)
    else:
        st.warning("Data files missing or empty. Please run your scrapers first.")