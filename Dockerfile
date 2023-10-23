# Use Python 3.11 as the base image
FROM python:3.11
# Set working directory
WORKDIR /betfair

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the code into the container
COPY . .

# Set the entrypoint to python
ENTRYPOINT ["python", "-m"]

# Set the default script to run if nothing else is specified
CMD ["betfair.main"]
