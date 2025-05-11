FROM python:3.13-slim

WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port the app runs on
EXPOSE 8080

# Command to run the application
CMD ["sh", "-c", "python manage.py migrate && python manage.py check && gunicorn splitfree_backend.wsgi --bind 0.0.0.0:8080"]
