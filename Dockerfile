FROM python:3

WORKDIR .

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app
COPY . ./

EXPOSE 8502

CMD [ "./run.sh" ]