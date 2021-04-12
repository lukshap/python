#!/usr/bin/python3

"""
1 Clones "" repository
2 Gets all tags from the repository
3 Gets all releases (i.e. PR merged to the master branch) from the repository
4 Clones "licenseHelper" repository
5 Copies the local "AssetRegisterCreator.jar" which is compiled with the correct credentials beforehand to the cloned "licenseHelper" repository
6 Define the list of dictionaries where each dictionary represents one release.
It is true for each release:
release = previous release + tagged commit
previous release = previous release' + tagged commit'
Since we need to pass tag and previous tag to the "AssetRegisterCreator.jar" we need to define tag and previous tag beforehand. And it is:
tag = tagged commit
previous tag = tagged commit'
7 Runs "AssetRegisterCreator.jar" command using tag and previous tag
8 Zips the report into the "licenseHelper/Change_Report_*.zip"
9 Sends emails to the recipients
"""

import os
import logging
import configparser
import subprocess
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import re

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
global_conf = getConfig('GLOBAL')

# set variables
mail_smtp_server = mail_conf['smtp_server']
mail_smtp_port = mail_conf['smtp_port']
mail_smtp_login = mail_conf['smtp_login']
mail_smtp_password = mail_conf['smtp_password']
mail_from_addr = mail_conf['from_addr']
mail_to_addr = mail_conf['to_addr']
mail_subject = mail_conf['subject']
mail_message = mail_conf['message']
pattern = global_conf['pattern']
report_sheets = global_conf['report_sheets']
target_repository = global_conf['target_repository']
target_repository_url = global_conf['target_repository_url']
jar_repository = global_conf['jar_repository']
jar_repository_url = global_conf['jar_repository_url']
jar_file = global_conf['jar_file']

# logging settings
logging.basicConfig(filename=log_file, level=logging.DEBUG, format='%(asctime)s %(levelname)s:  %(message)s')

# define email func
def send_email(attaches):
    logging.info('The email is going to be sent...')
    msg = MIMEMultipart()
    msg.attach(MIMEText(mail_message))
    msg['Subject'] = mail_subject
    msg['From'] = mail_from_addr
    for j in attaches:
        with open(basedir + '/' + jar_repository + '/' + j, "rb") as attach:
            part = MIMEApplication(attach.read(), Name=j)
            part['Content-Disposition'] = 'attachment; filename="{}"'.format(j)
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

# define clone_rep func
def clone_rep(repository, repository_url):
    logging.info('The "{}" repository is removing...'.format(repository))
    command = "rm -rf {}".format(repository)
    shell(command)
    logging.info('The "{}" repository is successfully removed'.format(repository))
    logging.info('The master branch of the "{}" repository is cloning...'.format(repository))
    command = "git clone -b master {}".format(repository_url)
    shell(command)
    logging.info('The master branch of the "{}" repository is successfully cloned...'.format(repository))
    logging.info('The "{}" repository is pulling...'.format(repository))
    command = "git pull"
    shell(command, basedir + "/" + repository)
    logging.info('The "{}" repository is successfully pulled...'.format(repository))

# define search_file func
def search_file(file, cwd):
    logging.info('Looking through the filesystem for the required "{}" file...'.format(file))
    command = 'find {} -name {}'.format(cwd, file)
    files = shell(command).decode("utf-8").split("\n")
    file_names = {i.split("/")[-1]: i.split("/")[:-1] for i in files if i}
    logging.info('The file names dict is successfully constructed: {}'.format(file_names))
    return file_names

# define find_tag func
def find_tag(tag_hash):
    """
    returns tag number basing on the hash input
    """
    for i in tags_fin:
        if tag_hash == i[2]:
            return i[1]
        
# define find_merges func
def find_merges(merge_hash):
    """
    returns merge dict basing on the hash input
    """
    for i in merges:
        if merge_hash == i['hash']:
            return i

# Cloning the repo
clone_rep(target_repository, target_repository_url)

# getting the all refs/tags along with it's date and hash
logging.info('The all refs/tags from the "{}" repository are getting...'.format(target_repository))
command = "git for-each-ref --format='%(*committerdate:iso8601)%(committerdate:iso8601) %(refname) %(objectname:short)' refs/tags"  # for prod command
output_tags = shell(command, basedir + "/" + target_repository).decode("utf-8").split("\n")  # for prod command
logging.info('The all refs/tags from the "{}" repository are successfully retrieved'.format(target_repository))

# here the list of all tags (and it's dates in string format, hashes) which match the regexp pattern is being constructed
logging.info('The refs/tags from the "{}" repository which match to the regexp "{}" are getting...'.format(target_repository, pattern))
tags = [[i.split(" ")[0] + " " + i.split(" ")[1] + " " + i.split(" ")[2], i.split(" ")[3], i.split(" ")[4]] for i in output_tags if i]
tags_fin = [[i[0], i[1].split("/")[2], i[2]] for i in tags if re.match(pattern, i[1].split("/")[2])]

