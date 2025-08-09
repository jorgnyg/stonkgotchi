FROM python:3.8

WORKDIR /app

# Copy the Python script into the container
COPY . .

# Install Python dependencies
RUN pip install playwright fastapi uvicorn

# Install Playwright browsers
RUN playwright install --with-deps

# Command to run the FastAPI app with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
