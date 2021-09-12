FROM python:2

WORKDIR /usr/src/app

COPY . ./

EXPOSE 3111

RUN python -m pip install -r requirements.txt
RUN python init_db.py

CMD [ "python", "app.py" ]
