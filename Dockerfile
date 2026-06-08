FROM registry.paas.psnc.pl/base/library/python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chgrp -R 0 /app && chmod -R g+rwX /app

EXPOSE 8501

CMD ["streamlit", "run", "TALLMesh.py", "--server.port=8501", "--server.address=0.0.0.0"]