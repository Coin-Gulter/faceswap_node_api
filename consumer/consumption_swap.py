from consumer import task_manage, db_manage
from consumer.cdn_manager import CDN
from node import settings
from faceSwapLib.roop import core
import shutil
import re
import os
import time


class Consumer():

    def __init__(self, rabbit_config_path='config/rabbit.cnf', mysql_config_path='config/mysql.cnf'):
        self.task_manager = task_manage.TaskManager(rabbit_config_path)  
        self.db = db_manage.MySQLDB(mysql_config_path)
        self.cdn = CDN(settings.CDN_UPLOAD_PATH)

        # Connect to the BD
        self.db.connect()

    def task_swap_face(self, task):
        # Implemented task processing logic
        task_id = task["task_id"]
        decoded_img = task["decoded_image"]
        template_id = task['template_id']
        source_extension = task['source_extension']

        try:
            print(f"Processing task: {task}")
            face_source = []
            from_face = os.listdir(os.path.join(decoded_img, 'from_face'))
            to_face = os.listdir(os.path.join(decoded_img, 'to_face'))
            output_folder_path = f'data/result/{str(task_id)}'
            os.mkdir(output_folder_path)
            
            output_file_path = f'{output_folder_path}/{str(template_id) + str(source_extension)}'

            cdn_result_path = None

            query_status = "UPDATE taskApp2 SET status = %s WHERE task_id = %s;"
            query_timer = "UPDATE taskApp2 SET timer = %s WHERE task_id = %s;"
            query_source = "UPDATE taskApp2 SET source = %s WHERE task_id = %s;"

            source_path = f"{settings.SOURCE_PATH + str(template_id) + str(source_extension)}"
            cdn_result_path = output_file_path

            if not os.path.isfile(source_path):
                video_byt = self.cdn.download_from_cdn(re.sub(r'^(\.\/)', '', source_path))

                with open(source_path, 'wb') as f:
                    f.write(video_byt)

            self.db.execute_query(query_status, ('in_work', task_id))

            for index, face_path in enumerate(from_face):
                face_source.append([f"{decoded_img + '/from_face/' + face_path}",
                                    f"{decoded_img + '/to_face/' + to_face[index]}"])

            print('resources --- ', face_source, source_path, output_file_path)

            core.run_multiple(face_source, source_path, output_file_path, task['watermark'], 'data/watermark/1.png', is_it_image=task['is_image'])
            
            self.db.execute_query(query_timer, (int(time.time())-task['timer'], task_id))
            self.db.execute_query(query_status, ('done', task_id))
            self.db.execute_query(query_source, (settings.CDN_UPLOAD_PATH + source_path, task_id))

            self.cdn.upload_to_cdn(cdn_result_path)

        except Exception as e:
            print(f'Error: unexpected error during face swap: {str(e)}')
            self.db.execute_query(query_status, ('Error', task_id))

        # if os.path.isdir(os.path.join(settings.IMAGES_PATH, task_id)):
        #     shutil.rmtree(os.path.join(settings.IMAGES_PATH, task_id)) 


    def start_consuming(self):
        self.task_manager.listen_for_tasks_1(self.task_swap_face)
        
        # Disconect from BD at the end
        self.db.disconnect()
