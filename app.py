import streamlit as st
import pandas as pd

# Set page configuration
st.set_page_config(page_title="Data Mining Dashboard", layout="wide")

# --- DATA LOADING HELPERS ---
@st.cache_data
def load_data(filename):
    try:
        df = pd.read_csv(filename)
        if 'Date' in df.columns:
            # Convert to datetime and then to just date (YYYY-MM-DD)
            df['Date'] = pd.to_datetime(df['Date']).dt.date
        return df
    except Exception as e:
        st.error(f"Error loading {filename}: {e}")
        return pd.DataFrame()

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", [
    "Products", 
    "Reviews", 
    "Testimonials", 
    "Products with Reviews"
])

st.title(f"Scraped Data: {page}")

# --- PAGE LOGIC ---

if page == "Products":
    st.header("🛒 Product Catalog")
    df_products = load_data("products.csv")
    # Using 'column_order' to hide pid if you want it hidden there too
    st.dataframe(df_products, use_container_width=True, hide_index=True)

elif page == "Testimonials":
    st.header("💬 Customer Testimonials")
    df_test = load_data("testimonials.csv")
    st.dataframe(df_test, use_container_width=True, hide_index=True)

elif page == "Reviews":
    st.header("⭐ Review Analysis (2023)")
    df_reviews = load_data("reviews.csv")

    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    selected_month_name = st.select_slider("Select a month in 2023:", options=months, value="May")
    month_num = months.index(selected_month_name) + 1

    # Filter by converted month number and Year 2023
    # Note: We convert back to datetime for filtering logic
    df_reviews['Date'] = pd.to_datetime(df_reviews['Date'])
    filtered_df = df_reviews[
        (df_reviews['Date'].dt.year == 2023) & 
        (df_reviews['Date'].dt.month == month_num)
    ].copy()
    
    # Clean the date display again after filtering
    filtered_df['Date'] = filtered_df['Date'].dt.date

    st.write(f"Showing **{len(filtered_df)}** reviews for **{selected_month_name} 2023**")
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)

elif page == "Products with Reviews":
    st.header("🔗 Linked Products & Reviews")
    
    df_p = load_data("products.csv")
    df_r = load_data("reviews.csv")
    df_map = load_data("product_reviews.csv")

    if not df_map.empty and not df_p.empty and not df_r.empty:
        # 1. Merge mapping with Products
        merged_p = pd.merge(df_map, df_p, on="pid", how="inner")
        
        # 2. Merge with global Reviews to get the clean text and stars
        # We use suffixes in case both files have a 'Review_Text' column
        final_df = pd.merge(merged_p, df_r, on="rid", how="inner", suffixes=('', '_global'))
        
        # 3. Identify the correct column for the review text
        # If there's a conflict, df_r's version is usually more reliable
        text_col = "Review_Text" if "Review_Text" in final_df.columns else "Review_Text_global"
        
        # 4. Define display columns based on what actually exists in the merged dataframe
        display_cols = []
        possible_cols = ["Title", "Price", "Date",text_col, "Stars"]
        
        for col in possible_cols:
            if col in final_df.columns:
                display_cols.append(col)
        
        st.write("Displaying product details alongside their matched reviews.")
        
        # Display the table
        st.dataframe(
            final_df[display_cols], 
            use_container_width=True, 
            hide_index=True
        )
    else:
        st.warning("Data files missing or empty. Please run your scrapers first.")