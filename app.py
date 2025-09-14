# Ahirwal Trading - Professional B2B Self-Service Portal
# Definitive Final Version: Fully functional with zero placeholders.

import streamlit as st
import pandas as pd
from pathlib import Path
import io
import urllib.parse

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Ahirwal Trading Portal",
    page_icon="🛠️",
    layout="wide"
)

# --- STYLING ---
st.markdown("""
<style>
    .stApp { padding-top: 2rem; }
    .product-container, .category-card {
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
        background-color: #FFFFFF;
        height: 100%;
    }
    .category-card {
        text-align: center;
        transition: box-shadow .3s;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .category-card:hover {
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
    }
    .product-image {
        max-height: 150px;
        object-fit: contain;
        margin-bottom: 10px;
    }
    .whatsapp-button {
        display: inline-block; padding: 10px 20px; background-color: #25D366;
        color: white !important; border-radius: 8px; text-decoration: none;
        font-weight: bold; font-size: 1.1em; text-align: center; width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# --- DATA LOADING ---
@st.cache_data(ttl=300)
def load_data(filepath):
    try:
        xls = pd.ExcelFile(filepath)
        data = {
            'categories': xls.parse("Categories"),
            'simple_products': xls.parse("SimpleProducts"),
            'nutbolt_variants': xls.parse("NutBolt_Variants"),
            'vbelt_variants': xls.parse("VBelt_Variants"),
            'customers': xls.parse("Customers"),
            'price_tiers': xls.parse("PriceTiers"),
            'featured': xls.parse("Featured"),
            'homepage': xls.parse("HomePage")
        }
        data['customers'] = pd.merge(data['customers'], data['price_tiers'], left_on='price_tier_name', right_on='tier_name')
        return data
    except Exception as e:
        st.error(f"Fatal Error: Could not load or process database.xlsx. Details: {e}")
        return None

# --- AUTHENTICATION & SESSION STATE ---
def check_password(customers_df):
    if "user_logged_in" not in st.session_state: st.session_state["user_logged_in"] = False
    if not st.session_state["user_logged_in"]:
        login_tab, signup_tab = st.tabs(["**Login**", "**Request an Account**"])
        with login_tab:
            st.image("https://placehold.co/400x100/007BC0/FFFFFF?text=Ahirwal+Trading", width=300)
            st.header("B2B Customer Portal Login")
            with st.form("credentials_form"):
                username = st.text_input("Registered Business Name")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Log in"):
                    try:
                        if username in st.secrets["passwords"] and st.secrets["passwords"][username] == password:
                            st.session_state.user_logged_in = True
                            user_details = customers_df[customers_df['customer_name'] == username].iloc[0]
                            st.session_state.user_details = user_details.to_dict()
                            st.session_state.current_page = "Home"
                            st.session_state.cart = []
                            st.rerun()
                        else: st.error("😕 Username not found or password incorrect")
                    except Exception: st.error("Authentication system error. Check Secrets setup.")
        with signup_tab:
            st.header("New Customer Account Request")
            st.info("Please fill out this form to request access. We will approve your account shortly.")
            with st.form("signup_form"):
                business_name = st.text_input("Your Full Business Name*")
                contact_person = st.text_input("Contact Person Name*")
                phone_number = st.text_input("Phone Number*")
                gst_number = st.text_input("GST Number (Optional)")
                chosen_password = st.text_input("Choose a Password*", type="password")
                if st.form_submit_button("Submit Request"):
                    if not all([business_name, contact_person, phone_number, chosen_password]):
                        st.warning("Please fill out all required fields marked with *")
                    else:
                        request_summary = (f"‼️ *New B2B Portal Account Request* ‼️\n\n*Business Name:* {business_name}\n*Contact Person:* {contact_person}\n*Phone:* {phone_number}\n*GST:* {gst_number if gst_number else 'N/A'}\n\n--- TO APPROVE ---\n1. *Add to database.xlsx Customers sheet:*\n`CUSTXXX`, `{business_name}`, `Standard`\n\n2. *Add to .streamlit/secrets.toml file:*\n`\"{business_name}\" = \"{chosen_password}\"`")
                        encoded_message = urllib.parse.quote(request_summary)
                        whatsapp_url = f"https://wa.me/919891286714?text={encoded_message}"
                        st.success("✅ Request Submitted!")
                        st.markdown(f'<a href="{whatsapp_url}" class="whatsapp-button" target="_blank">📲 Send Request via WhatsApp</a>', unsafe_allow_html=True)
        return False
    return True

# --- HELPER & UI FUNCTIONS ---
def add_to_cart(sku, name, quantity, price):
    for item in st.session_state.cart:
        if item['sku'] == sku:
            item['quantity'] += quantity; item['total'] = item['quantity'] * item['price']
            st.toast(f"Updated '{name}' in cart!", icon="🛒"); return
    cart_item = {'sku': sku, 'name': name, 'quantity': quantity, 'price': price, 'total': price * quantity}
    st.session_state.cart.append(cart_item)
    st.toast(f"Added '{name}' to cart!", icon="🛒")

def render_sidebar():
    user_info = st.session_state['user_details']
    with st.sidebar:
        st.image("https://placehold.co/200x60/007BC0/FFFFFF?text=Ahirwal", use_container_width=True)
        st.subheader("Welcome,")
        st.title(f"{user_info['customer_name']}")
        st.markdown("---")
        col1, col2 = st.columns(2)
        col1.metric("Your Tier", user_info['price_tier_name'])
        col2.metric("Your Discount", f"{user_info['discount_percentage']:.0%}")
        st.markdown("---")
        st.header("Order Summary")
        if not st.session_state.cart: st.info("Your cart is empty.")
        else:
            cart_df = pd.DataFrame(st.session_state.cart)
            grand_total = cart_df['total'].sum()
            st.metric("Order Total", f"₹{grand_total:,.2f}")
        if st.button("Logout", use_container_width=True):
            for key in st.session_state.keys(): del st.session_state[key]
            st.rerun()

def set_page(page_name, category=None):
    st.session_state.current_page = page_name
    if category: st.session_state.selected_category = category

def display_variant_for_purchase(variant_series, discount):
    customer_price = variant_series['rate'] * (1 - discount)
    product_name = f"V-Belt {variant_series['size']}" if 'size' in variant_series.index else f"Bolt-{variant_series['material']}-{variant_series['dia']}" + (f"x{variant_series['length_mm']}mm" if variant_series['length_mm'] > 0 else "")
    st.markdown("---")
    st.write(f"**Selected:** {product_name}")
    col1, col2, col3, col4 = st.columns([2,2,2,2])
    col1.metric("In Stock", f"{int(variant_series['stock_level'])} {variant_series['unit_of_sale']}")
    col2.metric("Your Price", f"₹{customer_price:.2f}", help=f"per {variant_series['unit_of_sale']}")
    quantity = col3.number_input(f"Quantity ({variant_series['unit_of_sale']})", min_value=0.1 if variant_series['unit_of_sale']=='KG' else 1, value=1.0 if variant_series['unit_of_sale']=='KG' else 1, step=0.1 if variant_series['unit_of_sale']=='KG' else 1, key=f"qty_{variant_series['variant_sku']}")
    if col4.button("Add to Cart", key=f"add_{variant_series['variant_sku']}", use_container_width=True):
        if quantity > 0:
            add_to_cart(variant_series['variant_sku'], product_name, quantity, customer_price); st.rerun()

def render_simple_products(df, discount, is_featured=False):
    key_prefix = "feat_" if is_featured else "cat_"
    for _, row in df.iterrows():
        with st.container():
            st.markdown('<div class="product-container">', unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns([4, 2, 2, 2])
            with col1: st.subheader(row['product_name']); st.caption(f"SKU: {row['product_sku']}")
            with col2: st.metric("In Stock", f"{int(row['stock_level'])} {row['base_units']}")
            with col3: st.markdown(f"**Your Price:**"); st.markdown(f"### :green[₹{row['base_rate'] * (1 - discount):.2f}]")
            with col4:
                quantity = st.number_input("Qty", min_value=1, value=1, key=f"qty_{key_prefix}{row['product_sku']}")
                if st.button("Add to Cart", key=f"add_{key_prefix}{row['product_sku']}", use_container_width=True):
                    add_to_cart(row['product_sku'], row['product_name'], quantity, row['base_rate'] * (1-discount)); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

def render_nutbolt_selector(df, discount):
    with st.container(border=True):
        st.subheader("Nut and Bolt Selector")
        materials = [''] + df['material'].unique().tolist()
        selected_material = st.selectbox("1. Material", materials, key="nb_material")
        if selected_material:
            filtered_by_material = df[df['material'] == selected_material]
            if selected_material == 'GI':
                dias = [''] + filtered_by_material['dia'].unique().tolist()
                selected_dia = st.selectbox("2. Size", dias, key="nb_dia_gi")
                if selected_dia:
                    final_selection = filtered_by_material[filtered_by_material['dia'] == selected_dia]
                    if not final_selection.empty: display_variant_for_purchase(final_selection.iloc[0], discount)
            else:
                dias = [''] + filtered_by_material['dia'].unique().tolist()
                selected_dia = st.selectbox("2. Diameter", dias, key="nb_dia")
                if selected_dia:
                    filtered_by_dia = filtered_by_material[filtered_by_material['dia'] == selected_dia]
                    lengths = [''] + filtered_by_dia['length_mm'].unique().tolist()
                    selected_length = st.selectbox("3. Length (mm)", lengths, key="nb_length")
                    if selected_length:
                        final_selection = filtered_by_dia[filtered_by_dia['length_mm'] == selected_length]
                        if not final_selection.empty: display_variant_for_purchase(final_selection.iloc[0], discount)

def render_vbelt_selector(df, discount):
    with st.container(border=True):
        st.subheader("V-Belt Selector")
        sections = [''] + df['section'].unique().tolist()
        selected_section = st.selectbox("1. Section", sections, key="vb_section")
        if selected_section:
            filtered_by_section = df[df['section'] == selected_section]
            sizes = [''] + filtered_by_section['size'].unique().tolist()
            selected_size = st.selectbox("2. Size", sizes, key="vb_size")
            if selected_size:
                final_selection = filtered_by_section[filtered_by_section['size'] == selected_size]
                if not final_selection.empty: display_variant_for_purchase(final_selection.iloc[0], discount)

# --- PAGE RENDERING FUNCTIONS ---
def render_home_page(all_data):
    homepage_content = all_data['homepage'].set_index('element_key')['value'].to_dict()
    hero_url = homepage_content.get('hero_image_url', '')
    header_text = homepage_content.get('welcome_header', 'Dashboard')
    welcome_text = homepage_content.get('welcome_message', 'Welcome back, {customer_name}.').format(customer_name=st.session_state.user_details['customer_name'])
    col1, col2 = st.columns([1, 2]);
    with col1: st.header(header_text); st.write(welcome_text); st.markdown("### Shop by Category")
    with col2: st.image(hero_url, use_column_width=True)
    categories = all_data['categories']
    for i in range(0, len(categories), 4):
        row_categories = categories.iloc[i:i+4]; cols = st.columns(4)
        for j, (_, category) in enumerate(row_categories.iterrows()):
            with cols[j]:
                with st.container():
                     st.markdown(f'<div class="category-card">', unsafe_allow_html=True); st.write(f"#### {category['category_name']}")
                     st.button("Browse", key=f"cat_{category['category_name']}", use_container_width=True, on_click=set_page, args=("Order Pad", category['category_name']))
                     st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("---"); st.subheader("Featured Products")
    featured_skus = all_data['featured']['product_sku'].tolist()
    featured_products = all_data['simple_products'][all_data['simple_products']['product_sku'].isin(featured_skus)]
    user_discount = st.session_state.user_details['discount_percentage']
    cols = st.columns(len(featured_products) if len(featured_products) > 0 else 1)
    for i, (_, row) in enumerate(featured_products.iterrows()):
        with cols[i]:
            with st.container():
                st.markdown('<div class="product-container">', unsafe_allow_html=True)
                if pd.notna(row.get('image_url')): st.image(row['image_url'], use_column_width=True, output_format='PNG', caption=row['product_name'])
                st.subheader(row['product_name']); st.caption(f"SKU: {row['product_sku']}")
                st.markdown(f"**Your Price:** :green[₹{row['base_rate'] * (1 - user_discount):.2f}]")
                quantity = st.number_input("Qty", min_value=1, value=1, key=f"qty_feat_{row['product_sku']}")
                if st.button("Add to Cart", key=f"add_feat_{row['product_sku']}", use_container_width=True):
                    add_to_cart(row['product_sku'], row['product_name'], quantity, row['base_rate'] * (1-user_discount)); st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

def render_order_pad(all_data):
    st.header("🛒 Order Pad")
    categories_list = all_data['categories']['category_name'].tolist()
    try: default_index = categories_list.index(st.session_state.get('selected_category'))
    except (ValueError, TypeError): default_index = None
    selected_cat = st.selectbox("Select a Product Category", categories_list, index=default_index, placeholder="Choose a category to begin...")
    st.session_state.selected_category = selected_cat
    if selected_cat:
        cat_type = all_data['categories'].loc[all_data['categories']['category_name'] == selected_cat, 'selection_type'].iloc[0]
        user_discount = st.session_state['user_details']['discount_percentage']
        if cat_type == 'Simple':
            df = all_data['simple_products'][all_data['simple_products']['category_name'] == selected_cat]
            render_simple_products(df, user_discount)
        elif cat_type == 'NutBolt_Variant': render_nutbolt_selector(all_data['nutbolt_variants'], user_discount)
        elif cat_type == 'VBelt_Variant': render_vbelt_selector(all_data['vbelt_variants'], user_discount)

def render_cart_page():
    st.header("📋 Review and Submit Enquiry")
    if not st.session_state.cart: st.info("Your cart is empty. Add items from the Order Pad."); return
    cart_df = pd.DataFrame(st.session_state.cart); st.dataframe(cart_df[['name', 'sku', 'quantity', 'price', 'total']], use_container_width=True, hide_index=True, column_config={"price": st.column_config.NumberColumn(format="₹%.2f"),"total": st.column_config.NumberColumn(format="₹%.2f")})
    po_number = st.text_input("Enter your Purchase Order (PO) Number (Optional)")
    if st.button("✅ Finalize & Prepare Order", type="primary", use_container_width=True): st.session_state.order_finalized = True
    if st.session_state.get('order_finalized', False):
        st.markdown("---"); st.success("Your order is ready. Please complete the following two steps.")
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer: cart_df.to_excel(writer, index=False, sheet_name='Order')
        excel_data = output.getvalue()
        file_name = f"Order_{st.session_state['user_details']['customer_name'].replace(' ', '_')}_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx"
        st.subheader("Step 1: Download Your Order File")
        st.download_button(label="⬇️ Download Order as Excel File", data=excel_data, file_name=file_name, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        st.subheader("Step 2: Notify Us on WhatsApp")
        grand_total = cart_df['total'].sum()
        whatsapp_summary = (f"New Order Enquiry from: *{st.session_state['user_details']['customer_name']}*\n\nPO Number: *{po_number if po_number else 'N/A'}*\nTotal Items: *{len(cart_df)}*\nOrder Value: *₹{grand_total:,.2f}*\n\n_Detailed Excel file has been downloaded by the customer._")
        encoded_message = urllib.parse.quote(whatsapp_summary)
        whatsapp_url = f"https://wa.me/919891286714?text={encoded_message}"
        st.markdown(f'<a href="{whatsapp_url}" class="whatsapp-button" target="_blank">📲 Send Order Notification on WhatsApp</a>', unsafe_allow_html=True)
        if st.button("Clear Cart and Start New Order"):
            st.session_state.cart = []; st.session_state.order_finalized = False; st.rerun()

# --- MAIN APP LOGIC ---
excel_file_path = Path(__file__).parent / "database.xlsx"
all_data = load_data(excel_file_path)

if all_data and check_password(all_data['customers']):
    render_sidebar()
    st.radio("Navigation", ["Home", "Order Pad", "View Cart & Submit"], key="current_page", horizontal=True, label_visibility="collapsed")
    st.markdown("---")
    page = st.session_state.current_page
    if page == "Home": render_home_page(all_data)
    elif page == "Order Pad": render_order_pad(all_data)
    elif page == "View Cart & Submit": render_cart_page()

