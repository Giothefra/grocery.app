# Grocery Manager & Inventory Tracker
# This app helps users manage grocery items, track expiry dates, and monitor spending.
# It uses object-oriented programming (OOP) with classes, encapsulation, and inheritance.

import streamlit as st  # Streamlit is a framework to build web apps easily in Python.
from datetime import datetime, timedelta  # Used for dates, times, and checking expiration.
from collections import defaultdict  # A special dictionary from the collections module.
import matplotlib.pyplot as plt  # Imported for plotting (not used in this version).


# BaseItem class holds shared attributes for items (name and category).
class BaseItem:
    def __init__(self, name, category):
        self.__name = name  # Private attribute for the name of the item.
        self.__category = category  # Private attribute for the item's category.

    # Getter for name
    @property   # @property decorator helps you access private attributes safely.
    def name(self):
        return self.__name

    # Getter for category
    @property   # @property decorator helps you access private attributes safely.
    def category(self):
        return self.__category

# GroceryItem class inherits from BaseItem and adds price, bought status, and expiry info.
class GroceryItem(BaseItem):
    def __init__(self, name, category, price=0.0, expiry_date=None):
        super().__init__(name, category)  # super() calls the constructor (__init__) of the parent class (BaseItem) to set the common attributes 'name' and 'category'.
        self.__price = price  # Private attribute for price.
        self.__bought = False  # Private attribute to track if item is bought.
        self.__added_on = datetime.now()  # Store the time the item was added.
        self.__expiry_date = expiry_date  # Optional expiry date.

    # Mark the item as bought.
    def mark_as_bought(self):
        self.__bought = True

    # Check if the item has been bought.
    def is_bought(self):
        return self.__bought

    # Check if the item is expiring soon (default: 3 days).
    def is_expiring_soon(self, days=3):
        if self.__expiry_date is None:
            return False  # If there's no expiry date, it can't expire.

        return 0 <= (self.__expiry_date.date() - datetime.now().date()).days <= days

    # Getter for price
    def get_price(self):
        return self.__price

    # Getter for expiry date
    def get_expiry_date(self):
        return self.__expiry_date

    # How the item is displayed when printed.
    def __repr__(self):
        status = '✅ Bought' if self.__bought else '🕒 Pending'
        expiry = self.__expiry_date.strftime("%Y-%m-%d") if self.__expiry_date else "N/A"
        return f"{self.name} ({self.category}) - {status} | ${self.__price:.2f} | Expiry: {expiry}"

# GroceryList class manages all the grocery items in a list.
class GroceryList:
    def __init__(self):
        self.__items = []  # Private list of all items.

    # Add a new item to the list.
    def add_item(self, name, category, price, expiry_date):
        item = GroceryItem(name, category, price, expiry_date)
        self.__items.append(item)

    # Mark a specific item as bought.
    def mark_as_bought(self, name):
        for item in self.__items:
            if item.name.lower() == name.lower() and not item.is_bought():
                item.mark_as_bought()
                return item  # Return the item after updating.
        return None  # If no item found.

    # Get items based on bought status: True, False, or None (all).
    def get_items(self, bought=None):
        if bought is None:
            return self.__items
        return [item for item in self.__items if item.is_bought() == bought]

    # Get all items that are expiring soon.
    def get_expiring_items(self, days=3, include_bought=True):
        return [
            item for item in self.__items
            if item.is_expiring_soon(days) and (include_bought or not item.is_bought())
        ]

# PurchaseHistory class stores past purchases and calculates total spent.
class PurchaseHistory:
    def __init__(self):
        self.__history = defaultdict(list)  # Dictionary to group items by date.
        self.__total_spent = 0.0  # Private variable to track total spending.

    # Add an item to the purchase history.
    def record_purchase(self, item):
        date_str = datetime.now().strftime("%Y-%m-%d")  # Use today's date as key.
        self.__history[date_str].append(item)
        self.__total_spent += item.get_price()  # Add item price to total.

    # Get total money spent so far.
    def get_total_spent(self):
        return self.__total_spent

# ------------------- STREAMLIT APP LOGIC ------------------- #

# Set page title and layout.
st.set_page_config(page_title="Grocery Tracker", layout="centered")

# Display app title
st.title("🛒 Grocery Manager & Inventory Tracker")

# Initialize session state objects to keep data across interactions.
if 'grocery_list' not in st.session_state:
    st.session_state.grocery_list = GroceryList()

if 'purchase_history' not in st.session_state:
    st.session_state.purchase_history = PurchaseHistory()

# Sidebar section for adding new items
with st.sidebar:
    st.header("➕ Add Grocery Item")
    name = st.text_input("Item name")  # Text input for item name
    category = st.text_input("Category")  # Text input for category
    price = st.number_input("Price", min_value=0.0, step=0.1)  # Price input
    expiry = st.date_input("Expiry date (optional)")  # Expiry date

    # When 'Add Item' button is clicked
    if st.button("Add Item"):
        expiry_dt = datetime.combine(expiry, datetime.min.time()) if expiry else None
        st.session_state.grocery_list.add_item(name, category, price, expiry_dt)
        st.success(f"Added item: {name}")

# Section for pending (not yet bought) items
st.subheader("📦 Pending Items")
pending_items = st.session_state.grocery_list.get_items(bought=False)
i = 0
while i < len(pending_items):
    item = pending_items[i]
    # Add a button to mark each item as bought
    if st.button(f"✅ Mark as Bought: {item.name}", key=f"buy_{item.name}_{i}"):
        updated = st.session_state.grocery_list.mark_as_bought(item.name)
        if updated:
            st.session_state.purchase_history.record_purchase(updated)
            st.rerun()  # Refresh the app to update state
    i += 1

if not pending_items:
    st.write("🎉 No pending items!")

# Section for items that have already been bought
st.subheader("✅ Bought Items")
bought_items = st.session_state.grocery_list.get_items(bought=True)
if bought_items:
    for item in bought_items:
        st.write("-", item)
else:
    st.info("No items bought yet.")

# Section for showing expiring soon items (within 3 days)
st.subheader("⏰ Expiring Soon (within 3 days)")
expiring_items = st.session_state.grocery_list.get_expiring_items(include_bought=True)
if expiring_items:
    for item in expiring_items:
        # ✅ Fix: compare date only
        days_left = (item.get_expiry_date().date() - datetime.now().date()).days
        label = f"{item} (Already bought)" if item.is_bought() else str(item)

        # Show different messages based on days left
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

# Display total money spent
st.subheader("💰 Money Spent")
total = st.session_state.purchase_history.get_total_spent()
if total > 0:
    st.write(f"Total spent: **${total:.2f}**")
elif total == 0:
    st.write("You haven't spent anything yet.")
else:
    st.warning("⚠️ Spending total seems off.")
