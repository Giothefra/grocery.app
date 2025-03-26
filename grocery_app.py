import streamlit as st
from datetime import datetime, timedelta
from collections import defaultdict
import matplotlib.pyplot as plt

# --- Constants ---
longer_lasting_items = ["frozen meat", "cheese", "vacuum-sealed", "hard cheese"]

# --- Core Classes ---

class GroceryItem:
    def __init__(self, name, category, price=0.0, expiry_date=None):
        self.name = name
        self.category = category
        self.price = price
        self.bought = False
        self.added_on = datetime.now()
        self.expiry_date = expiry_date
        self.opened_date = None  # NEW: Tracks when item was opened

    def mark_as_bought(self):
        self.bought = True

    def mark_as_opened(self):
        self.opened_date = datetime.now()

    def is_expiring_soon(self, days=3):
        if self.expiry_date is None:
            return False
        return (self.expiry_date - datetime.now()).days <= days

    def opened_expiry_date(self):
        if not self.opened_date:
            return None
        # Longer-lasting items get 7 days, otherwise 3
        shelf_life = 7 if any(item in self.name.lower() for item in longer_lasting_items) else 3
        return self.opened_date + timedelta(days=shelf_life)

    def days_until_opened_expiry(self):
        exp = self.opened_expiry_date()
        if not exp:
            return None
        return (exp - datetime.now()).days

    def __repr__(self):
        status = '✅ Bought' if self.bought else '🕒 Pending'
        expiry = self.expiry_date.strftime("%Y-%m-%d") if self.expiry_date else "N/A"
        opened = self.opened_date.strftime("%Y-%m-%d") if self.opened_date else "Not opened"
        return f"{self.name} ({self.category}) - {status} | ${self.price:.2f} | Expiry: {expiry} | Opened: {opened}"

class GroceryList:
    def __init__(self):
        self.items = []

    def add_item(self, name, category, price, expiry_date):
        item = GroceryItem(name, category, price, expiry_date)
        self.items.append(item)

    def mark_as_bought(self, name):
        for item in self.items:
            if item.name.lower() == name.lower() and not item.bought:
                item.mark_as_bought()
                return item
        return None

    def mark_as_opened(self, name):
        for item in self.items:
            if item.name.lower() == name.lower() and item.bought and not item.opened_date:
                item.mark_as_opened()
                return item
        return None

    def get_items(self, bought=None):
        if bought is None:
            return self.items
        return [item for item in self.items if item.bought == bought]

    def get_expiring_items(self, days=3):
        return [item for item in self.items if not item.bought and item.is_expiring_soon(days)]
        
    def get_opened_items_expiring_tomorrow(self):
        alert_list = []
        for item in self.items:
            days = item.days_until_opened_expiry()
            if days == 1:
                alert_list.append(item)
        return alert_list

class PurchaseHistory:
    def __init__(self):
        self.history = defaultdict(list)
        self.total_spent = 0.0

    def record_purchase(self, item):
        date_str = datetime.now().strftime("%Y-%m-%d")
        self.history[date_str].append(item)
        self.total_spent += item.price

    def display_chart(self):
        if not self.history:
            st.write("No purchase data yet.")
            return
        dates = sorted(self.history.keys())
        counts = [len(self.history[date]) for date in dates]
        fig, ax = plt.subplots()
        ax.bar(dates, counts)
        ax.set_title("Items Bought Per Day")
        ax.set_xlabel("Date")
        ax.set_ylabel("Count")
        plt.xticks(rotation=45)
        st.pyplot(fig)

# --- Streamlit App ---

st.set_page_config(page_title="Grocery Tracker", layout="centered")
st.title("🛒 Grocery Manager & Inventory Tracker")

if 'grocery_list' not in st.session_state:
    st.session_state.grocery_list = GroceryList()

if 'purchase_history' not in st.session_state:
    st.session_state.purchase_history = PurchaseHistory()

with st.sidebar:
    st.header("➕ Add Grocery Item")
    name = st.text_input("Item name")
    category = st.text_input("Category")
    price = st.number_input("Price", min_value=0.0, step=0.1)
    expiry = st.date_input("Expiry date (optional)", value=None)
    if st.button("Add Item"):
        expiry_dt = datetime.combine(expiry, datetime.min.time()) if expiry else None
        st.session_state.grocery_list.add_item(name, category, price, expiry_dt)
        st.success(f"Added item: {name}")

# --- Opened Food Expiry Alerts ---
alerts = st.session_state.grocery_list.get_opened_items_expiring_tomorrow()
if alerts:
    st.warning("⚠️ The following opened items will expire tomorrow:")
    for item in alerts:
        st.write(f"🔔 {item.name} (Opened on {item.opened_date.strftime('%Y-%m-%d')})")

# --- Pending Items ---
st.subheader("📦 Pending Items")
for item in st.session_state.grocery_list.get_items(bought=False):
    if st.button(f"✅ Mark as Bought: {item.name}", key=f"buy_{item.name}"):
        updated = st.session_state.grocery_list.mark_as_bought(item.name)
        if updated:
            st.session_state.purchase_history.record_purchase(updated)
            st.rerun()

if not st.session_state.grocery_list.get_items(bought=False):
    st.write("🎉 No pending items!")

# --- Bought Items ---
st.subheader("✅ Bought Items (Click to mark as opened)")
for item in st.session_state.grocery_list.get_items(bought=True):
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"- {item}")
    with col2:
        if not item.opened_date:
            if st.button("📤 Open", key=f"open_{item.name}"):
                st.session_state.grocery_list.mark_as_opened(item.name)
                st.rerun()

# --- Expiring Soon ---
st.subheader("⏰ Expiring Soon (within 3 days)")
expiring = st.session_state.grocery_list.get_expiring_items()
if expiring:
    for item in expiring:
        st.warning(f"{item}")
else:
    st.write("✅ No items expiring soon!")

# --- Money and Stats ---
st.subheader("💰 Money Spent")
st.write(f"Total spent: ${st.session_state.purchase_history.total_spent:.2f}")

st.subheader("📊 Purchase Chart")
st.session_state.purchase_history.display_chart()
