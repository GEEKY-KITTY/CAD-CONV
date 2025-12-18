---
title: Genesis Converter
emoji: ⚙️
colorFrom: gray
colorTo: green
sdk: docker
pinned: false
app_port: 8501
---

# Genesis Converter

A professional-grade STEP-to-STL converter and geometric analysis tool.

### Features
* **Ingestion:** Securely uploads STEP/STP files.
* **Conversion:** Uses CadQuery to tessellate B-Rep geometry into mesh data.
* **Analysis:** Calculates volume, vertex count, and checks for non-manifold edges.
* **Visualization:** Renders interactive 3D models using Plotly.

### Tech Stack
* **Engine:** Python 3.10 + CadQuery
* **Frontend:** Streamlit
* **Deployment:** Docker
