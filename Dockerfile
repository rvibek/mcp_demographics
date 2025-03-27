# Use official Python runtime as the base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy your script and setup files
COPY unhcr_demographics.py .
COPY setup.py .

# Install dependencies
RUN pip install --no-cache-dir -e .

# Command to run the MCP server
CMD ["python", "unhcr_demographics.py"]