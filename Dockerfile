FROM python:3.11

# Pull Python Image from Docker Hub
FROM python:3.11

# Set the working directory
WORKDIR /opt

# Install python3-venv
RUN apt-get update && \
    apt-get install -y python3-venv && \
    apt-get install -y ffmpeg libsm6 libxext6 && \
    rm -rf /var/lib/apt/lists/*

# Create a virtual environment
RUN python3 -m venv /opt/venv

# Ensure the virtual environment is used
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip to the latest version
RUN pip install --upgrade pip

# Copy the requirements file and install dependencies
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY app.py ./

CMD ["python", "app.py"]