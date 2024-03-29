from consumer import task_manage, db_manage
from consumer.cdn_manager import CDN
from node import settings
from faceSwapLib.roop import core
import shutil
import os


class Consumer():

    def __init__(self, rabbit_config_path='config/rabbit.cnf', mysql_config_path='config/mysql.cnf'):
        self.task_manager = task_manage.TaskManager(rabbit_config_path)  
        self.db = db_manage.MySQLDB(mysql_config_path)
        self.cdn = CDN(settings.CDN_UPLOAD_PATH)

        # Connect to the BD
        self.db.connect()
    

    def task_get_face(self, task):
        # Implemented task processing logic
        template_id = task["template_id"]

        try:
            print(f"Processing task: {task}")

            os.mkdir(f'data/unique_faces/{str(template_id)}')
            faces_dir = f'data/unique_faces/{str(template_id)}'
            
            core.get_referance_faces_from_source(task["source"], faces_dir)

            # Prepare the SQL query with placeholders for values
            query = "INSERT INTO facetemplateApp2 (template_id, source) VALUES (%s, %s)"

            for face in os.listdir(faces_dir):
                decode_faces_path = f'{faces_dir}/{face}'
                self.cdn.upload_to_cdn(decode_faces_path)
                # Provide the values to insert
                values = (template_id, settings.CDN_UPLOAD_PATH + '/' + decode_faces_path)  

                # Execute the query
                cursor = self.db.execute_query(query, values)

                if cursor:
                    print("Information uploaded successfully!")
                else:
                    print("Error uploading information.")


            if os.path.isdir(task["source"]):
                shutil.rmtree(faces_dir) 
        except Exception as e:
            print(f'Error: unexpected error during face getting: {str(e)}')


    def start_consuming(self):
        self.task_manager.listen_for_tasks_2(self.task_get_face)
        
        # Disconect from BD at the end
        self.db.disconnect()
