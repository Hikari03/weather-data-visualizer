FROM python:3.13-slim

WORKDIR .

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app
COPY . ./

EXPOSE 8502

CMD [ "./run.sh" ]
