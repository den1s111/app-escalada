import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# ─── CONFIG & DB ───────────────────────────────────────────────────────────────

load_dotenv()
st.set_page_config(
    page_title="Climbing Database Management",
    page_icon="🧗‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_resource
def init_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432")
    )

@st.cache_data(ttl=600)
def run_query(query, params=None, fetch=True):
    conn = init_connection()
    with conn.cursor() as cur:
        cur.execute(query, params)
        if fetch:
            return cur.fetchall()
        conn.commit()

def run_query_no_cache(query, params=None):
    conn = init_connection()
    with conn.cursor() as cur:
        cur.execute(query, params)
        conn.commit()

# ─── SESSION STATE FOR AUTH ────────────────────────────────────────────────────

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = ""

# ─── LOGIN / REGISTER PAGE ─────────────────────────────────────────────────────

if not st.session_state.authenticated:
    st.title("🧗‍♂️ Climbing App — Login / Register")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        st.subheader("Login")
        login_user = st.text_input("Username", key="login_user")
        login_pass = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            result = run_query(
                'SELECT nom_usuari FROM practica.escalador WHERE nom_usuari = %s AND contrasenya = %s',
                (login_user, login_pass)
            )
            if result:
                st.success(f"Welcome back, {login_user}!")
                st.session_state.authenticated = True
                st.session_state.username = login_user
                st.stop()
            else:
                st.error("Invalid username or password.")

    with tab2:
        st.subheader("Register")
        reg_user  = st.text_input("New Username", key="reg_user")
        reg_pass  = st.text_input("New Password", type="password", key="reg_pass")
        reg_dob   = st.date_input("Date of Birth", key="reg_dob")
        reg_level = st.selectbox(
            "Climbing Level",
            [
                "Principiant",
                "Iniciació",
                "Intermedi",
                "Avançat",
                "Expert",
                "Pro"
            ],
            key="reg_level"
        )

        if st.button("Register"):
            if not (reg_user and reg_pass):
                st.warning("Username and password are required.")
            else:
                try:
                    run_query_no_cache(
                        'INSERT INTO practica.escalador (nom_usuari, contrasenya, data_naixement, nivell) '
                        'VALUES (%s, %s, %s, %s)',
                        (reg_user, reg_pass, reg_dob, reg_level)
                    )
                    st.success("Registration successful! Please log in.")
                except Exception as e:
                    st.error(f"Registration failed: {e}")

    st.stop()


# ─── MAIN APP — AFTER LOGIN ────────────────────────────────────────────────────

# Logout button
if st.sidebar.button("Logout"):
    st.success(f"Logging out, {st.session_state.username}!")
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.stop()

st.sidebar.title(f"Hello, {st.session_state.username}!")
page = st.sidebar.radio(
    "Select a page",
    ["Dashboard", "Crags", "Sectors", "Routes", "Attempts", "Comments", "Recommendations"]
)

# ─── DASHBOARD ─────────────────────────────────────────────────────────────────

if page == "Dashboard":
    st.header("Dashboard")

    col1, col2, col3, col4 = st.columns(4)
    crags_count    = run_query("SELECT COUNT(*) FROM practica.crag")[0][0]
    routes_count   = run_query("SELECT COUNT(*) FROM practica.via")[0][0]
    climbers_count = run_query("SELECT COUNT(*) FROM practica.escalador")[0][0]
    attempts_count = run_query("SELECT COUNT(*) FROM practica.intent")[0][0]

    col1.metric("Total Crags", crags_count)
    col2.metric("Total Routes", routes_count)
    col3.metric("Registered Climbers", climbers_count)
    col4.metric("Total Attempts", attempts_count)

    # ... rest of your dashboard charts & recent activity ...

# ─── CRAGS PAGE ────────────────────────────────────────────────────────────────

elif page == "Crags":
    st.header("Crags Management")
    tab1, tab2, tab3 = st.tabs(["View", "Add", "Edit/Delete"])

    with tab1:
        crags = run_query("SELECT nom, localitzacio, descripcio FROM practica.crag ORDER BY nom")
        if crags:
            df = pd.DataFrame(crags, columns=["Name","Location","Description"])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No crags available")

    with tab2:
        with st.form("add_crag"):
            name = st.text_input("Name*")
            loc  = st.text_area("Location")
            desc = st.text_area("Description")
            if st.form_submit_button("Add"):
                if name:
                    try:
                        run_query_no_cache(
                            "INSERT INTO practica.crag(nom, localitzacio, descripcio) VALUES(%s,%s,%s)",
                            (name, loc, desc)
                        )
                        st.success("Added!")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"{e}")
                else:
                    st.warning("Name required")

    with tab3:
        crag_list = run_query("SELECT nom FROM practica.crag ORDER BY nom")
        if crag_list:
            names = [c[0] for c in crag_list]
            sel   = st.selectbox("Select Crag", names)
            data  = run_query("SELECT localitzacio, descripcio FROM practica.crag WHERE nom=%s",(sel,))
            if data:
                with st.form("edit_crag"):
                    loc_new  = st.text_area("Location", value=data[0][0] or "")
                    desc_new = st.text_area("Description", value=data[0][1] or "")
                    upd = st.form_submit_button("Update")
                    dl  = st.form_submit_button("Delete")
                    if upd:
                        run_query_no_cache(
                            "UPDATE practica.crag SET localitzacio=%s,descripcio=%s WHERE nom=%s",
                            (loc_new, desc_new, sel)
                        )
                        st.success("Updated"); st.experimental_rerun()
                    if dl:
                        run_query_no_cache("DELETE FROM practica.crag WHERE nom=%s",(sel,))
                        st.success("Deleted"); st.experimental_rerun()
        else:
            st.info("Add a crag first.")

# ─── SECTORS ───────────────────────────────────────────────────────────────────

elif page == "Sectors":
    st.header("Sectors Management")
    # ... your existing Sectors tab code ...

# ─── ROUTES ────────────────────────────────────────────────────────────────────

elif page == "Routes":
    st.header("Routes Management")
    # ... your existing Routes tab code ...

# ─── ATTEMPTS, COMMENTS, RECOMMENDATIONS ───────────────────────────────────────

elif page == "Attempts":
    st.header("Your Attempts")
    # ... query & insert attempts ...

elif page == "Comments":
    st.header("Comments")
    # ... your comments code ...

elif page == "Recommendations":
    st.header("Recommendations")
    # ... your recos code ...
