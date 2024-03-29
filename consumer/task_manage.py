import pika
from concurrent.futures import ThreadPoolExecutor
import configparser
import json
import time

def load_rabbit_config(config_path):
    """Reads and parses the rabbit.cnf configuration file.

    Args:
        config_file_path (str): Path to the rabbit.cnf file.

    Returns:
        dict: A dictionary containing the retrieved configuration values.
    """

    config = configparser.ConfigParser()
    config.read(config_path)

    rabbit_config = {}
    rabbit_config['host'] = config.get('main', 'host')
    rabbit_config['queue_name_1'] = config.get('main', 'queue_name_1')
    rabbit_config['queue_name_2'] = config.get('main', 'queue_name_2')
    rabbit_config['exchange'] = config.get('main', 'exchange')
    rabbit_config['port'] = config.getint('main', 'port')
    rabbit_config['username'] = config.get('main', 'username')
    rabbit_config['password'] = config.get('main', 'password')
    return rabbit_config

class TaskManager:
    def __init__(self, config_path):
        self.config = load_rabbit_config(config_path)
        self.queue_name_1 = self.config['queue_name_1']
        self.queue_name_2 = self.config['queue_name_2']
        self.exchange = self.config['exchange']
        self.connection = None
        self.channel = None
        self.executor = ThreadPoolExecutor(max_workers=4)  # Adjust as needed

    def connect(self):
        """Establishes a connection to RabbitMQ using the configuration values."""

        if not self.connection or not self.connection.is_open:
            credentials = pika.PlainCredentials(username=self.config['username'], password=self.config['password'])
            parameters = pika.ConnectionParameters(
                host=self.config['host'],
                port=self.config['port'], 
                credentials = credentials
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            self.channel.exchange_declare(exchange=self.exchange, durable=True)
            self.channel.queue_declare(queue=self.queue_name_1, durable=True)
            self.channel.queue_declare(queue=self.queue_name_2, durable=True)

    def disconnect(self):
        """Closes the connection to RabbitMQ if it's open."""

        if self.connection and self.connection.is_open:
            self.connection.close()

    def publish_task_1(self, task_data):
        """Publishes a task to the specified queue."""

        self.connect()  # Ensure connection before publishing
        self.channel.basic_publish(
            exchange=self.exchange,
            routing_key=self.queue_name_1,
            body=json.dumps(task_data)  # Serialize data to JSON
        )
        self.disconnect()  # Close connection after publishing


    def publish_task_2(self, task_data):
        """Publishes a task to the specified queue."""

        self.connect()  # Ensure connection before publishing
        self.channel.basic_publish(
            exchange=self.exchange,
            routing_key=self.queue_name_2,
            body=json.dumps(task_data)  # Serialize data to JSON
        )
        self.disconnect()  # Close connection after publishing


    def listen_for_tasks_1(self, callback):
        """Starts consuming tasks from the queue and submits them to the callback one by one."""

        while True:
            try:
                self.connect()  # Ensure connection before starting consumer

                while True:
                    method, properties, body = self.channel.basic_get(queue=self.queue_name_1, auto_ack=True)
                    if method:
                        # Received a message
                        message = json.loads(body)
                        try:
                            # Process the task (instead of submitting to a thread pool)
                            callback(message)
                        except Exception as e:
                            print(f"Error processing task: {message}")
                            print(e)
                            # Requeue the message in case of errors (optional)
                            # self.channel.basic_nack(delivery_tag=method_frame.delivery_tag, requeue=True)
                    else:
                        # No message received, take a brief break and check again
                        time.sleep(0.1)

            except Exception as ex:
                print(f"Error: {ex}")
                # Attempt to reconnect
                self.disconnect()
                time.sleep(0.5)  # Wait before reconnecting

            finally:
                self.disconnect()  # Close connection after finishing



    def listen_for_tasks_2(self, callback):
        """Starts consuming tasks from the queue and submits them to the callback one by one."""

        while True:
            try:
                self.connect()  # Ensure connection before starting consumer

                while True:
                    method, properties, body = self.channel.basic_get(queue=self.queue_name_2, auto_ack=True)
                    if method:
                        # Received a message
                        message = json.loads(body)
                        try:
                            # Process the task (instead of submitting to a thread pool)
                            callback(message)
                        except Exception as e:
                            print(f"Error processing task: {message}")
                            print(e)
                            # Requeue the message in case of errors (optional)
                            # self.channel.basic_nack(delivery_tag=method_frame.delivery_tag, requeue=True)
                    else:
                        # No message received, take a brief break and check again
                        time.sleep(0.1)

            except Exception as ex:
                print(f"Error: {ex}")
                # Attempt to reconnect
                self.disconnect()
                time.sleep(0.5)  # Wait before reconnecting

            finally:
                self.disconnect()  # Close connection after finishing

    def get_queue_tasks_1(self):
        """Retrieves a list of tasks currently in the queue."""

        self.connect()  # Ensure connection before fetching tasks

        try:
            method_frame, header_frame, body = self.channel.basic_get(queue=self.queue_name_1)
            tasks = []
            while method_frame:
                # Deserialize task data from JSON
                task_data = json.loads(body)
                tasks.append(task_data)

                # Fetch the next message
                method_frame, header_frame, body = self.channel.basic_get(queue=self.queue_name_1)

            return tasks

        except Exception as e:
            print(f"Error fetching tasks from queue: {e}")
            return []  # Return an empty list on error

        finally:
            self.disconnect()  # Close connection after fetching tasks

    def get_queue_tasks_2(self):
        """Retrieves a list of tasks currently in the queue."""

        self.connect()  # Ensure connection before fetching tasks

        try:
            method_frame, header_frame, body = self.channel.basic_get(queue=self.queue_name_2)
            tasks = []
            while method_frame:
                # Deserialize task data from JSON
                task_data = json.loads(body)
                tasks.append(task_data)

                # Fetch the next message
                method_frame, header_frame, body = self.channel.basic_get(queue=self.queue_name_2)

            return tasks

        except Exception as e:
            print(f"Error fetching tasks from queue: {e}")
            return []  # Return an empty list on error

        finally:
            self.disconnect()  # Close connection after fetching tasks


if __name__ == '__main__':
    # Example usage:
    task_data = {'some_key': 'some_value'}
    task_manager = TaskManager('node')
    task_manager.publish_task(task_data)

    tasks = task_manager.get_queue_tasks()
    print(tasks)  # Output: [{task_data}, {task_data}, ... ]

    # def process_task(task):
    #     # Implement your task processing logic here
    #     print(f"Processing task: {task}")

    # task_manager.listen_for_tasks(process_task)
