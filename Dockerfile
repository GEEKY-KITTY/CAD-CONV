FROM continuumio/miniconda3

WORKDIR /app

# 1. Install Linux System Libraries
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libglu1-mesa \
    libx11-6 \
    && rm -rf /var/lib/apt/lists/*

# 2. Install CadQuery
RUN conda install -c cadquery -c conda-forge cadquery=master -y

# 3. Install Python Tools (Added 'supabase' here if you are using the DB version)
RUN pip install streamlit trimesh plotly scipy numpy shapely path cadquery-essential supabase

# 4. Copy Application
COPY . .

# 5. Launch with Security Checks Disabled
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]
