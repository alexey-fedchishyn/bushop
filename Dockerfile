FROM python:3.10.13

WORKDIR /django

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY . .

RUN chmod +x ./web.sh

CMD [ "./web.sh" ]