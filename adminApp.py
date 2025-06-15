import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="Climbing Database Management",
    page_icon="🧗‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database connection function
@st.cache_resource
def init_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432")
    )

# Execute query with caching for read operations
@st.cache_data(ttl=600)
def run_query(query, params=None, fetch=True):
    conn = init_connection()
    with conn.cursor() as cur:
        cur.execute(query, params)
        if fetch:
            return cur.fetchall()
        conn.commit()

# Execute query without caching for write operations
def run_query_no_cache(query, params=None):
    conn = init_connection()
    with conn.cursor() as cur:
        cur.execute(query, params)
        conn.commit()

# Main app title
st.title("🧗‍♂️ Climbing Database Management System")

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select a page",
    ["Dashboard", "Crags", "Sectors", "Routes", "Climbers", "Attempts", "Completions", "Comments", "Recommendations"]
)

# Dashboard page
if page == "Dashboard":
    st.header("Dashboard")
    
    # Get some basic statistics
    col1, col2, col3, col4 = st.columns(4)
    
    # Count of crags
    crags_count = run_query("SELECT COUNT(*) FROM practica.crag")[0][0]
    col1.metric("Total Crags", crags_count)
    
    # Count of routes
    routes_count = run_query("SELECT COUNT(*) FROM practica.via")[0][0]
    col2.metric("Total Routes", routes_count)
    
    # Count of climbers
    climbers_count = run_query("SELECT COUNT(*) FROM practica.escalador")[0][0]
    col3.metric("Registered Climbers", climbers_count)
    
    # Count of attempts
    attempts_count = run_query("SELECT COUNT(*) FROM practica.intent")[0][0]
    col4.metric("Total Attempts", attempts_count)
    
    # Charts section
    st.subheader("Statistics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Routes by difficulty
        st.subheader("Routes by Difficulty")
        difficulty_data = run_query("""
            SELECT grau_dificultat, COUNT(*) as count 
            FROM practica.via 
            WHERE grau_dificultat IS NOT NULL 
            GROUP BY grau_dificultat 
            ORDER BY count DESC
        """)
        
        if difficulty_data:
            df_difficulty = pd.DataFrame(difficulty_data, columns=["Difficulty", "Count"])
            fig = px.bar(df_difficulty, x="Difficulty", y="Count", color="Count",
                        title="Routes by Difficulty Grade")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No difficulty data available")
    
    with col2:
        # Top rated routes
        st.subheader("Top Rated Routes")
        top_routes = run_query("""
            SELECT v.nom, v.nom_sector, v.nom_crag_sector, AVG(r.puntuacio) as avg_rating, COUNT(r.id_recomanacio) as num_ratings
            FROM practica.via v
            JOIN practica.recomanacio r ON v.nom = r.nom_via AND v.nom_sector = r.nom_sector_via AND v.nom_crag_sector = r.nom_crag_via
            GROUP BY v.nom, v.nom_sector, v.nom_crag_sector
            HAVING COUNT(r.id_recomanacio) > 0
            ORDER BY avg_rating DESC
            LIMIT 10
        """)
        
        if top_routes:
            df_top_routes = pd.DataFrame(top_routes, columns=["Route", "Sector", "Crag", "Average Rating", "Number of Ratings"])
            fig = px.bar(df_top_routes, x="Route", y="Average Rating", color="Number of Ratings",
                        hover_data=["Sector", "Crag"], title="Top Rated Routes")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No rating data available")
    
    # Recent activity
    st.subheader("Recent Activity")
    recent_activity = run_query("""
        SELECT 
            e.nom_usuari, 
            i.nom_via, 
            i.nom_sector_via, 
            i.nom_crag_via, 
            i.tipus_ascensio, 
            i.data_intent
        FROM practica.intent i
        JOIN practica.escalador e ON i.nom_usuari_escalador = e.nom_usuari
        ORDER BY i.data_intent DESC
        LIMIT 10
    """)
    
    if recent_activity:
        df_activity = pd.DataFrame(recent_activity, 
                                columns=["Climber", "Route", "Sector", "Crag", "Ascent Type", "Date"])
        st.dataframe(df_activity, use_container_width=True)
    else:
        st.info("No recent activity available")

# Crags page
elif page == "Crags":
    st.header("Crags Management")
    
    tab1, tab2, tab3 = st.tabs(["View", "Add", "Edit/Delete"])
    
    with tab1:
        st.subheader("All Crags")
        crags = run_query("SELECT nom, localitzacio, descripcio FROM practica.crag ORDER BY nom")
        if crags:
            df_crags = pd.DataFrame(crags, columns=["Name", "Location", "Description"])
            st.dataframe(df_crags, use_container_width=True)
        else:
            st.info("No crags available")
    
    with tab2:
        st.subheader("Add New Crag")
        with st.form("add_crag_form"):
            crag_name = st.text_input("Crag Name*")
            crag_location = st.text_area("Location")
            crag_description = st.text_area("Description")
            
            submit_button = st.form_submit_button("Add Crag")
            
            if submit_button:
                if crag_name:
                    try:
                        run_query_no_cache(
                            "INSERT INTO practica.crag (nom, localitzacio, descripcio) VALUES (%s, %s, %s)",
                            (crag_name, crag_location, crag_description)
                        )
                        st.success(f"Crag '{crag_name}' added successfully!")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error adding crag: {e}")
                else:
                    st.warning("Crag name is required")
    
    with tab3:
        st.subheader("Edit/Delete Crag")
        crag_list = run_query("SELECT nom FROM practica.crag ORDER BY nom")
        if crag_list:
            crag_names = [crag[0] for crag in crag_list]
            selected_crag = st.selectbox("Select Crag", crag_names)
            
            crag_data = run_query("SELECT nom, localitzacio, descripcio FROM practica.crag WHERE nom = %s", (selected_crag,))
            
            if crag_data:
                with st.form("edit_crag_form"):
                    crag_location = st.text_area("Location", value=crag_data[0][1] if crag_data[0][1] else "")
                    crag_description = st.text_area("Description", value=crag_data[0][2] if crag_data[0][2] else "")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        update_button = st.form_submit_button("Update Crag")
                    with col2:
                        delete_button = st.form_submit_button("Delete Crag", type="primary", use_container_width=True)
                    
                    if update_button:
                        try:
                            run_query_no_cache(
                                "UPDATE practica.crag SET localitzacio = %s, descripcio = %s WHERE nom = %s",
                                (crag_location, crag_description, selected_crag)
                            )
                            st.success(f"Crag '{selected_crag}' updated successfully!")
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Error updating crag: {e}")
                    
                    if delete_button:
                        try:
                            run_query_no_cache("DELETE FROM practica.crag WHERE nom = %s", (selected_crag,))
                            st.success(f"Crag '{selected_crag}' deleted successfully!")
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Error deleting crag: {e}")
        else:
            st.info("No crags available to edit")

# Sectors page
elif page == "Sectors":
    st.header("Sectors Management")
    
    tab1, tab2, tab3 = st.tabs(["View", "Add", "Edit/Delete"])
    
    with tab1:
        st.subheader("All Sectors")
        sectors = run_query("""
            SELECT s.nom, s.nom_crag, s.descripcio, c.localitzacio
            FROM practica.sector s
            JOIN practica.crag c ON s.nom_crag = c.nom
            ORDER BY s.nom_crag, s.nom
        """)
        
        if sectors:
            df_sectors = pd.DataFrame(sectors, columns=["Sector Name", "Crag", "Description", "Crag Location"])
            st.dataframe(df_sectors, use_container_width=True)
        else:
            st.info("No sectors available")
    
    with tab2:
        st.subheader("Add New Sector")
        with st.form("add_sector_form"):
            crag_list = run_query("SELECT nom FROM practica.crag ORDER BY nom")
            if crag_list:
                crag_names = [crag[0] for crag in crag_list]
                selected_crag = st.selectbox("Crag*", crag_names)
                
                sector_name = st.text_input("Sector Name*")
                sector_description = st.text_area("Description")
                
                submit_button = st.form_submit_button("Add Sector")
                
                if submit_button:
                    if sector_name and selected_crag:
                        try:
                            run_query_no_cache(
                                "INSERT INTO practica.sector (nom, nom_crag, descripcio) VALUES (%s, %s, %s)",
                                (sector_name, selected_crag, sector_description)
                            )
                            st.success(f"Sector '{sector_name}' added successfully to crag '{selected_crag}'!")
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Error adding sector: {e}")
                    else:
                        st.warning("Sector name and crag are required")
            else:
                st.warning("No crags available. Please add a crag first.")
    
    with tab3:
        st.subheader("Edit/Delete Sector")
        
        # First select crag
        crag_list = run_query("SELECT nom FROM practica.crag ORDER BY nom")
        if crag_list:
            crag_names = [crag[0] for crag in crag_list]
            selected_crag = st.selectbox("Select Crag", crag_names, key="edit_crag")
            
            # Then select sector within that crag
            sector_list = run_query("SELECT nom FROM practica.sector WHERE nom_crag = %s ORDER BY nom", (selected_crag,))
            
            if sector_list:
                sector_names = [sector[0] for sector in sector_list]
                selected_sector = st.selectbox("Select Sector", sector_names)
                
                sector_data = run_query(
                    "SELECT nom, descripcio FROM practica.sector WHERE nom = %s AND nom_crag = %s", 
                    (selected_sector, selected_crag)
                )
                
                if sector_data:
                    with st.form("edit_sector_form"):
                        sector_description = st.text_area("Description", value=sector_data[0][1] if sector_data[0][1] else "")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            update_button = st.form_submit_button("Update Sector")
                        with col2:
                            delete_button = st.form_submit_button("Delete Sector", type="primary", use_container_width=True)
                        
                        if update_button:
                            try:
                                run_query_no_cache(
                                    "UPDATE practica.sector SET descripcio = %s WHERE nom = %s AND nom_crag = %s",
                                    (sector_description, selected_sector, selected_crag)
                                )
                                st.success(f"Sector '{selected_sector}' updated successfully!")
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Error updating sector: {e}")
                        
                        if delete_button:
                            try:
                                run_query_no_cache(
                                    "DELETE FROM practica.sector WHERE nom = %s AND nom_crag = %s", 
                                    (selected_sector, selected_crag)
                                )
                                st.success(f"Sector '{selected_sector}' deleted successfully!")
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Error deleting sector: {e}")
            else:
                st.info(f"No sectors available for crag '{selected_crag}'")
        else:
            st.info("No crags available")

# Routes page
elif page == "Routes":
    st.header("Routes Management")
    
    tab1, tab2, tab3 = st.tabs(["View", "Add", "Edit/Delete"])
    
    with tab1:
        st.subheader("All Routes")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            crag_filter = st.selectbox(
                "Filter by Crag", 
                ["All"] + [crag[0] for crag in run_query("SELECT nom FROM practica.crag ORDER BY nom")]
            )
        
        with col2:
            if crag_filter != "All":
                sector_filter = st.selectbox(
                    "Filter by Sector",
                    ["All"] + [sector[0] for sector in run_query(
                        "SELECT nom FROM practica.sector WHERE nom_crag = %s ORDER BY nom", 
                        (crag_filter,)
                    )]
                )
            else:
                sector_filter = "All"
        
        with col3:
            difficulty_filter = st.selectbox(
                "Filter by Difficulty",
                ["All"] + [diff[0] for diff in run_query(
                    "SELECT DISTINCT grau_dificultat FROM practica.via WHERE grau_dificultat IS NOT NULL ORDER BY grau_dificultat"
                ) if diff[0]]
            )
        
        # Build query based on filters
        query = """
            SELECT v.nom, v.nom_sector, v.nom_crag_sector, v.grau_dificultat, v.estil, 
                   v.alcada_aproximada_metres, v.equipador, v.data_equipament, v.descripcio
            FROM practica.via v
            WHERE 1=1
        """
        params = []
        
        if crag_filter != "All":
            query += " AND v.nom_crag_sector = %s"
            params.append(crag_filter)
            
            if sector_filter != "All":
                query += " AND v.nom_sector = %s"
                params.append(sector_filter)
        
        if difficulty_filter != "All":
            query += " AND v.grau_dificultat = %s"
            params.append(difficulty_filter)
            
        query += " ORDER BY v.nom_crag_sector, v.nom_sector, v.nom"
        
        routes = run_query(query, tuple(params) if params else None)
        
        if routes:
            df_routes = pd.DataFrame(routes, columns=[
                "Route Name", "Sector", "Crag", "Difficulty", "Style", 
                "Height (m)", "Equipper", "Equipment Date", "Description"
            ])
            st.dataframe(df_routes, use_container_width=True)
        else:
            st.info("No routes available with the selected filters")
    
    with tab2:
        st.subheader("Add New Route")
        
        # First select crag
        crag_list = run_query("SELECT nom FROM practica.crag ORDER BY nom")
        if crag_list:
            crag_names = [crag[0] for crag in crag_list]
            selected_crag = st.selectbox("Crag*", crag_names, key="add_route_crag")
            
            # Then select sector within that crag
            sector_list = run_query("SELECT nom FROM practica.sector WHERE nom_crag = %s ORDER BY nom", (selected_crag,))
            
            if sector_list:
                sector_names = [sector[0] for sector in sector_list]
                selected_sector = st.selectbox("Sector*", sector_names, key="add_route_sector")
                
                with st.form("add_route_form"):
                    route_name = st.text_input("Route Name*")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        route_difficulty = st.text_input("Difficulty Grade")
                        route_style = st.text_input("Style")
                        route_height = st.number_input("Height (m)", min_value=0, step=1)
                    
                    with col2:
                        route_equipper = st.text_input("Equipper")
                        route_equipment_date = st.date_input("Equipment Date", value=None)
                    
                    route_description = st.text_area("Description")
                    
                    submit_button = st.form_submit_button("Add Route")
                    
                    if submit_button:
                        if route_name:
                            try:
                                run_query_no_cache(
                                    """
                                    INSERT INTO practica.via (
                                        nom, nom_sector, nom_crag_sector, grau_dificultat, estil, 
                                        alcada_aproximada_metres, equipador, data_equipament, descripcio
                                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                                    """,
                                    (
                                        route_name, selected_sector, selected_crag, 
                                        route_difficulty if route_difficulty else None, 
                                        route_style if route_style else None,
                                        route_height if route_height > 0 else None,
                                        route_equipper if route_equipper else None,
                                        route_equipment_date,
                                        route_description if route_description else None
                                    )
                                )
                                st.success(f"Route '{route_name}' added successfully!")
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Error adding route: {e}")
                        else:
                            st.warning("Route name is required")
            else:
                st.warning(f"No sectors available for crag '{selected_crag}'. Please add a sector first.")
        else:
            st.warning("No crags available. Please add a crag first.")
    
    with tab3:
        st.subheader("Edit/Delete Route")
        
        # First select crag
        crag_list = run_query("SELECT nom FROM practica.crag ORDER BY nom")
        if crag_list:
            crag_names = [crag[0] for crag in crag_list]
            selected_crag = st.selectbox("Select Crag", crag_names, key="edit_route_crag")
            
            # Then select sector within that crag
            sector_list = run_query("SELECT nom FROM practica.sector WHERE nom_crag = %s ORDER BY nom", (selected_crag,))
            
            if sector_list:
                sector_names = [sector[0] for sector in sector_list]
                selected_sector = st.selectbox("Select Sector", sector_names, key="edit_route_sector")
                
                # Then select route within that sector
                route_list = run_query(
                    "SELECT nom FROM practica.via WHERE nom_sector = %s AND nom_crag_sector = %s ORDER BY nom", 
                    (selected_sector, selected_crag)
                )
                
                if route_list:
                    route_names = [route[0] for route in route_list]
                    selected_route = st.selectbox("Select Route", route_names)
                    
                    route_data = run_query(
                        """
                        SELECT nom, grau_dificultat, estil, alcada_aproximada_metres, 
                               equipador, data_equipament, descripcio
                        FROM practica.via 
                        WHERE nom = %s AND nom_sector = %s AND nom_crag_sector = %s
                        """, 
                        (selected_route, selected_sector, selected_crag)
                    )
                    
                    if route_data:
                        with st.form("edit_route_form"):
                            col1, col2 = st.columns(2)
                            with col1:
                                route_difficulty = st.text_input(
                                    "Difficulty Grade", 
                                    value=route_data[0][1] if route_data[0][1] else ""
                                )
                                route_style = st.text_input(
                                    "Style", 
                                    value=route_data[0][2] if route_data[0][2] else ""
                                )
                                route_height = st.number_input(
                                    "Height (m)", 
                                    min_value=0, 
                                    step=1, 
                                    value=route_data[0][3] if route_data[0][3] else 0
                                )
                            
                            with col2:
                                route_equipper = st.text_input(
                                    "Equipper", 
                                    value=route_data[0][4] if route_data[0][4] else ""
                                )
                                route_equipment_date = st.date_input(
                                    "Equipment Date", 
                                    value=route_data[0][5] if route_data[0][5] else None
                                )
                            
                            route_description = st.text_area(
                                "Description", 
                                value=route_data[0][6] if route_data[0][6] else ""
                            )
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                update_button = st.form_submit_button("Update Route")
                            with col2:
                                delete_button = st.form_submit_button("Delete Route", type="primary", use_container_width=True)
                            
                            if update_button:
                                try:
                                    run_query_no_cache(
                                        """
                                        UPDATE practica.via 
                                        SET grau_dificultat = %s, estil = %s, alcada_aproximada_metres = %s,
                                            equipador = %s, data_equipament = %s, descripcio = %s
                                        WHERE nom = %s AND nom_sector = %s AND nom_crag_sector = %s
                                        """,
                                        (
                                            route_difficulty if route_difficulty else None,
                                            route_style if route_style else None,
                                            route_height if route_height > 0 else None,
                                            route_equipper if route_equipper else None,
                                            route_equipment_date,
                                            route_description if route_description else None,
                                            selected_route, selected_sector, selected_crag
                                        )
                                    )
                                    st.success(f"Route '{selected_route}' updated successfully!")
                                    st.experimental_rerun()
                                except Exception as e:
                                    st.error(f"Error updating route: {e}")
                            
                            if delete_button:
                                try:
                                    run_query_no_cache(
                                        "DELETE FROM practica.via WHERE nom = %s AND nom_sector = %s AND nom_crag_sector = %s", 
                                        (selected_route, selected_sector, selected_crag)
                                    )
                                    st.success(f"Route '{selected_route}' deleted successfully!")
                                    st.experimental_rerun()
                                except Exception as e:
                                    st.error(f"Error deleting route: {e}")
                else:
                    st.info(f"No routes available for sector '{selected_sector}'")
            else:
                st.info(f"No sectors available for crag '{selected_crag}'")
        else:
            st.info("No crags available")

# Climbers page
elif page == "Climbers":
    st.header("Climbers Management")
    
    tab1, tab2, tab3 = st.tabs(["View", "Add", "Edit/Delete"])
    
    with tab1:
        st.subheader("All Climbers")
        climbers = run_query("""
            SELECT nom_usuari, data_naixement, nivell,
                   (SELECT COUNT(*) FROM practica.intent WHERE nom_usuari_escalador = e.nom_usuari) as attempts,
                   (SELECT COUNT(*) FROM practica.encadenament en JOIN practica.intent i ON en.id_intent = i.id_intent 
                    WHERE i.nom_usuari_escalador = e.nom_usuari) as completions
            FROM practica.escalador e
            ORDER BY nom_usuari
        """)
        
        if climbers:
            df_climbers = pd.DataFrame(climbers, columns=[
                "Username", "Birth Date", "Level", "Total Attempts", "Total Completions"
            ])
            st.dataframe(df_climbers, use_container_width=True)
        else:
            st.info("No climbers available")
    
    with tab2:
        st.subheader("Add New Climber")
        with st.form("add_climber_form"):
            username = st.text_input("Username*")
            password = st.text_input("Password*", type="password")
            birth_date = st.date_input("Birth Date", value=None)
            level = st.selectbox("Level", ["", "Beginner", "Intermediate", "Advanced", "Expert"])
            
            submit_button = st.form_submit_button("Add Climber")
            
            if submit_button:
                if username and password:
                    try:
                        run_query_no_cache(
                            "INSERT INTO practica.escalador (nom_usuari, contrasenya, data_naixement, nivell) VALUES (%s, %s, %s, %s)",
                            (username, password, birth_date, level if level else None)
                        )
                        st.success(f"Climber '{username}' added successfully!")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error adding climber: {e}")
                else:
                    st.warning("Username and password are required")
    
    with tab3:
        st.subheader("Edit/Delete Climber")
        climber_list = run_query("SELECT nom_usuari FROM practica.escalador ORDER BY nom_usuari")
        
        if climber_list:
            climber_names = [climber[0] for climber in climber_list]
            selected_climber = st.selectbox("Select Climber", climber_names)
            
            climber_data = run_query(
                "SELECT nom_usuari, contrasenya, data_naixement, nivell FROM practica.escalador WHERE nom_usuari = %s", 
                (selected_climber,)
            )
            
            if climber_data:
                with st.form("edit_climber_form"):
                    password = st.text_input("Password*", value=climber_data[0][1], type="password")
                    birth_date = st.date_input(
                        "Birth Date", 
                        value=climber_data[0][2] if climber_data[0][2] else None
                    )
                    level = st.selectbox(
                        "Level", 
                        ["", "Beginner", "Intermediate", "Advanced", "Expert"],
                        index=["", "Beginner", "Intermediate", "Advanced", "Expert"].index(climber_data[0][3]) if climber_data[0][3] in ["Beginner", "Intermediate", "Advanced", "Expert"] else 0
                    )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        update_button = st.form_submit_button("Update Climber")
                    with col2:
                        delete_button = st.form_submit_button("Delete Climber", type="primary", use_container_width=True)
                    
                    if update_button:
                        if password:
                            try:
                                run_query_no_cache(
                                    "UPDATE practica.escalador SET contrasenya = %s, data_naixement = %s, nivell = %s WHERE nom_usuari = %s",
                                    (password, birth_date, level if level else None, selected_climber)
                                )
                                st.success(f"Climber '{selected_climber}' updated successfully!")
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Error updating climber: {e}")
                        else:
                            st.warning("Password is required")
                    
                    if delete_button:
                        try:
                            run_query_no_cache("DELETE FROM practica.escalador WHERE nom_usuari = %s", (selected_climber,))
                            st.success(f"Climber '{selected_climber}' deleted successfully!")
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Error deleting climber: {e}")
        else:
            st.info("No climbers available")

# Attempts page
elif page == "Attempts":
    st.header("Climbing Attempts Management")
    
    tab1, tab2, tab3 = st.tabs(["View", "Add", "Edit/Delete"])
    
    with tab1:
        st.subheader("All Attempts")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            climber_filter = st.selectbox(
                "Filter by Climber", 
                ["All"] + [climber[0] for climber in run_query("SELECT nom_usuari FROM practica.escalador ORDER BY nom_usuari")]
            )
        
        with col2:
            crag_filter = st.selectbox(
                "Filter by Crag", 
                ["All"] + [crag[0] for crag in run_query("SELECT nom FROM practica.crag ORDER BY nom")]
            )
        
        with col3:
            ascent_type_filter = st.selectbox(
                "Filter by Ascent Type",
                ["All"] + [atype[0] for atype in run_query(
                    "SELECT DISTINCT tipus_ascensio FROM practica.intent WHERE tipus_ascensio IS NOT NULL ORDER BY tipus_ascensio"
                ) if atype[0]]
            )
        
        # Build query based on filters
        query = """
            SELECT i.id_intent, i.nom_usuari_escalador, i.nom_via, i.nom_sector_via, i.nom_crag_via, 
                   i.tipus_ascensio, i.data_intent,
                   CASE WHEN e.id_intent IS NOT NULL THEN 'Yes' ELSE 'No' END as completed,
                   e.temps_ascensio
            FROM practica.intent i
            LEFT JOIN practica.encadenament e ON i.id_intent = e.id_intent
            WHERE 1=1
        """
        params = []
        
        if climber_filter != "All":
            query += " AND i.nom_usuari_escalador = %s"
            params.append(climber_filter)
        
        if crag_filter != "All":
            query += " AND i.nom_crag_via = %s"
            params.append(crag_filter)
        
        if ascent_type_filter != "All":
            query += " AND i.tipus_ascensio = %s"
            params.append(ascent_type_filter)
            
        query += " ORDER BY i.data_intent DESC"
        
        attempts = run_query(query, tuple(params) if params else None)
        
        if attempts:
            df_attempts = pd.DataFrame(attempts, columns=[
                "ID", "Climber", "Route", "Sector", "Crag", 
                "Ascent Type", "Date", "Completed", "Ascent Time"
            ])
            st.dataframe(df_attempts, use_container_width=True)
        else:
            st.info("No attempts available with the selected filters")
    
    with tab2:
        st.subheader("Add New Attempt")
        
        # Select climber
        climber_list = run_query("SELECT nom_usuari FROM practica.escalador ORDER BY nom_usuari")
        if climber_list:
            climber_names = [climber[0] for climber in climber_list]
            selected_climber = st.selectbox("Climber*", climber_names, key="add_attempt_climber")
            
            # Select crag
            crag_list = run_query("SELECT nom FROM practica.crag ORDER BY nom")
            if crag_list:
                crag_names = [crag[0] for crag in crag_list]
                selected_crag = st.selectbox("Crag*", crag_names, key="add_attempt_crag")
                
                # Select sector
                sector_list = run_query("SELECT nom FROM practica.sector WHERE nom_crag = %s ORDER BY nom", (selected_crag,))
                if sector_list:
                    sector_names = [sector[0] for sector in sector_list]
                    selected_sector = st.selectbox("Sector*", sector_names, key="add_attempt_sector")
                    
                    # Select route
                    route_list = run_query(
                        "SELECT nom FROM practica.via WHERE nom_sector = %s AND nom_crag_sector = %s ORDER BY nom", 
                        (selected_sector, selected_crag)
                    )
                    
                    if route_list:
                        route_names = [route[0] for route in route_list]
                        selected_route = st.selectbox("Route*", route_names, key="add_attempt_route")
                        
                        with st.form("add_attempt_form"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                attempt_date = st.date_input("Attempt Date*", value=datetime.now())
                                ascent_type = st.selectbox(
                                    "Ascent Type", 
                                    ["", "Onsight", "Flash", "Redpoint", "Pinkpoint", "Toprope", "Aid"]
                                )
                            
                            with col2:
                                is_completed = st.checkbox("Completed Successfully?")
                                
                                if is_completed:
                                    hours = st.number_input("Hours", min_value=0, max_value=23, step=1)
                                    minutes = st.number_input("Minutes", min_value=0, max_value=59, step=1)
                                    seconds = st.number_input("Seconds", min_value=0, max_value=59, step=1)
                            
                            submit_button = st.form_submit_button("Add Attempt")
                            
                            if submit_button:
                                try:
                                    # Insert attempt
                                    run_query_no_cache(
                                        """
                                        INSERT INTO practica.intent (
                                            tipus_ascensio, data_intent, nom_usuari_escalador, 
                                            nom_via, nom_sector_via, nom_crag_via
                                        ) VALUES (%s, %s, %s, %s, %s, %s)
                                        RETURNING id_intent
                                        """,
                                        (
                                            ascent_type if ascent_type else None,
                                            attempt_date,
                                            selected_climber,
                                            selected_route,
                                            selected_sector,
                                            selected_crag
                                        )
                                    )
                                    
                                    # Get the inserted attempt ID
                                    attempt_id = run_query(
                                        "SELECT id_intent FROM practica.intent WHERE nom_usuari_escalador = %s AND nom_via = %s AND nom_sector_via = %s AND nom_crag_via = %s AND data_intent = %s ORDER BY id_intent DESC LIMIT 1",
                                        (selected_climber, selected_route, selected_sector, selected_crag, attempt_date)
                                    )[0][0]
                                    
                                    # If completed, insert completion record
                                    if is_completed:
                                        ascent_time = timedelta(hours=hours, minutes=minutes, seconds=seconds)
                                        run_query_no_cache(
                                            "INSERT INTO practica.encadenament (id_intent, temps_ascensio) VALUES (%s, %s)",
                                            (attempt_id, ascent_time)
                                        )
                                    
                                    st.success("Attempt added successfully!")
                                    st.experimental_rerun()
                                except Exception as e:
                                    st.error(f"Error adding attempt: {e}")
                    else:
                        st.warning(f"No routes available for sector '{selected_sector}'. Please add a route first.")
                else:
                    st.warning(f"No sectors available for crag '{selected_crag}'. Please add a sector first.")
            else:
                st.warning("No crags available. Please add a crag first.")
        else:
            st.warning("No climbers available. Please add a climber first.")
    
    with tab3:
        st.subheader("Edit/Delete Attempt")
        
        # Select climber
        climber_list = run_query("SELECT nom_usuari FROM practica.escalador ORDER BY nom_usuari")
        if climber_list:
            climber_names = [climber[0] for climber in climber_list]
            selected_climber = st.selectbox("Select Climber", climber_names, key="edit_attempt_climber")
            
            # Get attempts for this climber
            attempt_list = run_query(
                """
                SELECT i.id_intent, i.nom_via, i.nom_sector_via, i.nom_crag_via, i.data_intent, i.tipus_ascensio
                FROM practica.intent i
                WHERE i.nom_usuari_escalador = %s
                ORDER BY i.data_intent DESC
                """,
                (selected_climber,)
            )
            
            if attempt_list:
                attempt_options = [f"ID: {a[0]} - {a[1]} ({a[2]}, {a[3]}) - {a[4]} - {a[5] if a[5] else 'No type'}" for a in attempt_list]
                selected_attempt_option = st.selectbox("Select Attempt", attempt_options)
                
                # Extract attempt ID from the selected option
                selected_attempt_id = int(selected_attempt_option.split(" - ")[0].replace("ID: ", ""))
                
                # Get attempt details
                attempt_data = run_query(
                    """
                    SELECT i.tipus_ascensio, i.data_intent, 
                           CASE WHEN e.id_intent IS NOT NULL THEN true ELSE false END as completed,
                           e.temps_ascensio
                    FROM practica.intent i
                    LEFT JOIN practica.encadenament e ON i.id_intent = e.id_intent
                    WHERE i.id_intent = %s
                    """,
                    (selected_attempt_id,)
                )
                
                if attempt_data:
                    with st.form("edit_attempt_form"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            attempt_date = st.date_input("Attempt Date*", value=attempt_data[0][1])
                            ascent_type = st.selectbox(
                                "Ascent Type", 
                                ["", "Onsight", "Flash", "Redpoint", "Pinkpoint", "Toprope", "Aid"],
                                index=["", "Onsight", "Flash", "Redpoint", "Pinkpoint", "Toprope", "Aid"].index(attempt_data[0][0]) if attempt_data[0][0] in ["Onsight", "Flash", "Redpoint", "Pinkpoint", "Toprope", "Aid"] else 0
                            )
                        
                        with col2:
                            is_completed = st.checkbox("Completed Successfully?", value=attempt_data[0][2])
                            
                            if is_completed:
                                # Parse the interval into hours, minutes, seconds
                                if attempt_data[0][3]:
                                    total_seconds = attempt_data[0][3].total_seconds()
                                    default_hours = int(total_seconds // 3600)
                                    default_minutes = int((total_seconds % 3600) // 60)
                                    default_seconds = int(total_seconds % 60)
                                else:
                                    default_hours, default_minutes, default_seconds = 0, 0, 0
                                
                                hours = st.number_input("Hours", min_value=0, max_value=23, step=1, value=default_hours)
                                minutes = st.number_input("Minutes", min_value=0, max_value=59, step=1, value=default_minutes)
                                seconds = st.number_input("Seconds", min_value=0, max_value=59, step=1, value=default_seconds)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            update_button = st.form_submit_button("Update Attempt")
                        with col2:
                            delete_button = st.form_submit_button("Delete Attempt", type="primary", use_container_width=True)
                        
                        if update_button:
                            try:
                                # Update attempt
                                run_query_no_cache(
                                    """
                                    UPDATE practica.intent 
                                    SET tipus_ascensio = %s, data_intent = %s
                                    WHERE id_intent = %s
                                    """,
                                    (
                                        ascent_type if ascent_type else None,
                                        attempt_date,
                                        selected_attempt_id
                                    )
                                )
                                
                                # Handle completion status
                                if is_completed:
                                    ascent_time = timedelta(hours=hours, minutes=minutes, seconds=seconds)
                                    
                                    # Check if completion record exists
                                    completion_exists = run_query(
                                        "SELECT COUNT(*) FROM practica.encadenament WHERE id_intent = %s",
                                        (selected_attempt_id,)
                                    )[0][0]
                                    
                                    if completion_exists:
                                        run_query_no_cache(
                                            "UPDATE practica.encadenament SET temps_ascensio = %s WHERE id_intent = %s",
                                            (ascent_time, selected_attempt_id)
                                        )
                                    else:
                                        run_query_no_cache(
                                            "INSERT INTO practica.encadenament (id_intent, temps_ascensio) VALUES (%s, %s)",
                                            (selected_attempt_id, ascent_time)
                                        )
                                else:
                                    # Remove completion record if it exists
                                    run_query_no_cache(
                                        "DELETE FROM practica.encadenament WHERE id_intent = %s",
                                        (selected_attempt_id,)
                                    )
                                
                                st.success("Attempt updated successfully!")
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Error updating attempt: {e}")
                        
                        if delete_button:
                            try:
                                # Delete attempt (cascade will handle completion record)
                                run_query_no_cache(
                                    "DELETE FROM practica.intent WHERE id_intent = %s",
                                    (selected_attempt_id,)
                                )
                                st.success("Attempt deleted successfully!")
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Error deleting attempt: {e}")
            else:
                st.info(f"No attempts available for climber '{selected_climber}'")
        else:
            st.info("No climbers available")

# Completions page
elif page == "Completions":
    st.header("Climbing Completions")
    
    # View completions
    st.subheader("All Completions")
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        climber_filter = st.selectbox(
            "Filter by Climber", 
            ["All"] + [climber[0] for climber in run_query("SELECT nom_usuari FROM practica.escalador ORDER BY nom_usuari")]
        )
    
    with col2:
        crag_filter = st.selectbox(
            "Filter by Crag", 
            ["All"] + [crag[0] for crag in run_query("SELECT nom FROM practica.crag ORDER BY nom")]
        )
    
    # Build query based on filters
    query = """
        SELECT i.id_intent, i.nom_usuari_escalador, i.nom_via, i.nom_sector_via, i.nom_crag_via, 
               i.tipus_ascensio, i.data_intent, e.temps_ascensio,
               v.grau_dificultat
        FROM practica.encadenament e
        JOIN practica.intent i ON e.id_intent = i.id_intent
        JOIN practica.via v ON i.nom_via = v.nom AND i.nom_sector_via = v.nom_sector AND i.nom_crag_via = v.nom_crag_sector
        WHERE 1=1
    """
    params = []
    
    if climber_filter != "All":
        query += " AND i.nom_usuari_escalador = %s"
        params.append(climber_filter)
    
    if crag_filter != "All":
        query += " AND i.nom_crag_via = %s"
        params.append(crag_filter)
        
    query += " ORDER BY i.data_intent DESC"
    
    completions = run_query(query, tuple(params) if params else None)
    
    if completions:
        df_completions = pd.DataFrame(completions, columns=[
            "ID", "Climber", "Route", "Sector", "Crag", 
            "Ascent Type", "Date", "Ascent Time", "Difficulty"
        ])
        st.dataframe(df_completions, use_container_width=True)
        
        # Statistics
        st.subheader("Completion Statistics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Completions by difficulty
            difficulty_data = run_query(
                """
                SELECT v.grau_dificultat, COUNT(*) as count
                FROM practica.encadenament e
                JOIN practica.intent i ON e.id_intent = i.id_intent
                JOIN practica.via v ON i.nom_via = v.nom AND i.nom_sector_via = v.nom_sector AND i.nom_crag_via = v.nom_crag_sector
                WHERE v.grau_dificultat IS NOT NULL
                """ + 
                (" AND i.nom_usuari_escalador = %s" if climber_filter != "All" else "") +
                (" AND i.nom_crag_via = %s" if crag_filter != "All" else "") +
                """
                GROUP BY v.grau_dificultat
                ORDER BY v.grau_dificultat
                """,
                tuple(params) if params else None
            )
            
            if difficulty_data:
                df_difficulty = pd.DataFrame(difficulty_data, columns=["Difficulty", "Count"])
                fig = px.bar(df_difficulty, x="Difficulty", y="Count", color="Count",
                            title="Completions by Difficulty Grade")
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Completions by ascent type
            ascent_type_data = run_query(
                """
                SELECT i.tipus_ascensio, COUNT(*) as count
                FROM practica.encadenament e
                JOIN practica.intent i ON e.id_intent = i.id_intent
                WHERE i.tipus_ascensio IS NOT NULL
                """ + 
                (" AND i.nom_usuari_escalador = %s" if climber_filter != "All" else "") +
                (" AND i.nom_crag_via = %s" if crag_filter != "All" else "") +
                """
                GROUP BY i.tipus_ascensio
                ORDER BY count DESC
                """,
                tuple(params) if params else None
            )
            
            if ascent_type_data:
                df_ascent_type = pd.DataFrame(ascent_type_data, columns=["Ascent Type", "Count"])
                fig = px.pie(df_ascent_type, values="Count", names="Ascent Type",
                            title="Completions by Ascent Type")
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No completions available with the selected filters")

# Comments page
elif page == "Comments":
    st.header("Comments Management")
    
    tab1, tab2, tab3 = st.tabs(["View", "Add", "Edit/Delete"])
    
    with tab1:
        st.subheader("All Comments")
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            climber_filter = st.selectbox(
                "Filter by Climber", 
                ["All"] + [climber[0] for climber in run_query("SELECT nom_usuari FROM practica.escalador ORDER BY nom_usuari")]
            )
        
        with col2:
            crag_filter = st.selectbox(
                "Filter by Crag", 
                ["All"] + [crag[0] for crag in run_query("SELECT nom FROM practica.crag ORDER BY nom")]
            )
        
        # Build query based on filters
        query = """
            SELECT c.id_comentari, c.nom_usuari_escalador, c.nom_via, c.nom_sector_via, c.nom_crag_via, 
                   c.text_comentari, c.data_comentari
            FROM practica.comentari c
            WHERE 1=1
        """
        params = []
        
        if climber_filter != "All":
            query += " AND c.nom_usuari_escalador = %s"
            params.append(climber_filter)
        
        if crag_filter != "All":
            query += " AND c.nom_crag_via = %s"
            params.append(crag_filter)
            
        query += " ORDER BY c.data_comentari DESC"
        
        comments = run_query(query, tuple(params) if params else None)
        
        if comments:
            df_comments = pd.DataFrame(comments, columns=[
                "ID", "Climber", "Route", "Sector", "Crag", "Comment", "Date"
            ])
            st.dataframe(df_comments, use_container_width=True)
        else:
            st.info("No comments available with the selected filters")
    
    with tab2:
        st.subheader("Add New Comment")
        
        # Select climber
        climber_list = run_query("SELECT nom_usuari FROM practica.escalador ORDER BY nom_usuari")
        if climber_list:
            climber_names = [climber[0] for climber in climber_list]
            selected_climber = st.selectbox("Climber*", climber_names, key="add_comment_climber")
            
            # Select crag
            crag_list = run_query("SELECT nom FROM practica.crag ORDER BY nom")
            if crag_list:
                crag_names = [crag[0] for crag in crag_list]
                selected_crag = st.selectbox("Crag*", crag_names, key="add_comment_crag")
                
                # Select sector
                sector_list = run_query("SELECT nom FROM practica.sector WHERE nom_crag = %s ORDER BY nom", (selected_crag,))
                if sector_list:
                    sector_names = [sector[0] for sector in sector_list]
                    selected_sector = st.selectbox("Sector*", sector_names, key="add_comment_sector")
                    
                    # Select route
                    route_list = run_query(
                        "SELECT nom FROM practica.via WHERE nom_sector = %s AND nom_crag_sector = %s ORDER BY nom", 
                        (selected_sector, selected_crag)
                    )
                    
                    if route_list:
                        route_names = [route[0] for route in route_list]
                        selected_route = st.selectbox("Route*", route_names, key="add_comment_route")
                        
                        with st.form("add_comment_form"):
                            comment_text = st.text_area("Comment*", height=150)
                            
                            submit_button = st.form_submit_button("Add Comment")
                            
                            if submit_button:
                                if comment_text:
                                    try:
                                        run_query_no_cache(
                                            """
                                            INSERT INTO practica.comentari (
                                                text_comentari, nom_usuari_escalador, 
                                                nom_via, nom_sector_via, nom_crag_via
                                            ) VALUES (%s, %s, %s, %s, %s)
                                            """,
                                            (
                                                comment_text,
                                                selected_climber,
                                                selected_route,
                                                selected_sector,
                                                selected_crag
                                            )
                                        )
                                        st.success("Comment added successfully!")
                                        st.experimental_rerun()
                                    except Exception as e:
                                        st.error(f"Error adding comment: {e}")
                                else:
                                    st.warning("Comment text is required")
                    else:
                        st.warning(f"No routes available for sector '{selected_sector}'. Please add a route first.")
                else:
                    st.warning(f"No sectors available for crag '{selected_crag}'. Please add a sector first.")
            else:
                st.warning("No crags available. Please add a crag first.")
        else:
            st.warning("No climbers available. Please add a climber first.")
    
    with tab3:
        st.subheader("Edit/Delete Comment")
        
        # Select climber
        climber_list = run_query("SELECT nom_usuari FROM practica.escalador ORDER BY nom_usuari")
        if climber_list:
            climber_names = [climber[0] for climber in climber_list]
            selected_climber = st.selectbox("Select Climber", climber_names, key="edit_comment_climber")
            
            # Get comments for this climber
            comment_list = run_query(
                """
                SELECT c.id_comentari, c.nom_via, c.nom_sector_via, c.nom_crag_via, 
                       c.data_comentari, LEFT(c.text_comentari, 50) as preview
                FROM practica.comentari c
                WHERE c.nom_usuari_escalador = %s
                ORDER BY c.data_comentari DESC
                """,
                (selected_climber,)
            )
            
            if comment_list:
                comment_options = [
                    f"ID: {c[0]} - {c[1]} ({c[2]}, {c[3]}) - {c[4]} - {c[5]}{'...' if len(c[5]) >= 50 else ''}" 
                    for c in comment_list
                ]
                selected_comment_option = st.selectbox("Select Comment", comment_options)
                
                # Extract comment ID from the selected option
                selected_comment_id = int(selected_comment_option.split(" - ")[0].replace("ID: ", ""))
                
                # Get comment details
                comment_data = run_query(
                    "SELECT text_comentari FROM practica.comentari WHERE id_comentari = %s",
                    (selected_comment_id,)
                )
                
                if comment_data:
                    with st.form("edit_comment_form"):
                        comment_text = st.text_area("Comment*", value=comment_data[0][0], height=150)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            update_button = st.form_submit_button("Update Comment")
                        with col2:
                            delete_button = st.form_submit_button("Delete Comment", type="primary", use_container_width=True)
                        
                        if update_button:
                            if comment_text:
                                try:
                                    run_query_no_cache(
                                        "UPDATE practica.comentari SET text_comentari = %s WHERE id_comentari = %s",
                                        (comment_text, selected_comment_id)
                                    )
                                    st.success("Comment updated successfully!")
                                    st.experimental_rerun()
                                except Exception as e:
                                    st.error(f"Error updating comment: {e}")
                            else:
                                st.warning("Comment text is required")
                        
                        if delete_button:
                            try:
                                run_query_no_cache(
                                    "DELETE FROM practica.comentari WHERE id_comentari = %s",
                                    (selected_comment_id,)
                                )
                                st.success("Comment deleted successfully!")
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Error deleting comment: {e}")
            else:
                st.info(f"No comments available for climber '{selected_climber}'")
        else:
            st.info("No climbers available")

# Recommendations page
elif page == "Recommendations":
    st.header("Recommendations Management")
    
    tab1, tab2, tab3 = st.tabs(["View", "Add", "Edit/Delete"])
    
    with tab1:
        st.subheader("All Recommendations")
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            climber_filter = st.selectbox(
                "Filter by Climber", 
                ["All"] + [climber[0] for climber in run_query("SELECT nom_usuari FROM practica.escalador ORDER BY nom_usuari")]
            )
        
        with col2:
            crag_filter = st.selectbox(
                "Filter by Crag", 
                ["All"] + [crag[0] for crag in run_query("SELECT nom FROM practica.crag ORDER BY nom")]
            )
        
        # Build query based on filters
        query = """
            SELECT r.id_recomanacio, r.nom_usuari_escalador, r.nom_via, r.nom_sector_via, r.nom_crag_via, 
                   r.puntuacio, r.descripcio_recomanacio, r.data_recomanacio
            FROM practica.recomanacio r
            WHERE 1=1
        """
        params = []
        
        if climber_filter != "All":
            query += " AND r.nom_usuari_escalador = %s"
            params.append(climber_filter)
        
        if crag_filter != "All":
            query += " AND r.nom_crag_via = %s"
            params.append(crag_filter)
            
        query += " ORDER BY r.data_recomanacio DESC"
        
        recommendations = run_query(query, tuple(params) if params else None)
        
        if recommendations:
            df_recommendations = pd.DataFrame(recommendations, columns=[
                "ID", "Climber", "Route", "Sector", "Crag", "Rating", "Description", "Date"
            ])
            st.dataframe(df_recommendations, use_container_width=True)
            
            # Statistics
            st.subheader("Rating Statistics")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Average rating by route
                avg_ratings = run_query(
                    """
                                        SELECT r.nom_via, r.nom_sector_via, r.nom_crag_via, AVG(r.puntuacio) as avg_rating, COUNT(*) as count
                    FROM practica.recomanacio r
                    WHERE 1=1
                    """ + 
                    (" AND r.nom_usuari_escalador = %s" if climber_filter != "All" else "") +
                    (" AND r.nom_crag_via = %s" if crag_filter != "All" else "") +
                    """
                    GROUP BY r.nom_via, r.nom_sector_via, r.nom_crag_via
                    ORDER BY avg_rating DESC
                    LIMIT 10
                    """,
                    tuple(params) if params else None
                )
                
                if avg_ratings:
                    df_avg_ratings = pd.DataFrame(avg_ratings, columns=["Route", "Sector", "Crag", "Average Rating", "Count"])
                    fig = px.bar(df_avg_ratings, x="Route", y="Average Rating", color="Count",
                                hover_data=["Sector", "Crag"], title="Top Rated Routes")
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Rating distribution
                rating_dist = run_query(
                    """
                    SELECT r.puntuacio, COUNT(*) as count
                    FROM practica.recomanacio r
                    WHERE 1=1
                    """ + 
                    (" AND r.nom_usuari_escalador = %s" if climber_filter != "All" else "") +
                    (" AND r.nom_crag_via = %s" if crag_filter != "All" else "") +
                    """
                    GROUP BY r.puntuacio
                    ORDER BY r.puntuacio
                    """,
                    tuple(params) if params else None
                )
                
                if rating_dist:
                    df_rating_dist = pd.DataFrame(rating_dist, columns=["Rating", "Count"])
                    fig = px.pie(df_rating_dist, values="Count", names="Rating",
                                title="Rating Distribution")
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No recommendations available with the selected filters")
    
    with tab2:
        st.subheader("Add New Recommendation")
        
        # Select climber
        climber_list = run_query("SELECT nom_usuari FROM practica.escalador ORDER BY nom_usuari")
        if climber_list:
            climber_names = [climber[0] for climber in climber_list]
            selected_climber = st.selectbox("Climber*", climber_names, key="add_rec_climber")
            
            # Select crag
            crag_list = run_query("SELECT nom FROM practica.crag ORDER BY nom")
            if crag_list:
                crag_names = [crag[0] for crag in crag_list]
                selected_crag = st.selectbox("Crag*", crag_names, key="add_rec_crag")
                
                # Select sector
                sector_list = run_query("SELECT nom FROM practica.sector WHERE nom_crag = %s ORDER BY nom", (selected_crag,))
                if sector_list:
                    sector_names = [sector[0] for sector in sector_list]
                    selected_sector = st.selectbox("Sector*", sector_names, key="add_rec_sector")
                    
                    # Select route
                    route_list = run_query(
                        "SELECT nom FROM practica.via WHERE nom_sector = %s AND nom_crag_sector = %s ORDER BY nom", 
                        (selected_sector, selected_crag)
                    )
                    
                    if route_list:
                        route_names = [route[0] for route in route_list]
                        selected_route = st.selectbox("Route*", route_names, key="add_rec_route")
                        
                        # Check if recommendation already exists
                        existing_rec = run_query(
                            """
                            SELECT id_recomanacio FROM practica.recomanacio 
                            WHERE nom_usuari_escalador = %s AND nom_via = %s AND nom_sector_via = %s AND nom_crag_via = %s
                            """,
                            (selected_climber, selected_route, selected_sector, selected_crag)
                        )
                        
                        if existing_rec:
                            st.warning(f"You already have a recommendation for this route. Please edit the existing one.")
                        else:
                            with st.form("add_rec_form"):
                                rating = st.slider("Rating*", min_value=1, max_value=5, value=3, step=1)
                                description = st.text_area("Description", height=150)
                                
                                submit_button = st.form_submit_button("Add Recommendation")
                                
                                if submit_button:
                                    try:
                                        run_query_no_cache(
                                            """
                                            INSERT INTO practica.recomanacio (
                                                puntuacio, descripcio_recomanacio, nom_usuari_escalador, 
                                                nom_via, nom_sector_via, nom_crag_via
                                            ) VALUES (%s, %s, %s, %s, %s, %s)
                                            """,
                                            (
                                                rating,
                                                description if description else None,
                                                selected_climber,
                                                selected_route,
                                                selected_sector,
                                                selected_crag
                                            )
                                        )
                                        st.success("Recommendation added successfully!")
                                        st.experimental_rerun()
                                    except Exception as e:
                                        st.error(f"Error adding recommendation: {e}")
                    else:
                        st.warning(f"No routes available for sector '{selected_sector}'. Please add a route first.")
                else:
                    st.warning(f"No sectors available for crag '{selected_crag}'. Please add a sector first.")
            else:
                st.warning("No crags available. Please add a crag first.")
        else:
            st.warning("No climbers available. Please add a climber first.")
    
    with tab3:
        st.subheader("Edit/Delete Recommendation")
        
        # Select climber
        climber_list = run_query("SELECT nom_usuari FROM practica.escalador ORDER BY nom_usuari")
        if climber_list:
            climber_names = [climber[0] for climber in climber_list]
            selected_climber = st.selectbox("Select Climber", climber_names, key="edit_rec_climber")
            
            # Get recommendations for this climber
            rec_list = run_query(
                """
                SELECT r.id_recomanacio, r.nom_via, r.nom_sector_via, r.nom_crag_via, 
                       r.puntuacio, r.data_recomanacio
                FROM practica.recomanacio r
                WHERE r.nom_usuari_escalador = %s
                ORDER BY r.data_recomanacio DESC
                """,
                (selected_climber,)
            )
            
            if rec_list:
                rec_options = [
                    f"ID: {r[0]} - {r[1]} ({r[2]}, {r[3]}) - Rating: {r[4]} - {r[5]}" 
                    for r in rec_list
                ]
                selected_rec_option = st.selectbox("Select Recommendation", rec_options)
                
                # Extract recommendation ID from the selected option
                selected_rec_id = int(selected_rec_option.split(" - ")[0].replace("ID: ", ""))
                
                # Get recommendation details
                rec_data = run_query(
                    "SELECT puntuacio, descripcio_recomanacio FROM practica.recomanacio WHERE id_recomanacio = %s",
                    (selected_rec_id,)
                )
                
                if rec_data:
                    with st.form("edit_rec_form"):
                        rating = st.slider("Rating*", min_value=1, max_value=5, value=rec_data[0][0], step=1)
                        description = st.text_area("Description", value=rec_data[0][1] if rec_data[0][1] else "", height=150)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            update_button = st.form_submit_button("Update Recommendation")
                        with col2:
                            delete_button = st.form_submit_button("Delete Recommendation", type="primary", use_container_width=True)
                        
                        if update_button:
                            try:
                                run_query_no_cache(
                                    "UPDATE practica.recomanacio SET puntuacio = %s, descripcio_recomanacio = %s WHERE id_recomanacio = %s",
                                    (rating, description if description else None, selected_rec_id)
                                )
                                st.success("Recommendation updated successfully!")
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Error updating recommendation: {e}")
                        
                        if delete_button:
                            try:
                                run_query_no_cache(
                                    "DELETE FROM practica.recomanacio WHERE id_recomanacio = %s",
                                    (selected_rec_id,)
                                )
                                st.success("Recommendation deleted successfully!")
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Error deleting recommendation: {e}")
            else:
                st.info(f"No recommendations available for climber '{selected_climber}'")
        else:
            st.info("No climbers available")

# Add footer
st.markdown("---")
st.markdown("### 🧗‍♂️ Climbing Database Management System")
st.markdown("Developed with Streamlit and PostgreSQL")