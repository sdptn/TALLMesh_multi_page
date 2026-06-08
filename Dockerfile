FROM registry.paas.psnc.pl/base/library/python:3.12-slim

WORKDIR /app

# System deps (needed for PyMuPDF etc.)
RUN apt-get update && apt-get install -y \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

#OpenShift permissions
RUN chgrp -R 0 /app && chmod -R g+rwX /app

# Streamlit port
EXPOSE 8501

# Run app
CMD ["streamlit", "run", "TALLMesh.py", "--server.port=8501", "--server.address=0.0.0.0"]