# Ahirwal Trading - Professional B2B Self-Service Portal
# Inspired by the Bosch B2B interface and powered by an Excel database.

import streamlit as st
import pandas as pd
from pathlib import Path

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Ahirwal Trading Portal",
    page_icon="🛠️",
    layout="wide"
)

# --- STYLING ---
# Inject custom CSS to mimic the professional look and feel of the Bosch portal
st.markdown("""
<style>
    /* Main container and sidebar styling */
    .stApp {
        background-color: #F0F2F5; /* Light grey background */
    }
    .st-emotion-cache-16txtl3 {
        padding: 2rem 2rem;
    }
    .st-emotion-cache-1cypcdb {
         background-color: #FFFFFF; /* White sidebar */
    }
    /* Button styling */
    .stButton>button {
        background-color: #007BC0; /* Bosch Blue */
        color: white;
        border-radius: 4px;
        border: none;
    }
    .stButton>button:hover {
        background-color: #005A9C;
        color: white;
    }
    /* Metric styling in sidebar */
    .st-emotion-cache-16txtl3 .st-emotion-cache-1d5k2r9 {
        background-color: #F0F2F5;
        border-radius: 8px;
        padding: 10px;
    }
    /* Custom container for product items */
    .product-container {
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
        background-color: #FFFFFF;
    }
</style>
""", unsafe_allow_html=True)


# --- DATA LOADING ---
@st.cache_data(ttl=300) # Cache for 5 minutes
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
        st.error(f"Fatal Error: Could not load the database.xlsx file. Ensure it is in the same folder as the app and has all 5 required sheets. Details: {e}")
        return None

# --- AUTHENTICATION ---
def check_password(customers_df):
    if "user_logged_in" not in st.session_state:
        st.session_state["user_logged_in"] = False

    if not st.session_state["user_logged_in"]:
        st.title("Ahirwal Trading & Mill Store")
        st.subheader("B2B Customer Portal Login")

        with st.form("credentials"):
            username = st.text_input("Registered Business Name")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log in")

            if submitted:
                try:
                    if username in st.secrets["passwords"] and st.secrets["passwords"][username] == password:
                        st.session_state["user_logged_in"] = True
                        user_details = customers_df[customers_df['customer_name'] == username].iloc[0]
                        st.session_state["user_details"] = user_details.to_dict()
                        st.rerun()
                    else:
                        st.error("😕 Username not found or password incorrect")
                except Exception:
                    st.error("Authentication system error. Please contact support.")
        return False
    return True


# --- UI RENDERERS ---
def render_variant_selector(df, user_discount, category_name):
    st.subheader(f"Adding from: {category_name}")

    if category_name == "Nuts and Bolts":
        render_nutbolt_selector(df, user_discount)
    elif category_name == "V-Belts":
        render_vbelt_selector(df, user_discount)

def render_simple_product_list(df, user_discount):
    for _, row in df.iterrows():
        customer_price = row['base_rate'] * (1 - user_discount)
        with st.container():
            st.markdown('<div class="product-container">', unsafe_allow_html=True)
            col1, col2, col3, col4 = st.columns([4, 2, 2, 2])
            with col1:
                st.subheader(row['product_name'])
                st.caption(f"SKU: {row['product_sku']}")
            with col2:
                st.metric("In Stock", f"{int(row['stock_level'])} {row['base_units']}")
            with col3:
                st.markdown(f"**Your Price:**")
                st.markdown(f"### :green[₹{customer_price:.2f}]")
            with col4:
                quantity = st.number_input("Qty", min_value=1, value=1, key=f"qty_{row['product_sku']}")
                if st.button("Add to Cart", key=f"add_{row['product_sku']}", use_container_width=True):
                    add_to_cart(row['product_sku'], row['product_name'], quantity, customer_price)
            st.markdown('</div>', unsafe_allow_html=True)

def render_nutbolt_selector(df, discount):
    materials = df['material'].unique()
    selected_material = st.selectbox("1. Material", materials, index=None, placeholder="Select material...")
    if selected_material:
        # Filtering logic for dependent dropdowns
        # ... (This logic would be implemented here to show Dia and Length based on material)
        st.info("Nut & Bolt variant selection logic would be fully implemented here.")

