FROM python:3-alpine

RUN apk add --no-cache py3-pip py3-setuptools

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install git+https://github.com/yupix/Mi.py.git@v3.3.0

COPY . .

CMD [ "python", "-u", "./rdbot.py" ]
