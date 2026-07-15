FROM python:3.13.5-slim

WORKDIR /app

COPY ./requirements.prod.txt /app/requirements.prod.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.prod.txt

COPY ./src /app/src

EXPOSE 8000

CMD ["uvicorn","src.main:app","--host","0.0.0.0","--port","8000","--reload"]