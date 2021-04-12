#! /usr/bin/python

"""
Check how much time an issue is not being updated and send email basing on the defined time periods:
1. Gets issues from JIRA basing on jql.
2. Defines how much time an issue is not being updated and compare this value with 'Alert', 'Blocker', 'Achtung' delay values:
    If triggers:
    3. Defines the "General_Status" custom field value:
        3.1 if it is in ('Loading', 'Delivering') - sends email to users set in the "Bosun", "Navigator", "Serviceman" custom fields.
        3.2 if it is "Making an order" value - sends email to users set in the "Navigator", "Serviceman" custom fields.
        3.3 If "General_Status" value is either equal to "None" or not exists - emails are not sent.
"""

from jira import JIRA
from datetime import datetime
from datetime import timedelta
import smtplib
from email.mime.text import MIMEText
import logging
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

## variables
# jira
jira_url = ''
jira_login = ''
jira_password = ''
jira_timezone = '0300'
# jql
jql = 'issuetype=Chemodan'
#jql = 'issue=CHEM-19'
max_jql_rez = 200
# logging
log_path = '/home/p_luksha/bitbucket/logs/ping.log'
# smtp
smtp_server = ''
smtp_port = 587
smtp_login = ''
smtp_password = ''
from_addr = ''
# custom_fields_id
roles = {'Bosun': {'cf_id': 'customfield_10200', 'email': 'None'},
        'Navigator': {'cf_id': 'customfield_10201', 'email': 'None'},
        'Serviceman': {'cf_id': 'customfield_10202', 'email': 'None'}
        }
General_Status_customfield_id = 'customfield_10600'
# lack of activity in an issue
delays = {'Alert': 3, 'Blocker': 5, 'Achtung': 10}

# Logging settings
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler = logging.FileHandler(log_path)
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)
logger.addHandler(handler)

def send_email(to_address_list,severity_level,issue):
    #subject = severity_level + '!' + ' No Action on "{}" from "{}" for {} days!'.format(issue.key, issue.fields.assignee.name, delays[severity_level])
    subject = severity_level + '!' + ' No Action on "{}" from "{}" for {} hours!'.format(issue.key,issue.fields.assignee.name,delays[severity_level])
    message = 'Reaction needed from "{}" for "{}","{}",{}/browse/{}'.format(issue.fields.assignee.name,issue.key, issue.fields.status.name.encode('utf-8'), jira_url, issue.key)
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = from_addr
    try:
        server = smtplib.SMTP(smtp_server,smtp_port)
    except Exception, e:
        logger.critical('Error due connection to SMTP server: {}'.format(e))
        exit(1)
    try:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(smtp_login, smtp_password)
        for i in to_address_list:
            msg['To'] = i
        server.sendmail(from_addr, to_address_list, msg.as_string())
        server.quit()
    except Exception, e:
        logger.critical('Error due email sending: {}'.format(e))
        exit(1)

def email(issue,severity_level):
    # filling dict with Bosun,Navigator,Serviceman emails
    for i in roles.keys():
        if hasattr(issue.fields, roles[i]['cf_id']) and getattr(issue.fields, roles[i]['cf_id']) is not None:
            roles[i]['email'] = getattr(issue.fields, roles[i]['cf_id']).emailAddress

    # Check and set "General_Status" custom field value
    if hasattr(issue.fields, General_Status_customfield_id) and getattr(issue.fields, General_Status_customfield_id) is not None:
        General_Status = getattr(issue.fields, General_Status_customfield_id).value
    else: General_Status = 'None'

    # send emails to Bosun,Navigator,Serviceman depending on the "General_Status" custom field value
    if General_Status in ('Loading', 'Delivering'):
        logger.info('The issue "{}" is either in "Loading" or "Delivering" status, so sending "'.format(issue.key) + severity_level + '" email to to Bosun({}), Navigator({}), Serviceman({})'.format(roles['Bosun']['email'],roles['Navigator']['email'],roles['Serviceman']['email']))
        send_email([roles['Bosun']['email'],roles['Navigator']['email'],roles['Serviceman']['email']], severity_level, issue)
    elif General_Status == 'Making an order':
        logger.info('The issue "{}" is in "Making an order" status, so sending "'.format(issue.key) + severity_level + '" email to Navigator({}), Serviceman({})'.format(roles['Navigator']['email'],roles['Serviceman']['email']))
        send_email([roles['Navigator']['email'],roles['Serviceman']['email']], severity_level, issue)
    else: logger.info('The custom field\'s "General_Status" value is either equal to "None" or not exists in the issue "{}" - not processed.'.format(issue.key))

def updated(issue):
    """
    1. format updated issue date from unicode to datetime format
    2. define diff between current time and updated time in an issue
    """
    issue_updated = issue.fields.updated
    updated_issue_date_time = datetime.strptime(issue_updated,'%Y-%m-%dT%H:%M:%S.%f+' + jira_timezone)
    no_action_time = datetime.now() - updated_issue_date_time
    return no_action_time

## main
try:
    j = JIRA(server=jira_url, basic_auth=(jira_login, jira_password))
except Exception, e:
    logger.critical('Error while connecting to JIRA: {}'.format(e))
    exit(1)
# Get issue list from JIRA basing on the jql query
try:
    issues_list = j.search_issues(jql_str=jql,
                                startAt=0,
                                maxResults=max_jql_rez,
                                fields=None,
                                expand=None)
except Exception, e:
    logger.critical('Error while making jql search: {}'.format(e))
    exit(1)
for i in issues_list:
    logger.info('The issue "{}" is processing"'.format(i.key))
    if updated(i) > timedelta(hours=delays['Achtung']):
    #if updated(i) > timedelta(days=delays['Achtung']):
        email(i,'Achtung')
    elif updated(i) > timedelta(hours=delays['Blocker']):
    #elif updated(i) > timedelta(hours=delays['Blocker']):
        email(i,'Blocker')
    elif updated(i) > timedelta(hours=delays['Alert']):
    #elif updated(i) > timedelta(days=delays['Alert'])
        email(i,'Alert')
    else: logger.info('All chemodans are not being delayed')