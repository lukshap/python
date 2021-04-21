from jira.client import JIRA
from datetime import datetime, timedelta

class JiraHdmIssue():
    def __init__(self, jira, key):
        self.jira = jira
        self.issue = jira.issue(key, expand='changelog')
        self.assignee = self.issue.fields.assignee.name
        self.status = self.issue.fields.status.name
        self.summary = self.issue.fields.summary
        self.issuetype = self.issue.fields.issuetype
        self.key = self.issue.key
        self.get_time_in_status()
        self.get_comment_info()

    def get_time_in_status(self):
        work_log = self.issue.changelog.histories
        self.status_changed = False
        self.status_time = None
        self.updated = ''

        for history_block in work_log[::-1]:
            for block_record in history_block.items:
                if block_record.field == 'status':
                    self.updated = datetime.strptime(history_block.created.split('.')[0], '%Y-%m-%dT%H:%M:%S')
                    self.status_changed = True
                    if datetime.utcnow() > self.updated:
                        self.status_time = datetime.utcnow() - self.updated
                    else:
                        raise Exception('TimeNotSyncError')
                    break
            if self.updated:
                break

    def get_comment_info(self):
        self.bot_comment = False
        self.bot_comment_time = None
        self.user_comment = False
        self.user_comment_time = None
        comment_log = filter(lambda x: datetime.strptime(x.created.split('.')[0], '%Y-%m-%dT%H:%M:%S') > self.updated,
                             self.issue.fields.comment.comments)

        try:
            last_comment = filter(lambda x: x.author.name != 'wg_hd', comment_log)[-1]
        except IndexError:
            last_comment = None

        if last_comment:
            self.user_comment_time = datetime.utcnow() - datetime.strptime(last_comment.created.split('.')[0],
                                                                           '%Y-%m-%dT%H:%M:%S')
            self.user_comment = True

        try:
            bot_comment = filter(lambda x: x.author.name == 'wg_hd', comment_log)[-1]
        except IndexError:
            bot_comment = None

        if bot_comment:
            self.bot_comment_time = datetime.utcnow() - datetime.strptime(bot_comment.created.split('.')[0],
                                                                          '%Y-%m-%dT%H:%M:%S')
            self.bot_comment = True

    def add_comment(self, comment):
        self.jira.add_comment(self.issue.key, comment)

    def close(self, comment=None, transitionId=2):
        self.jira.transition_issue(
            issue=self.issue.key,
            transitionId=transitionId,
            comment=comment,
        )

    def open(self):
        self.jira.transition_issue(
            issue=self.issue.key,
            transitionId=741,
        )

    def assign(self, user):
        self.jira.assign_issue(self.key, user)
