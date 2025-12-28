import streamlit as st
import pandas as pd
from transformers import pipeline
from wordcloud import WordCloud
import matplotlib.pyplot as plt

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
page = st.sidebar.radio("Go to:", ["Products", "Reviews", "Testimonials", "Products with Reviews"])

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
    st.header("⭐ Review Analysis (2023)")
    df_reviews = load_data("data/reviews.csv")

    if not df_reviews.empty:
        # 1. Word Cloud Logic (Above the slider)
        # We need to filter the data first to get the words for the selected month
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        
        # We create a temporary month selection to power the Word Cloud and Slider
        selected_month_name = st.select_slider("Select a month in 2023:", options=months, value="May")
        month_num = months.index(selected_month_name) + 1

        # Filtering Logic
        df_reviews['Date'] = pd.to_datetime(df_reviews['Date'])
        filtered_df = df_reviews[
            (df_reviews['Date'].dt.year == 2023) & 
            (df_reviews['Date'].dt.month == month_num)
        ].copy()
        filtered_df['Date'] = filtered_df['Date'].dt.date

        # --- BONUS: WORD CLOUD GENERATION ---
        if not filtered_df.empty:
            st.subheader(f"Word Cloud for {selected_month_name}")
            
            # Combine all reviews into one big string
            text = " ".join(review for review in filtered_df.Review_Text.astype(str))
            
            # Create the wordcloud
            wordcloud = WordCloud(
                width=800, 
                height=400, 
                background_color='black',
                colormap='viridis',
                max_words=100
            ).generate(text)

            # Display using matplotlib
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis("off")
            st.pyplot(fig)
        
        st.divider()

        # 2. Main Analysis Section
        st.write(f"Showing **{len(filtered_df)}** reviews for **{selected_month_name} 2023**")

        if not filtered_df.empty:
            # --- 3. CLEAN MODEL SELECTOR & BUTTON ---
            col_drop, col_btn = st.columns([2, 1])
            with col_drop:
                selected_model_key = st.selectbox(
                    "Model Selection", 
                    list(MODEL_OPTIONS.keys()), 
                    label_visibility="collapsed" 
                )
            with col_btn:
                analyze_clicked = st.button("🔍 Analyze & Visualize", use_container_width=True)

            if analyze_clicked:
                # ... [Sentiment Analysis and Table Logic from previous turn] ...
                with st.spinner(f'Analyzing with {selected_model_key}...'):
                    current_pipeline = load_sentiment_model(selected_model_key)
                    texts = filtered_df['Review_Text'].tolist()
                    results = current_pipeline(texts)
                    
                    labels, scores = [], []
                    for res in results:
                        label = res['label'].upper()
                        if any(x in label for x in ['POS', '4', '5', 'LABEL_1']):
                            labels.append("POSITIVE")
                        else:
                            labels.append("NEGATIVE")
                        scores.append(res['score'])

                    filtered_df['Sentiment'] = labels
                    filtered_df['Confidence'] = scores
                    
                    def color_sentiment(val):
                        if val == "POSITIVE": return 'background-color: rgba(0, 255, 0, 0.2);'
                        if val == "NEGATIVE": return 'background-color: rgba(255, 0, 0, 0.2);'
                        return ''

                    display_df = filtered_df.drop(columns=['Confidence'])
                    styled_df = display_df.style.applymap(color_sentiment, subset=['Sentiment'])
                    st.dataframe(styled_df, use_container_width=True, hide_index=True)

                    # --- 4. BAR CHART (BELOW TABLE) ---
                    st.divider()
                    st.subheader(f"Sentiment Counts ({selected_model_key})")
                    avg_conf = filtered_df['Confidence'].mean()
                    st.metric("Avg. Model Confidence", f"{avg_conf:.2%}")
                    st.bar_chart(filtered_df['Sentiment'].value_counts())
            else:
                st.dataframe(filtered_df, use_container_width=True, hide_index=True)
        else:
            st.info(f"No reviews found for {selected_month_name} 2023.")

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