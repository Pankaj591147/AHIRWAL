# Ahirwal Trading - Professional B2B Self-Service Portal
# Definitive Version based on the user's prototype structure.

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
   .st-emotion-cache-16txtl3 { padding: 1rem 2rem; } /* Reduce padding on main content */
    h1, h2, h3 { color: #003366; } /* Ahirwal Blue */
   .highlight-card {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        transition: box-shadow.3s;
        height: 100%;
    }
   .highlight-card:hover {
        box-shadow: 0 4px 15px 0 rgba(0,0,0,0.1);
    }
   .brand-logo {
        max-height: 60px;
        margin: 15px;
        object-fit: contain;
    }
   .whatsapp-button {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background-color: #25D366;
        color: white;
        padding: 15px;
        border-radius: 50%;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.3);
        z-index: 1000;
        font-size: 24px;
        line-height: 0;
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
            'products': xls.parse("Products"),
            'brands': xls.parse("Brands"),
            'franchise': xls.parse("Franchise"),
            'customers': xls.parse("Customers"),
            'price_tiers': xls.parse("PriceTiers")
        }
        data['customers'] = pd.merge(data['customers'], data['price_tiers'], left_on='price_tier_name', right_on='tier_name')
        return data
    except Exception as e:
        st.error(f"Fatal Error: Could not load or process database.xlsx. Details: {e}")
        return None

# --- AUTHENTICATION & SESSION MANAGEMENT ---
def check_password(customers_df):
    if "user_logged_in" not in st.session_state: st.session_state["user_logged_in"] = False
    if not st.session_state["user_logged_in"]:
        with st.form("credentials_form"):
            st.subheader("Login / Sign Up")
            username = st.text_input("Registered Business Name", placeholder="Enter your business name")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            col1, col2 = st.columns(2)
            if col1.form_submit_button("Login", use_container_width=True, type="primary"):
                try:
                    if username in st.secrets["passwords"] and st.secrets["passwords"][username] == password:
                        st.session_state.user_logged_in = True
                        user_details = customers_df[customers_df['customer_name'] == username].iloc
                        st.session_state.user_details = user_details.to_dict()
                        st.session_state.current_page = "Dashboard"
                        st.session_state.rfq_cart =
                        st.rerun()
                    else: st.error("😕 Username not found or password incorrect")
                except Exception: st.error("Authentication system error.")
            if col2.form_submit_button("Request an Account", use_container_width=True):
                 st.session_state.current_page = "Contact"
                 st.rerun()
        return False
    return True

def set_page(page_name):
    st.session_state.current_page = page_name

# --- PAGE RENDERING FUNCTIONS ---
def render_header(is_logged_in):
    cols = st.columns([1, 3, 1.5])
    with cols:
        st.image("https://placehold.co/200x60/003366/FFFFFF?text=AHIRWAL", use_column_width=True)
    
    with cols[1]:
        menu_items =
        if is_logged_in:
            menu_items.insert(1, "Dashboard")
        
        # Use a callback to handle page changes
        def on_page_change():
            set_page(st.session_state.main_nav)

        st.radio("Navigation", menu_items, key="main_nav", on_change=on_page_change, horizontal=True, label_visibility="collapsed")
    
    with cols[2]:
        if is_logged_in:
            if st.button(f"Logout, {st.session_state.user_details['customer_name']}", use_container_width=True):
                for key in list(st.session_state.keys()): del st.session_state[key]
                st.rerun()
        else:
            if st.button("Login / Sign Up", use_container_width=True):
                 set_page("Login")
                 st.rerun()

def render_home_page(content_df):
    content = content_df.set_index('key')['value'].to_dict()
    st.markdown(f"<div style='background-color:#003366; padding: 4rem; text-align:center; border-radius:10px;'>"
                f"<h1 style='color:white;'>{content.get('headline', '')}</h1>"
                "</div>", unsafe_allow_html=True)
    st.markdown("---")
    cols = st.columns(4)
    cols.markdown(f"<div class='highlight-card'><h3>{content.get('highlight1_val', '')}</h3><p>{content.get('highlight1_desc', '')}</p></div>", unsafe_allow_html=True)
    cols.[1]markdown(f"<div class='highlight-card'><h3>{content.get('highlight2_val', '')}</h3><p>{content.get('highlight2_desc', '')}</p></div>", unsafe_allow_html=True)
    cols.[2]markdown(f"<div class='highlight-card'><h3>{content.get('highlight3_val', '')}</h3><p>{content.get('highlight3_desc', '')}</p></div>", unsafe_allow_html=True)
    cols.[3]markdown(f"<div class='highlight-card'><h3>{content.get('highlight4_val', '')}</h3><p>{content.get('highlight4_desc', '')}</p></div>", unsafe_allow_html=True)

