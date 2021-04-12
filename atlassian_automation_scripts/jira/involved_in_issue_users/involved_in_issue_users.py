#!/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'p_luksha'

"""
Gets issues from jql, gathers unique users from assignee,reporter,watchers,participants,feature_owner,reviewer fields and puts them into the variable "users_list"
"""

from jira.client import JIRA
from datetime import datetime, timedelta, date
import logging
import fcntl
import os
import ConfigParser
import smtplib
import httplib

# import requests.packages.urllib3
# requests.packages.urllib3.disable_warnings()

class JiraIssueExtends:
    def __init__(self, jira, issue_object):
        self.jira = jira
        self.issue = issue_object
        self.fields = self.issue.fields
        ## if assignee was not disabled
        if hasattr(self.fields,'assignee') and getattr(self.fields,'assignee'):
            self.assignee = self.issue.fields.assignee.key
        else: self.assignee = 'removed_user'
        ## if reporter was not disabled
        if hasattr(self.fields,'reporter') and getattr(self.fields,'reporter'):
            self.reporter = self.issue.fields.reporter.key
        else: self.reporter = 'removed_user'
        self.key = self.issue.key
        self.watchers = jira.watchers(self.key).watchers
        self.participants = getattr(self.issue.fields,participants)
        self.reviewer = getattr(self.issue.fields,reviewer)
        self.feature_owner = getattr(self.issue.fields,feature_owner)

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
custom_fields = get_properties('CUSTOM_FIELDS')
log_path = global_conf['log_path']
fields = global_conf['fields']
jql = global_conf['jql']
users_list = global_conf['users_list']
participants = custom_fields['participants']
reviewer = custom_fields['reviewer']
feature_owner = custom_fields['feature_owner']

users = []

# Logging settings
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler = logging.FileHandler(log_path)
handler.setLevel(logging.DEBUG)
handler.setFormatter(formatter)
logger.addHandler(handler)
httplib.HTTPConnection.debuglevel = 0

maxResults = 100
startPos = 0
issue_array = []
next_result = True
debug = False

#   Main
if __name__ == '__main__':
    fp = open(global_conf['lock_path'], 'w')
    try:
        fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError, e:
        logger.critical('error getting lock, another instance running? Reason: %s', e)
        exit(1)
    jira = None
    jira_user = global_conf['user']
    jira_password = global_conf['password']
    try:
        jira = JIRA({'server': global_conf['jira_url']}, basic_auth=(jira_user, jira_password))
    except Exception, e:
        logger.critical('JIRA instance unavailable, detail: %s' % e)
        exit(1)
    # Строим список issue потенциально требующих обработки
    while next_result:
        issue_set = []
        try:
            issue_set = jira.search_issues(
                jql,
                fields=fields,
                startAt=startPos,
                maxResults=maxResults,
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
    # Обрабатываем issue
    for issue_object in issue_array:
            issue = JiraIssueExtends(jira, issue_object)
            ## Get assignee if not exists in the list of users
            if issue.assignee != 'removed_user' and issue.assignee not in users:
                users.append(issue.assignee)
            ## Get reporter if not exists in the list of users
            if issue.reporter != 'removed_user' and issue.reporter not in users:
                users.append(issue.reporter)
            ## Get all participants if not exist in the list of users
            if issue.participants:
                if hasattr(issue.participants,'__iter__'):
                    [users.append(i.key) for i in issue.participants if i.key not in users]
                elif issue.participants.key not in users:
                    users.append(issue.participants.key)
            ## Get all reviewers if not exist in the list of users
            if issue.reviewer:
                if hasattr(issue.reviewer, '__iter__'):
                    [users.append(i.key) for i in issue.reviewer if i.key not in users]
                elif issue.reviewer.key not in users:
                    users.append(issue.reviewer.key)
            ## Get all feature_owners if not exist in the list of users
            if issue.feature_owner:
                if hasattr(issue.feature_owner, '__iter__'):
                    [users.append(i.key) for i in issue.feature_owner if i.key not in users]
                elif issue.feature_owner.key not in users:
                    users.append(issue.feature_owner.key)
            ## Get all watchers if not exist in the list of users
            if len(issue.watchers) != 0:
                [users.append(i.key) for i in issue.watchers if i.key not in users]

    with open(users_list, 'w') as file:
        for i in users:
            file.write(i+'\n')


      # Удаляем lock файл
    try:
        os.remove(global_conf['lock_path'])
    except IOError, e:
        logger.critical('error deleting lock file. Reason: %s', e)
        exit(1)

