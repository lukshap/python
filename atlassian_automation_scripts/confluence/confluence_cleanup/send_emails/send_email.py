#!/usr/bin/python3
import pymysql.cursors
import os
import logging
import configparser
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta

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
mysql_conf = getConfig('MYSQL')
mail_conf = getConfig('MAIL')

# set variables
mail_smtp_server = mail_conf['smtp_server']
mail_smtp_port = mail_conf['smtp_port']
mail_smtp_login = mail_conf['smtp_login']
mail_smtp_password = mail_conf['smtp_password']
mail_from_addr = mail_conf['from_addr']
subject_first = mail_conf['subject_first']
subject_reminder = mail_conf['subject_reminder']
message_first = mail_conf['message_first']
message_reminder = mail_conf['message_reminder']
mysql_host = mysql_conf['mysql_host']
mysql_user = mysql_conf['mysql_user']
mysql_password = mysql_conf['mysql_password']
mysql_db_bxe_info = mysql_conf['mysql_db_bxe_info']
mysql_table = mysql_conf['mysql_table']
sql_select_bxe_info = mysql_conf['sql_select_bxe_info']
sql_insert_bxe_info = mysql_conf['sql_insert_bxe_info']
bxe_info_dict = {}  # a dict with all entries from the table
sorted_date_list = []  # an ordered list of lastmoddate dates for each page from the table
email_recipient_dict = {}  # a dict with email_recipients for pages that have NEVER been sent an email
n = 0  # just a counter
remind_email_recipients = {} # a dict with email_recipients for pages that have ALREADY been sent an email

# logging settings
logging.basicConfig(filename=log_file, level=logging.DEBUG, format='%(asctime)s %(levelname)s:  %(message)s')

def send_email(mail_subject, mail_message, mail_to_addr):
    logging.info('The email is going to be sent...')
    msg = MIMEMultipart()
    msg.attach(MIMEText(mail_message))
    msg['Subject'] = mail_subject
    msg['From'] = mail_from_addr
    msg['To'] = mail_to_addr
    for i in mail_to_addr.split(","):
        try:
            server = smtplib.SMTP(mail_smtp_server, mail_smtp_port)
            logging.info('Connected to the mail server successfully')
        except Exception as e:
            logging.critical('Error due connection to SMTP server: {}'.format(e))
            fin_script()
            exit(1)
        try:
            logging.info('Email to the {} is being sent...'.format(i))
            server.sendmail(mail_from_addr, i, msg.as_string())
            server.quit()
            logging.info('Email to the "{}" has been successfully sent'.format(i))
        except Exception as e:
            logging.critical('Error due email sending: {}'.format(e))
            fin_script()
            exit(1)

# define create_sql_con func
def create_sql_con(mysql_db):
    ## Connect to MySQL
    logging.info('Creating a connection to the MySQL server:{}host:"{}"{}db:"{}"{}user:"{}"{}'.format("\n", mysql_host, "\n", mysql_db, "\n", mysql_user, "\n"))
    try:
        connection = pymysql.connect(host=mysql_host,
                                     user=mysql_user,
                                     password=mysql_password,
                                     db=mysql_db,
                                     charset='utf8mb4',
                                     cursorclass=pymysql.cursors.DictCursor)
        return connection
    except Exception as e:
        logging.critical('Error during creating connection to the MySQL server: "{}"'.format(e))
        fin_script()
        exit(1)

# define exec_sql func
def exec_sql(connection, sql, req_type):
    if req_type == 'select':
        with connection.cursor() as cursor:
            try:
                logging.info('Executing sql query:{}"{}"{}'.format("\n", sql, "\n"))
                cursor.execute(sql)
            except Exception as e:
                logging.critical('Error during executing sql query: "{}"'.format(e))
                fin_script()
                exit(1)
    elif req_type == 'insert':
        with connection.cursor() as cursor:
            try:
                logging.info('Executing sql query:{}"{}"{}'.format("\n", sql, "\n"))
                cursor.execute(sql)
                connection.commit()
            except Exception as e:
                logging.critical('Error during executing sql query: "{}"'.format(e))
                fin_script()
                exit(1)
    return cursor

# define close_sql_con func
def close_sql_con(connection, mysql_db):
    try:
        logging.info('Closing the connection to the MySQL server:{}host:"{}"{}db:"{}"{}user:"{}"{}'.format("\n", mysql_host, "\n", mysql_db, "\n", mysql_user, "\n"))
        connection.close()
    except Exception as e:
        logging.critical('Error during closing connection to the MySQL server: "{}"'.format(e))
        exit(1)

