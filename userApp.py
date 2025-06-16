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
    ["Dashboard", "Route Searcher", "Profile"]
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
    
    st.markdown("---")
    st.subheader("Previous Month’s Route Activity")

    month_stats = run_query(
        """
        SELECT
            i.nom_via         AS via,
            i.nom_sector_via  AS sector,
            i.nom_crag_via    AS crag,
            TO_CHAR(i.data_intent, 'YYYY-MM') AS mes_any,
            COUNT(DISTINCT i.id_intent)      AS total_intents,
            COUNT(DISTINCT r.id_recomanacio) AS total_recomanacions,
            ROUND(AVG(r.puntuacio)::numeric, 2) AS puntuacio_mitjana,
            COUNT(DISTINCT c.id_comentari)    AS total_comentaris
        FROM practica.intent i
        LEFT JOIN practica.recomanacio r
        ON i.nom_via        = r.nom_via
        AND i.nom_sector_via = r.nom_sector_via
        AND i.nom_crag_via   = r.nom_crag_via
        AND date_trunc('month', i.data_intent)
            = date_trunc('month', r.data_recomanacio)
        LEFT JOIN practica.comentari c
        ON i.nom_via        = c.nom_via
        AND i.nom_sector_via = c.nom_sector_via
        AND i.nom_crag_via   = c.nom_crag_via
        AND date_trunc('month', i.data_intent)
            = date_trunc('month', c.data_comentari)
        WHERE date_trunc('month', i.data_intent)
            = (date_trunc('month', CURRENT_DATE) - INTERVAL '1 month')
        GROUP BY
            i.nom_via,
            i.nom_sector_via,
            i.nom_crag_via,
            TO_CHAR(i.data_intent, 'YYYY-MM')
        ORDER BY total_intents DESC
        """
    )

    if month_stats:
        df_month = pd.DataFrame(
            month_stats,
            columns=[
                "Route", "Sector", "Crag", "Month",
                "Intents", "Recommendations", "Avg. Rating", "Comments"
            ]
        )
        st.dataframe(df_month, use_container_width=True)
    else:
        st.info("No activity in the previous month.")
    

# ─── CRAGS PAGE ────────────────────────────────────────────────────────────────