# getting the all merges (and it's parents) which were committed to master
logging.info('The all merges to master from the "{}" repository are getting...'.format(target_repository))
command = "git log --merges --grep=\"Merge pull request .* to master\" --pretty='%ci %h %p'"  # for prod command
output_merges = shell(command, basedir + "/" + target_repository).decode("utf-8").split("\n")  # for prod command
logging.info('The all merges to master from the "{}" repository are successfully retrieved'.format(target_repository))

# here the list of dicts of all merges (and it's dates in string format, hashes, parent's hashes) is being constructed
merges = [{"date": i.split(" ")[0] + " " + i.split(" ")[1] + " " + i.split(" ")[2], "hash": i.split(" ")[3], "prev_merge_hash": i.split(" ")[4], "tag_hash": i.split(" ")[5]} for i in output_merges if i]

# here the list of dicts of today's releases (i.e. PR merged to the master branch) is being constructed
logging.info('The merges from the "{}" repository which were committed today are getting...'.format(target_repository))
today = datetime.date(datetime.today())  # only date without time
today_release = [i for i in merges if today == datetime.date(datetime.strptime(i['date'], '%Y-%m-%d %H:%M:%S %z'))] # for prod today's  release
# today_release = [i for i in merges if datetime.date(datetime.strptime('2017-05-17', '%Y-%m-%d')) == datetime.date(datetime.strptime(i['date'], '%Y-%m-%d %H:%M:%S %z'))] # for test one release
# today_release = [i for i in merges if datetime.date(datetime.strptime('2017-02-08', '%Y-%m-%d')) == datetime.date(datetime.strptime(i['date'], '%Y-%m-%d %H:%M:%S %z'))] # for test two release
# today_release = [i for i in merges if datetime.date(datetime.strptime('2017-05-17', '%Y-%m-%d')).year == datetime.date(datetime.strptime(i['date'], '%Y-%m-%d %H:%M:%S %z')).year] # for test in a year
logging.info('Here is the list of today\'s releases:{}{}'.format('\n', today_release))

# Cloning the repo
clone_rep(jar_repository, jar_repository_url)

# Remove the remote binary jar file and copy the local binary jar file instead
logging.info('The remote binary jar file "{}" is searching...'.format(jar_file))
files_dict = search_file(jar_file, jar_repository)
logging.info('The remote binary jar file "{}" is removing...'.format(jar_file))
path = ''
for i in files_dict[jar_file]:
    path += '{}/'.format(i)
command = 'rm -f ' + path + jar_file
shell(command)
logging.info('The local binary jar "{}" instead of remote is copying...'.format(jar_file))
command = 'cp {} {}'.format(jar_file, path)
shell(command)

# Defining a tag from the today's release (i.e. PR merged to the master branch), then defining a tag from the previous release => creating reports
if today_release:
    logging.info('The reports are being constructed...')
    report_sheets = report_sheets.split(",")
    for i in today_release:
        tag = find_tag(i["tag_hash"])
        prev_merge = find_merges(i["prev_merge_hash"])
        prev_tag = find_tag(prev_merge["tag_hash"])
        # here the reports are being constructed and zipped
        for j in report_sheets:
            command = 'java -jar AssetRegisterCreator.jar --sheet {} --outputFile {} --from {} --to {} --repository {}/{}'.format(j, j, tag, prev_tag, basedir, target_repository)
            shell(command, basedir + "/" + jar_repository)
        # command = 'java -jar AssetRegisterCreator.jar --file raw_service_component_lists/common.txt --from {} --to {} --repository {}/{}'.format(tag, prev_tag,
        #                                                                                                                     basedir, target_repository)
        # shell(command, basedir + "/" + jar_repository)
        logging.info('The reports from tag "{}" to tag "{}" are successfully constructed'.format(prev_tag, tag))
        # zipping reports
        logging.info('The reports from tag "{}" to tag "{}" are being zipped...'.format(prev_tag, tag))
        command = 'zip -r Change_Report_from_{}_to_{}.zip {}_assetregister_with_common'.format(prev_tag, tag, tag)
        shell(command, basedir + "/" + jar_repository)
        logging.info('The reports from tag "{}" to tag "{}" are successfully zipped'.format(prev_tag, tag))
else:
    logging.critical('There are not any releases on "{}"'.format(datetime.today()))
    exit(1)

# find the report file produced by shell script
logging.info('The Change_Report_*.zip file in the "{}" directory is searching...'.format(jar_repository))
files_dict = search_file('Change_Report_*.zip', jar_repository)

# send email
send_email(files_dict)
