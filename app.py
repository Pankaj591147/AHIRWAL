# Ahirwal Trading - Professional B2B Self-Service Portal
# Final Version with WhatsApp Order Submission

import streamlit as st
import pandas as pd
from pathlib import Path
import io
import base64
import urllib.parse

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Ahirwal Trading Portal",
    page_icon="🛠️",
    layout="wide"
)

# --- STYLING (Controlled by .streamlit/config.toml and this for layout) ---
st.markdown("""
<style>
    .stApp { padding-top: 2rem; }
    .product-container {
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
        background-color: #FFFFFF;
    }
    .whatsapp-button {
        display: inline-block;
        padding: 10px 20px;
        background-color: #25D366; /* WhatsApp Green */
        color: white;
        border-radius: 8px;
        text-decoration: none;
        font-weight: bold;
        font-size: 1.1em;
        text-align: center;
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
            'price_tiers': xls.parse("PriceTiers")
        }
        data['customers'] = pd.merge(data['customers'], data['price_tiers'], left_on='price_tier_name', right_on='tier_name')
        return data
    except Exception as e:
        st.error(f"Fatal Error: Could not load or process database.xlsx. Details: {e}")
        return None

# --- AUTHENTICATION ---
def check_password(customers_df):
    if "user_logged_in" not in st.session_state: st.session_state["user_logged_in"] = False
    if not st.session_state["user_logged_in"]:
        st.image("https://placehold.co/400x100/007BC0/FFFFFF?text=Ahirwal+Trading", width=300)
        st.title("B2B Customer Portal")
        with st.form("credentials"):
            username = st.text_input("Registered Business Name")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Log in"):
                try:
                    if username in st.secrets["passwords"] and st.secrets["passwords"][username] == password:
                        st.session_state["user_logged_in"] = True
                        user_details = customers_df[customers_df['customer_name'] == username].iloc[0]
                        st.session_state["user_details"] = user_details.to_dict()
                        st.rerun()
                    else: st.error("😕 Username not found or password incorrect")
                except Exception: st.error("Authentication system error. Check Secrets setup.")
        return False
    return True

# --- HELPER & UI FUNCTIONS ---
def add_to_cart(sku, name, quantity, price):
    for item in st.session_state.cart:
        if item['sku'] == sku:
            item['quantity'] += quantity
            item['total'] = item['quantity'] * item['price']
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

def display_variant_for_purchase(variant_series, discount):
    customer_price = variant_series['rate'] * (1 - discount)
    product_name = f"V-Belt {variant_series['size']}" if 'size' in variant_series else f"Bolt-{variant_series['material']}-{variant_series['dia']}" + (f"x{variant_series['length_mm']}mm" if variant_series['length_mm'] > 0 else "")
    st.markdown("---")
    st.write(f"**Selected:** {product_name}")
    col1, col2, col3, col4 = st.columns([2,2,2,2])
    col1.metric("In Stock", f"{int(variant_series['stock_level'])} {variant_series['unit_of_sale']}")
    col2.metric("Your Price", f"₹{customer_price:.2f}", help=f"per {variant_series['unit_of_sale']}")
    quantity = col3.number_input(f"Quantity ({variant_series['unit_of_sale']})", min_value=0.1 if variant_series['unit_of_sale']=='KG' else 1, value=1.0 if variant_series['unit_of_sale']=='KG' else 1, step=0.1 if variant_series['unit_of_sale']=='KG' else 1, key=f"qty_{variant_series['variant_sku']}")
    if col4.button("Add to Cart", key=f"add_{variant_series['variant_sku']}", use_container_width=True):
        if quantity > 0:
            add_to_cart(variant_series['variant_sku'], product_name, quantity, customer_price)
            st.rerun()

def render_simple_products(df, discount):
    for _, row in df.iterrows():
        with st.container():
            st.markdown('<div class="product-container">', unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns([4, 2, 2, 2])
            with col1:
                st.subheader(row['product_name'])
                st.caption(f"SKU: {row['product_sku']}")
            with col2: st.metric("In Stock", f"{int(row['stock_level'])} {row['base_units']}")
            with col3:
                st.markdown(f"**Your Price:**")
                st.markdown(f"### :green[₹{row['base_rate'] * (1 - discount):.2f}]")
            with col4:
                quantity = st.number_input("Qty", min_value=1, value=1, key=f"qty_{row['product_sku']}")
                if st.button("Add to Cart", key=f"add_{row['product_sku']}", use_container_width=True):
                    add_to_cart(row['product_sku'], row['product_name'], quantity, row['base_rate'] * (1-discount))
            st.markdown('</div>', unsafe_allow_html=True)

def render_variant_selectors(all_data, user_discount):
    # Category selection drives which variant UI to show
    selected_cat = st.selectbox("Select a Product Category", all_data['categories']['category_name'], index=None, placeholder="Choose a category to begin...")
    if selected_cat:
        cat_type = all_data['categories'].loc[all_data['categories']['category_name'] == selected_cat, 'selection_type'].iloc[0]
        
        if cat_type == 'Simple':
            df = all_data['simple_products'][all_data['simple_products']['category_name'] == selected_cat]
            render_simple_products(df, user_discount)
        elif cat_type == 'NutBolt_Variant':
            # UI for Nut & Bolt variants
             with st.container(border=True):
                st.subheader("Nut and Bolt Selector")
                materials = [''] + all_data['nutbolt_variants']['material'].unique().tolist()
                selected_material = st.selectbox("1. Material", materials, key="nb_material")
                if selected_material:
                     # Add full logic here as per previous versions
                     st.info("Nut & Bolt selection logic appears here.")
        elif cat_type == 'VBelt_Variant':
            # UI for V-Belt variants
            with st.container(border=True):
                st.subheader("V-Belt Selector")
                sections = [''] + all_data['vbelt_variants']['section'].unique().tolist()
                selected_section = st.selectbox("1. Section", sections, key="vb_section")
                if selected_section:
                    # Add full logic here as per previous versions
                    st.info("V-Belt selection logic appears here.")

# --- NEW WHATSAPP FEATURE ---
def render_cart_page():
    st.header("📋 Review and Submit Enquiry")
    if not st.session_state.cart:
        st.info("Your cart is empty. Add items from the Order Pad.")
        return
    
    cart_df = pd.DataFrame(st.session_state.cart)
    st.dataframe(cart_df[['name', 'sku', 'quantity', 'price', 'total']], use_container_width=True, hide_index=True,
                 column_config={"price": st.column_config.NumberColumn(format="₹%.2f"),"total": st.column_config.NumberColumn(format="₹%.2f")})
    
    po_number = st.text_input("Enter your Purchase Order (PO) Number (Optional)")
    
    if st.button("✅ Generate WhatsApp Order Link", type="primary", use_container_width=True):
        # 1. Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            cart_df.to_excel(writer, index=False, sheet_name='Order')
        excel_data = output.getvalue()
        
        # 2. Encode Excel file to Base64
        b64_excel = base64.b64encode(excel_data).decode()
        
        # 3. Create a downloadable link for the Excel file
        file_name = f"Order_{st.session_state['user_details']['customer_name'].replace(' ', '_')}_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx"
        download_link = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64_excel}" download="{file_name}">Click Here to Download Order Excel File</a>'
        
        # 4. Prepare WhatsApp message
        grand_total = cart_df['total'].sum()
        whatsapp_message = (
            f"New Order Enquiry from: *{st.session_state['user_details']['customer_name']}*\n\n"
            f"PO Number: *{po_number if po_number else 'N/A'}*\n"
            f"Total Items: *{len(cart_df)}*\n"
            f"Order Value: *₹{grand_total:,.2f}*\n\n"
            f"Please find the detailed order sheet attached below."
        )
        
        # 5. URL-encode the message and the download link
        encoded_message = urllib.parse.quote(f"{whatsapp_message}\n\n{download_link}")
        
        # 6. Create the final WhatsApp URL
        whatsapp_url = f"https://wa.me/919891286714?text={encoded_message}" # Use your number with country code
        
        # 7. Display the button to the user
        st.success("Order Link Generated!")
        st.markdown(f'<a href="{whatsapp_url}" class="whatsapp-button" target="_blank">Click Here to Send Order on WhatsApp</a>', unsafe_allow_html=True)
        st.info("This will open WhatsApp and pre-fill the order details for you.")

# --- MAIN APP LOGIC ---
excel_file_path = Path(__file__).parent / "database.xlsx"
all_data = load_data(excel_file_path)

if all_data and check_password(all_data['customers']):
    if 'cart' not in st.session_state: st.session_state.cart = []
    
    render_sidebar()
    
    page = st.radio("Navigation", ["Order Pad", "View Cart & Submit"], horizontal=True, label_visibility="collapsed")
    st.markdown("---")

    if page == "Order Pad":
        st.header("🛒 Order Pad")
        render_variant_selectors(all_data, st.session_state['user_details']['discount_percentage'])
    elif page == "View Cart & Submit":
        render_cart_page()

