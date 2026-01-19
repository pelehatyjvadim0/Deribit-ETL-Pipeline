FROM python:3.12-slim
WORKDIR /deribit_tracker
ENV PYTHONPATH=/deribit_tracker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]