elif page == "Route Searcher":
    st.header("🔍 Route Searcher")

    # 1) Select a Crag
    crag_list = run_query("SELECT nom FROM practica.crag ORDER BY nom")
    if not crag_list:
        st.info("No crags available.")
    else:
        crag_names = [r[0] for r in crag_list]
        selected_crag = st.selectbox("Choose a Crag", ["–"] + crag_names)
        
        if selected_crag and selected_crag != "–":
            # 2) Select a Sector in that Crag
            sector_list = run_query(
                "SELECT nom FROM practica.sector WHERE nom_crag = %s ORDER BY nom",
                (selected_crag,)
            )
            if not sector_list:
                st.info(f"No sectors for crag '{selected_crag}'.")
            else:
                sector_names = [r[0] for r in sector_list]
                selected_sector = st.selectbox("Choose a Sector", ["–"] + sector_names)
                
                if selected_sector and selected_sector != "–":
                    # 3) Select a Route in that Sector
                    route_list = run_query(
                        "SELECT nom FROM practica.via WHERE nom_crag_sector = %s AND nom_sector = %s ORDER BY nom",
                        (selected_crag, selected_sector)
                    )
                    if not route_list:
                        st.info(f"No routes in sector '{selected_sector}'.")
                    else:
                        route_names = [r[0] for r in route_list]
                        selected_route = st.selectbox("Choose a Route", ["–"] + route_names)
                        
                        if selected_route and selected_route != "–":
                            # 4) Show route details
                            st.subheader(f"Route: {selected_route}")
                            route_info = run_query(
                                """
                                SELECT descripcio, grau_dificultat, estil,
                                       alcada_aproximada_metres, equipador, data_equipament
                                FROM practica.via
                                WHERE nom_crag_sector=%s AND nom_sector=%s AND nom=%s
                                """,
                                (selected_crag, selected_sector, selected_route)
                            )[0]
                            desc, grade, style, height, equipper, eq_date = route_info
                            st.markdown(f"**Description:** {desc or '—'}")
                            st.markdown(f"**Difficulty:** {grade or '—'}")
                            st.markdown(f"**Style:** {style or '—'}")
                            st.markdown(f"**Height:** {height or '—'} m")
                            st.markdown(f"**Equipper:** {equipper or '—'}")
                            st.markdown(f"**Equipped on:** {eq_date or '—'}")

                            # 4.1) Show Average Rating
                            avg_rating = run_query(
                                """
                                SELECT ROUND(AVG(puntuacio)::numeric, 2)
                                FROM practica.recomanacio
                                WHERE nom_via=%s AND nom_sector_via=%s AND nom_crag_via=%s
                                """,
                                (selected_route, selected_sector, selected_crag)
                            )[0][0] or 0.0

                            st.metric("⭐ Avg. Rating", f"{avg_rating} / 5")

                            st.markdown("---")

                            # 4.2) Four action buttons
                            col_a, col_b, col_c, col_d = st.columns(4)

                            show_attempts = col_a.button("Attempts", key="btn_attempts")
                            show_completions = col_b.button("Completions", key="btn_completions")
                            show_comments = col_c.button("Comments", key="btn_comments")
                            show_recos = col_d.button("Recommendations", key="btn_recos")

                            st.markdown("---")

                            # 4.3) Conditionally display each section
                            if show_attempts:
                                st.subheader("🗒️ Attempts")
                                attempts = run_query(
                                    """
                                    SELECT tipus_ascensio, data_intent, nom_usuari_escalador
                                    FROM practica.intent
                                    WHERE nom_via=%s AND nom_sector_via=%s AND nom_crag_via=%s
                                    ORDER BY data_intent DESC
                                    """,
                                    (selected_route, selected_sector, selected_crag)
                                )
                                if attempts:
                                    df_att = pd.DataFrame(attempts, columns=["Type", "Date", "Climber"])
                                    st.dataframe(df_att, use_container_width=True)
                                else:
                                    st.info("No attempts logged yet.")

                            elif show_completions:
                                st.subheader("✅ Completions")
                                completions = run_query(
                                    """
                                    SELECT e.temps_ascensio, i.data_intent, i.nom_usuari_escalador
                                    FROM practica.encadenament e
                                    JOIN practica.intent i ON e.id_intent = i.id_intent
                                    WHERE i.nom_via=%s AND i.nom_sector_via=%s AND i.nom_crag_via=%s
                                    ORDER BY i.data_intent DESC
                                    """,
                                    (selected_route, selected_sector, selected_crag)
                                )
                                if completions:
                                    df_comp = pd.DataFrame(
                                        [(str(c[0]), c[1], c[2]) for c in completions],
                                        columns=["Time Spent", "Date", "Climber"]
                                    )
                                    st.dataframe(df_comp, use_container_width=True)
                                else:
                                    st.info("No completions recorded yet.")

                            elif show_comments:
                                st.subheader("💬 Comments")
                                comments = run_query(
                                    """
                                    SELECT text_comentari, nom_usuari_escalador, data_comentari
                                    FROM practica.comentari
                                    WHERE nom_via=%s AND nom_sector_via=%s AND nom_crag_via=%s
                                    ORDER BY data_comentari DESC
                                    """,
                                    (selected_route, selected_sector, selected_crag)
                                )
                                if comments:
                                    df_com = pd.DataFrame(comments, columns=["Comment", "Climber", "Date"])
                                    st.dataframe(df_com, use_container_width=True)
                                else:
                                    st.info("No comments yet.")

                            elif show_recos:
                                st.subheader("🌟 Recommendations")
                                recos = run_query(
                                    """
                                    SELECT puntuacio, descripcio_recomanacio, nom_usuari_escalador, data_recomanacio
                                    FROM practica.recomanacio
                                    WHERE nom_via=%s AND nom_sector_via=%s AND nom_crag_via=%s
                                    ORDER BY data_recomanacio DESC
                                    """,
                                    (selected_route, selected_sector, selected_crag)
                                )
                                if recos:
                                    df_rec = pd.DataFrame(recos, columns=["Rating","Note","Climber","Date"])
                                    st.dataframe(df_rec, use_container_width=True)
                                else:
                                    st.info("No recommendations yet.")
                            
                            st.markdown("---")

                            # 5) Add your own Attempt
                            st.subheader("⛰️ Log a New Attempt")

                            att_type      = st.selectbox("Ascent Type", ["A vista","Flash","Assajat","Top-rope"])
                            att_date      = st.date_input("Date of Attempt", key="att_date")
                            completed_chk = st.checkbox("Route completed?", key="att_completed")

                            # Only show duration if completed
                            if completed_chk:
                                # use time_input to pick HH:MM:SS
                                time_spent = st.time_input("Time Spent (HH:MM:SS)", value=datetime.strptime("00:00:00", "%H:%M:%S").time(), key="att_time")

                            if st.button("Submit Attempt"):
                                try:
                                    # 1) insert into intent and return its new id_intent
                                    insert_intent_sql = """
                                        INSERT INTO practica.intent
                                        (tipus_ascensio, data_intent, nom_usuari_escalador,
                                        nom_via, nom_sector_via, nom_crag_via)
                                        VALUES (%s, %s, %s, %s, %s, %s)
                                        RETURNING id_intent
                                    """
                                    intent_id = run_query(insert_intent_sql, (
                                        att_type, att_date,
                                        st.session_state.username,
                                        selected_route,
                                        selected_sector,
                                        selected_crag
                                    ))[0][0]

                                    # 2) if completed, insert into encadenament
                                    if completed_chk:
                                        # convert time_spent (datetime.time) to interval string "HH:MM:SS"
                                        duration_str = time_spent.strftime("%H:%M:%S")
                                        run_query_no_cache(
                                            """
                                            INSERT INTO practica.encadenament (id_intent, temps_ascensio)
                                            VALUES (%s, %s)
                                            """,
                                            (intent_id, duration_str)
                                        )

                                    st.success("Attempt logged!" + (" Completion recorded." if completed_chk else ""))
                                    run_query.clear(); st.rerun()
                                except Exception as e:
                                    st.error(f"Failed to log attempt: {e}")
                            st.markdown("---")

                            # 6) Add a Comment
                            st.subheader("💬 Leave a Comment")
                            comment = st.text_area("Your comment", key="comment")
                            if st.button("Submit Comment"):
                                try:
                                    run_query_no_cache(
                                        """
                                        INSERT INTO practica.comentari
                                        (text_comentari, nom_usuari_escalador,
                                         nom_via, nom_sector_via, nom_crag_via)
                                        VALUES (%s, %s, %s, %s, %s)
                                        """,
                                        (
                                            comment,
                                            st.session_state.username,
                                            selected_route,
                                            selected_sector,
                                            selected_crag
                                        )
                                    )
                                    st.success("Comment added!")
                                    run_query.clear(); st.rerun()
                                except Exception as e:
                                    st.error(f"Failed to add comment: {e}")

                            
                            st.markdown("---")
                            # 7) Add a Recommendation
                            st.subheader("⭐ Give a Rating")
                            rating = st.slider("Rating (1–5)", 1, 5, 3, key="rating")
                            reco_text = st.text_area("Optional note", key="reco_text")
                            if st.button("Submit Recommendation"):
                                try:
                                    run_query_no_cache(
                                        """
                                        INSERT INTO practica.recomanacio
                                        (puntuacio, descripcio_recomanacio,
                                         nom_usuari_escalador, nom_via, nom_sector_via, nom_crag_via)
                                        VALUES (%s, %s, %s, %s, %s, %s)
                                        """,
                                        (
                                            rating, reco_text or None,
                                            st.session_state.username,
                                            selected_route,
                                            selected_sector,
                                            selected_crag
                                        )
                                    )
                                    st.success("Recommendation submitted!")
                                    run_query.clear(); st.rerun()
                                except Exception as e:
                                    st.error(f"Failed to submit recommendation: {e}")


