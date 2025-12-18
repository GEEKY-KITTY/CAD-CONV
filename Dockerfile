FROM continuumio/miniconda3

# 1. Set up the working folder
WORKDIR /app

# 2. Install Linux System Libraries (Required for 3D Graphics)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libglu1-mesa \
    libx11-6 \
    && rm -rf /var/lib/apt/lists/*

# 3. Install the CAD Engine via Conda (The heavy lifter)
RUN conda install -c cadquery -c conda-forge cadquery=master -y

# 4. Install Web & Analysis Tools (Updated to include 'feedparser')
RUN pip install streamlit trimesh plotly scipy numpy shapely path feedparser

# 5. Copy your code into the container
COPY . .

# 6. Open the port for the website
EXPOSE 8501

# 7. Launch the app
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]