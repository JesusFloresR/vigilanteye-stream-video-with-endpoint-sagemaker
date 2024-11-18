FROM python:3.11

WORKDIR /opt

COPY requirements.txt .
COPY app.py .

RUN pip install -r requirements.txt

CMD ["python", "app.py"]