#!/usr/bin/python3
import pymysql.cursors
import csv
import os
import logging
import configparser
import subprocess
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
global_conf = getConfig('GLOBAL')
mysql_conf = getConfig('MYSQL')

# set variables
scp = global_conf['scp']
grep = global_conf['grep']
rm = global_conf['rm']
sql_select = mysql_conf['sql_select']
sql_insert = mysql_conf['sql_insert']
mysql_host = mysql_conf['mysql_host']
mysql_user = mysql_conf['mysql_user']
mysql_password = mysql_conf['mysql_password']
mysql_db_select = mysql_conf['mysql_db_select']
mysql_db_insert = mysql_conf['mysql_db_insert']

# logging settings
logging.basicConfig(filename=log_file, level=logging.DEBUG, format='%(asctime)s %(levelname)s:  %(message)s')

# define shell func
def shell(commandlinestr, cwd = None):
    try:
        if cwd:
            p = subprocess.Popen(commandlinestr, stdout=subprocess.PIPE, shell=True, cwd=cwd)
        else:
            p = subprocess.Popen(commandlinestr, stdout=subprocess.PIPE, shell=True, cwd=basedir)
    except Exception as e:
        logging.critical('Error during performing the command: "{}": {}'.format(commandlinestr, e))
        fin_script()
        exit(1)
    output, err = p.communicate()
    return output

# define search_file func
def search_file(file, cwd):
    logging.info('Looking through the filesystem for the required "{}" file...'.format(file))
    command = 'find {} -name {}'.format(cwd, file)
    files = shell(command).decode("utf-8").split("\n")
    file_names = [i.split("/")[-1] for i in files if i]
    logging.info('The file names list is successfully constructed: {}{}'.format("\n", file_names))
    return file_names

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

# define close_sql_con func
def close_sql_con(connection, mysql_db):
    try:
        logging.info('Closing the connection to the MySQL server:{}host:"{}"{}db:"{}"{}user:"{}"{}'.format("\n", mysql_host, "\n", mysql_db, "\n", mysql_user, "\n"))
        connection.close()
    except Exception as e:
        logging.critical('Error during closing connection to the MySQL server: "{}"'.format(e))
        fin_script()
        exit(1)

# define exec_sql func
def exec_sql(connection, sql, req_type):
    if req_type == 'select':
        with connection.cursor() as cursor:
            try:
                logging.info('Executing sql query{}"{}"{}'.format("\n", sql, "\n"))
                cursor.execute(sql)
            except Exception as e:
                logging.critical('Error during executing sql query: "{}"'.format(e))
                fin_script()
                exit(1)
    elif req_type == 'insert':
        with connection.cursor() as cursor:
            try:
                logging.info('Executing sql query{}"{}"{}'.format("\n", sql, "\n"))
                cursor.execute(sql)
                connection.commit()
            except Exception as e:
                logging.critical('Error during executing sql query: "{}"'.format(e))
                fin_script()
                exit(1)
    return cursor

# define remove_file()
def remove_file():
    file_name = 'tomcat-confluence-access.{}.log'.format(yesterday)
    logging.info('Removing yesterday\'s log file "{}" from the "{}"'.format(file_name, basedir))
    command = rm.format(file_name, basedir)
    shell(command)

# define fin_script func
def fin_script():
    logging.info('Script run is finished.{}##############################################################'.format("\n"))

# copy yesterday's log file from the Confluence server
today = datetime.date(datetime.today())
yesterday = today - timedelta(days=1)
file_name = 'tomcat-confluence-access.{}.log'.format(yesterday)
logging.info('Copying yesterday\'s log file "{}" from the Confluence server'.format(file_name))
command = scp.format(file_name, basedir)
shell(command)

## find file in the filesystem
files_list = search_file(file_name, basedir)

if files_list:
    # grep copied log file
    logging.info('Grepping yesterday\'s log file "{}" in order to find "doremovepage.action" pages entries'.format(file_name))
    command = grep.format(files_list[0], '{ print $1" "$3" "$5 }')
    rows = shell(command).decode("utf-8").replace("[", "").replace("]", "").split("\n")
else:
    logging.info('The file "{}" isn\'t found in the directory "{}".{}Stopping script run.'.format(file_name, basedir, "\n"))
    fin_script()
    exit(1)

# Composing data about removed page
logging.info('Composing data about removed page')
data = [{'removed_date': datetime.strptime(i.split(" ")[0], '%d/%b/%Y:%H:%M:%S'), 'removed_by': i.split(" ")[1], 'pageid': i.split(" ")[2].split("=")[1], 'spacekey':'', 'page_title':''} for i in rows if i]

if data:
    # fetch data from confdb, compose request and then insert data to db
    connection_select = create_sql_con(mysql_db_select)
    connection_insert = create_sql_con(mysql_db_insert)
    for i in data:
        sql_query = sql_select.format(i['pageid'])
        cursor = exec_sql(connection_select, sql_query, 'select')
        for row in cursor:
            i['spacekey'] = row['spacekey']
            i['page_title'] = row['TITLE']
        sql_query = sql_insert.format(i['pageid'], i['page_title'], i['removed_by'], i['removed_date'], i['spacekey'])
        cursor = exec_sql(connection_insert, sql_query, 'insert')
    close_sql_con(connection_select, mysql_db_select)
    close_sql_con(connection_insert, mysql_db_insert)
    # remove log file for yesterday from the local filesystem
    remove_file()
    fin_script()
else:
    logging.info('There aren\'t any "doremovepage.action" pages entries in the yesterday\'s log file "{}".{}Stopping script run.'.
                 format(file_name, "\n"))
    # remove log file for yesterday from the local filesystem
    remove_file()
    fin_script()
