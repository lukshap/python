from jira import JIRA
from datetime import datetime
import configparser
import requests
import os
import logging

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

# set variables
user = global_conf['user']
password = global_conf['password']
jira_url = global_conf['jira_url']
conf_url = global_conf['conf_url']
bitb_url = global_conf['bitb_url']
bitb_teams_pr = global_conf['bitb_teams_pr']
bitb_teams_repo = global_conf['bitb_teams_repo']
bitb_teams_file = global_conf['bitb_teams_file']
bitb_url = global_conf['bitb_url']

# set header and auth for requests
headers = {'Content-Type': 'application/json'}
auth = (user, password)

# logging settings
logging.basicConfig(filename=log_file, level=logging.DEBUG, format='%(asctime)s %(levelname)s:  %(message)s')

# create instance(object) of JIRA class
jira = JIRA(jira_url, basic_auth=(user, password))

# get all boards from JIRA
def get_all_boards():
    boards_startAt = 0
    boards_maxResults = 50
    try:
        logging.info('Getting all boards from "{}" ...'.format(jira_url))
        all_boards = jira.boards(startAt=boards_startAt, maxResults=boards_maxResults)
    except Exception as e:
        logging.critical('Error while getting all boards from "{}":{}'.format(jira_url, e))
        exit(1)
    while not all_boards.isLast:
        boards_startAt += boards_maxResults
        all_boards = jira.boards(startAt=boards_startAt, maxResults=boards_maxResults)
    return all_boards

def req(req_type, uri, data = None):
    if req_type == 'GET':
        try:
            response = requests.get(uri, auth=auth).json()
        except Exception as e:
            logging.critical('The error "{}" happens while trying to "GET" uri "{}"'.format(e, uri))
            exit(1)
    elif req_type == 'POST':
        try:
            response = requests.post(uri, headers=headers, data=payload, auth=auth).json()
        except Exception as e:
            logging.critical('The error "{}" happens while trying to "POST" uri "{}"'.format(e, uri))
            exit(1)
    return response

# get json file with data about teams, boards, confluence pages
logging.info('The information about teams, boards, confluence pages is getting from the bitbucket repo "{}/projects/{}/repos/{}" ...'.format(bitb_url, bitb_teams_pr, bitb_teams_repo))
bitb_teams_json_uri = '{}/projects/{}/repos/{}/raw/{}'.format(bitb_url, bitb_teams_pr, bitb_teams_repo, bitb_teams_file)
rb = req('GET', bitb_teams_json_uri)

