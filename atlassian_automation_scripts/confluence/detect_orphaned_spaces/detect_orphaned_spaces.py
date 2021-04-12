#!/usr/bin/python3
import pymysql.cursors
import csv
import os
import logging
import configparser
import subprocess
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText

# get script_name and config file
script_name = os.path.basename(__file__)    # get script_name
basedir = os.path.dirname(os.path.abspath(__file__))    # get absolute directory path to the script
config_file = basedir + '/server.conf'   # set absolute path to the script
log_file = ('{}/{}.log'.format(basedir, script_name))   # set absolute path to the log

# get properties from config file
def getConfig(section):
    config = configparser.ConfigParser()
    config.read(config_file)
    props = {}
    if section:
        for key, val in config.items(section):
            props[key] = val
    return props

# get configs
mail_conf = getConfig('MAIL')
mysql_conf = getConfig('MYSQL')

# set variables
mail_smtp_server = mail_conf['smtp_server']
mail_smtp_port = mail_conf['smtp_port']
mail_smtp_login = mail_conf['smtp_login']
mail_smtp_password = mail_conf['smtp_password']
mail_from_addr = mail_conf['from_addr']
mail_to_addr = mail_conf['to_addr']
mail_subject = mail_conf['subject']
mail_message = mail_conf['message']
sql_six_month = mysql_conf['sql_six_month']
sql_less_10_pages = mysql_conf['sql_less_10_pages']
mysql_host = mysql_conf['mysql_host']
mysql_user = mysql_conf['mysql_user']
mysql_password = mysql_conf['mysql_password']
mysql_db = mysql_conf['mysql_db']

six_month = []
less_10_pages = []

# logging settings
logging.basicConfig(filename=log_file, level=logging.DEBUG, format='%(asctime)s %(levelname)s:  %(message)s')

# define send_email func
def send_email(attaches):
    logging.info('The email is going to be sent...')
    msg = MIMEMultipart()
    msg.attach(MIMEText(mail_message))
    msg['Subject'] = mail_subject
    msg['From'] = mail_from_addr
    for i in attaches:
        with open(basedir + '/' + i, "rb") as attach:
            part = MIMEApplication(attach.read(), Name=i)
            part['Content-Disposition'] = 'attachment; filename="{}"'.format(i)
            msg.attach(part)
    msg['To'] = mail_to_addr
    for i in mail_to_addr.split(","):
        try:
            server = smtplib.SMTP(mail_smtp_server, mail_smtp_port)
            logging.info('Connected to the mail server successfully')
        except Exception as e:
            logging.critical('Error due connection to SMTP server: {}'.format(e))
            exit(1)
        try:
            logging.info('Email to the {} is being sent...'.format(i))
            server.sendmail(mail_from_addr, i, msg.as_string())
            server.quit()
            logging.info('Email to the "{}" has been successfully sent'.format(i))
        except Exception as e:
            logging.critical('Error due email sending: {}'.format(e))
            exit(1)

# define shell func
def shell(commandlinestr, cwd = None):
    try:
        if cwd:
            p = subprocess.Popen(commandlinestr, stdout=subprocess.PIPE, shell=True, cwd=cwd)
        else:
            p = subprocess.Popen(commandlinestr, stdout=subprocess.PIPE, shell=True, cwd=basedir)
    except Exception as e:
        logging.critical('Error during performing the command: "{}": {}'.format(commandlinestr, e))
        exit(1)
    output, err = p.communicate()
    return output

# define search_file func
def search_file(file, cwd):
    logging.info('Looking through the filesystem for the required "{}" file...'.format(file))
    command = 'find {} -name {}'.format(cwd, file)
    files = shell(command).decode("utf-8").split("\n")
    file_names = {i.split("/")[-1]: i.split("/")[:-1] for i in files if i}
    logging.info('The file names dict is successfully constructed: {}{}'.format("\n", file_names))
    return file_names

# define exec_sql func
def exec_sql(sql, csv_report):
    ## Connect to MySQL
    logging.info('Creating a connection to the MySQL server:{}host:"{}"{}db:"{}"{}user"{}"{}'.format("\n", mysql_host, "\n", mysql_db, "\n", mysql_user,"\n"))
    try:
        connection = pymysql.connect(host=mysql_host,
                                     user=mysql_user,
                                     password=mysql_password,
                                     db=mysql_db,
                                     charset='utf8mb4',
                                     cursorclass=pymysql.cursors.DictCursor)
    except Exception as e:
        logging.critical('Error during creating connection to the MySQL server: "{}"'.format(e))
        exit(1)
    with connection.cursor() as cursor:
        try:
            logging.info('Executing sql query{}"{}"{}'.format("\n", sql, "\n"))
            cursor.execute(sql)
        except Exception as e:
            logging.critical('Error during executing sql query: "{}"'.format(e))
            exit(1)
        for row in cursor:
            csv_report.append(row)

# define create_csv_report func
def create_csv_report(csv_report, csv_report_name):
    logging.info('Creating report file:"{}"'.format(csv_report_name))
    with open(csv_report_name, 'w') as f:
        n = 0
        for i in csv_report:
            w = csv.DictWriter(f, i.keys())
            if n == 0:
                w.writeheader()
                n += 1
            w.writerow(i)

# execute sql and compose report files
exec_sql(sql_six_month, six_month)
create_csv_report(six_month, 'six_month.csv')
exec_sql(sql_less_10_pages, less_10_pages)
create_csv_report(less_10_pages, 'less_10_pages.csv')

# find the report files
logging.info('The report files in the "{}" directory are being searched...'.format(basedir))
files_dict = search_file('"*csv"', basedir)

# send email with reports
send_email(files_dict)
