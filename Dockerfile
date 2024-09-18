FROM python:3.9-slim

# Set directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose port
EXPOSE 8002

# Command to run the migrations and then the application
CMD ["python", "app.py"]
#CMD ["sh", "-c", "flask db upgrade || flask db init && flask db migrate && flask db upgrade && python app.py"]



