# Ahirwal Trading - Professional B2B Self-Service Portal
# Themed version - styling is controlled by .streamlit/config.toml

import streamlit as st
import pandas as pd
from pathlib import Path

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Ahirwal Trading Portal",
    page_icon="🛠️",
    layout="wide"
)

# --- STYLING (Layout Only) ---
# Colors are now controlled by .streamlit/config.toml
# This CSS is only for layout and structure.
st.markdown("""
<style>
    /* Custom container for product items */
    .product-container {
        border: 1px solid #E0E0E0;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
        background-color: #FFFFFF;
    }
    /* Reduce top padding */
    .stApp {
        padding-top: 2rem;
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
        st.error(f"Fatal Error: Could not load or process database.xlsx. Please check the file and sheet names. Details: {e}")
        return None

# --- AUTHENTICATION ---
def check_password(customers_df):
    if "user_logged_in" not in st.session_state:
        st.session_state["user_logged_in"] = False

    if not st.session_state["user_logged_in"]:
        st.image("https://placehold.co/400x100/007BC0/FFFFFF?text=Ahirwal+Trading", width=300)
        st.title("B2B Customer Portal")

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

# --- UI RENDERERS & HELPERS (No changes from previous version) ---
def add_to_cart(sku, name, quantity, price):
    # Check if item already in cart
    for item in st.session_state.cart:
        if item['sku'] == sku:
            item['quantity'] += quantity
            item['total'] = item['quantity'] * item['price']
            st.toast(f"Updated '{name}' in cart!", icon="🛒")
            return

    # If not, add new item
    cart_item = {'sku': sku, 'name': name, 'quantity': quantity, 'price': price, 'total': price * quantity}
    st.session_state.cart.append(cart_item)
    st.toast(f"Added '{name}' to cart!", icon="🛒")


def render_sidebar():
    user_info = st.session_state['user_details']
    with st.sidebar:
        st.image("https://placehold.co/200x60/007BC0/FFFFFF?text=Ahirwal", use_column_width=True)
        st.subheader("Welcome,")
        st.title(f"{user_info['customer_name']}")
        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Your Tier", user_info['price_tier_name'])
        with col2:
            st.metric("Your Discount", f"{user_info['discount_percentage']:.0%}")
        st.markdown("---")

        st.header("Order Summary")
        if not st.session_state.cart:
            st.info("Your cart is empty.")
        else:
            cart_df = pd.DataFrame(st.session_state.cart)
            grand_total = cart_df['total'].sum()
            st.metric("Order Total", f"₹{grand_total:,.2f}")

        if st.button("Logout", use_container_width=True):
            # Clear all session state keys
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()

def render_simple_products(df, discount):
    # ... (code for rendering simple products, no changes)
    st.info("Render simple products logic here.")


def render_variant_selectors(all_data, user_discount):
    # ... (code for category selection and calling variant renderers, no changes)
    st.info("Render variant selectors logic here.")

def render_cart_page():
    # ... (code for showing the cart and placing the order, no changes)
    st.info("Render cart page logic here.")


# --- MAIN APP LOGIC ---
excel_file_path = Path(__file__).parent / "database.xlsx"
all_data = load_data(excel_file_path)

if all_data:
    if check_password(all_data['customers']):
        if 'cart' not in st.session_state:
            st.session_state.cart = []

        render_sidebar()

        page = st.radio("Navigation", ["Order Pad", "View Cart & Submit"], horizontal=True)
        st.markdown("---")

        if page == "Order Pad":
            st.header("🛒 Order Pad")
            st.write("Select a category to start adding products to your order.")
            render_variant_selectors(all_data, st.session_state['user_details']['discount_percentage'])

        elif page == "View Cart & Submit":
            st.header("📋 Review and Submit Enquiry")
            render_cart_page()

