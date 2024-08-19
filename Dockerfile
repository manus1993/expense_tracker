FROM python:3.11.9-slim-bullseye

COPY requirements.txt requirements.txt  
RUN pip3 install -r requirements.txt 

EXPOSE 8000

COPY . .
WORKDIR .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
