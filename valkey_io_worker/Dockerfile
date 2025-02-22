# Use a lightweight Python image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install uv (fast dependency manager)
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync

# Copy script
COPY main.py ./

# Default command
CMD ["uv", "run", "python", "main.py"]