def render_vbelt_selector(df, discount):
    sections = df['section'].unique()
    selected_section = st.selectbox("1. Section", sections, index=None, placeholder="Select section...")
    if selected_section:
         # ... (This logic would be implemented here to show Size based on Section)
         st.info("V-Belt variant selection logic would be fully implemented here.")

def add_to_cart(sku, name, quantity, price):
    cart_item = {'sku': sku, 'name': name, 'quantity': quantity, 'price': price, 'total': price * quantity}
    st.session_state.cart.append(cart_item)
    st.toast(f"Added '{name}' to cart!", icon="🛒")

def render_sidebar():
    user_info = st.session_state['user_details']
    with st.sidebar:
        st.image("https://placehold.co/200x60/007BC0/FFFFFF?text=Ahirwal", use_column_width=True)
        st.subheader(f"Welcome,")
        st.title(f"{user_info['customer_name']}")
        st.markdown("---")

        st.metric("Your Pricing Tier", user_info['price_tier_name'])
        st.metric("Your Discount", f"{user_info['discount_percentage']:.0%}")
        st.markdown("---")

        st.subheader("Order Summary")
        if not st.session_state.cart:
            st.info("Your cart is empty.")
        else:
            cart_df = pd.DataFrame(st.session_state.cart)
            grand_total = cart_df['total'].sum()
            st.metric("Order Total", f"₹{grand_total:,.2f}")
            if st.button("Clear Cart", use_container_width=True):
                st.session_state.cart = []
                st.rerun()

        if st.button("Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()

# --- MAIN APP LOGIC ---
excel_file_path = Path(__file__).parent / "database.xlsx"
all_data = load_data(excel_file_path)

if all_data:
    if check_password(all_data['customers']):
        if 'cart' not in st.session_state:
            st.session_state.cart = []

        render_sidebar()

        st.header("🛒 Order Pad")
        st.write("Select a category to start adding products to your order.")

        # Category Selection
        selected_cat_name = st.selectbox(
            "Product Category",
            all_data['categories']['category_name'],
            index=None,
            placeholder="Choose a category..."
        )

        if selected_cat_name:
            cat_info = all_data['categories'][all_data['categories']['category_name'] == selected_cat_name].iloc[0]
            selection_type = cat_info['selection_type']
            user_discount = st.session_state['user_details']['discount_percentage']

            if selection_type == 'Simple':
                df = all_data['simple_products'][all_data['simple_products']['category_name'] == selected_cat_name]
                render_simple_product_list(df, user_discount)
            elif selection_type == 'NutBolt_Variant':
                render_variant_selector(all_data['nutbolt_variants'], user_discount, "Nuts and Bolts")
            elif selection_type == 'VBelt_Variant':
                render_variant_selector(all_data['vbelt_variants'], user_discount, "V-Belts")
        
        st.markdown("---")
        st.header("📋 Current Order Details")
        if st.session_state.cart:
            cart_display_df = pd.DataFrame(st.session_state.cart)
            st.dataframe(cart_display_df[['name', 'sku', 'quantity', 'price', 'total']], use_container_width=True, hide_index=True,
                         column_config={
                             "price": st.column_config.NumberColumn(format="₹%.2f"),
                             "total": st.column_config.NumberColumn(format="₹%.2f"),
                         })
            
            po_number = st.text_input("Enter your Purchase Order (PO) Number (Optional)")
            
            if st.button("✅ Submit Enquiry", type="primary", use_container_width=True):
                user_info = st.session_state['user_details']
                grand_total = cart_display_df['total'].sum()
                order_summary = f"**Customer:** {user_info['customer_name']}\n"
                if po_number:
                    order_summary += f"**PO Number:** {po_number}\n\n"
                
                order_summary += cart_display_df[['name', 'quantity', 'price']].to_markdown(index=False)
                order_summary += f"\n\n**GRAND TOTAL: ₹{grand_total:,.2f}**"
                
                st.success("Enquiry Submitted!")
                st.code(order_summary, language=None)
                st.info("Please copy the summary above and send it to us via WhatsApp or Email for processing.")
                st.session_state.cart = []
        else:
            st.info("Add products to your order using the Order Pad above.")

