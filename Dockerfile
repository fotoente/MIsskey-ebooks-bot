FROM python:3.10-alpine

RUN apk add --no-cache \
	py3-pip \
	py3-setuptools \
	python3-dev \
	git \
	build-base

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip3.10 install --upgrade pip
RUN pip3.10 install --no-cache-dir -r requirements.txt
RUN pip3.10 install git+https://github.com/yupix/MiPA.git
RUN pip3.10 install git+https://github.com/yupix/MiPAC.git
COPY . .

CMD [ "python3.10", "-u", "rdbot" ]
