# Start from a Python 3.11 base image
FROM python:3.11-rc

# Install necessary system packages
RUN apt-get update -y && \
    apt-get install -y gnupg2 \
    curl \
    build-essential

# Install pyodbc dependencies
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/9/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update -y && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    unixodbc \
    unixodbc-dev 

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file to the Docker image 
COPY requirements.txt ./

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the remaining application files to the Docker image
COPY . .

# Make sure your application listens on 0.0.0.0 interface
# You may need to modify this step according to your app configuration
RUN sed -i 's/app.run()/app.run(host="0.0.0.0")/g' ./stream.py

# Setup gunicorn HTTP server as a command
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:5000"]
