FROM continuumio/miniconda3

WORKDIR /app

# 1. Install Linux System Libraries (Required for 3D engine)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libglu1-mesa \
    libx11-6 \
    && rm -rf /var/lib/apt/lists/*

# 2. Install CadQuery & Math Engine via Conda (Prevents build errors)
RUN conda install -c cadquery -c conda-forge cadquery=master numpy scipy -y

# 3. Install Web & App Tools via Pip
# ADDED: 'kaleido' (For image rendering) and 'supabase' (For database)
RUN pip install streamlit trimesh plotly shapely path supabase kaleido

# 4. Copy Application Files
COPY . .

# 5. Launch Command (Includes Security Bypasses for Hugging Face)
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]
