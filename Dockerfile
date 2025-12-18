FROM continuumio/miniconda3

WORKDIR /app

# 1. Install Linux System Libraries
# We added 'libnss3', 'libgtk-3-0', 'libasound2' etc. for the Rendering Engine (Kaleido)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libglu1-mesa \
    libx11-6 \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# 2. Install CadQuery & Math Engine via Conda
RUN conda install -c cadquery -c conda-forge cadquery=master numpy scipy -y

# 3. Install Web & App Tools via Pip
# We force a specific version of Kaleido (0.2.1) which is most stable on Docker
RUN pip install streamlit trimesh plotly shapely path supabase "kaleido==0.2.1"

# 4. Copy Application Files
COPY . .

# 5. Launch Command
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]