# define fin_script func
def fin_script():
    close_sql_con(connection_bxe_info, mysql_db_bxe_info)
    logging.info(
        'Script run is finished.{}###################################################################################################'.format("\n"))

# create a connection, execute sql query
connection_bxe_info = create_sql_con(mysql_db_bxe_info)
logging.info('Fetching data from the "{}" table from "{}" database'.format(mysql_table, mysql_db_bxe_info))
cursor = exec_sql(connection_bxe_info, sql_select_bxe_info, 'select')

# fill a dict with with data from sql query
logging.info('Filling the dict with data from sql query')
for i in cursor:
    bxe_info_dict.update({i['lastmoddate']: {'email_recipient': i['email_recipient'], 'space_key': i['space_key'],'creator': i['creator'], 'last_notification': i['last_notification'], 'message_sent': i['message_sent'], 'page_URL': i['page_URL'], 'page_id': i['page_id'], 'last_editor': i['last_editor']}})

# compose the ordered (starting from the oldest date) list of lastmoddate dates for each page from the table
logging.info('Composing the ordered (starting from the oldest date) list of lastmoddate dates for each page from the "{}" table'.format(mysql_table))
sorted_date_list = sorted(bxe_info_dict.keys())

# compose a dict of 10 different recipients of the most outdated pages, who haven't ever been sent an email to, from the bxe_info_dict
logging.info('Composing a dict of 10 different recipients of the most outdated pages, who haven\'t ever been sent an email to')
for i in sorted_date_list:
    if bxe_info_dict[i]['email_recipient'] not in email_recipient_dict.keys() and bxe_info_dict[i]['message_sent'] == int('0') and n < 10:
        email_recipient_dict.update({i: bxe_info_dict[i]['email_recipient']})
        n += 1

# for each entry from the email_recipient_dict
for i in email_recipient_dict:
    logging.info('The FIRST email concerning the following page will be sent:{}{}'.format("\n", bxe_info_dict[i]['page_URL']))
    # send email for 10 different recipients of the most outdated pages, who haven't ever been sent an email to
    send_email(subject_first, message_first.format(bxe_info_dict[i]['page_URL']), bxe_info_dict[i]['email_recipient'])
    #send_email(subject_first, message_first.format(bxe_info_dict[i]['page_URL']), 'pavel_luksha@epam.com')

    # flag a relevant record with an message_sent bit and update the "last_notification" field with the current date for the sent email
    logging.info('The relevant fields will be updated in the "{}" database'.format(mysql_db_bxe_info))
    sql_query = sql_insert_bxe_info.format(datetime.today(), bxe_info_dict[i]['space_key'], bxe_info_dict[i]['page_id'])
    cursor = exec_sql(connection_bxe_info, sql_query, 'insert')

# for each entry from the bxe_info_dict
for i in bxe_info_dict:
    # check for pages with a set message_sent bit and a email sent date from 3 weeks or older
    # for test minutes
    #if bxe_info_dict[i]['message_sent'] == int('1') and bxe_info_dict[i]['last_notification'] < (datetime.today() - timedelta(minutes=1)):
    # #for prod weeks
    if bxe_info_dict[i]['message_sent'] == int('1') and bxe_info_dict[i]['last_notification'] < (datetime.today() - timedelta(weeks=3)):
        if bxe_info_dict[i]['email_recipient'] not in remind_email_recipients.keys():
            remind_email_recipients.update({bxe_info_dict[i]['email_recipient']: [bxe_info_dict[i]['page_URL']]})
        else:
            remind_email_recipients[bxe_info_dict[i]['email_recipient']].append(bxe_info_dict[i]['page_URL'])

        # update the "last_notification" field date for this record to the current date
        logging.info('The relevant fields will be updated in the "{}" table in the "{}" database'.format(mysql_table, mysql_db_bxe_info))
        sql_query = sql_insert_bxe_info.format(datetime.today(), bxe_info_dict[i]['space_key'], bxe_info_dict[i]['page_id'])
        cursor = exec_sql(connection_bxe_info, sql_query, 'insert')

# compose a dict with email_recipients for pages that have ALREADY been sent an email (each recipient should receive one reminder email for all holding pages by him)
for i in remind_email_recipients:
    logging.info('The REMINDER email to "{}" concerning the following pages will be sent:{}{}'.format(i, "\n", ",".join(remind_email_recipients[i]).replace(",", "\n")))
    # send out reminder email to the each recipient
    send_email(subject_reminder, message_reminder.format(",".join(remind_email_recipients[i]).replace(",", "\n")), i)
    #send_email(subject_reminder, message_reminder.format(",".join(remind_email_recipients[i]).replace(",", "\n")), 'pavel_luksha@epam.com')

# close mysql connection and text finish script message
fin_script()
