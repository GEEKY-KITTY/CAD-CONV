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

# --- 4. ENGINE (CONVERSION & RENDERING) ---
def convert_geometry(step_path, export_path, format_key):
    """Universal Converter using CadQuery & Trimesh."""
    model = cq.importers.importStep(step_path)
    
    if format_key in ["STL", "AMF"]:
        cq.exporters.export(model, export_path, format_key)
        return model

    with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as tmp:
        cq.exporters.export(model, tmp.name, "STL")
        mesh = trimesh.load(tmp.name)
    
    ext_map = {"OBJ": "obj", "GLTF": "glb", "3MF": "3mf", "PLY": "ply"}
    if format_key in ext_map:
        mesh.export(export_path, file_type=ext_map[format_key])
        
    return model

def render_preview(mesh):
    """Generates an ISOMETRIC engineering view."""
    x, y, z = mesh.vertices.T
    i, j, k = mesh.faces.T
    
    fig = go.Figure(data=[go.Mesh3d(
        x=x, y=y, z=z, i=i, j=j, k=k,
        color='#e5e5e5', 
        opacity=1.0, 
        flatshading=True,
        lighting=dict(ambient=0.4, diffuse=0.6, roughness=0.1, specular=0.3, fresnel=0.1),
        lightposition=dict(x=100, y=200, z=500)
    )])
    
    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False),
            bgcolor='rgba(0,0,0,0)',
            aspectmode='data',
            camera=dict(projection=dict(type='orthographic'), eye=dict(x=1.25, y=1.25, z=1.25))
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        height=450,
        paper_bgcolor='rgba(0,0,0,0)'
    )
    return fig

# --- 5. DATA ---
# CHANGED: Default page is now "converter"
if 'page' not in st.session_state: st.session_state.page = "converter"

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
        if st.button("GENESIS", key="nav_home"): st.session_state.page = "converter"
    with c3: 
        if st.button("ARCHIVE", key="nav_lib"): st.session_state.page = "library"
    st.markdown("<hr style='border-top: 1px solid #eee; margin: 10px 0 30px 0;'>", unsafe_allow_html=True)

# --- PAGE: CONVERTER (DEFAULT) ---
if st.session_state.page == "converter":
    col_view, col_ctrl = st.columns([1.5, 1], gap="large")
    
    uploaded_file = None 
    
    with col_ctrl:
        st.markdown("### IMPORT")
        uploaded_file = st.file_uploader("Upload STEP File", type=["step", "stp"], label_visibility="collapsed")
        
        # AUTO-PREVIEW
        if uploaded_file:
            if "current_file" not in st.session_state or st.session_state.current_file != uploaded_file.name:
                with st.spinner("Analyzing Geometry..."):
                    with tempfile.TemporaryDirectory() as temp_dir:
                        step_path = os.path.join(temp_dir, "preview.step")
                        stl_path = os.path.join(temp_dir, "preview.stl")
                        with open(step_path, "wb") as f: f.write(uploaded_file.getbuffer())
                        try:
                            convert_geometry(step_path, stl_path, "STL")
                            st.session_state.mesh = trimesh.load(stl_path)
                            st.session_state.current_file = uploaded_file.name
                            if 'dl_data' in st.session_state: del st.session_state.dl_data
                        except Exception as e: st.error(f"Preview Error: {e}")

        st.markdown("### EXPORT CONFIG")
        export_fmt = st.selectbox("Export Format", ["STL", "OBJ", "GLTF", "3MF", "PLY", "AMF"])
        c_archive = st.checkbox("Add to Public Archive", value=True)
        c_material = st.selectbox("Material Tag", ["ALUMINUM 6061", "STAINLESS STEEL", "PLA PLASTIC"])

        if uploaded_file:
            if st.button("GENERATE DOWNLOAD FILE"):
                with st.spinner(f"Converting to {export_fmt}..."):
                    with tempfile.TemporaryDirectory() as temp_dir:
                        step_path = os.path.join(temp_dir, "input.step")
                        ext_map = {"STL":".stl", "OBJ":".obj", "GLTF":".glb", "3MF":".3mf", "PLY":".ply", "AMF":".amf"}
                        out_ext = ext_map[export_fmt]
                        out_path = os.path.join(temp_dir, f"output{out_ext}")
                        with open(step_path, "wb") as f: f.write(uploaded_file.getbuffer())
                        try:
                            convert_geometry(step_path, out_path, export_fmt)
                            with open(out_path, "rb") as f:
                                st.session_state.dl_data = f.read()
                                st.session_state.dl_name = f"genesis_export{out_ext}"
                                st.session_state.dl_mime = "model/gltf-binary" if export_fmt == "GLTF" else "application/octet-stream"
                            if c_archive and supabase:
                                supabase.table("assets").insert({
                                    "name": uploaded_file.name.split('.')[0].upper(),
                                    "type": c_material
                                }).execute()
                        except Exception as e: st.error(f"Conversion Error: {e}")

    with col_view:
        if 'mesh' in st.session_state:
            st.markdown("### ISOMETRIC STUDIO")
            # 1. Render Chart
            fig = render_preview(st.session_state.mesh)
            st.plotly_chart(fig, use_container_width=True)
            
            # 2. Controls & Downloads
            m = st.session_state.mesh
            st.caption(f"Geometry: {len(m.vertices):,} Vertices | {len(m.faces):,} Faces")
            
            # DOWNLOAD ROW
            d1, d2 = st.columns([1, 1])
            
            with d1:
                # IMAGE GENERATION
                try:
                    # Generate High-Res PNG
                    img_bytes = fig.to_image(format="png", width=2000, height=1500, scale=2)
                    st.download_button(
                        label="📷 SAVE RENDER (PNG)",
                        data=img_bytes,
                        file_name="genesis_render.png",
                        mime="image/png"
                    )
                except Exception as e:
                    # More detailed error message for debugging
                    st.warning(f"Render Busy (Needs Kaleido in Docker): {e}")
            
            with d2:
                # 3D FILE DOWNLOAD
                if 'dl_data' in st.session_state:
                    st.download_button(
                        label=f"⬇ SAVE {export_fmt}",
                        data=st.session_state.dl_data,
                        file_name=st.session_state.dl_name,
                        mime=st.session_state.dl_mime
                    )
        else:
            st.markdown("### VISUALIZER")
            st.markdown("<div style='border:1px solid #eee; height:450px; display:flex; align-items:center; justify-content:center; color:#999; background:#fafafa;'>Drop STEP file to preview</div>", unsafe_allow_html=True)

# --- PAGE: LIBRARY ---
elif st.session_state.page == "library":
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
