#!/usr/bin/python3
import pymysql.cursors
import os
import logging
import configparser
import smtplib
from string import Template
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
mysql_conf = getConfig('MYSQL')
mail_conf = getConfig('MAIL')

# set variables
mail_smtp_server = mail_conf['smtp_server']
mail_smtp_port = mail_conf['smtp_port']
mail_smtp_login = mail_conf['smtp_login']
mail_smtp_password = mail_conf['smtp_password']
mail_from_addr = mail_conf['from_addr']
mail_to_addr = mail_conf['to_addr']
subject = mail_conf['subject']
message = mail_conf['message']
mysql_host = mysql_conf['mysql_host']
mysql_user = mysql_conf['mysql_user']
mysql_password = mysql_conf['mysql_password']
mysql_db_confdb = mysql_conf['mysql_db_confdb']
sql_select_confdb = mysql_conf['sql_select_confdb']
confdb_list = []  # a list with all entries from the table


# logging settings
logging.basicConfig(filename=log_file, level=logging.DEBUG, format='%(asctime)s %(levelname)s:  %(message)s')

def send_email(mail_subject, mail_message, mail_to_addr):
    logging.info('The email is going to be sent...')
    msg = MIMEText(mail_message, 'html', 'utf-8')
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
    close_sql_con(connection_confdb, mysql_db_confdb)
    logging.info(
        'Script run is finished.{}###################################################################################################'.format("\n"))

# create a connection, execute sql query
connection_confdb = create_sql_con(mysql_db_confdb)
logging.info('Fetching data from the "{}" database'.format(mysql_db_confdb))
cursor = exec_sql(connection_confdb, sql_select_confdb, 'select')

# Compose a nice table where all pages with label "review" OR "doublecheck" are listed
logging.info('Composing a nice table where all pages with label "review" OR "doublecheck" are listed')
for i in cursor:
    message += """<tr>
                  <td>""" + i['space_key'] + """</td>
                  <td>""" + i['page_title'] + """</td>
                  <td>""" + str(i['page_id']) + """</td>
                  <td>""" + i['page_url'] + """</td>
                  <td>""" + i['page_creator'] + """</td>
                  <td>""" + i['creator_active_flag'] + """</td>
                  <td>""" + i['page_creator_email'] + """</td>
                  </tr>
               """

# send email
send_email(subject, message, mail_to_addr)

# close mysql connection and text finish script message
fin_script()
