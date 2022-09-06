#!/bin/bash

echo "Starting entrypoint.sh..."

echo "Saving environment to file"
export -p > /enironment

echo "Crontab:"
touch /etc/cron.d/its-time-cron
chmod 0644 /etc/cron.d/its-time-cron
touch /var/log/cron.log
echo "$CRON_TIME root /cron.sh >> /var/log/cron.log 2>&1" >> /etc/cron.d/its-time-cron
echo '# Dont remove the empty line at the end of this file. It is required to run the cron job' >> /etc/cron.d/its-time-cron
cat /etc/cron.d/its-time-cron

echo "Starting looped bot"
bash -c 'cd /looped-bot; python3 -u main.py' &

echo "Starting crontab"
cron && tail -f /var/log/cron.log