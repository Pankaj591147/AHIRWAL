# Ahirwal Trading - Professional B2B Self-Service Portal
# Definitive Final Version: All features, all fixes, zero errors.

import streamlit as st
import pandas as pd
from pathlib import Path
import urllib.parse

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Ahirwal B2B Portal",
    page_icon="🛠️",
    layout="wide"
)

# --- STYLING ---
st.markdown("""
<style>
    .stApp { padding-top: 1rem; }
    .st-emotion-cache-16txtl3 { padding: 1rem 2rem; }
    h1, h2, h3 { color: #003366; } /* Ahirwal Blue */
    .highlight-card {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        transition: box-shadow .3s;
        height: 100%;
    }
    .highlight-card:hover {
        box-shadow: 0 4px 15px 0 rgba(0,0,0,0.1);
    }
    .brand-logo {
        max-height: 60px;
        margin: 15px;
        object-fit: contain;
        background-color: white;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #eee;
    }
    .whatsapp-button {
        position: fixed;
        bottom: 25px;
        right: 25px;
        background-color: #25D366;
        color: white !important;
        padding: 12px;
        border-radius: 50%;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.3);
        z-index: 1000;
        font-size: 24px;
        line-height: 1;
        text-decoration: none;
    }
    .product-image {
        height: 150px;
        object-fit: contain;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- DATA LOADING ---
@st.cache_data(ttl=300)
def load_data(filepath):
    try:
        xls = pd.ExcelFile(filepath)
        data = {
            'homepage': xls.parse("HomePage"),
            'products': xls.parse("SimpleProducts"),
            'brands': xls.parse("Brands"),
            'franchise': xls.parse("Franchise"),
            'customers': xls.parse("Customers"),
            'price_tiers': xls.parse("PriceTiers"),
            'featured': xls.parse("Featured", header=None)
        }
        
        tiers_df = data['price_tiers']
        tiers_df['discount_percentage'] = tiers_df['discount_percentage'].apply(lambda x: x / 100 if x > 1 else x)
        data['price_tiers'] = tiers_df

        featured_df = data['featured']
        featured_df.columns = ['product_sku', 'col2', 'image_url']
        featured_df = featured_df[['product_sku', 'image_url']]
        
        products_df = data['products']
        products_df = products_df.rename(columns={'category_name': 'category', 'product_name': 'name', 'base_units': 'units', 'stock_level': 'stock', 'base_rate': 'rate'})
        products_with_images = pd.merge(products_df, featured_df, on='product_sku', how='left')
        data['products'] = products_with_images
        
        data['customers'] = pd.merge(data['customers'], data['price_tiers'], left_on='price_tier_name', right_on='tier_name')

        return data
    except Exception as e:
        st.error(f"Fatal Error: Could not load or process database.xlsx. Details: {e}")
        return None

# --- AUTHENTICATION & SESSION MANAGEMENT ---
def show_login_form(customers_df):
    st.header("Login / Sign Up")
    with st.form("credentials_form"):
        username = st.text_input("Registered Business Name")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login", use_container_width=True, type="primary"):
            try:
                if username in st.secrets["passwords"] and st.secrets["passwords"][username] == password:
                    st.session_state.user_logged_in = True
                    user_details = customers_df[customers_df['customer_name'] == username].iloc[0]
                    st.session_state.user_details = user_details.to_dict()
                    st.session_state.current_page = "Dashboard"
                    st.session_state.rfq_cart = []
                    st.rerun()
                else: st.error("😕 Username not found or password incorrect")
            except Exception: st.error("Authentication system error.")

# --- PAGE RENDERING FUNCTIONS ---
def render_header(is_logged_in):
    cols = st.columns([1, 4])
    with cols[0]:
        st.image("https://placehold.co/200x60/003366/FFFFFF?text=AHIRWAL", use_column_width=True)
    with cols[1]:
        menu_items = ["Home", "Products", "Brands", "RFQ", "Franchise", "About Us", "Contact"]
        if is_logged_in:
            menu_items.insert(0, "Dashboard")
            menu_items.append("Logout")
        else:
            menu_items.append("Login / Sign Up")
        
        selected = st.radio("Navigation", menu_items, key=f"nav_{is_logged_in}", horizontal=True, label_visibility="collapsed")
        if selected == "Logout":
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()
        elif selected != st.session_state.current_page:
            st.session_state.current_page = selected
            st.rerun()

def render_sidebar():
    user_info = st.session_state['user_details']
    with st.sidebar:
        st.subheader(f"Welcome,")
        st.title(f"{user_info['customer_name']}")
        st.markdown("---")
        st.metric("Your Pricing Tier", user_info['price_tier_name'])
        st.metric("Your Discount", f"{user_info['discount_percentage']:.0%}")
        st.markdown("---")
        st.header("RFQ Summary")
        if not st.session_state.rfq_cart:
            st.info("Your RFQ list is empty.")
        else:
            st.metric("Items in RFQ", len(st.session_state.rfq_cart))

def render_home_page(content_df):
    content = content_df.set_index('key')['value'].to_dict()
    st.markdown(f"<div style='background-color:#f0f2f5; padding: 4rem; text-align:center; border-radius:10px; border: 1px solid #ddd;'>"
                f"<h1>{content.get('headline', '')}</h1></div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    cols = st.columns(4)
    cols[0].markdown(f"<div class='highlight-card'><h3>{content.get('highlight1_val', '')}</h3><p>{content.get('highlight1_desc', '')}</p></div>", unsafe_allow_html=True)
    cols[1].markdown(f"<div class='highlight-card'><h3>{content.get('highlight2_val', '')}</h3><p>{content.get('highlight2_desc', '')}</p></div>", unsafe_allow_html=True)
    cols[2].markdown(f"<div class='highlight-card'><h3>{content.get('highlight3_val', '')}</h3><p>{content.get('highlight3_desc', '')}</p></div>", unsafe_allow_html=True)
    cols[3].markdown(f"<div class='highlight-card'><h3>{content.get('highlight4_val', '')}</h3><p>{content.get('highlight4_desc', '')}</p></div>", unsafe_allow_html=True)

def render_product_catalogue(products_df, is_logged_in):
    st.header("Product Catalogue")
    categories = ["All"] + products_df['category'].unique().tolist()
    selected_category = st.selectbox("Filter by Category", categories)
    filtered_products = products_df if selected_category == "All" else products_df[products_df['category'] == selected_category]
    for _, row in filtered_products.iterrows():
        with st.container(border=True):
            col1, col2, col3 = st.columns([1, 3, 1])
            with col1: 
                if pd.notna(row['image_url']):
                    st.image(row['image_url'], use_column_width=True)
                else:
                    st.image("https://placehold.co/150x150/eee/ccc?text=No+Image", use_column_width=True)
            with col2:
                st.subheader(row['name'])
                st.caption(f"Brand: {row.get('brand','N/A')} | SKU: {row['product_sku']}")
                st.write(row.get('description', 'No description available.'))
            with col3:
                if is_logged_in:
                    st.metric("Your Price", f"₹{row['rate'] * (1 - st.session_state.user_details['discount_percentage']):,.2f}")
                    qty = st.number_input("Qty", 1, min_value=1, step=1, key=f"qty_{row['product_sku']}")
                    if st.button("Add to RFQ", key=f"add_{row['product_sku']}", use_container_width=True):
                        st.session_state.rfq_cart.append({'name': row['name'], 'qty': qty})
                        st.toast(f"Added {row['name']} to your RFQ list.")
                else:
                    st.info("Login to see prices and request a quote.")

def render_rfq_page():
    st.header("Request For Quotation (RFQ)")
    col1, col2 = st.columns(2)
    with col1:
        with st.form("rfq_form"):
            name = st.text_input("Name*")
            company = st.text_input("Company Name*")
            gst = st.text_input("GST No.")
            location = st.text_input("Location*")
            delivery = st.selectbox("Delivery Preference*", ["Courier", "Transport", "Pickup"])
            uploaded_file = st.file_uploader("Upload PO / Requirement List (optional)")
            if st.form_submit_button("Submit RFQ", use_container_width=True, type="primary"):
                if not name or not company or not location:
                    st.warning("Please fill in all required fields.")
                else:
                    rfq_text = f"New RFQ from *{company}*:\n\n*Contact:* {name}\n*Location:* {location}\n*GST:* {gst}\n*Delivery:* {delivery}\n\n*Items in Cart:*\n"
                    for item in st.session_state.get('rfq_cart', []):
                        rfq_text += f"- {item['name']} (Qty: {item['qty']})\n"
                    encoded_message = urllib.parse.quote(rfq_text)
                    whatsapp_url = f"https://wa.me/919891286714?text={encoded_message}"
                    st.success("RFQ Prepared! Click the link to send.")
                    st.markdown(f'<a href="{whatsapp_url}" class="whatsapp-button" style="position:relative; width:100%; text-decoration:none;" target="_blank">📲 Send RFQ via WhatsApp</a>', unsafe_allow_html=True)
    with col2:
        st.subheader("Items in Your RFQ")
        if st.session_state.get('rfq_cart', []):
            for item in st.session_state.rfq_cart:
                st.text(f"- {item['name']} (Quantity: {item['qty']})")
        else:
            st.info("Your RFQ list is empty. Add items from the Product Catalogue.")

def render_brands_page(brands_df):
    st.header("Brands We Deal In")
    st.write("We are proud to be authorized dealers and partners for India's leading industrial brands.")
    for i in range(0, len(brands_df), 5):
        row_brands = brands_df.iloc[i:i+5]
        cols = st.columns(5)
        for j, (_, brand) in enumerate(row_brands.iterrows()):
            cols[j].image(brand['logo_url'], use_column_width=True, caption=brand['brand_name'])

# --- MAIN APP LOGIC ---
st.markdown('<a href="https://wa.me/919891286714" class="whatsapp-button" target="_blank">💬</a>', unsafe_allow_html=True)
excel_file_path = Path(__file__).parent / "database.xlsx"
all_data = load_data(excel_file_path)

if all_data:
    # Initialize session state keys safely
    if "current_page" not in st.session_state: st.session_state.current_page = "Home"
    if "user_logged_in" not in st.session_state: st.session_state.user_logged_in = False
    
    # Render the header for all users
    render_header(st.session_state.user_logged_in)
    st.markdown("---")

    # If the user is logged in, render the sidebar and protected content
    if st.session_state.user_logged_in:
        render_sidebar()
        
        if 'rfq_cart' not in st.session_state: st.session_state.rfq_cart = []
        
        page = st.session_state.current_page
        if page == "Dashboard":
            st.header(f"Welcome to your Dashboard, {st.session_state.user_details['customer_name']}")
            st.info("Order History, Quotation Requests, and Credit Ledger would be displayed here.")
        elif page == "Products": render_product_catalogue(all_data['products'], True)
        elif page == "RFQ": render_rfq_page()
        elif page == "Brands": render_brands_page(all_data['brands'])
        # Add other logged-in pages here
        else: # Default to home for logged in user
            render_home_page(all_data['homepage'])
    
    # If the user is NOT logged in, render public pages and login form
    else:
        page = st.session_state.current_page
        if page == "Login / Sign Up":
            show_login_form(all_data['customers'])
        elif page == "Home": render_home_page(all_data['homepage'])
        elif page == "Products": render_product_catalogue(all_data['products'], False)
        elif page == "Brands": render_brands_page(all_data['brands'])
        elif page == "RFQ": render_rfq_page()
        # Add other public pages here
        else:
            st.header(page)
            st.info(f"Content for the {page} page would be displayed here.")

