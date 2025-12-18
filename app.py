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

# --- 3. CRAIGHILL DESIGN SYSTEM ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

    :root { --primary-color: #000000; --background-color: #ffffff; }
    .stApp { background-color: #ffffff; }
    .block-container { padding-top: 2rem !important; padding-bottom: 5rem !important; max-width: 1400px !important; }
    
    h1, h2, h3 { font-family: 'Inter', sans-serif !important; text-transform: uppercase; font-weight: 600 !important; color: #000 !important; }
    
    /* SHARP BUTTONS */
    div.stButton > button {
        background-color: #000000; color: #ffffff; border: 1px solid #000000; border-radius: 0px;
        padding: 0.75rem 1.5rem; font-weight: 500; text-transform: uppercase; width: 100%; transition: all 0.2s;
    }
    div.stButton > button:hover { background-color: #ffffff; color: #000000; }
    
    /* UPLOAD & UI */
    .stFileUploader { border: 1px dashed #cccccc; padding: 2rem; border-radius: 0px; background-color: #fafafa; }
    #MainMenu, footer, header { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# --- 4. ADVANCED CONVERSION ENGINE ---
def convert_geometry(step_path, export_path, format_key):
    """
    Universal Converter. 
    1. CadQuery converts STEP -> STL (Tessellation).
    2. Trimesh loads STL.
    3. Trimesh exports to OBJ/GLTF/3MF/PLY.
    """
    # 1. Base Tessellation (STEP -> Intermediate STL)
    # We use high tolerance (0.01) for smooth curves
    model = cq.importers.importStep(step_path)
    
    # Direct CadQuery Exports (Fastest for STL/AMF)
    if format_key in ["STL", "AMF"]:
        cq.exporters.export(model, export_path, format_key)
        return model

    # For complex formats, we route through Trimesh
    # Generate temp mesh in memory
    with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as tmp:
        cq.exporters.export(model, tmp.name, "STL")
        mesh = trimesh.load(tmp.name)
    
    # Export using Trimesh (The Universal Translator)
    if format_key == "OBJ":
        mesh.export(export_path, file_type="obj")
    elif format_key == "GLTF":
        mesh.export(export_path, file_type="glb") # Binary GLTF is safer
    elif format_key == "3MF":
        mesh.export(export_path, file_type="3mf")
    elif format_key == "PLY":
        mesh.export(export_path, file_type="ply")
        
    return model

def render_preview(mesh):
    x, y, z = mesh.vertices.T
    i, j, k = mesh.faces.T
    fig = go.Figure(data=[go.Mesh3d(
        x=x, y=y, z=z, i=i, j=j, k=k,
        color='#eeeeee', opacity=1.0, flatshading=True,
        lighting=dict(ambient=0.4, diffuse=0.5, roughness=0.1, specular=0.1)
    )])
    fig.update_layout(
        scene=dict(xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False), bgcolor='rgba(0,0,0,0)'),
        margin=dict(l=0,r=0,b=0,t=0), height=400, paper_bgcolor='rgba(0,0,0,0)'
    )
    return fig

# --- 5. DATA ---
if 'page' not in st.session_state: st.session_state.page = "library"
def fetch_assets():
    mock_data = [{"name": "HELIX KEYRING", "type": "BRASS"}, {"name": "SIDEWINDER KNIFE", "type": "STEEL"}]
    if not supabase: return mock_data
    try:
        data = supabase.table("assets").select("*").order("created_at", desc=True).execute().data
        return data if data else mock_data
    except: return mock_data

# --- 6. NAVIGATION ---
nav = st.container()
with nav:
    c1, c2, c3 = st.columns([1, 4, 1])
    with c1: 
        if st.button("GENESIS", key="nav_home"): st.session_state.page = "library"
    with c3: 
        if st.button("CONVERTER", key="nav_tool"): st.session_state.page = "converter"
    st.markdown("<hr style='border-top: 1px solid #eee; margin: 10px 0 30px 0;'>", unsafe_allow_html=True)

# --- PAGE: LIBRARY ---
if st.session_state.page == "library":
    st.markdown("### ARCHIVE / ASSETS")
    assets = fetch_assets()
    rows = [assets[i:i + 3] for i in range(0, len(assets), 3)]
    for row in rows:
        cols = st.columns(3)
        for idx, asset in enumerate(row):
            with cols[idx]:
                st.markdown(f"""
                <div style="background-color: #f9f9f9; height: 200px; width: 100%; margin-bottom: 10px;"></div>
                <div style="font-weight: 600; font-size: 0.9rem;">{asset['name']}</div>
                <div style="color: #666; font-size: 0.8rem;">{asset['type']}</div>
                <div style="margin-bottom: 30px;"></div>
                """, unsafe_allow_html=True)

# --- PAGE: CONVERTER ---
elif st.session_state.page == "converter":
    col_view, col_ctrl = st.columns([1.5, 1], gap="large")
    
    with col_ctrl:
        st.markdown("### IMPORT")
        uploaded_file = st.file_uploader("Upload STEP File", type=["step", "stp"], label_visibility="collapsed")
        
        st.markdown("### CONFIGURATION")
        # NEW: Expanded Format List
        export_fmt = st.selectbox("Export Format", ["STL", "OBJ", "GLTF", "3MF", "PLY", "AMF"])
        
        c_archive = st.checkbox("Add to Public Archive", value=True)
        c_material = st.selectbox("Material Tag", ["ALUMINUM 6061", "STAINLESS STEEL", "PLA PLASTIC"])

        if uploaded_file:
            st.success(f"Loaded: {uploaded_file.name}")
            
            if st.button("PROCESS GEOMETRY"):
                with st.spinner("Tessellating & Converting..."):
                    with tempfile.TemporaryDirectory() as temp_dir:
                        step_path = os.path.join(temp_dir, "input.step")
                        
                        # Map Extension
                        ext_map = {"STL":".stl", "OBJ":".obj", "GLTF":".glb", "3MF":".3mf", "PLY":".ply", "AMF":".amf"}
                        out_ext = ext_map[export_fmt]
                        out_path = os.path.join(temp_dir, f"output{out_ext}")
                        
                        with open(step_path, "wb") as f: f.write(uploaded_file.getbuffer())
                            
                        try:
                            # 1. RUN CONVERSION
                            convert_geometry(step_path, out_path, export_fmt)
                            
                            # 2. GENERATE PREVIEW (Always needs an STL/Mesh for Plotly)
                            # If we exported GLTF/OBJ, we need to reload it or use the temp STL
                            preview_mesh = None
                            if export_fmt == "STL":
                                preview_mesh = trimesh.load(out_path)
                            else:
                                # For others, we regenerate a temp STL just for the viewer
                                tmp_stl = os.path.join(temp_dir, "view.stl")
                                convert_geometry(step_path, tmp_stl, "STL")
                                preview_mesh = trimesh.load(tmp_stl)
                                
                            st.session_state.mesh = preview_mesh
                            
                            # 3. PREPARE DOWNLOAD
                            with open(out_path, "rb") as f:
                                st.session_state.dl_data = f.read()
                                st.session_state.dl_name = f"genesis_export{out_ext}"
                                st.session_state.dl_mime = "model/gltf-binary" if export_fmt == "GLTF" else "application/octet-stream"

                            # 4. DATABASE
                            if c_archive and supabase:
                                supabase.table("assets").insert({
                                    "name": uploaded_file.name.split('.')[0].upper(),
                                    "type": c_material
                                }).execute()
                                
                        except Exception as e:
                            st.error(f"Conversion Error: {e}")

    with col_view:
        if 'mesh' in st.session_state:
            st.markdown("### PREVIEW")
            st.plotly_chart(render_preview(st.session_state.mesh), use_container_width=True)
            
            if 'dl_data' in st.session_state:
                st.download_button(
                    label=f"DOWNLOAD {export_fmt} FILE",
                    data=st.session_state.dl_data,
                    file_name=st.session_state.dl_name,
                    mime=st.session_state.dl_mime
                )
        else:
            st.markdown("### VISUALIZER")
            st.markdown("<div style='border:1px solid #eee; height:400px; display:flex; align-items:center; justify-content:center; color:#999;'>Waiting for input...</div>", unsafe_allow_html=True)
