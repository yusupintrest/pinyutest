FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create downloads directory
RUN mkdir -p downloads
RUN chmod 777 downloads

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"] 