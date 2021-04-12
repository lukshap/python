import logging
import os

script_name = os.path.basename(__file__)
basedir = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s:  %(message)s')

class FilesHandler():
    def read_file(self, source: str) -> str:
        """
        Read file

        :return: (str) file with sql queries
        """
        try:
            with open(source, "r") as file:
                data = file.read()
        except Exception as e:
            logging.info('Error: \n{}'.format(e))
        return data

    def write_file(self, dst: str, content: str):
        """
        Write file

        :param dst: the file name that will be created

        :return: (dict) parameters of the certain replication task
        """
        try:
            with open(dst, "a") as file:
                for sql_query in content:
                    if "awsdms" not in sql_query:
                        file.write(sql_query)
        except Exception as e:
            logging.info('Error: \n{}'.format(e))

    def parse_file(self, parsed_sql: str) -> dict:
        """
        Read file

        :return: (dict) parameters of the certain replication task
        """
        content = []
        for statement in parsed_sql:
            for token in statement.flatten():
                if str(token.ttype) == "Token.Keyword":
                    if str(token.value) == "FUNCTION":
                        content.append(statement.normalized)
                    if str(token.value) == "SEQUENCE":
                        content.append(statement.normalized)
                    if str(token.value) == "CONSTRAINT":
                        content.append(statement.normalized)
                    if str(token.value) == "INDEX":
                        content.append(statement.normalized)
        return content