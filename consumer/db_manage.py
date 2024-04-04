import pymysql
import configparser
import ssl

def load_mysql_config(config_path):
    """Reads and parses the mysql.cnf configuration file."""

    config = configparser.ConfigParser()
    config.read(config_path)

    mysql_config = {}
    mysql_config['database'] = config.get('client', 'database')
    mysql_config['host'] = config.get('client', 'host')
    mysql_config['port'] = config.getint('client', 'port')
    mysql_config['user'] = config.get('client', 'user')
    mysql_config['password'] = config.get('client', 'password')
    # mysql_config['ssl_ca'] = config.get('client', 'ssl_ca')
    return mysql_config

class MySQLDB:
    def __init__(self, mysql_config_path="./mysql.cnf"):

        mysql_config = load_mysql_config(mysql_config_path)

        self.host = mysql_config['host']
        self.user = mysql_config['user']
        self.port = mysql_config['port']
        self.password = mysql_config['password']
        self.database = mysql_config['database']
        # self.ssl = mysql_config['ssl_ca']
        self.connection = None

    def connect(self):

        try:
            self.connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                # ssl=ssl.create_default_context(cafile=self.ssl)
            )
        except Exception as e:
            print(f"Error, can't connect to the database: {e}")
            return False
        return True

    def disconnect(self):

        if self.connection:
            self.connection.close()
            self.connection = None

    def execute_query(self, query, params=None):

        with self.connection.cursor() as cursor:
            try:
                cursor.execute(query, params)
                self.connection.commit()
                return cursor
            except Exception as e:
                print(f"Error, can't execute SQL command: {e}")
                return None

    def fetch_all(self, cursor):

        if cursor:
            return cursor.fetchall()
        return None

    def fetch_one(self, cursor):

        if cursor:
            return cursor.fetchone()
        return None

if __name__ == "__main__":
    db = MySQLDB(mysql_config_path="./mysql.cnf")  # Use config file

    if db.connect():
        cursor = db.execute_query("SELECT * FROM users")
        results = db.fetch_all(cursor)
        result = db.fetch_one(cursor)
        db.disconnect()



