import subprocess
from datetime import datetime, timedelta
import os
import configparser
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

# get script_name and config file
script_name = os.path.basename(__file__)    # get script_name
basedir = os.path.dirname(os.path.abspath(__file__))    # get absolute directory path to the script
config_file = basedir + '/server.conf'   # set absolute path to the script file
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
global_conf = getConfig('GLOBAL')

# set variables
smtp_server = mail_conf['smtp_server']
smtp_port = mail_conf['smtp_port']
smtp_login = mail_conf['smtp_login']
smtp_password = mail_conf['smtp_password']
from_addr = mail_conf['from_addr']
to_addr = mail_conf['to_addr']
subject = mail_conf['subject']
message = mail_conf['message']
days_all = global_conf['days_all']
days_merged = global_conf['days_merged']
repository = global_conf['repository']
repository_url = global_conf['repository_url']
dry_run = False

# logging settings
logging.basicConfig(filename=log_file, level=logging.DEBUG, format='%(asctime)s %(levelname)s:  %(message)s')

# define email func
def send_email():
    logging.info('The email is going to be sent...')
    msg = MIMEMultipart()
    msg.attach(MIMEText(message))
    msg['Subject'] = subject
    msg['From'] = from_addr
    msg['To'] = to_addr
    for i in to_addr.split(","):
        try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            logging.info('Connected to the mail server successfully')
        except Exception as e:
            logging.critical('Error due connection to SMTP server: {}'.format(e))
            exit(1)
        try:
            logging.info('Email to the {} is being sent...'.format(i))
            server.sendmail(from_addr, i, msg.as_string())
            server.quit()
            logging.info('Email to the "{}" has been successfully sent'.format(i))
        except Exception as e:
            logging.critical('Error due email sending: {}'.format(e))
            exit(1)

# define shell func
def shell(commandlinestr, cwd=None):
    try:
        if cwd:
            p = subprocess.Popen(commandlinestr, stdout=subprocess.PIPE, shell=True, cwd=cwd)
        else:
            p = subprocess.Popen(commandlinestr, stdout=subprocess.PIPE, shell=True, cwd=basedir)
    except Exception as e:
        logging.critical('Error during performing the command: "{}": {}.{} The email will be sent to the COD team members'.format(commandlinestr, e, '\n'))
        send_email()
        exit(1)
    output, err = p.communicate()
    return output

# define rem_local_repo func
def rem_local_repo(repository, repository_url):
    logging.info('The "{}" repository is removing from the filesystem...'.format(repository))
    command = "rm -rf {}".format(repository)
    shell(command)
    logging.info('The "{}" repository is successfully removed from the filesystem'.format(repository))

# define clone_rep func
def clone_rep(repository, repository_url):
    rem_local_repo(repository, repository_url)
    logging.info('The "{}" repository is cloning...'.format(repository))
    command = "git clone {}".format(repository_url)
    shell(command)
    logging.info('The "{}" repository is successfully cloned...'.format(repository))
    logging.info('The "{}" repository is pulling...'.format(repository))
    command = "git pull"
    shell(command, basedir + "/" + repository)
    logging.info('The "{}" repository is successfully pulled...'.format(repository))

# define format_list func
def format_list(rawlist, merged=None):
    for branch in rawlist:
        branchDate = branch[0:10]
        branchName = branch.split(' t')[1]
        allBranches.append([branchDate, branchName, merged])

# Cloning the repo
clone_rep(repository, repository_url)

# define all (branches + their last commit's date) where a branch name contains either feature' or 'bugfix' or 'hotfix
logging.info('Defining all branches(which names contain either "feature" or "bugfix" or "hotfix" words) + their last commit\'s date')
allBranchesWithDatesCommand = "for branch in `git branch -r | grep -v HEAD`;do echo -e `git show --format=\"%ci\" $branch | head -n 1` \\t$branch; done"
allBranchesWithDatesList = str(shell(allBranchesWithDatesCommand, basedir + "/" + repository)).replace("\\n", ",").split(',')
FeatureBugfixHotfix = [x for x in allBranchesWithDatesList if 'feature' in x or 'bugfix' in x or 'hotfix' in x]

# define all merged branches from the FeatureBugfixHotfix list defined above
logging.info('Defining merged branches(which names contain either "feature" or "bugfix" or "hotfix" words)  + their last commit\'s date')
allMergesCommand = "git log --merges --oneline --grep 'to development' | sed -e 's/.*from //g' -e 's/ to developme.*//g' -e 's/.*branch .origin\///g' -e 's/. into development//g'"
allMergesList = str(shell(allMergesCommand, basedir + "/" + repository)).replace("\\n", ",").replace('b"', "").split(',')
FeatureBugfixHotfixMerged = [x for x in FeatureBugfixHotfix if x.split(' torigin/')[1] in allMergesList]

# format list allBranches
allBranches = []
format_list(FeatureBugfixHotfix, merged=None)
format_list(FeatureBugfixHotfixMerged, merged='merged')

# define threshold dates
before_day_all = datetime.today() - timedelta(days=int(days_all))
before_day_all_str = datetime.strftime(before_day_all, '%Y-%m-%d')
before_day_merged = datetime.today() - timedelta(days=int(days_merged))
before_day_merged_str = datetime.strftime(before_day_merged, '%Y-%m-%d')
logging.info('Defining threshold dates:{} For all branches - "{}"{} For merged branches - "{}"'.format('\n', before_day_all_str, '\n', before_day_merged_str))

# define a list of branches (both merged and not merged) to be removed
logging.info('Defining all  branches that need to be removed')
toRemove = [x for x in allBranches if x[0] <= before_day_all_str or (x[2] == 'merged' and x[0] <= before_day_merged_str)]
logging.info('There are {} branches will be removed'.format(len(toRemove)))
logging.info('Here is the list of branches have to be removed:{} {}'.format('\n', toRemove))


# remove remote branches from the repository
for branch in toRemove:
    deleteBranchCommand = "git push origin --delete " + branch[1].replace("origin/", "")
    if not dry_run:
        logging.info('This command is running now - "{}"'.format(deleteBranchCommand))
        shell(deleteBranchCommand, basedir + "/" + repository)
    else:
        logging.info('Dry_run mode: branch to be deleted: - "{}"'.format(deleteBranchCommand))

# remove local repo from the filesystem
rem_local_repo(repository, repository_url)
