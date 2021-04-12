#!/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'p_luksha'

"""
1. The script gets a list of issues from JQL.
2. Chooses only those where assignee is inactive or missed.
3. Creates a dict to match project's "component - component lead" for each project among chosen in step 1 issues,by the way if component lead is inactive or missed it is replaced by project lead.
4. In the each chosen in step 1 issue assignee field is changed to correspondent component lead (or project lead) from a dict created on the step 3, but if component field is empty in the certain issue -
the message is being generated and being sent to o_koval,p_luksha.
"""

from jira.client import JIRA
from datetime import datetime, timedelta, date
from email.mime.text import MIMEText
import logging
import fcntl
import os
import ConfigParser
import smtplib
import re
import base64
import httplib
import requests
import sys
import csv
import time

## To eliminate a A true SSLContext object warnings
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

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
smtp_conf = get_properties('SMTP')

log_path = global_conf['log_path']
jira_user = global_conf['jira_user']
jira_password = global_conf['jira_password']
smtp_host = smtp_conf['smtp_host']
from_email = smtp_conf['from_email']
to_email_1 = smtp_conf['to_email_1']
to_email_2 = smtp_conf['to_email_2']
subject = smtp_conf['subject']
email_msg_no_components = smtp_conf['email_msg_no_components']
email_msg_no_reassign = smtp_conf['email_msg_no_reassign']

def send_email(email_msg,to_email):
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

# Logging settings
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler = logging.FileHandler(log_path)
#handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)
logger.addHandler(handler)
httplib.HTTPConnection.debuglevel = 0

maxResults = 100
startPos = 0
issue_array = []
next_result = True
debug = False

projects_dict = {0:0}
count=0
reassigned_issues_lst = [['issue','summary','description','assignee','reporter','components','labels']]
no_components = []
no_reassign = []

