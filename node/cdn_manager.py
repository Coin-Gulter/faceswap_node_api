import requests
from node import settings
import configparser
import re

def load_cdn_config():
    """Reads and parses the cdn.cnf configuration file.

    Args:
        config_file_path (str): Path to the cdn.cnf file.

    Returns:
        dict: A dictionary containing the retrieved configuration values.
    """

    config = configparser.ConfigParser()
    config.read(settings.CDN)

    cdn_config = {}
    cdn_config['base_url'] = config.get('main', 'base_url')
    return cdn_config

class CDN:

    def __init__(self):
        self.config = load_cdn_config()
        self.base_url = self.config['base_url']

    def upload_to_cdn(self, file_path):
        """
        Load file to the CDN.

        Args:
            file_path (str): path on the local disk.
            file_type (str): file type ("video/mp4", "image/webp").

        Returns:
            bool: True if succeced or False.
        """
        if file_path.endswith('.mp4'):
            file_type = "video/mp4"
        elif file_path.endswith('.png'):
            file_type = "image/png"
        elif file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
            file_type = "image/jpg"
        elif file_path.endswith('.webp'):
            file_type = "image/webp"

        headers = {
            "Content-Type": file_type,
        }
        with open(file_path, "rb") as f:
            response = requests.put(
                self.base_url + "/" + re.sub(r'^(\.\/)', '', file_path), headers=headers, data=f
            )
        return response.status_code == 200

    def download_from_cdn(self, file_name):
        """
        Завантажує файл з CDN.

        Args:
            file_name (str): Ім'я файлу на CDN.

        Returns:
            bytes: Вміст файлу.
        """
            
        response = requests.get(f"{self.base_url}{file_name}")
        return response.content


if __name__=="__main__":
    # Usage example
    cdn = CDN()

    # Download file
    file_path = "/path/to/1.mp4"
    cdn.upload_to_cdn(file_path)

    # Load file
    file_name = "1.mp4"
    file_content = cdn.download_from_cdn(file_name)
