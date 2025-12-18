FROM continuumio/miniconda3

WORKDIR /app

# 1. Install Linux System Libraries
# These are required for the 3D geometry engine to run
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libglu1-mesa \
    libx11-6 \
    && rm -rf /var/lib/apt/lists/*

# 2. Install CadQuery (The Geometry Kernel)
RUN conda install -c cadquery -c conda-forge cadquery=master -y

# 3. Install Python Tools
# Removed 'feedparser' since we removed the News section
RUN pip install streamlit trimesh plotly scipy numpy shapely path

# 4. Copy Application Files
COPY . .

# 5. Launch Command
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
