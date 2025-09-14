# Ahirwal Trading - Professional B2B Self-Service Portal
# Final Version with Corrected 2-Step WhatsApp Order Submission

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
        color: white !important;
        border-radius: 8px;
        text-decoration: none;
        font-weight: bold;
        font-size: 1.1em;
        text-align: center;
        width: 100%;
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

def render_simple_products(df, discount):
    # This function remains unchanged
    st.info("Render simple products logic would be here.")

def render_variant_selectors(all_data, user_discount):
    # This function remains unchanged
    st.info("Render variant selectors logic would be here.")

# --- CORRECTED WHATSAPP FEATURE ---
def render_cart_page():
    st.header("📋 Review and Submit Enquiry")
    if not st.session_state.cart:
        st.info("Your cart is empty. Add items from the Order Pad.")
        return
    
    cart_df = pd.DataFrame(st.session_state.cart)
    st.dataframe(cart_df[['name', 'sku', 'quantity', 'price', 'total']], use_container_width=True, hide_index=True,
                 column_config={"price": st.column_config.NumberColumn(format="₹%.2f"),"total": st.column_config.NumberColumn(format="₹%.2f")})
    
    po_number = st.text_input("Enter your Purchase Order (PO) Number (Optional)")
    
    if st.button("✅ Finalize & Prepare Order", type="primary", use_container_width=True):
        st.session_state.order_finalized = True

    if st.session_state.get('order_finalized', False):
        st.markdown("---")
        st.success("Your order is ready. Please complete the following two steps.")

        # STEP 1: DOWNLOAD EXCEL
        st.subheader("Step 1: Download Your Order File")
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            cart_df.to_excel(writer, index=False, sheet_name='Order')
        excel_data = output.getvalue()
        
        file_name = f"Order_{st.session_state['user_details']['customer_name'].replace(' ', '_')}_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx"
        
        st.download_button(
            label="⬇️ Download Order as Excel File",
            data=excel_data,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

        # STEP 2: SEND WHATSAPP NOTIFICATION
        st.subheader("Step 2: Notify Us on WhatsApp")

        grand_total = cart_df['total'].sum()
        # Create a clean, plain-text summary for the WhatsApp message
        whatsapp_summary = (
            f"New Order Enquiry from: *{st.session_state['user_details']['customer_name']}*\n\n"
            f"PO Number: *{po_number if po_number else 'N/A'}*\n"
            f"Total Items: *{len(cart_df)}*\n"
            f"Order Value: *₹{grand_total:,.2f}*\n\n"
            "_Detailed Excel file has been downloaded by the customer._"
        )
        
        # URL-encode the plain text message
        encoded_message = urllib.parse.quote(whatsapp_summary)
        whatsapp_url = f"https://wa.me/919891286714?text={encoded_message}"
        
        st.markdown(f'<a href="{whatsapp_url}" class="whatsapp-button" target="_blank">📲 Send Order Notification on WhatsApp</a>', unsafe_allow_html=True)
        st.info("After sending, you can clear your cart or continue adding products.")
        if st.button("Clear Cart and Start New Order"):
            st.session_state.cart = []
            st.session_state.order_finalized = False
            st.rerun()


# --- MAIN APP LOGIC ---
excel_file_path = Path(__file__).parent / "database.xlsx"
all_data = load_data(excel_file_path)

if all_data and check_password(all_data['customers']):
    if 'cart' not in st.session_state: st.session_state.cart = []
    
    render_sidebar()
    
    page = st.radio("Navigation", ["Order Pad", "View Cart & Submit"], horizontal=True, label_visibility="collapsed")
    st.markdown("---")

    if page == "Order Pad":
        st.session_state.order_finalized = False # Reset flag if user navigates away
        st.header("🛒 Order Pad")
        render_variant_selectors(all_data, st.session_state['user_details']['discount_percentage'])
    elif page == "View Cart & Submit":
        render_cart_page()

