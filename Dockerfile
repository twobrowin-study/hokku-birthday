FROM ubuntu:latest

ENV DEBIAN_FRONTEND 'noninteractive'
ENV TZ 'Europe/Moscow'

RUN apt-get update && apt-get install -y python3 python3-psycopg2 \
    libpq-dev python3-waitress python3-setuptools python3-pandas \
    python3-sqlalchemy python3-xlsxwriter cron

COPY requirenments.txt /
RUN pip3 install -r /requirenments.txt

ENV BOT_TOKEN ''
ENV SHEETS_ACC_JSON ''
ENV SHEETS_NAME 'Таблица для бота дней рождений в Пивном Петушке'

ENV SHEET_HBS 'Дни рождения'
ENV SHEET_HBS_NAME 'Род. падеж имени'
ENV SHEET_HBS_DATE 'Дата рождения'
ENV SHEET_HBS_ADD_TEXT 'Дополнительный текст'

ENV SHEET_EMOJI 'Emoji'
ENV SHEET_HOKKU 'Строчки Хокку'

ENV SHEET_MAIN_TEXT 'Основной текст'
ENV SHEET_MAIN_TEXT_CONDITION 'Условие'
ENV SHEET_MAIN_TEXT_CONDITION_ONE 'Одно ДР'
ENV SHEET_MAIN_TEXT_CONDITION_MANY 'Несколько ДР'
ENV SHEET_MAIN_TEXT_TEXT 'Текст'

ENV SHEET_TO_WHOM_SEND 'Каналы для отправки'
ENV SHEET_TO_WHOM_SEND_ID 'Telegram ID'

ENV CRON_TIME '* * * * *'

RUN  mkdir /looped-bot
COPY looped-bot/*.py /looped-bot/

RUN  mkdir /its-time-bot
COPY its-time-bot/*.py /its-time-bot/

RUN sed -i '/session    required     pam_loginuid.so/c\#session    required   pam_loginuid.so' /etc/pam.d/cron
COPY cron.sh /

COPY entrypoint.sh /
CMD [ "/entrypoint.sh" ]