FROM python:3

RUN apt-get update && apt-get -y upgrade

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install git+https://github.com/yupix/Mi.py.git@v3.3.0

COPY . .

CMD [ "python", "-u", "./rdbot.py" ]
