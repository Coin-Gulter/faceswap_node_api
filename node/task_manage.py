import pika
from concurrent.futures import ThreadPoolExecutor
from node import settings
import configparser
import json

def load_rabbit_config():
    """Reads and parses the rabbit.cnf configuration file.

    Args:
        config_file_path (str): Path to the rabbit.cnf file.

    Returns:
        dict: A dictionary containing the retrieved configuration values.
    """

    config = configparser.ConfigParser()
    config.read(settings.REBBIT)

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
    def __init__(self, ):
        self.config = load_rabbit_config()
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
            self.channel.exchange_declare(exchange=self.exchange, durable=True, exchange_type='direct')
            self.channel.queue_declare(queue=self.queue_name_1, durable=True)
            self.channel.queue_declare(queue=self.queue_name_2, durable=True)

    def disconnect(self):
        """Closes the connection to RabbitMQ if it's open."""

        if self.connection and self.connection.is_open:
            self.connection.close()

    def publish_task_1(self, task_data):
        """Publishes a task to the specified queue."""

        self.connect()  # Ensure connection before publishing
        self.channel.queue_bind(self.queue_name_1, self.exchange, routing_key=self.queue_name_1)
        self.channel.basic_publish(
            exchange=self.exchange,
            routing_key=self.queue_name_1,
            body=json.dumps(task_data)  # Serialize data to JSON
        )
        self.disconnect()  # Close connection after publishing

    def publish_task_2(self, task_data):
        """Publishes a task to the specified queue."""

        self.connect()  # Ensure connection before publishing
        self.channel.queue_bind(self.queue_name_2, self.exchange, routing_key=self.queue_name_2)
        self.channel.basic_publish(
            exchange=self.exchange,
            routing_key=self.queue_name_2,
            body=json.dumps(task_data)  # Serialize data to JSON
        )
        self.disconnect()  # Close connection after publishing

    def listen_for_tasks_1(self, callback):
        """Starts consuming tasks from the queue and submitting them to the callback."""

        self.connect()  # Ensure connection before starting consumer

        def on_message(channel, method, properties, body):
            message = json.loads(body)  # Deserialize JSON
            try:
                # Submit task to thread pool for asynchronous execution
                self.executor.submit(callback, message)
                channel.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                # Handle exceptions gracefully, e.g., log error and re-queue
                print(f"Error processing task: {message}")
                print(e)
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        self.channel.basic_consume(queue=self.queue_name_1, on_message_callback=on_message)
        self.channel.start_consuming()

    def listen_for_tasks_2(self, callback):
        """Starts consuming tasks from the queue and submitting them to the callback."""

        self.connect()  # Ensure connection before starting consumer

        def on_message(channel, method, properties, body):
            message = json.loads(body)  # Deserialize JSON
            try:
                # Submit task to thread pool for asynchronous execution
                self.executor.submit(callback, message)
                channel.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                # Handle exceptions gracefully, e.g., log error and re-queue
                print(f"Error processing task: {message}")
                print(e)
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        self.channel.basic_consume(queue=self.queue_name_2, on_message_callback=on_message)
        self.channel.start_consuming()

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
