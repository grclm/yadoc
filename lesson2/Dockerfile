# Use an official Python runtime as a parent image
FROM python:3.9

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app

# Expose port 8000 for the Flask app to listen on
EXPOSE 5000

# Set the default command to start the Flask app using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
