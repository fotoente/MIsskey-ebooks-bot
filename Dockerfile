FROM python:3-alpine

RUN apk add --no-cache \
	py3-pip \
	py3-setuptools \
	python3-dev \
	git \
	build-base

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install git+https://github.com/yupix/Mi.py.git@v3.9.9

COPY . .

CMD [ "python", "-u", "./rdbot.py" ]
