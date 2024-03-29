from consumer import consumption_get_face
from faceSwapLib.roop import core

if __name__=="__main__":
    print(f"Getting configuration for face getter service")
    client = consumption_get_face.Consumer(rabbit_config_path = './config/rabbit.cnf', mysql_config_path = './config/mysql.cnf')

    print(f"Face get service started")
    client.start_consuming()

    print(f"Face getter service closed")
