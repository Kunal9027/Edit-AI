FROM python:3.11.9-slim

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --cache-dir /pip-cache --no-cache-dir -r requirements.txt

# Install Node.js and npm
RUN apt-get update && apt-get install -y nodejs npm

# Install ImageMagick
RUN apt-get update && apt-get install -y imagemagick

# Update the policy.xml file to allow all operations
RUN sed -i 's/policy.cdf "rights" "none"/policy.cdf "rights" "all"/g' /etc/ImageMagick-6/policy.xml

# Check the ImageMagick configuration
RUN identify -list policy

# Copy the project files
COPY . .

# Set up the theme directory and Tailwind CSS
RUN cd theme && npm init -y && npm install -D tailwindcss@latest postcss@latest autoprefixer@latest

# Create necessary directories and set permissions
RUN mkdir -p media/input_videos media/output_videos && chmod -R 755 media

# Collect static files and compile Tailwind CSS
RUN python manage.py tailwind install && python manage.py tailwind build && python manage.py collectstatic --noinput

# Expose the port
EXPOSE 8000

# Set the default command
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]