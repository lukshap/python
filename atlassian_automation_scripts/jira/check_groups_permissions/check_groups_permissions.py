#!/bin/env python
# -*- coding: utf-8 -*-
"""
1. Getting from DB all Permission schemes all entities which are in the 'ADMINISTER_PROJECTS','BROWSE_PROJECTS' permissions.
2. Checking if 'jira-operations' is in 'ADMINISTER_PROJECTS' and 'BROWSE_PROJECTS'; if 'special-access' is in 'BROWSE_PROJECTS'.
3. Sending emails if there is not 'jira-operations' in 'ADMINISTER_PROJECTS' and 'BROWSE_PROJECTS'; there is not special-access' is in 'BROWSE_PROJECTS'.
"""
import logging
import fcntl
import httplib
import os
import re
import ConfigParser
import mysql.connector
from mysql.connector import errorcode
import smtplib
from email.mime.text import MIMEText
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

# Get config
def get_properties(section):
    config = ConfigParser.SafeConfigParser()
    config.read(config_file)
    props = {}
    if section:
        for key, val in config.items(section):
            props[key] = val
    return props

# Settings
config_file = 'config.ini'
global_conf = get_properties('GLOBAL')
jira_conf = get_properties('JIRA')
mysql_conf = get_properties('MYSQL')
smtp_conf = get_properties('SMTP')

# Variables form config.ini
log_path = global_conf['log_path']
checked_group_1 = jira_conf['checked_group_1']
checked_group_2 = jira_conf['checked_group_2']
user = mysql_conf['user']
password = mysql_conf['password']
host = mysql_conf['host']
database = mysql_conf['database']
smtp_host= smtp_conf['smtp_host']
from_email= smtp_conf['from_email']
to_email = smtp_conf['to_email']
subject = smtp_conf['subject']
email_msg_wrong = smtp_conf['email_msg_wrong']
daily_duty_message = smtp_conf['daily_duty_message']
email_msg_ok = smtp_conf['email_msg_ok']
email_msg_mysql_err = smtp_conf['email_msg_mysql_err']

# Logging settings
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler = logging.FileHandler(log_path)
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)
logger.addHandler(handler)
httplib.HTTPConnection.debuglevel = 0

def send_email(email_msg):
    mail_object = None
    try:
        mail_object = smtplib.SMTP(smtp_host)
        mail_object.ehlo_or_helo_if_needed()
    except Exception, e:
        logger.critical('Unable to connect to SMTP server. Detail info: %s' % e)
        exit(1)
    message = MIMEText(email_msg, _charset="UTF-8")
    message['Subject'] = subject
    message['From'] = from_email
    message['To'] = to_email
    try:
        mail_object.sendmail(from_email,to_email,message.as_string())
        logger.info('Successful sending mail to %s' % (to_email))
    except Exception, e:
        logger.critical('Error sending mail to %s: %s' % (to_email,e))

perm_schemes={}
email_msg_send=''
dct={}

# Main
if __name__ == '__main__':
    fp = open(global_conf['lock_path'], 'w')
    try:
        fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError, e:
        logger.critical('error getting lock, another instance running? Reason: %s', e)
        exit(1)

    ## Connect to MySQL
    config = {
        'user': user,
        'password': password,
        'host': host,
        'database': database,
    }
    try:
        cnx = mysql.connector.connect(**config)
        logger.info('Successful connection to mysql')
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            logger.critical('Something is wrong with your user name or password')
            send_email(email_msg_mysql_err)
            exit(1)
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            logger.critical('Database does not exist')
            send_email(email_msg_mysql_err)
            exit(1)
        else:
            logger.critical('%s', err)
            send_email(email_msg_mysql_err)
            exit(1)
    else:
        cursor = cnx.cursor()
        query = ("""
	        SELECT p.name,s.`PERMISSION_KEY`,s.`perm_parameter`
            FROM permissionscheme p
            JOIN schemepermissions s ON p.`ID`=s.`SCHEME`
            AND s.`PERMISSION_KEY` IN ('ADMINISTER_PROJECTS','BROWSE_PROJECTS')
            """)
        cursor.execute(query)
        cnx.close()
    # Create dict of Permissions schemes and 'ADMINISTER_PROJECTS','BROWSE_PROJECTS' permissions entities.
    for i in cursor:
        if str(i[0]) in perm_schemes.keys():
            if str(i[1]) in perm_schemes[str(i[0])].keys():
                perm_schemes[str(i[0])][str(i[1])].append(str(i[2]))
            else:
                perm_schemes[str(i[0])].update({str(i[1]):[str(i[2])]})
        else:
            perm_schemes.update({str(i[0]):{str(i[1]):[str(i[2])]}})
    print perm_schemes
    # Create dict of Permissions schemes and permissions where jira-operations and special-access groups do not exist
    for i in perm_schemes:
        lst=[]
        lst_2=[]
        for j in perm_schemes[i].keys():
            if checked_group_1 not in perm_schemes[i][j]:
                lst.append(j)
                {dct[i].update({checked_group_1: lst}) if i in dct.keys() else dct.update({i: {checked_group_1: lst}})}
            if checked_group_2 not in perm_schemes[i][j] and j == 'BROWSE_PROJECTS':
                lst_2.append(j)
                {dct[i].update({checked_group_2: lst_2}) if i in dct.keys() else dct.update({i: {checked_group_2: lst_2}})}
    # Sending emails
    if dct:
        for i in dct:
            for j in dct[i].keys():
                email_msg_send = email_msg_send + re.sub('\[permission_scheme\]', i, email_msg_wrong)
                email_msg_send = re.sub('\[group\]', j, email_msg_send)
                email_msg_send = re.sub('\[permission\]', str(dct[i][j]), email_msg_send) + '\n'
        send_email(email_msg_send + '\n' + daily_duty_message)
    else: send_email(email_msg_ok)

    # Delete lock file
    try:
        os.remove(global_conf['lock_path'])
    except IOError, e:
        logger.critical('error deleting lock file. Reason: %s', e)
        exit(1)