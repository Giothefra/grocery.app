import streamlit as st
from datetime import datetime, timedelta
from collections import defaultdict
import matplotlib.pyplot as plt

# --- Core Classes with Inheritance and Encapsulation --- #

class BaseItem:
    def __init__(self, name, category):
        self.__name = name
        self.__category = category

    @property
    def name(self):
        return self.__name

    @property
    def category(self):
        return self.__category


class GroceryItem(BaseItem):
    def __init__(self, name, category, price=0.0, expiry_date=None):
        super().__init__(name, category)
        self.__price = price
        self.__bought = False
        self.__added_on = datetime.now()
        self.__expiry_date = expiry_date

    def mark_as_bought(self):
        self.__bought = True

    def is_bought(self):
        return self.__bought

    def is_expiring_soon(self, days=3):
        if self.__expiry_date is None:
            return False
        return 0 <= (self.__expiry_date - datetime.now()).days <= days

    def get_price(self):
        return self.__price

    def get_expiry_date(self):
        return self.__expiry_date

    def __repr__(self):
        status = '✅ Bought' if self.__bought else '🕒 Pending'
        expiry = self.__expiry_date.strftime("%Y-%m-%d") if self.__expiry_date else "N/A"
        return f"{self.name} ({self.category}) - {status} | ${self.__price:.2f} | Expiry: {expiry}"


class GroceryList:
    def __init__(self):
        self.__items = []

    def add_item(self, name, category, price, expiry_date):
        item = GroceryItem(name, category, price, expiry_date)
        self.__items.append(item)

    def mark_as_bought(self, name):
        for item in self.__items:
            if item.name.lower() == name.lower() and not item.is_bought():
                item.mark_as_bought()
                return item
        return None

    def get_items(self, bought=None):
        if bought is None:
            return self.__items
        return [item for item in self.__items if item.is_bought() == bought]

    def get_expiring_items(self, days=3, include_bought=True):
        return [
            item for item in self.__items
            if item.is_expiring_soon(days) and (include_bought or not item.is_bought())
        ]


class PurchaseHistory:
    def __init__(self):
        self.__history = defaultdict(list)
        self.__total_spent = 0.0

    def record_purchase(self, item):
        date_str = datetime.now().strftime("%Y-%m-%d")
        self.__history[date_str].append(item)
        self.__total_spent += item.get_price()

    def get_total_spent(self):
        return self.__total_spent

    def display_chart(self):
        if not self.__history:
            st.write("No purchase data yet.")
            return
        dates = sorted(self.__history.keys())
        counts = [len(self.__history[date]) for date in dates]
        fig, ax = plt.subplots()
        ax.bar(dates, counts)
        ax.set_title("Items Bought Per Day")
        ax.set_xlabel("Date")
        ax.set_ylabel("Count")
        plt.xticks(rotation=45)
        st.pyplot(fig)

# --- Streamlit App UI --- #

st.set_page_config(page_title="Grocery Tracker", layout="centered")
st.title("🛒 Grocery Manager & Inventory Tracker")

# Session state
if 'grocery_list' not in st.session_state:
    st.session_state.grocery_list = GroceryList()

if 'purchase_history' not in st.session_state:
    st.session_state.purchase_history = PurchaseHistory()

# Sidebar to add new items
with st.sidebar:
    st.header("➕ Add Grocery Item")
    name = st.text_input("Item name")
    category = st.text_input("Category")
    price = st.number_input("Price", min_value=0.0, step=0.1)
    expiry = st.date_input("Expiry date (optional)")
    if st.button("Add Item"):
        expiry_dt = datetime.combine(expiry, datetime.min.time()) if expiry else None
        st.session_state.grocery_list.add_item(name, category, price, expiry_dt)
        st.success(f"Added item: {name}")

# Pending items section using while loop
st.subheader("📦 Pending Items")
pending_items = st.session_state.grocery_list.get_items(bought=False)
i = 0
while i < len(pending_items):
    item = pending_items[i]
    if st.button(f"✅ Mark as Bought: {item.name}", key=f"buy_{item.name}_{i}"):
        updated = st.session_state.grocery_list.mark_as_bought(item.name)
        if updated:
            st.session_state.purchase_history.record_purchase(updated)
            st.rerun()
    i += 1

if not pending_items:
    st.write("🎉 No pending items!")

# Bought items section
st.subheader("✅ Bought Items")
bought_items = st.session_state.grocery_list.get_items(bought=True)
if bought_items:
    for item in bought_items:
        st.write("-", item)
else:
    st.info("No items bought yet.")

# Expiring soon (now includes bought items too)
st.subheader("⏰ Expiring Soon (within 3 days)")
expiring_items = st.session_state.grocery_list.get_expiring_items(include_bought=True)
if expiring_items:
    for item in expiring_items:
        days_left = (item.get_expiry_date() - datetime.now()).days
        label = f"{item} (Already bought)" if item.is_bought() else str(item)
        if days_left < 0:
            st.error(f"❌ Expired: {label}")
        elif days_left == 0:
            st.warning(f"⚠️ Expires today: {label}")
        elif days_left == 1:
            st.warning(f"⚠️ Expires tomorrow: {label}")
        else:
            st.info(f"📅 Expires in {days_left} days: {label}")
else:
    st.success("✅ No items expiring soon!")

# Total spending section
st.subheader("💰 Money Spent")
total = st.session_state.purchase_history.get_total_spent()
if total > 0:
    st.write(f"Total spent: **${total:.2f}**")
elif total == 0:
    st.write("You haven't spent anything yet.")
else:
    st.warning("⚠️ Spending total seems off.")

# Purchase chart
st.subheader("📊 Purchase Chart")
st.session_state.purchase_history.display_chart()
