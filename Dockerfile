FROM python:3.11

WORKDIR /opt

COPY requirements.txt .
COPY app.py .

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y
RUN pip install -r requirements.txt

CMD ["python", "app.py"]