# ─── PROFILE ───────────────────────────────────────────────────────────────────

elif page == "Profile":
    st.header("👤 Your Profile")

    username = st.session_state.username

    # — 1) Show basic climber info
    st.subheader("Account Details")
    user_info = run_query(
        """
        SELECT nom_usuari, data_naixement, nivell
        FROM practica.escalador
        WHERE nom_usuari = %s
        """,
        (username,)
    )
    if user_info:
        nom, dob, nivell = user_info[0]
        col1, col2, col3 = st.columns(3)
        col1.markdown(f"**Username:** {nom}")
        col2.markdown(f"**Date of Birth:** {dob}")
        col3.markdown(f"**Climbing Level:** {nivell}")
    else:
        st.error("Could not load your profile info.")

    st.markdown("---")

    # — 2) Tabs for Attempts / Completions / Comments / Recommendations
    tab_att, tab_comp, tab_com, tab_rec = st.tabs(
        ["Attempts", "Completions", "Comments", "Recommendations"]
    )

    # --- Attempts Tab ---
    with tab_att:
        st.subheader("🗒️ Your Attempts")
        attempts = run_query(
            """
            SELECT id_intent, tipus_ascensio, data_intent, nom_via, nom_sector_via, nom_crag_via
            FROM practica.intent
            WHERE nom_usuari_escalador = %s
            ORDER BY data_intent DESC
            """,
            (username,)
        )
        if attempts:
            df = pd.DataFrame(attempts, columns=["ID","Type","Date","Route","Sector","Crag"])
            st.dataframe(df, use_container_width=True)

            # Edit/Delete an attempt
            selected = st.selectbox("Select an attempt to edit/delete", df["ID"])
            record = df[df["ID"] == selected].iloc[0]
            with st.form("edit_attempt"):
                new_type = st.selectbox("Ascent Type", ["A vista","Flash","Assajat","Top-rope"], index=["A vista","Flash","Assajat","Top-rope"].index(record["Type"]))
                new_date = st.date_input("Date of Attempt", value=record["Date"])
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Update Attempt"):
                        run_query_no_cache(
                            "UPDATE practica.intent SET tipus_ascensio=%s, data_intent=%s WHERE id_intent=%s",
                            (new_type, new_date, selected)
                        )
                        run_query.clear(); st.rerun()
                with col2:
                    if st.form_submit_button("Delete Attempt"):
                        run_query_no_cache(
                            "DELETE FROM practica.intent WHERE id_intent=%s",
                            (selected,)
                        )
                        run_query.clear(); st.rerun()
        else:
            st.info("You haven't logged any attempts yet.")

    # --- Completions Tab ---
    with tab_comp:
        st.subheader("✅ Your Completions")
        comps = run_query(
            """
            SELECT e.id_intent, i.data_intent, e.temps_ascensio, i.nom_via
            FROM practica.encadenament e
            JOIN practica.intent i ON e.id_intent = i.id_intent
            WHERE i.nom_usuari_escalador = %s
            ORDER BY i.data_intent DESC
            """,
            (username,)
        )
        if comps:
            df = pd.DataFrame(comps, columns=["Intent ID","Date","Time Spent","Route"])
            st.dataframe(df, use_container_width=True)

            sel = st.selectbox("Select a completion to delete", df["Intent ID"], key="sel_comp")
            if st.button("Delete Completion"):
                run_query_no_cache(
                    "DELETE FROM practica.encadenament WHERE id_intent = %s",
                    (sel,)
                )
                run_query.clear(); st.rerun()
        else:
            st.info("No completions recorded yet.")

    # --- Comments Tab ---
    with tab_com:
        st.subheader("💬 Your Comments")
        comments = run_query(
            """
            SELECT id_comentari, text_comentari, data_comentari, nom_via
            FROM practica.comentari
            WHERE nom_usuari_escalador = %s
            ORDER BY data_comentari DESC
            """,
            (username,)
        )
        if comments:
            df = pd.DataFrame(comments, columns=["ID","Comment","Date","Route"])
            st.dataframe(df, use_container_width=True)

            sel = st.selectbox("Select a comment to edit/delete", df["ID"], key="sel_com")
            record = df[df["ID"] == sel].iloc[0]
            with st.form("edit_comment"):
                new_text = st.text_area("Comment", value=record["Comment"])
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Update Comment"):
                        run_query_no_cache(
                            "UPDATE practica.comentari SET text_comentari=%s WHERE id_comentari=%s",
                            (new_text, sel)
                        )
                        run_query.clear(); st.rerun()
                with col2:
                    if st.form_submit_button("Delete Comment"):
                        run_query_no_cache(
                            "DELETE FROM practica.comentari WHERE id_comentari=%s",
                            (sel,)
                        )
                        run_query.clear(); st.rerun()
        else:
            st.info("You haven't made any comments yet.")

    # --- Recommendations Tab ---
    with tab_rec:
        st.subheader("🌟 Your Recommendations")
        recos = run_query(
            """
            SELECT id_recomanacio, puntuacio, descripcio_recomanacio, data_recomanacio, nom_via
            FROM practica.recomanacio
            WHERE nom_usuari_escalador = %s
            ORDER BY data_recomanacio DESC
            """,
            (username,)
        )
        if recos:
            df = pd.DataFrame(recos, columns=["ID","Rating","Note","Date","Route"])
            st.dataframe(df, use_container_width=True)

            sel = st.selectbox("Select a recommendation to edit/delete", df["ID"], key="sel_rec")
            record = df[df["ID"] == sel].iloc[0]
            with st.form("edit_reco"):
                new_rating = st.slider("Rating", 1, 5, record["Rating"])
                new_note   = st.text_area("Note", value=record["Note"] or "")
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Update Recommendation"):
                        run_query_no_cache(
                            "UPDATE practica.recomanacio SET puntuacio=%s, descripcio_recomanacio=%s WHERE id_recomanacio=%s",
                            (new_rating, new_note, sel)
                        )
                        run_query.clear(); st.rerun()
                with col2:
                    if st.form_submit_button("Delete Recommendation"):
                        run_query_no_cache(
                            "DELETE FROM practica.recomanacio WHERE id_recomanacio=%s",
                            (sel,)
                        )
                        run_query.clear(); st.rerun()
        else:
            st.info("You haven't made any recommendations yet.")

    
