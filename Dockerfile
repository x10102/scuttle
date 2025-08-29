FROM python:3.11-alpine

WORKDIR /app

COPY requirements.txt /app

RUN apk add --no-cache gcc python3-dev musl-dev linux-headers

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 8080

CMD ["python", "App.py"]