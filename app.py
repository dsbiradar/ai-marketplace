import streamlit as st
import pandas as pd
import hashlib
import sqlite3
from time import time
from sklearn.metrics.pairwise import cosine_similarity

# ----------------------
# PAGE CONFIG + STYLE
# ----------------------
st.set_page_config(page_title="AI Marketplace", layout="wide")

st.markdown("""
<style>
.main {background-color: #f5f5f5;}
.stButton>button {
    background-color: #ff9900;
    color: white;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

st.title("🛒 AI Powered Marketplace with Blockchain")

st.image("https://via.placeholder.com/1200x200.png?text=AI+Marketplace", use_column_width=True)

# ----------------------
# DATABASE
# ----------------------
conn = sqlite3.connect("market.db", check_same_thread=False)
c = conn.cursor()

c.execute("CREATE TABLE IF NOT EXISTS users(username TEXT, password TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS purchases(user TEXT, product TEXT)")
conn.commit()

# ----------------------
# DATA
# ----------------------
products = [
("Laptop","Computing",50000,1,0,1,1),
("Mouse","Accessories",500,0,1,1,0),
("Keyboard","Accessories",1000,0,1,0,0),
("Phone","Mobile",20000,1,0,1,1),
("Headphones","Audio",2000,0,1,1,1),
("Smart TV","Entertainment",30000,1,0,0,1)
]

data = pd.DataFrame(products, columns=["product","category","price","f1","f2","f3","f4"])

# ----------------------
# SESSION
# ----------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user" not in st.session_state:
    st.session_state.user = ""

if "blockchain" not in st.session_state:
    st.session_state.blockchain = []

if "cart" not in st.session_state:
    st.session_state.cart = []

# ----------------------
# BLOCKCHAIN
# ----------------------
def add_block(data_text):
    prev_hash = hashlib.sha256(str(st.session_state.blockchain[-1]).encode()).hexdigest() if st.session_state.blockchain else "0"
    block = {
        "index": len(st.session_state.blockchain)+1,
        "timestamp": str(time()),
        "data": data_text,
        "prev_hash": prev_hash
    }
    st.session_state.blockchain.append(block)

# ----------------------
# AI RECOMMENDATION
# ----------------------
def recommend(product):
    sim = cosine_similarity(data.iloc[:,3:])
    idx = data[data["product"] == product].index[0] if product in data["product"].values else 0
    scores = sorted(list(enumerate(sim[idx])), key=lambda x: x[1], reverse=True)
    return [data.iloc[i[0]]["product"] for i in scores[1:4]]

# ----------------------
# LOGIN
# ----------------------
st.sidebar.title("👤 Account")
menu = st.sidebar.radio("Choose", ["Signup","Login"])

uname = st.sidebar.text_input("Username")
pwd = st.sidebar.text_input("Password", type="password")

if menu == "Signup":
    if st.sidebar.button("Signup"):
        c.execute("SELECT * FROM users WHERE username=?", (uname,))
        if c.fetchone():
            st.sidebar.error("User exists")
        else:
            c.execute("INSERT INTO users VALUES (?,?)",(uname,pwd))
            conn.commit()
            st.sidebar.success("Account created!")

if menu == "Login":
    if st.sidebar.button("Login"):
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (uname,pwd))
        if c.fetchone():
            st.session_state.logged_in = True
            st.session_state.user = uname
            st.rerun()
        else:
            st.sidebar.error("Invalid login")

# ----------------------
# MAIN APP
# ----------------------
if st.session_state.logged_in:

    st.success(f"Welcome {st.session_state.user} 👋")

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    # ADD PRODUCT
    st.subheader("➕ Add Product")
    new_p = st.text_input("Product Name")
    new_c = st.text_input("Category")
    new_price = st.number_input("Price", min_value=0)

    if st.button("Add Product"):
        if new_p and new_c:
            data.loc[len(data)] = [new_p,new_c,new_price,1,1,1,1]
            st.success("Product added!")

    # SEARCH
    search = st.text_input("🔍 Search")
    filtered = data[data["product"].str.contains(search, case=False)] if search else data

    st.subheader("🔥 Products")

    # PRODUCT CARDS
    for i in range(0,len(filtered),3):
        cols = st.columns(3)
        for col,(_,row) in zip(cols, filtered.iloc[i:i+3].iterrows()):
            with col:
                st.image("https://via.placeholder.com/150")
                st.write(f"**{row['product']}**")
                st.write(row["category"])
                st.write(f"₹{row['price']}")

                if st.button(f"Add to Cart {row['product']}"):
                    st.session_state.cart.append(row["product"])

    # CART
    st.subheader("🛒 Cart")
    st.write(st.session_state.cart)

    # BUY
    st.subheader("🛍 Buy Product")
    product = st.text_input("Enter ANY product")

    rating = st.slider("⭐ Rating",1,5)
    review = st.text_area("Write Review")

    if st.button("Buy Now"):
        if product not in data["product"].values:
            data.loc[len(data)] = [product,"Custom",1000,1,1,1,1]

        c.execute("INSERT INTO purchases VALUES (?,?)",(st.session_state.user,product))
        conn.commit()

        add_block(f"{st.session_state.user} bought {product}")

        st.success(f"{product} purchased!")

        rec = recommend(product)

        st.write("🤖 Recommended:")
        for r in rec:
            st.write("-", r)

        st.success("Review submitted!")

    # HISTORY
    st.subheader("📜 Purchase History")
    hist = pd.read_sql(f"SELECT * FROM purchases WHERE user='{st.session_state.user}'", conn)
    st.dataframe(hist)

    # ANALYTICS
    st.subheader("📊 Analytics")
    if not hist.empty:
        st.bar_chart(hist["product"].value_counts())

    # BLOCKCHAIN
    st.subheader("⛓ Blockchain")
    for block in st.session_state.blockchain:
        st.markdown(f"""
        ### 🔗 Block {block['index']}
        - ⏱ {block['timestamp']}
        - 📦 {block['data']}
        - 🔐 {block['prev_hash'][:10]}...
        """)

else:
    st.warning("Login first")