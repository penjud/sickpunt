# Use Python 3.11 as the base image
FROM python:3.11
# Set working directory
WORKDIR /betfair

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the code into the container
COPY . .

# Start the application
CMD ["python", "-m", "betfair.main"]
