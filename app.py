import streamlit as st
import cadquery as cq
import trimesh
import numpy as np
import tempfile
import os
import plotly.graph_objects as go
import time
import random
from datetime import datetime
from supabase import create_client, Client

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="GENESIS",
    page_icon="⚫",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. BACKEND CONNECTIONS ---
@st.cache_resource
def init_connection():
    try:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        if not url or not key: return None
        return create_client(url, key)
    except: return None

supabase = init_connection()

# --- 3. CRAIGHILL DESIGN SYSTEM (FIXED CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

    /* FORCE LIGHT THEME VARIABLES */
    :root {
        --primary-color: #000000;
        --background-color: #ffffff;
        --secondary-background-color: #f4f4f5;
        --text-color: #000000;
        --font: 'Inter', sans-serif;
    }

    /* GLOBAL RESET */
    .stApp {
        background-color: #ffffff;
    }
    
    /* REMOVE DEFAULT PADDING */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 5rem !important;
        max-width: 1400px !important;
    }

    /* HEADERS */
    h1, h2, h3 {
        font-family: 'Inter', sans-serif !important;
        text-transform: uppercase;
        font-weight: 600 !important;
        letter-spacing: -0.02em;
        color: #000000 !important;
    }

    /* BUTTONS - SHARP & MINIMAL */
    div.stButton > button {
        background-color: #000000;
        color: #ffffff;
        border: 1px solid #000000;
        border-radius: 0px; /* Sharp corners */
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        text-transform: uppercase;
        font-size: 0.85rem;
        width: 100%;
        transition: all 0.2s;
    }
    div.stButton > button:hover {
        background-color: #ffffff;
        color: #000000;
    }
    
    /* FILE UPLOADER STYLE FIX */
    .stFileUploader {
        border: 1px dashed #cccccc;
        padding: 2rem;
        border-radius: 0px;
        background-color: #fafafa;
    }
    div[data-testid="stFileUploaderDropzone"] {
        color: #333;
    }

    /* HIDE STREAMLIT BRANDING */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 4. LOGIC ENGINE (WORKING MODEL) ---
def convert_step(step_path, export_path, export_format="STL"):
    """
    Converts STEP to STL/AMF using CadQuery.
    """
    model = cq.importers.importStep(step_path)
    
    if export_format == "STL (Binary)":
        cq.exporters.export(model, export_path, "STL")
    elif export_format == "STL (ASCII)":
        cq.exporters.export(model, export_path, "STL", opt={"ascii": True})
    elif export_format == "AMF":
        cq.exporters.export(model, export_path, "AMF")
        
    return model

def render_preview(mesh):
    """
    Generates the 3D visualization using Plotly.
    """
    x, y, z = mesh.vertices.T
    i, j, k = mesh.faces.T
    
    fig = go.Figure(data=[go.Mesh3d(
        x=x, y=y, z=z, i=i, j=j, k=k,
        color='#eeeeee', 
        opacity=1.0, 
        flatshading=True,
        lighting=dict(ambient=0.4, diffuse=0.5, roughness=0.1, specular=0.1)
    )])
    
    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            zaxis=dict(visible=False),
            bgcolor='rgba(0,0,0,0)',
            aspectmode='data'
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        height=400,
        paper_bgcolor='rgba(0,0,0,0)'
    )
    return fig

# --- 5. DATA FETCHING (LIBRARY) ---
if 'page' not in st.session_state: st.session_state.page = "library"

def fetch_assets():
    """Fetches assets from Supabase or returns mock data."""
    mock_data = [
        {"name": "HELIX KEYRING", "type": "BRASS"},
        {"name": "SIDEWINDER KNIFE", "type": "STEEL"},
        {"name": "VECTOR STAND", "type": "ALUMINUM"},
    ]
    if not supabase: return mock_data
    try:
        data = supabase.table("assets").select("*").order("created_at", desc=True).execute().data
        return data if data else mock_data
    except: return mock_data

# --- 6. NAVIGATION ---
# A clean top bar using columns
nav_container = st.container()
with nav_container:
    c1, c2, c3 = st.columns([1, 4, 1])
    with c1:
        if st.button("GENESIS", key="nav_home"): st.session_state.page = "library"
    with c3:
        if st.button("CONVERTER tool", key="nav_tool"): st.session_state.page = "converter"
    st.markdown("<hr style='border-top: 1px solid #eee; margin: 10px 0 30px 0;'>", unsafe_allow_html=True)

