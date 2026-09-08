
FROM registry.paas.psnc.pl/base/library/python:3.12-slim

WORKDIR /app

ENV HOME=/app
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/ .streamlit \
    && chgrp -R 0 /app \
    && chmod -R g+rwX /app

EXPOSE 8501

CMD ["streamlit", "run", "TALLMesh.py", "--server.port=8501", "--server.address=0.0.0.0"]