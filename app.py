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

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="GENESIS HUB",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. SWISS/INDUSTRIAL DESIGN CSS (BULLETPROOF) ---
st.markdown("""
    <style>
    /* FORCE LIGHT MODE & RESET */
    .stApp {
        background-color: #ffffff !important;
        color: #000000 !important;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    
    /* TYPOGRAPHY - BOLD & READABLE */
    h1, h2, h3, h4, h5, h6 {
        color: #000000 !important;
        font-weight: 800 !important;
        letter-spacing: -0.5px;
    }
    h1 { font-size: 3.5rem !important; margin-bottom: 0px; }
    p, li, div { color: #333333 !important; line-height: 1.6; }
    
    /* REMOVE STREAMLIT PADDING */
    .block-container { padding-top: 2rem; padding-bottom: 5rem; max-width: 1200px; }

    /* NAVIGATION BUTTONS */
    div.stButton > button {
        background-color: #f4f4f5;
        color: #000000;
        border: 1px solid #e4e4e7;
        border-radius: 6px;
        padding: 0.75rem 1rem;
        font-weight: 600;
        width: 100%;
        transition: all 0.2s;
    }
    div.stButton > button:hover {
        background-color: #000000;
        color: #ffffff;
        border-color: #000000;
    }
    
    /* PRIMARY ACTION BUTTON */
    div.stButton > button:active {
        background-color: #333;
        color: white;
    }

    /* CARDS & CONTAINERS */
    .feature-card {
        background-color: #ffffff;
        border: 1px solid #e5e5e5;
        border-radius: 8px;
        padding: 24px;
        margin-bottom: 16px;
    }
    
    /* UPLOAD BOX */
    .stFileUploader {
        border: 2px dashed #000000;
        padding: 30px;
        background-color: #fafafa;
        border-radius: 0px;
    }
    
    /* LIBRARY ITEM */
    .lib-item {
        border-bottom: 1px solid #eee;
        padding: 15px 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .tag {
        background: #000;
        color: #fff;
        padding: 2px 8px;
        font-size: 0.7rem;
        font-weight: bold;
        text-transform: uppercase;
    }
    
    /* REMOVE UGLY DEFAULTS */
    .stDeployButton { display:none; }
    footer { display: none; }
    </style>
""", unsafe_allow_html=True)

# --- 3. STATE MANAGEMENT ---
if 'page' not in st.session_state: st.session_state.page = "converter"
if 'library_db' not in st.session_state:
    st.session_state.library_db = [
        {"name": "Industrial Gear Assembly", "type": "Mechanical", "date": "2024-12-01"},
        {"name": "Turbine Blade Prototype", "type": "Aerospace", "date": "2024-11-20"},
        {"name": "NEMA 17 Mount Bracket", "type": "Robotics", "date": "2025-01-10"},
        {"name": "V6 Engine Block Cast", "type": "Automotive", "date": "2024-10-05"},
    ]

# --- 4. LOGIC ENGINE ---
def convert_step_to_stl(step_path, stl_path):
    model = cq.importers.importStep(step_path)
    cq.exporters.export(model, stl_path)
    return model

def render_preview(mesh):
    x, y, z = mesh.vertices.T
    i, j, k = mesh.faces.T
    fig = go.Figure(data=[go.Mesh3d(
        x=x, y=y, z=z, i=i, j=j, k=k,
        color='#222222', 
        opacity=1.0,
        flatshading=True,
        lighting=dict(ambient=0.4, diffuse=0.5, roughness=0.1, specular=0.1)
    )])
    fig.update_layout(
        scene=dict(xaxis_visible=False, yaxis_visible=False, zaxis_visible=False, bgcolor='white'),
        margin=dict(l=0, r=0, b=0, t=0), height=300
    )
    return fig

# --- 5. UI LAYOUT ---

# HEADER
c1, c2 = st.columns([3, 1])
with c1:
    st.markdown("# GENESIS HUB")
    st.markdown("##### The Open Standard for CAD Interoperability.")