# --- PAGE: LIBRARY (SHOP VIEW) ---
if st.session_state.page == "library":
    st.markdown("### ARCHIVE / ASSETS")
    st.markdown("Engineering assets converted and verified by the community.")
    st.write("") # Spacer

    assets = fetch_assets()
    
    # 3-Column Grid
    rows = [assets[i:i + 3] for i in range(0, len(assets), 3)]
    for row in rows:
        cols = st.columns(3)
        for idx, asset in enumerate(row):
            with cols[idx]:
                # Minimalist Card
                st.markdown(f"""
                <div style="background-color: #f9f9f9; height: 200px; width: 100%; margin-bottom: 10px;"></div>
                <div style="font-weight: 600; font-size: 0.9rem;">{asset['name']}</div>
                <div style="color: #666; font-size: 0.8rem;">{asset['type']}</div>
                <div style="margin-bottom: 30px;"></div>
                """, unsafe_allow_html=True)

# --- PAGE: CONVERTER (TOOL VIEW) ---
elif st.session_state.page == "converter":
    
    # Layout: Left (3D View), Right (Controls)
    col_view, col_ctrl = st.columns([1.5, 1], gap="large")
    
    with col_ctrl:
        st.markdown("### IMPORT")
        uploaded_file = st.file_uploader("Upload STEP File", type=["step", "stp"], label_visibility="collapsed")
        
        st.markdown("### SETTINGS")
        export_type = st.selectbox("Export Format", ["STL (Binary)", "STL (ASCII)", "AMF"])
        c_archive = st.checkbox("Add to Public Archive", value=True)
        c_material = st.selectbox("Material Tag", ["ALUMINUM 6061", "STAINLESS STEEL", "PLA PLASTIC", "TITANIUM"])

        if uploaded_file:
            st.success(f"Loaded: {uploaded_file.name}")
            
            if st.button("PROCESS GEOMETRY"):
                with st.spinner("Tessellating..."):
                    with tempfile.TemporaryDirectory() as temp_dir:
                        # Paths
                        step_path = os.path.join(temp_dir, "input.step")
                        out_ext = ".stl" if "STL" in export_type else ".amf"
                        out_path = os.path.join(temp_dir, f"output{out_ext}")
                        
                        # Write Input
                        with open(step_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                            
                        try:
                            # 1. Convert
                            convert_step(step_path, out_path, export_type)
                            
                            # 2. Load Mesh for Preview (Always load as STL for Trimesh compat)
                            # (We re-export a temp STL just for visualization if user selected AMF)
                            preview_path = out_path
                            if export_type == "AMF":
                                preview_stl = os.path.join(temp_dir, "preview.stl")
                                convert_step(step_path, preview_stl, "STL (Binary)")
                                preview_path = preview_stl
                            
                            st.session_state.mesh = trimesh.load(preview_path)
                            
                            # 3. Read File for Download
                            with open(out_path, "rb") as f:
                                st.session_state.dl_data = f.read()
                                st.session_state.dl_name = f"genesis_export{out_ext}"

                            # 4. Save to DB
                            if c_archive and supabase:
                                supabase.table("assets").insert({
                                    "name": uploaded_file.name.split('.')[0].upper(),
                                    "type": c_material
                                }).execute()
                                
                        except Exception as e:
                            st.error(f"Conversion Error: {e}")

    with col_view:
        # 3D PREVIEW AREA
        if 'mesh' in st.session_state:
            st.markdown("### PREVIEW")
            # Render the mesh
            st.plotly_chart(render_preview(st.session_state.mesh), use_container_width=True)
            
            # Stats Overlay
            m = st.session_state.mesh
            st.caption(f"Vertices: {len(m.vertices)} | Faces: {len(m.faces)} | Watertight: {m.is_watertight}")
            
            # DOWNLOAD BUTTON (Only shows after successful conversion)
            if 'dl_data' in st.session_state:
                st.download_button(
                    label="DOWNLOAD FILE",
                    data=st.session_state.dl_data,
                    file_name=st.session_state.dl_name,
                    mime="application/octet-stream"
                )
        else:
            # Empty State
            st.markdown("### VISUALIZER")
            st.markdown("""
            <div style="
                border: 1px solid #eee; 
                background-color: #fafafa; 
                height: 400px; 
                display: flex; 
                align-items: center; 
                justify-content: center; 
                color: #999;">
                Waiting for input...
            </div>
            """, unsafe_allow_html=True)
