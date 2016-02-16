==========================================
DevOps - Servers, Configuration, Deployment, Common tasks
==========================================

Servers
============================

 Following is the servers configuration (as it was on Feb. 16, 2016):
 
db1
  DB server, runs cronjobs, (EC2 Name: Postgres1)

small1
  web app

small2
  web app

Configuration
=============

web app servers
  Runs supervisor service which includes oknesset app
  
  The file /etc/supervisor/conf.d/oknesset.conf contains the relevant configuration
  
  This is the command that it runs: command=newrelic-admin run-program gunicorn knesset.wsgi:application -w 4 -t 60

db servers
  Runs the DB
  Runs cronjobs, see https://github.com/hasadna/Open-Knesset/blob/master/deploy/crontab.txt
