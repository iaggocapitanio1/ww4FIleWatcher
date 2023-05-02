FROM python:3.8-slim-buster

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONBUFFERED=1 \
    APP_DIR=/home/app\
    WHATCH_DIR=/home/app/Projects

WORKDIR $APP_DIR

COPY . $APP_DIR/
COPY requirements.txt $APP_DIR/requirements.txt

RUN chmod +x $APP_DIR/requirements.txt && mkdir -pv $WHATCH_DIR

RUN python3 -m pip install -r requirements.txt

COPY main.py .

CMD [ "python", "./main.py" ]