with c2:
    # Navigation Buttons aligned to right
    c2a, c2b = st.columns(2)
    with c2a:
        if st.button("CONVERTER"): st.session_state.page = "converter"
    with c2b:
        if st.button("LIBRARY"): st.session_state.page = "library"

st.divider()

# --- PAGE: CONVERTER ---
if st.session_state.page == "converter":
    
    col_left, col_right = st.columns([1, 1], gap="large")
    
    with col_left:
        st.markdown("### 01. Ingestion")
        st.markdown("Upload a **STEP** file to generate a watertight STL mesh.")
        
        uploaded_file = st.file_uploader("Upload Geometry", type=["step", "stp"], label_visibility="collapsed")
        
        st.markdown("### 02. Configuration")
        c_check = st.checkbox("Contribute to Open Library", value=True)
        c_cat = st.selectbox("Industry Category", ["Mechanical", "Automotive", "Aerospace", "Medical"])
        
        if uploaded_file:
            st.success(f"loaded: {uploaded_file.name}")
            
            if st.button("RUN CONVERSION PROCESS", type="primary"):
                with st.spinner("Processing Geometry..."):
                    with tempfile.TemporaryDirectory() as temp_dir:
                        # Save & Convert
                        step_path = os.path.join(temp_dir, "in.step")
                        stl_path = os.path.join(temp_dir, "out.stl")
                        with open(step_path, "wb") as f: f.write(uploaded_file.getbuffer())
                        
                        try:
                            convert_step_to_stl(step_path, stl_path)
                            st.session_state.mesh = trimesh.load(stl_path)
                            with open(stl_path, "rb") as f: st.session_state.stl_data = f.read()
                            
                            # Add to Library Mock
                            if c_check:
                                st.session_state.library_db.insert(0, {
                                    "name": uploaded_file.name.split('.')[0],
                                    "type": c_cat,
                                    "date": datetime.now().strftime("%Y-%m-%d")
                                })
                        except Exception as e:
                            st.error(f"Kernel Error: {e}")

    with col_right:
        st.markdown("### 03. Visualization")
        
        if 'mesh' in st.session_state:
            # Stats Bar
            s1, s2, s3 = st.columns(3)
            s1.metric("Volume", f"{st.session_state.mesh.volume/1000:.1f}cc")
            s2.metric("Triangles", len(st.session_state.mesh.faces))
            s3.metric("Manifold", str(st.session_state.mesh.is_watertight))
            
            # 3D View
            st.plotly_chart(render_preview(st.session_state.mesh), use_container_width=True)
            
            # Download
            if 'stl_data' in st.session_state:
                st.download_button("DOWNLOAD STL ARTIFACT", st.session_state.stl_data, "genesis_export.stl", "model/stl")
        else:
            st.markdown("""
            <div style="border:1px solid #ddd; height:300px; display:flex; align-items:center; justify-content:center; color:#999; background:#f9f9f9;">
                Awaiting Geometric Data
            </div>
            """, unsafe_allow_html=True)

# --- PAGE: LIBRARY ---
elif st.session_state.page == "library":
    st.markdown("### Global Asset Index")
    st.markdown("Verified engineering assets available for public use.")
    
    # Filter Bar
    f1, f2 = st.columns([3, 1])
    with f1: st.text_input("Search Index...", placeholder="Filter by keywords")
    with f2: st.selectbox("Sort By", ["Newest", "Downloads", "Rating"])
    
    st.markdown("---")
    
    # Simple List View (Cleaner than cards)
    for item in st.session_state.library_db:
        c_name, c_type, c_date, c_action = st.columns([3, 1, 1, 1])
        with c_name:
            st.markdown(f"**{item['name']}**")
        with c_type:
            st.markdown(f"<span class='tag'>{item['type']}</span>", unsafe_allow_html=True)
        with c_date:
            st.markdown(f"<span style='color:#666; font-size:0.8rem'>{item['date']}</span>", unsafe_allow_html=True)
        with c_action:
            st.button("Download", key=random.randint(0,99999))
        st.markdown("<div style='border-bottom:1px solid #eee; margin:5px 0;'></div>", unsafe_allow_html=True)
