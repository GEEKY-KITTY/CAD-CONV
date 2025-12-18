import streamlit as st
import cadquery as cq
import trimesh
import numpy as np
import tempfile
import os
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import feedparser

# --- 1. CONFIGURATION & SESSION STATE ---
st.set_page_config(
    page_title="CURIOSITY 3D | Platform",
    page_icon="🧊",
    layout="wide"
)

# Initialize current page in session state
if 'page' not in st.session_state:
    st.session_state.page = "Home"

# --- 2. GLOBAL CSS (PROFESSIONAL THEME) ---
st.markdown("""
    <style>
    /* --- Global Variables --- */
    :root {
        --bg-color: #0e1117;
        --card-bg: #1c2128;
        --text-primary: #ffffff;
        --text-secondary: #a3b3bc;
        --accent-color: #3498db; /* Professional Blue */
        --border-color: #30363d;
    }

    .stApp { background-color: var(--bg-color); }

    /* --- Typography --- */
    h1, h2, h3 {
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        color: var(--text-primary);
        font-weight: 600;
    }
    p, li, a {
        color: var(--text-secondary);
        font-size: 1rem;
        line-height: 1.6;
    }

    /* --- Navigation Button Style --- */
    div.stButton > button {
        background-color: transparent;
        border: 1px solid var(--border-color);
        color: var(--text-secondary);
        border-radius: 6px;
        padding: 0.5rem 1rem;
        transition: all 0.2s ease-in-out;
        font-weight: 500;
    }
    div.stButton > button:hover {
        border-color: var(--accent-color);
        color: var(--accent-color);
        background-color: rgba(52, 152, 219, 0.1);
    }
    /* Style for the active page button */
    div.stButton > button[kind="primary"] {
        background-color: var(--accent-color);
        border-color: var(--accent-color);
        color: white;
    }

    /* --- Metric & Analysis Cards --- */
    div[data-testid="stMetric"] {
        background-color: var(--card-bg);
        border: 1px solid var(--border-color);
        padding: 15px;
        border-radius: 8px;
    }
    div[data-testid="stMetricLabel"] { color: var(--text-secondary); }
    div[data-testid="stMetricValue"] { color: var(--text-primary); }

    /* --- News Card Style --- */
    .news-card {
        background-color: var(--card-bg);
        padding: 24px;
        border-radius: 8px;
        margin-bottom: 16px;
        border: 1px solid var(--border-color);
        transition: transform 0.2s, border-color 0.2s;
    }
    .news-card:hover {
        border-color: var(--accent-color);
        transform: translateY(-2px);
    }
    .news-title {
        margin: 0 0 12px 0;
        color: var(--text-primary);
        font-size: 1.2rem;
        font-weight: 600;
        text-decoration: none;
        display: block;
    }
    .news-title:hover { color: var(--accent-color); }
    .news-meta {
        color: var(--text-secondary);
        font-size: 0.85rem;
        display: flex;
        align-items: center;
    }

    /* --- Footer Style --- */
    footer {
        margin-top: 60px;
        padding: 40px 0;
        border-top: 1px solid var(--border-color);
        text-align: center;
        color: var(--text-secondary);
        font-size: 0.9rem;
    }
    footer a {
        color: var(--text-secondary);
        text-decoration: none;
        margin: 0 15px;
        transition: color 0.2s;
    }
    footer a:hover { color: var(--accent-color); }
    .footer-links { margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---
def visualize_mesh(mesh):
    x, y, z = mesh.vertices.T
    i, j, k = mesh.faces.T
    fig = go.Figure(data=[go.Mesh3d(
        x=x, y=y, z=z, i=i, j=j, k=k,
        color='#3498db', opacity=0.5, name='Model',
        flatshading=True,
        lighting=dict(ambient=0.6, diffuse=0.5, roughness=0.1, specular=0.1)
    )])
    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False),
            bgcolor='rgba(0,0,0,0)', aspectmode='data'
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    return fig

def change_page(page_name):
    st.session_state.page = page_name

# --- 4. NAVIGATION & LAYOUT ---

# Top Navigation Bar
def top_nav():
    cols = st.columns([1, 1, 1, 1, 1])
    pages = ["Home", "Future of CAD", "News", "About Us", "Contact"]
    
    for i, page_name in enumerate(pages):
        with cols[i]:
            button_type = "primary" if st.session_state.page == page_name else "secondary"
            if st.button(page_name, key=f"nav_{page_name}", use_container_width=True, type=button_type):
                change_page(page_name)
                st.rerun()

# Page Header
st.title("CURIOSITY 3D")
st.caption("Engineering & Design Intelligence Platform")
top_nav()
st.markdown("---")

# --- 5. PAGE CONTENT LOGIC ---

# === PAGE: HOME (Converter Tool) ===
if st.session_state.page == "Home":
    st.header("Intelligent CAD Converter")
    st.markdown("Transform **STEP** files into manufacturing-ready formats with instant **DFM analysis**.")
    
    col_setup, col_upload = st.columns([1, 2])
    with col_setup:
        st.subheader("⚙️ Setup")
        nozzle_size = st.number_input("Printer Nozzle Size (mm)", 0.2, 1.2, 0.4, step=0.1)
        export_format = st.selectbox("Target Format", ["stl", "obj", "3mf", "ply", "glb"])
    
    with col_upload:
        st.subheader("📂 File Input")
        uploaded_file = st.file_uploader("Drop your .STEP file here", type=["step", "stp"])

    if uploaded_file:
        st.markdown("---")
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = os.path.join(temp_dir, uploaded_file.name)
            temp_stl = os.path.join(temp_dir, "temp.stl")
            base_name = os.path.splitext(uploaded_file.name)[0]
            
            with open(input_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            with st.status("Processing Geometry...", expanded=True) as status:
                try:
                    st.write("Importing STEP model...")
                    model = cq.importers.importStep(input_path)
                    st.write("Generating high-fidelity mesh...")
                    cq.exporters.export(model, temp_stl, tolerance=0.01, angularTolerance=0.1)
                    status.update(label="✅ Geometry Processed Successfully", state="complete", expanded=False)
                except Exception as e:
                    st.error(f"Processing Failed: {e}")
                    st.stop()

            mesh = trimesh.load(temp_stl)
            
            c_viz, c_data = st.columns([3, 2])
            with c_viz:
                st.subheader("Interactive 3D Preview")
                st.plotly_chart(visualize_mesh(mesh), use_container_width=True)
            with c_data:
                st.subheader("📊 DFM Analysis")
                
                m1, m