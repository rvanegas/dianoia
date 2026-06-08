FROM python:3.13-slim
WORKDIR /app/src
COPY src/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY LOGIC-ASCII.md /app/LOGIC-ASCII.md
COPY LOGIC-JSON.md /app/LOGIC-JSON.md
COPY src/ .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
