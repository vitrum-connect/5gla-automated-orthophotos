import os
import requests
import time
import json
import zipfile

from custom_logger.custom_logger import CustomLogger


def switch_case(status_code):
    switcher = {
        10: "Task queued.",
        20: "Task running.",
        30: "Task failed.",
        40: "Task completed.",
        50: "Task canceled."
    }
    return switcher.get(status_code, "Invalid status code")


class NodeodmClient:
    """ A class to interact with the NodeODM API.

    """

    def __init__(self):
        temp = os.path.dirname(os.path.abspath(__file__))
        self.project_dir = os.path.dirname(temp)
        self.local_image_dir = os.path.join(self.project_dir, 'images')
        self.odm_output_dir = os.path.join(self.project_dir, 'odm_output')
        self.nodeodm_url = 'http://192.168.2.39:4000'
        self.logger = CustomLogger()

    def http_get(self, url):
        response = requests.get(url)
        response.raise_for_status()
        if response.status_code != 200:
            self.logger.log_warning(f"Error fetching data from {url}: {response['text']}")
        return response

    def http_post(self, url, data, files=None):
        response = requests.post(url, data=data, files=files)
        response.raise_for_status()
        if response.status_code != 200:
            self.logger.log_warning(f"Error posting data to {url}: {response.text}")
        return response

    def remove_task(self, task_id):
        """ Removes a task from NodeODM

        :param task_id: The task ID to remove
        :return: True if the task was removed successfully, None if an error occurred

        """
        response = self.http_post(f'{self.nodeodm_url}/task/remove', data={'uuid': task_id})
        response_json = json.loads(response.text)
        if response.status_code != 200:
            self.logger.log_warning(f"Error removing task {task_id}: {response_json['text']}")
            return None
        self.logger.log_info(f"Task {task_id} removed.")
        return True

    def get_task_status(self, task_id):
        response = self.http_get(f'{self.nodeodm_url}/task/{task_id}/info')
        response_json = json.loads(response.text)
        if response.status_code != 200:
            self.logger.log_warning(f"Error getting task status for task {task_id}: {response.text}")
            return None
        status_code = response_json['status']['code']
        return status_code

    def create_task(self, images_path, options):
        """ Creates a new task in NodeODM

        :param images_path: The path to the images directory
        :param options: The NodeODM task options
        :return: The task ID of the created task or None if an error occurred

        """
        files = [(f'images', open(os.path.join(images_path, f), 'rb')) for f in os.listdir(images_path) if
                 os.path.isfile(os.path.join(images_path, f))]
        response = self.http_post(f'{self.nodeodm_url}/task/new', files=files, data=options)
        response_json = json.loads(response.text)
        if response.status_code != 200:
            self.logger.log_warning(f"Error creating task: {response.text}")
            return None
        task_id = response_json['uuid']
        self.logger.log_info(f'Creating task with UUID: {task_id} .')
        return task_id

    def download_results(self, task_id, output_dir):
        response = self.http_get(f'{self.nodeodm_url}/task/{task_id}/download/all.zip')
        content = response.content
        if response.status_code != 200:
            self.logger.log_warning(f"Error downloading results for task {task_id}: {response.text}")
            return None
        zip_path = os.path.join(output_dir, 'results.zip')
        with open(zip_path, 'wb') as f:
            f.write(content)
        self.logger.log_info(f"Results downloaded to {zip_path}")

    def calculate_orthophoto(self):
        # Workflow
        try:
            # Define task options
            task_options = {
                'end-with': 'odm_orthophoto',
                'feature-quality': 'high',
                'skip-3dmodel': 'true',
                'fast-orthophoto': 'true',
                'pc-quality': 'high'
            }

            # Create a new task
            task_id = self.create_task(self.local_image_dir, task_options)
            if task_id is None:
                self.logger.log_warning("Calculating the orthophoto failed.")
                return
            status_code = 0
            while status_code != 40 and status_code != 30 and status_code != 50:
                status_code = self.get_task_status(task_id)
                if status_code is None:
                    self.logger.log_warning("Error getting task status.")
                    return
                time.sleep(60)

            if status_code == 30 or status_code == 50:
                self.logger.log_warning(switch_case(status_code))
                return
            if status_code == 40:
                self.logger.log_info(switch_case(status_code))
                os.makedirs(self.odm_output_dir, exist_ok=True)
                self.download_results(task_id, self.odm_output_dir)
                self.remove_task(task_id)

        except Exception as e:
            self.logger.log_warning(f"An error occurred: {str(e)}")