def render_product_catalogue(products_df, is_logged_in):
    st.header("Product Catalogue")
    col1, col2 = st.columns([1, 3])
    with col1:
        categories = ["All Categories"] + products_df['category'].unique().tolist()
        selected_category = st.radio("Filter by Category", categories)
    with col2:
        filtered_products = products_df if selected_category == "All Categories" else products_df[products_df['category'] == selected_category]
        for _, row in filtered_products.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([1, 3, 1])
                with c1: st.image(row['image_url'], width=150)
                with c2:
                    st.subheader(row['product_name'])
                    st.caption(f"Brand: {row['brand']} | SKU: {row['sku']}")
                    st.write(row['description'])
                with c3:
                    if is_logged_in:
                        st.metric("Your Price", f"₹{row['rate'] * (1 - st.session_state.user_details['discount_percentage']):,.2f}")
                        if st.button("Add to RFQ", key=f"add_{row['sku']}", use_container_width=True):
                            st.session_state.rfq_cart.append(row.to_dict())
                            st.toast(f"Added {row['product_name']} to your RFQ list.")
                    else:
                        st.info("Login to see prices and add to quote.")

def render_rfq_page():
    st.header("Request For Quotation (RFQ)")
    col1, col2 = st.columns(2)
    with col1:
        with st.form("rfq_form"):
            st.text_input("Name")
            st.text_input("Company")
            st.text_input("GST No.")
            st.multiselect("Products Required", options=[p['product_name'] for p in st.session_state.get('rfq_cart',)])
            st.file_uploader("Upload requirement list (optional)")
            if st.form_submit_button("Submit RFQ", use_container_width=True, type="primary"):
                st.success("Your RFQ has been submitted! We will contact you shortly.")
    with col2:
        st.subheader("Items in Your RFQ")
        if st.session_state.get('rfq_cart',):
            for item in st.session_state.rfq_cart:
                st.write(f"- {item['product_name']}")
        else:
            st.info("Your RFQ list is empty. Add products from the catalogue.")

def render_brands_page(brands_df):
    st.header("Brands We Deal In")
    st.write("We are proud to be authorized dealers and partners for India's leading industrial brands.")
    for i in range(0, len(brands_df), 4):
        cols = st.columns(4)
        for j, (_, brand) in enumerate(brands_df.iloc[i:i+4].iterrows()):
            with cols[j]:
                with st.container(border=True):
                    st.image(brand['logo_url'], use_column_width=True)
                    st.write(brand['description'])

#... Other page renderers (Franchise, About, Contact, Dashboard) would be defined similarly...

# --- MAIN APP LOGIC ---
st.markdown('<a href="https://wa.me/919891286714" class="whatsapp-button" target="_blank">💬</a>', unsafe_allow_html=True)
excel_file_path = Path(__file__).parent / "database.xlsx"
all_data = load_data(excel_file_path)

if all_data:
    if "current_page" not in st.session_state: st.session_state.current_page = "Home"
    if "rfq_cart" not in st.session_state: st.session_state.rfq_cart =

    is_logged_in = st.session_state.get("user_logged_in", False)
    render_header(is_logged_in)
    st.markdown("---")

    page = st.session_state.current_page
    if page == "Home":
        render_home_page(all_data['homepage'])
    elif page == "Products":
        render_product_catalogue(all_data['products'], is_logged_in)
    elif page == "RFQ":
        render_rfq_page()
    elif page == "Brands":
        render_brands_page(all_data['brands'])
    elif page == "Login":
         if not check_password(all_data['customers']):
             st.stop()
    elif page == "Dashboard" and is_logged_in:
        st.header("Customer Dashboard")
        st.info("Order History, Quotation Requests, and Credit Ledger would be displayed here.")
    else:
        st.header(page)
        st.info(f"Content for the {page} page would be displayed here.")

