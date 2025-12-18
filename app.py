import streamlit as st
import cadquery as cq
import trimesh
import numpy as np
import tempfile
import os
import plotly.graph_objects as go
import time
from io import BytesIO

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="GENESIS CONVERTER",  # REBRANDED
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. GENESIS UI THEME (Shared Design Language) ---
st.markdown("""
    <style>
    /* FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=JetBrains+Mono:wght@400;700&display=swap');

    /* GLOBAL THEME */
    .stApp {
        background: #050505;
        font-family: 'Inter', sans-serif;
    }
    
    /* ANIMATED BACKGROUND (The "Engineering Void") */
    .stApp::before {
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100vw; height: 100vh;
        background: 
            radial-gradient(circle at 10% 20%, rgba(0, 255, 157, 0.08), transparent 20%), 
            radial-gradient(circle at 90% 80%, rgba(0, 163, 255, 0.08), transparent 20%);
        z-index: -1;
        pointer-events: none;
    }

    /* TYPOGRAPHY */
    h1, h2, h3 { color: #fff; font-weight: 800; letter-spacing: -0.02em; }
    h1 {
        background: linear-gradient(90deg, #fff, #94a3b8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem !important;
    }
    p, li { color: #94a3b8; font-weight: 300; line-height: 1.6; font-size: 1.05rem; }
    strong { color: #fff; font-weight: 600; }

    /* GLASSMORPHISM CARDS */
    div[data-testid="stVerticalBlock"] > div {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 25px;
        backdrop-filter: blur(10px);
    }
    .main > div { background: transparent !important; border: none !important; }

    /* BUTTONS */
    div.stButton > button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%); /* Emerald Green Theme */
        color: white;
        border: none;
        padding: 0.6rem 1.5rem;
        border-radius: 6px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease;
        width: 100%;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px -10px rgba(16, 185, 129, 0.4);
    }

    /* UPLOADER STYLE */
    .stFileUploader {
        border: 2px dashed #333;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        transition: border-color 0.3s;
    }
    .stFileUploader:hover { border-color: #10b981; }

    /* METRIC CARDS */
    div[data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace;
        color: #10b981 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIC FUNCTIONS ---
def convert_step_to_stl(step_file_path, stl_file_path):
    """Core Engine: Converts STEP to STL using CadQuery."""
    # Import
    model = cq.importers.importStep(step_file_path)
    # Export
    cq.exporters.export(model, stl_file_path)
    return model

def get_mesh_data(stl_path):
    """Analysis Engine: Extracts physical properties."""
    mesh = trimesh.load(stl_path)
    return mesh

def render_interactive(mesh):
    """Visualization Engine: High-fidelity rendering."""
    x, y, z = mesh.vertices.T
    i, j, k = mesh.faces.T
    fig = go.Figure(data=[go.Mesh3d(
        x=x, y=y, z=z, i=i, j=j, k=k,
        color='#10b981', # Emerald Green
        opacity=0.90,
        name='Model',
        flatshading=False,
        lighting=dict(ambient=0.3, diffuse=0.6, roughness=0.1, specular=0.4)
    )])
    fig.update_layout(
        scene=dict(
            xaxis=dict(visible=False), yaxis=dict(visible=False), zaxis=dict(visible=False),
            bgcolor='rgba(0,0,0,0)',
            camera=dict(eye=dict(x=1.4, y=1.4, z=1.4))
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        paper_bgcolor="rgba(0,0,0,0)",
        height=500
    )
    return fig

# --- 4. NAVIGATION STATE ---
if 'page' not in st.session_state:
    st.session_state.page = "tool"

# Navbar
c1, c2, c3 = st.columns([1, 1, 6])
with c1:
    if st.button("🛠️ CONVERTER"): st.session_state.page = "tool"
with c2:
    if st.button("📚 KNOWLEDGE"): st.session_state.page = "info"

st.markdown("---")

# --- PAGE 1: THE TOOL (Converter) ---
if st.session_state.page == "tool":
    
    # Generic Professional Header
    st.markdown("<h1>GENESIS <span style='color:#10b981'>CONVERTER</span></h1>", unsafe_allow_html=True)
    st.markdown("<p>Professional Grade STEP-to-STL Translation Engine with Geometric Analysis.</p>", unsafe_allow_html=True)

    col_upload, col_view = st.columns([1, 2], gap="large")

    with col_upload:
        st.subheader("1. INGESTION")
        uploaded_file = st.file_uploader("Upload .STEP / .STP File", type=["step", "stp"])
        
        if uploaded_file:
            st.success(f"File loaded: {uploaded_file.name}")
            
            # Processing Hook
            with tempfile.TemporaryDirectory() as temp_dir:
                step_path = os.path.join(temp_dir, "input.step")
                stl_path = os.path.join(temp_dir, "output.stl")
                
                # Write to temp
                with open(step_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # CONVERT
                with st.spinner("Processing Geometry... Tessellating Surfaces..."):
                    try:
                        convert_step_to_stl(step_path, stl_path)
                        mesh = get_mesh_data(stl_path)
                        
                        # Store in session state for the view column
                        st.session_state.mesh = mesh
                        with open(stl_path, "rb") as f:
                            st.session_state.stl_data = f.read()
                            
                    except Exception as e:
                        st.error("Conversion Failed. File may be corrupted or non-manifold.")
                        st.error(e)

            if 'stl_data' in st.session_state:
                st.subheader("3. EXPORT")
                st.download_button(
                    label="💾 DOWNLOAD .STL",
                    data=st.session_state.stl_data,
                    file_name=uploaded_file.name.replace(".step", ".stl").replace(".stp", ".stl"),
                    mime="model/stl"
                )

    with col_view:
        st.subheader("2. ANALYSIS & VISUALIZATION")
        
        if 'mesh' in st.session_state:
            mesh = st.session_state.mesh
            
            # Metrics Row
            m1, m2, m3 = st.columns(3)
            m1.metric("Volume", f"{mesh.volume/1000:.2f} cm³")
            m2.metric("Vertices", f"{len(mesh.vertices):,}")
            m3.metric("Faces", f"{len(mesh.faces):,}")
            
            # 3D Render
            st.plotly_chart(render_interactive(mesh), use_container_width=True)
            
            if not mesh.is_watertight:
                st.warning("⚠ WARNING: Mesh is not watertight (Non-Manifold). May fail 3D printing.")
            else:
                st.markdown("✅ **Status:** Manifold / Watertight (Ready for Print)")
        else:
            # Empty State
            st.info("Awaiting Input File...")
            st.markdown("""
            <div style='text-align: center; opacity: 0.3; padding: 50px;'>
                <h1>🧊</h1>
                <p>Upload a file to visualize</p>
            </div>
            """, unsafe_allow_html=True)

# --- PAGE 2: KNOWLEDGE BASE (History & Research) ---
elif st.session_state.page == "info":
    
    st.markdown("<h1>THE EVOLUTION OF <span style='color:#10b981'>CAD</span></h1>", unsafe_allow_html=True)
    
    # 1. HISTORY SECTION
    st.markdown("### 🏛️ FROM SKETCHPAD TO CLOUD")
    st.markdown("""
    The journey of Computer-Aided Design (CAD) is the story of humanity transitioning from physical abstraction to digital precision.
    
    * **1963: The Genesis (Sketchpad):** Ivan Sutherland developed *Sketchpad* at MIT. It was the first time a human interacted with a computer graphically. It introduced the concept of "constraints" and "instancing."
    * **1970s: The 2D Era:** Systems like *AutoCAD* replaced drafting tables. While revolutionary, they were essentially "digital paper"—lines and arcs without physical awareness.
    * **1990s: Solid Modeling:** Tools like *SolidWorks* and *Pro/ENGINEER* introduced Parametric Modeling. Designers could now define relationships (e.g., "This hole is always 5mm from the edge").
    * **2010s: Cloud & Simulation:** *Fusion 360* and *Onshape* moved CAD to the cloud, allowing real-time collaboration and integrating FEM (Finite Element Method) simulation directly into the design workflow.
    * **Now:** We are entering the age of **Generative Design**, where AI acts as a co-pilot, suggesting topologies based on load constraints.
    """)
    
    st.markdown("---")
    
    # 2. DESIGN PROCESS SECTION
    st.markdown("### 📐 THE MODERN DESIGN LIFECYCLE")
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.markdown("""
        **PHASE 1: IDEATION & CONSTRAINT MAPPING**
        Before a single line is drawn, the engineer must define the 'Physics of the Problem'.
        * *Load Cases:* What forces will the part endure?
        * *Material Constraints:* Is it Aluminum 6061 or PLA Plastic?
        * *Assembly Context:* How does it fit with other parts?
        
        **PHASE 2: TOPOLOGY & MODELING**
        Using Constructive Solid Geometry (CSG):
        1.  **Sketching:** Defining 2D profiles on planes.
        2.  **Extrusion/Revolution:** Adding the Z-axis to create mass.
        3.  **Boolean Operations:** Cutting holes or adding bosses.
        4.  **Filleting:** Reducing stress concentrations at sharp corners.
        """)
        
    with c2:
        st.markdown("""
        **PHASE 3: SIMULATION (CAE)**
        We test without building. Using FEA (Finite Element Analysis), we simulate stress, heat, and fluid flow. If the Safety Factor < 1.5, we return to Phase 2.
        
        **PHASE 4: DESIGN FOR MANUFACTURING (DFM)**
        The model must be buildable.
        * *For CNC:* Are there undercuts? Is the tool radius too large?
        * *For 3D Printing:* Are overhangs > 45 degrees? Is the mesh watertight?
        * *For Injection Molding:* Do we have draft angles?
        """)

    st.markdown("---")

    # 3. PROS & CONS
    st.markdown("### ⚖️ CAD VS. TRADITIONAL DRAFTING")
    
    col_pros, col_cons = st.columns(2)
    with col_pros:
        st.success("**THE ADVANTAGES (PROS)**")
        st.markdown("""
        * **Infinite Iteration:** Changing a dimension updates the entire assembly instantly.
        * **Precision:** Mathematical accuracy down to the micron.
        * **Simulation:** Ability to test failure points before wasting material.
        * **CAM Integration:** Direct output to CNC machines and 3D printers.
        """)
        
    with col_cons:
        st.error("**THE CHALLENGES (CONS)**")
        st.markdown("""
        * **The "Perfect" Trap:** Designers can obsess over details that don't matter in the real world.
        * **Loss of Scale:** On a screen, a 10m wall looks the same as a 10mm clip.
        * **Complexity:** The learning curve for parametric constraints is steep.
        """)