# find active sprints in the each found board, define the date, compose pages, post pages to confluence
today = datetime.date(datetime.today())  # only date without time
all_boards = get_all_boards()
for team in rb.keys():
    for board in all_boards:
        if rb[team]['scrumBoard'] == board.name:
            try:
                logging.info('Getting all sprints from the board "{}"'.format(board.name))
                sprints = jira.sprints(board.id, extended=True)
            except Exception as e:
                logging.critical('Error while getting all sprints from the board "{}":{}'.format(board.name, e))
                exit(1)
            # define active sprint
            for sprint in sprints:
                if sprint.state == 'ACTIVE':
                    logging.info('Board "{}": the active sprint "{}" is identified'.format(board.name, sprint.name))
                    active_sprints = True
                    # First define page name, parent page space key,parent page name, attach_space_key, attach_page and attach_name from the gotten bitbucket json file
                    page_name = sprint.name
                    par_page_space_key = rb[team]['sprintsParentPage'].split("/")[-2]
                    par_page_name = rb[team]['sprintsParentPage'].split("/")[-1]
                    attach_space_key = rb[team]['loggedHoursImage'].split("/")[-2]
                    attach_page = rb[team]['loggedHoursImage'].split("/")[-1].replace("+", " ")
                    attach_name = sprint.name + '.png'
                    sprintEnd = datetime.date(datetime.strptime(sprint.endDate, '%Y-%m-%d %H:%M'))

                    if sprintEnd == today: # for prod
                    #if sprintEnd == datetime.date(datetime.strptime('2017-07-21', '%Y-%m-%d')): # for test
                        logging.info('Board "{}": sprint "{}" => today "{}" is the last day of the sprint => the relevant Confluence page should be created'
                                     .format(board.name, sprint.name, today))

                        # check if page already exists in a Confluence space
                        logging.info('Checking if the page "{}" already exists in the space "{}"'.format(page_name, par_page_space_key))
                        conf_uri = '{}/rest/api/content?spaceKey={}&title={}'.format(conf_url, par_page_space_key, page_name)
                        r = req('GET', conf_uri)

                        # if page doesn't exist in a Confluence space
                        if not r['results']:
                            ## creating the page's content
                            logging.info('Board "{}": the page "{}" reffered to the active sprint "{}" is composing to be created in the space "{}"'
                                         .format(board.name, page_name, sprint.name, par_page_space_key))

                            # define a velocity link value
                            velocity = '{}/secure/RapidBoard.jspa?rapidView={}&view=reporting&chart=velocityChart'\
                                .format(jira_url, str(board.id))

                            # define a Burndown gadget value
                            burndown = "{gadget:width=450|border=true|url=" + jira_url + "/rest/gadgets/1.0/g/com.pyxis.greenhopper.jira:greenhopper-gadget-sprint-burndown/gadgets/greenhopper-sprint-burndown.xml}" \
                                                                                         " rapidViewId=" + str(board.id) + "&showRapidViewName=false&sprintId=" + str(sprint.id) + "&showSprintName=false&isConfigured=true&refresh=false&=false {gadget}"

                            # define a Scope gadget value
                            scope = "{gadget:width=450|border=true|url=" + jira_url + "/rest/gadgets/1.0/g/com.pyxis.greenhopper.jira:greenhopper-gadget-sprint-health/gadgets/greenhopper-sprint-health.xml}" \
                                                                                      " rapidViewId=" + str(board.id) + "&showRapidViewName=true&sprintId=" + str(sprint.id) + "&showSprintName=true&showAssignees=false&isConfigured=true&refresh=false&=false {gadget}"

                            # define a time_distribution attachment value
                            time_distr = "!{}:{}^{}|align=left,border=2,width=450!"\
                                .format(attach_space_key, attach_page, attach_name)

                            # The value for page content is composed
                            value = 'h2. Velocity' + '\\n' + velocity + '\\n' + 'h2. Burndown' + '\\n' + burndown + '\\n' + 'h2. Scope' + '\\n' + scope + '\\n' + 'h2. Time distribution' + '\\n' + time_distr

                            # getting Confluence parent page id (par_page_id)
                            logging.info('Getting the parent page id of the parent page "{}" from the space "{}"'.format(par_page_name, par_page_space_key))
                            conf_uri = '{}/rest/api/content?spaceKey={}&title={}'.format(conf_url, par_page_space_key, par_page_name)
                            r = req('GET', conf_uri)
                            par_page_id = r['results'][0]['id']

                            # compose payload for the POST request
                            payload = '{"type": "page","title": "' + page_name + '","ancestors": [{"id": "' + par_page_id + '"}], "space":{"key":"' + par_page_space_key + '"},"body": {"storage": {"value": "' + value + '", "representation": "wiki"}}}'

                            # create a page in Confluence
                            logging.info('The page "{}" is going to be created in the Confluence space "{}" underneath the parent page "{}".'
                                         .format(page_name, par_page_space_key, par_page_name))
                            conf_uri = '{}/rest/api/content'.format(conf_url)
                            r = req('POST', conf_uri, data=payload)
                            logging.info('The page "{}" has been just successfully created in the Confluence space "{}". Please follow the link - "{}"'
                                         .format(page_name, par_page_space_key, r['_links']['base'] + r['_links']['webui']))
                        else:
                            logging.info('The page "{}" already exists in the space "{}" => will not be created'.format(page_name, par_page_space_key))
                    else:
                        logging.info('Board "{}": sprint "{}" => today "{}" IS NOT the last day of the sprint'.format(board.name, sprint.name, today))
            if not active_sprints:
                logging.info('Seems there is no active sprint in the board "{}" for the team "{}"'.format(board.name, team))