#   Main
if __name__ == '__main__':
    fp = open(global_conf['lock_path'], 'w')
    try:
        fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError, e:
        logger.critical('error getting lock, another instance running? Reason: %s', e)
        exit(1)
    jira = None
    try:
        jira = JIRA({'server': global_conf['jira_url']}, basic_auth=(jira_user,jira_password))
    except Exception, e:
        logger.critical('JIRA instance unavailable, detail: %s' % e)
        exit(1)
    # Строим список issue потенциально требующих обработки
    while next_result:
        issue_set = []
        try:
            issue_set = jira.search_issues(
                global_conf['jql'],
                fields=global_conf['fields'],
                startAt=startPos,
                maxResults=maxResults,
#               expand=global_conf['expand'],
            )
        except Exception, e:
            logger.critical('Jira request failed, detail: %s' % e)
            exit(1)
        issue_array = issue_array + issue_set
        if len(issue_set) < maxResults:
            next_result = False
            issue_set = None
        else:
            startPos += maxResults
    logger.info('Count of issues: ' + str(len(issue_array)))

    # Create dictionary of projects->components->and mapping components<->component_lead
    def create_dict(issue_object):
        ## Check if projects_dict is empty or not:
        if issue_object.fields.project.key in projects_dict:
            logger.info('The project "%s" is in the projects_dict and have been already filled with components<->leads values' % (issue_object.fields.project.key))
        else:
        ## Just Filling the dictionary of projects->components->and mapping components<->component_lead
            logger.info('The project "%s" is going to be created in the projects_dict and filled with components<->leads values' % (issue_object.fields.project.key))
            projects_dict.update({issue_object.fields.project.key: {'component-lead_mapping': {}}})
            try:
                components = jira.project_components(issue_object.fields.project.key)
                ## We need identify project lead for componetns without project leads
            except Exception, e:
                logger.critical('Component_objects have not been retrieved because of: %s' % e)
                exit(1)
            for i in components:
                try:
                    component = jira.component(i.id)
                except Exception, e:
                    logger.critical('Component_objects have not been retrieved because of: %s' % e)
                    exit(1)
                ## check whether component lead active or inactive/disabled/doesn't exist
                try:
                    if component.lead.active:
                        projects_dict[issue_object.fields.project.key]['component-lead_mapping'].update(
                            {component.name: component.lead.key})
                        logger.info(
                            'The component "%s" lead user of project "%s" is ACTIVE => the issues with this component will be reassigned to component lead user "%s"' % (
                                component.name, issue_object.fields.project.key, component.lead.key))
                    else:
                        project = jira.project(issue_object.fields.project.key)
                        projects_dict[issue_object.fields.project.key]['component-lead_mapping'].update({component.name: project.lead.key})
                        logger.info(
                            'The component "%s" lead user of project "%s" is INACTIVE => the issues with this component will be reassigned to project lead user "%s"' % (
                            component.name, issue_object.fields.project.key, project.lead.key))
                except Exception, e:
                    project = jira.project(issue_object.fields.project.key)
                    projects_dict[issue_object.fields.project.key]['component-lead_mapping'].update(
                        {component.name: project.lead.key})
                    logger.info(
                        'The component "%s" lead user of project "%s" is MISSED => the issues with this component will be reassigned to project lead user "%s"' % (
                            component.name, issue_object.fields.project.key, project.lead.key))

    # reassign the issue
    def reassign(issue_object):
        ## reassign the issue to the component lead of the first turned up component in the issue or to project_lead
        if issue_object.fields.components:
            try:
                ## to build list of issues those we are obliged to make reassign
                jira.assign_issue(issue_object.key,
                                  projects_dict[issue_object.fields.project.key]['component-lead_mapping'][
                                      issue_object.fields.components[0].name])
                reassigned_issues_lst.append([issue_object.key,
                                              issue_object.fields.summary.encode('utf-8').rstrip().replace('\t',
                                                                                                           '') if issue_object.fields.summary else 'The summary is missed',
                                              issue_object.fields.description.encode('utf-8').rstrip().replace('\t',
                                                                                                               '') if issue_object.fields.description else 'The description is misssed',
                                issue_object.fields.assignee.displayName if issue_object.fields.assignee else 'The assignee user has been deleted from AD',
                                issue_object.fields.reporter.displayName if issue_object.fields.reporter else 'The reporter user has been deleted from AD',
                                ",".join([i.name for i in issue_object.fields.components]),
                                ",".join([i for i in issue_object.fields.labels])])
                logger.info('The issue "%s" has been just reassigned to the component "%s" lead (or project lead) - "%s"' % (issue_object.key, issue_object.fields.components[0].name,projects_dict[issue_object.fields.project.key]['component-lead_mapping'][issue_object.fields.components[0].name]))
            except Exception, e:
                no_reassign.append(issue_object.key)
                logger.critical('Reassign of the issue "%s" has not been completed because of: %s' % (issue_object.key,e))
                #exit(1)
        else:
            no_components.append(issue_object.key)
            logger.info('The issue "%s" doesn\'t have any component\'s, the email will be sent to "p_luksha","o_koval"' % (issue_object.key))

    # Processing each issue
    for issue_object in issue_array:
        ## if user whether inactive or even deleted from AD
        if not issue_object.fields.assignee:
            logger.info('The assignee user has been deleted from AD => the issue "%s" must be reassigned to the component lead' % (issue_object.key))
            create_dict(issue_object)
            reassign(issue_object)
        elif not issue_object.fields.assignee.active:
            logger.info('The assignee user "%s" has been disabled in AD => the issue "%s" must be reassigned to the component lead' % (issue_object.fields.assignee.key,issue_object.key))
            create_dict(issue_object)
            reassign(issue_object)
        else:logger.info('The assignee user "%s" is active => the issue "%s" is skipped' % (issue_object.fields.assignee.key, issue_object.key))
    ## Create emails bodies
    no_components_issues=",".join(no_components)
    no_reassign_issues=",".join(no_reassign)
    email_msg_send_no_components = email_msg_no_components + ' ' + no_components_issues
    email_msg_send_no_reassign = email_msg_no_reassign + ' ' + no_reassign_issues
    send_email(email_msg_send_no_components + '\n' + email_msg_send_no_reassign, to_email_1)
    send_email(email_msg_send_no_components + '\n' + email_msg_send_no_reassign, to_email_2)

    print projects_dict
    print reassigned_issues_lst
    print no_components_issues
    print no_reassign_issues

    ## to create an csv file of issues those we are obliged to make reassign
    with open('/home/p_luksha/github/logs/HD-87417.csv','wb') as csvfile:
        w = csv.writer(csvfile)
        for i in reassigned_issues_lst:
            w.writerow(i)

    # Remove lock file
    try:
        os.remove(global_conf['lock_path'])
    except IOError, e:
        logger.critical('error deleting lock file. Reason: %s', e)
        exit(1)
