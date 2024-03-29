from consumer import consumption_swap
from faceSwapLib.roop import core

if __name__=="__main__":
    print(f"Getting configuration for face swap service")
    client = consumption_swap.Consumer(rabbit_config_path = './config/rabbit.cnf', mysql_config_path = './config/mysql.cnf')

    print(f"Face swap service started")
    client.start_consuming()

    print(f"Face swap service closed")
