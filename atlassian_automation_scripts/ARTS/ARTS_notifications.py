#!/bin/env python
# -*- coding: utf-8 -*-

from jira.client import JIRA
from datetime import datetime, timedelta
import logging
import smtplib
from email.mime.text import MIMEText
from bot_libs import JiraHdmIssue

#   Settings

# SMTP gateway settings
# smtp_host = ''
smtp_host = ''
# smtp_login = ''
# smtp_password = ''
jira_from_email = ''

# JIRA settings
jira_url = ''
user = ''
password = ''
info_field_name = 'assignee'
maxResults = 100

need_info_timeout = timedelta(days=14)
resolved_timeout = timedelta(days=7)
comment_timeout = timedelta(days=1)
first_notify_timeout = timedelta(hours=1)

lock_path = '/home/jirabot/lock/ARTS_notifications.lock'
log_path = '/home/jirabot/logs/ARTS_notifications.log'

debug = False

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(process)d - %(levelname)s - %(message)s')
handler = logging.FileHandler(log_path)
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)
logger.addHandler(handler)


def send_email(email, issue):
    mail_object = None

    if not debug:
        try:
            mail_object = smtplib.SMTP(smtp_host)
            mail_object.ehlo_or_helo_if_needed()
        except Exception, e:
            logger.critical('Unable to connect to SMTP server. Detail info: %s' % e)
            exit(1)

    str_one = '''
При предоставлении информации не забудьте нажать Send Info!'''

    str_two = '''
Если информация не будет предоставлена указанным способом в течение 5 дней, то задача автоматически закрывается и переходит в статус Resolved (Won`t Fix). При переоткрытии задача будет обрабатываться в зависимости от текущей загрузки отдела.
'''

    str_one_new = str_one.decode('utf-8')
    str_two_new = str_two.decode('utf-8')

    msg = '''
Art Studio Publisher requested info in: %s (%s)

%s ( %sbrowse/%s ).
%s
==========================

When providing information do not forget to use Send Info button! ( %sbrowse/%s ).
If the information is not provided using the method mentioned above during 5 days, the task is automatically resolved with resolution Resolved (Won`t fix). If the task is reopened it will be processed according to the current workload.
''' % (issue.issue.key, issue.summary, str_one_new, jira_url, issue.issue.key, str_two_new, jira_url, issue.issue.key)

    subject = '[JIRA] %s: Art Studio Publisher Need more information' % (issue.issue.key)

    message = MIMEText(msg, _charset="UTF-8")
    message['Subject'] = subject
    message['From'] = jira_from_email
    message['To'] = email
    if not debug:
        try:
            mail_object.sendmail(jira_from_email, email, message.as_string())
        except Exception, e:
            logger.critical('Error sending mail to %s: %s' % (email, e))

    logger.debug('Sending email to %s issueKey = %s' % (email, issue.issue.key))

    if not debug and mail_object:
        mail_object.close()


def get_message(status):
    if status == 'Need Info':
        msg = '''Not enough information has been provided to resolve the task. Work on the issue is stopped. If you have any comments please reopen the task.'''
    else:
        msg = ''

    return msg

#   Main
if __name__ == '__main__':
    # global start time
    now_datetime = datetime.utcnow()
    now_datetime = now_datetime.replace(second=0, microsecond=0)

    jira = None

    try:
        jira = JIRA({'server': jira_url}, basic_auth=(user, password))
    except Exception, e:
        logger.critical('Jira instance unavailable, detail: %s' % e)
        exit(1)

    operated_issues = {}

    next_result = True
    startPos = 0

    # Строим список issue потенциально требующих обработки
    while next_result:

        issue_set = []

        try:
            issue_set = jira.search_issues(
                'project=ARTS and status in ("Need Info")',
                fields=[],
                startAt=startPos,
                maxResults=maxResults,
            )
        except Exception, e:
            logger.critical('Jira request failed, detail: %s' % e)
            exit(1)

        for issue_object in issue_set:
            operated_issues[issue_object.key] = issue_object.key

        if len(issue_set) < maxResults:
            next_result = False
            issue_set = None
        else:
            startPos += maxResults

    for issue_key in operated_issues:
        issue = JiraHdmIssue(jira, issue_key)
        message = get_message(issue.status)
        logger.debug('Issue %s - processing' % issue.key)

        if issue.status == 'Need Info':
            logger.warning(
                'Sending Issue %s notification: updated %s, now %s' % (issue_key, issue.updated, now_datetime))
            info_user = getattr(issue.issue.fields, info_field_name)
            if info_user.emailAddress != '':
                logger.debug('Issue %s send_email(%s,issue)' % (issue_key, info_user.emailAddress))
                if not debug:
                    send_email(info_user.emailAddress, issue)
        else:
            logger.debug('Issue %s all conditions are false, skipped' % issue_key)

logger.warning('All done.')

