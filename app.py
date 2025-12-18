import streamlit as st
import cadquery as cq
import trimesh
import numpy as np
import tempfile
import os
import plotly.graph_objects as go
import time

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="GENESIS CONVERTER",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. MODERN LIGHT THEME CSS ---
st.markdown("""
    <style>
    /* IMPORT FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;500;700;800&display=swap');

    /* RESET & BACKGROUND */
    .stApp {
        background-color: #f8fafc; /* Very light blue-grey */
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* REMOVE DEFAULT PADDING */
    .block-container {
        padding-top: 3rem;
        padding-bottom: 5rem;
    }

    /* TYPOGRAPHY */
    h1, h2, h3 {
        color: #0f172a; /* Slate 900 */
        font-weight: 800;
        letter-spacing: -0.03em;
    }
    h1 {
        font-size: 3.5rem !important;
        background: linear-gradient(135deg, #0f172a 0%, #334155 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    p, li, label {
        color: #475569; /* Slate 600 */
        font-size: 1.1rem;
        line-height: 1.6;
    }

    /* CARDS (The white boxes) */
    div[data-testid="stVerticalBlock"] > div {
        background-color: #ffffff;
        border-radius: 16px;
        padding: 30px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        border: 1px solid #e2e8f0;
    }
    
    /* FIX THE BUTTONS / NAV CARDS */
    div.stButton > button {
        background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%); /* Indigo */
        color: white;
        border: none;
        padding: 1rem 2rem;
        border-radius: 12px;
        font-weight: 700;
        font-size: 1rem;
        width: 100%;
        transition: all 0.2s ease;
        box-shadow: 0 10px 15px -3px rgba(79, 70, 229, 0.2);
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 20px 25px -5px rgba(79, 70, 229, 0.3);
    }
    
    /* FILE UPLOADER */
    .stFileUploader {
        border: 2px dashed #cbd5e1;
        border-radius: 12px;
        padding: 40px;
        background-color: #f1f5f9;
        transition: border-color 0.3s;
    }
    .stFileUploader:hover { border-color: #4f46e5; }
    
    /* REMOVE CARD STYLE FROM MAIN LAYOUT (So columns don't look boxed) */
    .main > div { background: transparent !important; border: none !important; box-shadow: none !important; }

    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIC FUNCTIONS ---
def convert_step_to_stl(step_path, stl_path):
    model = cq.importers.importStep(step_path)
    cq.exporters.export(model, stl_path)
    return model

def get_mesh_data(stl_path):
    return trimesh.load(stl_path)

def render_interactive(mesh):
    x, y, z = mesh.vertices.T
    i, j, k = mesh.faces.T
    fig = go.Figure(data=[go.Mesh3d(
        x=x, y=y, z=z, i=i, j=j, k=k,
        color='#4f46e5', 
        opacity=0.95,
        name='Model',
        flatshading=False,
        lighting=dict(ambient=0.4, diffuse=0.5, roughness=0.1, specular=0.4)
    )])
    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False),
            bgcolor='rgba(0,0,0,0)',
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        paper_bgcolor="rgba(0,0,0,0)",
        height=500
    )
    return fig

# --- 4. NAVIGATION ---
if 'page' not in st.session_state:
    st.session_state.page = "tool"

# HERO HEADER
c1, c2 = st.columns([2, 1])
with c1:
    st.markdown("# GENESIS **CONVERTER**")
    st.markdown("### The Bridge Between Parametric Design & Digital Manufacturing.")
    st.markdown("Transform mathematical STEP files into production-ready meshes with a single click.")
with c2:
    # Use a nice abstract 3D illustration
    st.image("https://images.unsplash.com/photo-1633613286991-611fe299c4be?q=80&w=2070&auto=format&fit=crop", use_container_width=True)

st.markdown("---")

# NAVIGATION BAR (Fixed Widths to prevent ugly squashing)
col_nav1, col_nav2, col_spacer = st.columns([1, 1, 4])
with col_nav1:
    if st.button("🛠️ LAUNCH TOOL"): st.session_state.page = "tool"
with col_nav2:
    if st.button("📚 READ GUIDE"): st.session_state.page = "info"

# --- PAGE 1: THE TOOL ---
if st.session_state.page == "tool":
    st.markdown("## **Workspace**")
    
    c_upload, c_view = st.columns([1, 2], gap="large")
    
    with c_upload:
        st.info("**Step 1:** Upload your geometry.")
        uploaded_file = st.file_uploader("Drop STEP file here", type=["step", "stp"])
        
        if uploaded_file:
            # SAVE & CONVERT
            with tempfile.TemporaryDirectory() as temp_dir:
                step_path = os.path.join(temp_dir, "input.step")
                stl_path = os.path.join(temp_dir, "output.stl")
                
                with open(step_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                with st.spinner("Tessellating Surfaces..."):
                    try:
                        convert_step_to_stl(step_path, stl_path)
                        st.session_state.mesh = get_mesh_data(stl_path)
                        with open(stl_path, "rb") as f:
                            st.session_state.stl_data = f.read()
                    except Exception as e:
                        st.error(f"Error: {e}")

            if 'stl_data' in st.session_state:
                st.success("Conversion Complete!")
                st.download_button(
                    "⬇️ Download .STL File",
                    data=st.session_state.stl_data,
                    file_name="converted_model.stl",
                    mime="model/stl",
                    use_container_width=True
                )

    with c_view:
        if 'mesh' in st.session_state:
            st.markdown("#### **Interactive Preview**")
            # Metrics
            m1, m2, m3 = st.columns(3)
            mesh = st.session_state.mesh
            m1.metric("Volume (cm³)", f"{mesh.volume/1000:.2f}")
            m2.metric("Faces", f"{len(mesh.faces):,}")
            m3.metric("Watertight", str(mesh.is_watertight))
            
            st.plotly_chart(render_interactive(mesh), use_container_width=True)
        else:
            # Placeholder Image
            st.image("https://plus.unsplash.com/premium_photo-1661963874418-d111a31a306c?q=80&w=2070&auto=format&fit=crop", caption="Awaiting Geometry...", use_container_width=True)

# --- PAGE 2: KNOWLEDGE BASE ---
elif st.session_state.page == "info":
    
    # ILLUSTRATED HEADER
    st.image("https://images.unsplash.com/photo-1581091226825-a6a2a5aee158?q=80&w=2070&auto=format&fit=crop", use_container_width=True)
    
    st.markdown("## **The Engineering Handbook**")
    
    col_text, col_details = st.columns([2, 1], gap="large")
    
    with col_text:
        st.markdown("""
        ### Why do we convert STEP to STL?
        
        **STEP (Standard for the Exchange of Product model data)** is a "Brep" format. It uses mathematical formulas to define curves and surfaces. It is infinite resolution.
        
        **STL (Stereolithography)** is a "Mesh" format. It uses thousands of tiny triangles to approximate the shape. 
        
        **The Problem:** 3D Printers and Game Engines cannot read math formulas. They only understand triangles.
        
        **The Solution:** This tool "Tessellates" the model—it calculates exactly where to place triangles to match the mathematical curve as closely as possible.
        """)
        
        st.markdown("### Best Practices for DFM (Design for Mfg)")
        st.markdown("""
        * **Wall Thickness:** Ensure walls are > 1.2mm for injection molding.
        * **Draft Angles:** Add 2° draft to vertical walls so the part can eject from the mold.
        * **Fillets:** Add radii to internal corners to reduce stress concentrations.
        """)

    with col_details:
        st.info("💡 **Did you know?**")
        st.markdown("The STL format was invented in 1987 by 3D Systems specifically for the first SLA printers. It is over 35 years old and still the standard!")
        
        st.warning("⚠️ **Common Error**")
        st.markdown("**Non-Manifold Geometry:** If your STEP file has a 'gap' between surfaces, the STL will have a hole. This causes prints to fail. Always check the 'Watertight' metric in this tool.")
