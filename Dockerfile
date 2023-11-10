FROM python:3.9-slim-buster

COPY requirements.txt requirements.txt  
RUN pip3 install -r requirements.txt 

EXPOSE 8000

COPY . .
WORKDIR .

CMD ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]