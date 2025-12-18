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

# --- 2. SUPABASE CONNECTION ---
@st.cache_resource
def init_connection():
    try:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        if not url or not key: return None
        return create_client(url, key)
    except: return None

supabase = init_connection()

# --- 3. CRAIGHILL-INSPIRED CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

    /* GLOBAL RESET */
    .stApp {
        background-color: #ffffff !important;
        font-family: 'Inter', sans-serif;
        color: #1a1a1a;
    }
    
    /* REMOVE PADDING */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 5rem !important;
        max-width: 1400px !important;
    }

    /* TYPOGRAPHY */
    h1, h2, h3 {
        text-transform: uppercase;
        font-weight: 600 !important;
        letter-spacing: 0.05em;
        color: #000 !important;
        margin-bottom: 0.5rem;
    }
    
    /* BUTTONS */
    div.stButton > button {
        background-color: #000000;
        color: #ffffff;
        border: 1px solid #000000;
        border-radius: 0px;
        padding: 1rem 2rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-size: 0.8rem;
        width: 100%;
        transition: all 0.2s;
    }
    div.stButton > button:hover {
        background-color: #ffffff;
        color: #000000;
    }
    
    /* UPLOAD BOX */
    .stFileUploader {
        border: 1px solid #e0e0e0;
        padding: 40px;
        background-color: #ffffff;
        border-radius: 0px;
    }
    
    /* HIDE JUNK */
    footer, header { display: none !important; }
    </style>
""", unsafe_allow_html=True)

# --- 4. DATA MOCK & FETCH ---
if 'page' not in st.session_state: st.session_state.page = "library"

mock_images = [
    "https://images.unsplash.com/photo-1586022137667-17eb1082697e?q=80&w=800&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1618419266782-62281fa04910?q=80&w=800&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1535384661727-b06d87786196?q=80&w=800&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1555664424-778a696fa8db?q=80&w=800&auto=format&fit=crop",
]

def fetch_assets():
    if not supabase: 
        return [
            {"name": "HELIX KEYRING", "type": "BRASS", "img": mock_images[0]},
            {"name": "SIDEWINDER KNIFE", "type": "STEEL", "img": mock_images[1]},
            {"name": "VECTOR STAND", "type": "ALUMINUM", "img": mock_images[2]},
            {"name": "NEMA ASSEMBLY", "type": "VAPOR BLACK", "img": mock_images[3]},
        ]
    try:
        data = supabase.table("assets").select("*").order("created_at", desc=True).execute().data
        for item in data: 
            # If no image in DB, verify one from mock list
            if 'img' not in item:
                item['img'] = random.choice(mock_images)
        return data
    except: return []

# --- 5. LOGIC ENGINE ---
def convert_step_to_stl(step_path, stl_path):
    model = cq.importers.importStep(step_path)
    cq.exporters.export(model, stl_path)
    return model

def render_preview(mesh):
    x, y, z = mesh.vertices.T
    i, j, k = mesh.faces.T
    
    # THIS WAS THE BLOCK CAUSING ERRORS - BRACKETS ARE FIXED NOW
    fig = go.Figure(data=[go.Mesh3d(
        x=x, y=y, z=z, i=i, j=j, k=k,
        color='#e5e5e5', 
        opacity=1.0, 
        flatshading=True,
        lighting=dict(ambient=0.5, diffuse=0.5, roughness=0.1, specular=0.1)
    )])
    
    fig.update_layout(
        scene=dict(xaxis_visible=False, yaxis_visible=False, zaxis_visible=False, bgcolor='white'),
        margin=dict(l=0,r=0,b=0,t=0), height=500
    )
    return fig

# --- 6. NAVIGATION HEADER ---
c_head = st.container()
with c_head:
    cols = st.columns([1, 4, 1, 1])
    with cols[0]:
        if st.button("GENESIS", key="home"): st.session_state.page = "library"
    with cols[2]:
        if st.button("SHOP", key="nav_shop"): st.session_state.page = "library"
    with cols[3]:
        if st.button("CREATE", key="nav_tool"): st.session_state.page = "converter"
    st.markdown("<div style='height: 1px; background: #eee; margin: 20px 0 40px 0;'></div>", unsafe_allow_html=True)

# --- PAGE: SHOP (LIBRARY) ---
if st.session_state.page == "library":
    st.markdown("### DAILY CARRY / ARCHIVE")
    st.markdown("<p style='font-size: 0.9rem; color: #666; max-width: 600px; margin-bottom: 40px;'>These are our daily necessities, the engineering assets you will reach for time and time again.</p>", unsafe_allow_html=True)
    
    assets = fetch_assets()
    rows = [assets[i:i + 3] for i in range(0, len(assets), 3)]
    
    for row in rows:
        cols = st.columns(3)
        for idx, asset in enumerate(row):
            with cols[idx]:
                st.image(asset.get('img', mock_images[0]), use_container_width=True)
                st.markdown(f"""
                <div style="margin-top: 10px;">
                    <div style="font-weight: 600; font-size: 0.95rem; letter-spacing: 0.02em;">{asset['name']}</div>
                    <div style="color: #666; font-size: 0.85rem; margin-top: 2px;">{asset['type']}</div>
                    <div style="color: #000; font-size: 0.85rem; margin-top: 5px;">$ DOWNLOAD</div>
                </div>
                <br>
                """, unsafe_allow_html=True)

# --- PAGE: CREATE (CONVERTER) ---
elif st.session_state.page == "converter":
    col_img, col_info = st.columns([1.5, 1], gap="large")
    
    with col_img:
        if 'mesh' in st.session_state:
            st.plotly_chart(render_preview(st.session_state.mesh), use_container_width=True)
        else:
            st.image("https://images.unsplash.com/photo-1629737683709-e85df649f875?q=80&w=1200", caption="Awaiting Geometry Input")

    with col_info:
        st.markdown("<h1>GENESIS CONVERTER</h1>")
        st.markdown("<p style='font-size: 1.1rem; color: #444; margin-bottom: 30px;'>Transform mathematical STEP files into production-ready STL meshes.</p>", unsafe_allow_html=True)
        st.markdown("---")
        
        uploaded_file = st.file_uploader("UPLOAD GEOMETRY (STEP)", type=["step", "stp"])
        c_check = st.checkbox("ADD TO ARCHIVE", value=True)
        c_type = st.selectbox("MATERIAL / TYPE", ["STAINLESS STEEL", "BRASS", "VAPOR BLACK", "ALUMINUM"])
        st.markdown("<br>", unsafe_allow_html=True)
        
        if uploaded_file:
            if st.button("PROCESS GEOMETRY — FREE"):
                with st.spinner("PROCESSING..."):
                    with tempfile.TemporaryDirectory() as temp_dir:
                        step_path = os.path.join(temp_dir, "in.step")
                        stl_path = os.path.join(temp_dir, "out.stl")
                        with open(step_path, "wb") as f: f.write(uploaded_file.getbuffer())
                        
                        try:
                            convert_step_to_stl(step_path, stl_path)
                            st.session_state.mesh = trimesh.load(stl_path)
                            with open(stl_path, "rb") as f: st.session_state.stl_data = f.read()
                            
                            if c_check and supabase:
                                supabase.table("assets").insert({
                                    "name": uploaded_file.name.split('.')[0].upper(),
                                    "type": c_type,
                                    "author": "GUEST"
                                }).execute()
                        except Exception as e:
                            st.error(f"ERROR: {e}")

            if 'stl_data' in st.session_state:
                st.download_button("DOWNLOAD ARTIFACT (.STL)", st.session_state.stl_data, "genesis.stl", "model/stl")
