#!/usr/bin/python3
import pymysql.cursors
import os
import logging
import configparser
import subprocess

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
global_conf = getConfig('GLOBAL')

# set variables
mysql_host = mysql_conf['mysql_host']
mysql_user = mysql_conf['mysql_user']
mysql_password = mysql_conf['mysql_password']
db_confdb = mysql_conf['db_confdb']
db_bxe_info = mysql_conf['db_bxe_info']
sql_select_confdb = mysql_conf['sql_select_confdb']
sql_select_bxe_info = mysql_conf['sql_select_bxe_info']
sql_insert_bxe_info_1 = mysql_conf['sql_insert_bxe_info_1']
sql_insert_bxe_info_2 = mysql_conf['sql_insert_bxe_info_2']
sql_insert_bxe_info_3 = mysql_conf['sql_insert_bxe_info_3']
sql_insert_bxe_info_4 = mysql_conf['sql_insert_bxe_info_4']
gardener_email = global_conf['gardener_email']

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
        exit(1)
    output, err = p.communicate()
    return output

# define fin_script func
def fin_script():
    logging.info('Script run is finished.{}##############################################################'.format("\n"))

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

# define close_sql_con func
def close_sql_con(connection, mysql_db):
    try:
        logging.info('Closing the connection to the MySQL server:{}host:"{}"{}db:"{}"{}user:"{}"{}'.format("\n", mysql_host, "\n", mysql_db, "\n", mysql_user, "\n"))
        connection.close()
    except Exception as e:
        logging.critical('Error during closing connection to the MySQL server: "{}"'.format(e))
        fin_script()
        exit(1)

# define variable's lists
confdb_list = []
bxe_info_list = []
bxe_info_compare_list = []

# create connection, execute sql query and fill relevant list
connection_confdb = create_sql_con(db_confdb)
cursor = exec_sql(connection_confdb, sql_select_confdb, 'select')
close_sql_con(connection_confdb, db_confdb)
for i in cursor:
    confdb_list.append(i)

# create connection, execute sql query and fill relevant list
connection_bxe_info = create_sql_con(db_bxe_info)
cursor = exec_sql(connection_bxe_info, sql_select_bxe_info, 'select')
for i in cursor:
    bxe_info_list.append(i)
    bxe_info_compare_list.append(i['space_key'] + str(i['page_id']))

# fill table
for i in confdb_list:
    logging.info('Checking if entry (spacekey="{}", pageid="{}") already exists in the "conf_orphaned_pages" table in the "{}" database'.format(i['space_key'], str(i['page_id']), db_bxe_info))
    # check if the entry already exists in conf_orphaned_pages
    if i['space_key'] + str(i['page_id']) not in bxe_info_compare_list:
        # if a pages' creator is active
        if i['creator_active'] == 'T':
            # and if a pages' last_editor is active
            if i['last_editor_active'] == 'T':
                # and if a pages' creator_email exists and is not equal to "devnull@booxware.de"
                if i['creator_email'] and i['creator_email'] != 'devnull@booxware.de':
                    # then compose sql query with all fields and put to the field "email_recipient" value from the "creator_email" field
                    sql_query = sql_insert_bxe_info_1.format(i['space_key'], i['page_id'], i['page_URL'], i['creator'], i['last_editor'], i['lastmoddate'], i['creator_email'])
                # but if (a pages' creator_email either doesn't exist or is equal to "devnull@booxware.de") and (last_editor_email exists and is not equal "devnull@booxware.de")
                elif i['last_editor_email'] and i['last_editor_email'] != 'devnull@booxware.de':
                    # then compose sql query with all fields and put to the field "email_recipient" value from the "last_editor_email" field
                    sql_query = sql_insert_bxe_info_1.format(i['space_key'], i['page_id'], i['page_URL'], i['creator'], i['last_editor'], i['lastmoddate'], i['last_editor_email'])
                # but if both a pages' creator_email and last_editor_email don't exist or are equal to "devnull@booxware.de"
                else:
                    # then compose sql query with all fields and put to the field "email_recipient" value from "gardener_email" variable
                    sql_query = sql_insert_bxe_info_1.format(i['space_key'], i['page_id'], i['page_URL'], i['creator'], i['last_editor'], i['lastmoddate'], gardener_email)
            # but if a pages' last_editor is inactive
            elif i['last_editor_active'] != 'T':
                # and if a pages' creator_email exists and is not equal to "devnull@booxware.de"
                if i['creator_email'] and i['creator_email'] != 'devnull@booxware.de':
                    # then compose sql query without field "last_editor" and put to the field "email_recipient" value from the "creator_email" field
                    sql_query = sql_insert_bxe_info_2.format(i['space_key'], i['page_id'], i['page_URL'], i['creator'], i['lastmoddate'], i['creator_email'])
                # but if a pages' creator_email either doesn't exist or is equal to "devnull@booxware.de"
                else:
                    # then compose sql query without field "last_editor" and put to the field "email_recipient" value from the "gardener_email" variable
                    sql_query = sql_insert_bxe_info_2.format(i['space_key'], i['page_id'], i['page_URL'], i['creator'], i['lastmoddate'], gardener_email)
        # but if a pages' creator is inactive and last_editor is active
        elif i['creator_active'] != 'T' and i['last_editor_active'] == 'T':
            # and if last_editor_email exists and is not equal to "devnull@booxware.de"
            if i['last_editor_email'] and i['last_editor_email'] != 'devnull@booxware.de':
                # then compose sql query without field "creator" and put to the field "email_recipient" value from the "last_editor_email" field
                sql_query = sql_insert_bxe_info_3.format(i['space_key'], i['page_id'], i['page_URL'], i['last_editor'], i['lastmoddate'], i['last_editor_email'])
            # but if last_editor_email either doesn't exist or is equal to "devnull@booxware.de"
            else:
                # then compose sql query without field "creator" and put to the field "email_recipient" value from "gardener_email" variable
                sql_query = sql_insert_bxe_info_3.format(i['space_key'], i['page_id'], i['page_URL'], i['last_editor'], i['lastmoddate'], gardener_email)
        # but if both a pages' creator and last_editor are inactive
        elif i['creator_active'] != 'T' and i['last_editor_active'] != 'T':
            # then compose sql query without both fields "creator" and "last_editor" and put to the field "email_recipient" value from the "gardener_email" variable
            sql_query = sql_insert_bxe_info_4.format(i['space_key'], i['page_id'], i['page_URL'], i['lastmoddate'], gardener_email)
        cursor = exec_sql(connection_bxe_info, sql_query, 'insert')
    else:
        logging.info('The entry (spacekey="{}", pageid="{}") already exists n the "conf_orphaned_pages" table in the "{}" database'.format(i['space_key'], str(i['page_id']), db_bxe_info))
close_sql_con(connection_bxe_info, db_bxe_info)
fin_script()
