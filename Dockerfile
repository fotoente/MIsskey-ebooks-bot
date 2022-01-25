FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install git+https://github.com/yupix/Mi.py.git@v3.2.1

COPY . .

CMD [ "python", "./rdbot.py" ]
