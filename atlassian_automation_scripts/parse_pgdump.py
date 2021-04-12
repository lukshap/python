import logging
import os
import sqlparse
from files_handler import FilesHandler

script_name = os.path.basename(__file__)
basedir = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s:  %(message)s')

pgdumps = {"172.23.89.111_labe2esi_watchlist.sql": "labe2esi_watchlist",
         "172.23.89.111_labe2esi_analytics_service.sql": "labe2esi_analytics_service"
         }

## awk -i inplace '/FROM stdin/{while(getline && $0 != ""){}}1' 172.23.89.111_labe2esi_analytics_service.sql

def main():
    file = FilesHandler()
    for source, dst in pgdumps.items():
        data = file.read_file(source)
        parsed_sql = sqlparse.parse(data)
        content = file.parse_file(parsed_sql)
        file.write_file(dst, content)

if __name__ == '__main__':
    main()