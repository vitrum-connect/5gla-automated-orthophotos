import asyncio
import json
import os

import requests

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

    def __init__(self, image_dir):
        temp = os.path.dirname(os.path.abspath(__file__))
        self.project_dir = os.path.dirname(temp)
        self.image_dir = image_dir
        self.nodeodm_url = 'http://192.168.2.39:4000'
        self.logger = CustomLogger()
        self.CHUNK_SIZE = 20

    def http_get(self, url):
        """ Makes a HTTP GET request to a given URL.

        :param url: The URL to make the request to
        :return: The response of the request
        """
        response = requests.get(url)
        response.raise_for_status()
        if response.status_code != 200:
            self.logger.log_warning(f"Error fetching data from {url}: {response.text}")
        return response

    def http_post(self, url, data, files=None):
        """ Makes a HTTP POST request to a specified URL.

        :param url: The URL to make the request to
        :param data: The data to send in the request
        :param files: The files to send in the request

        :return: The response of the request
        """
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
            return
        self.logger.log_info(f"Task {task_id} removed.")
        return

    def get_task_status(self, task_id):
        """ Gets the status of a task on NodeODM.

        :param task_id: The task ID to get the status for
        :return: The status code of the task or None if an error occurred
        """
        try:
            response = self.http_get(f'{self.nodeodm_url}/task/{task_id}/info')
            response_json = json.loads(response.text)
            if response.status_code != 200:
                self.logger.log_warning(f"Error getting task status for task {task_id}: {response.text}")
                return None
            status_code = response_json['status']['code']
            return status_code
        except Exception as e:
            self.logger.log_warning(f"An error occurred: {str(e)}")
            return None

    def create_task_new_init(self, options):
        """ Creates a new task on NodeODM.

        :param options: The options for the task
        :return: The task ID of the created task or None if an error occurred
        """
        options_json = json.dumps(options)
        files = {
            'options': (None, options_json, 'application/json')
        }
        response = self.http_post(f'{self.nodeodm_url}/task/new/init', data={}, files=files)
        response_json = json.loads(response.text)
        if response.status_code != 200:
            self.logger.log_warning(f"Error creating task: {response.text}")
            return None
        task_id = response_json['uuid']
        self.logger.log_info(f'Creating task with UUID: {task_id} .')
        return task_id

    def task_new_commit(self, task_id):
        """ Starts a task on NodeODM.

        :param task_id: The task ID to start
        :return: True if the task was started successfully, False if an error occurred
        """
        response = self.http_post(f'{self.nodeodm_url}/task/new/commit/{task_id}', data={})
        if response.status_code != 200:
            self.logger.log_warning(f"Error starting task: {response.text}")
            return False
        self.logger.log_info(f'Task with UUID: {task_id} was started successfully.')
        return True

    def task_new_upload(self, task_id, images_path):
        """ Uploads images to a task on NodeODM. The images are uploaded in chunks of 20 images.
        It is neccessary to upload the images in chunks because otherwise python will open too many files at once.

        :param task_id: The task ID to upload the images to
        :param images_path: The path to the directory containing the images
        :return: True if the images were uploaded successfully, False if an error occurred
        """
        files_to_upload = [f for f in os.listdir(images_path) if os.path.isfile(os.path.join(images_path, f))]

        for i in range(0, len(files_to_upload), self.CHUNK_SIZE):
            chunk_files = files_to_upload[i:i + self.CHUNK_SIZE]
            files = [(f'images', open(os.path.join(images_path, f), 'rb')) for f in chunk_files]

            try:
                response = self.http_post(f'{self.nodeodm_url}/task/new/upload/{task_id}', files=files, data={})

                if response.status_code != 200:
                    self.logger.log_warning(
                        f"Error uploading chunk {i // self.CHUNK_SIZE + 1} for task {task_id}: {response.text}")
                    return False

                self.logger.log_info(
                    f'Uploaded chunk {i // self.CHUNK_SIZE + 1} of {len(files_to_upload) // self.CHUNK_SIZE} to task with UUID: {task_id} .')
            except Exception as e:
                self.logger.log_warning(f"An error occurred: {str(e)}")
                return False
            finally:
                for _, file_obj in files:
                    file_obj.close()

        self.logger.log_info(f'All images uploaded to task with UUID: {task_id} .')
        return True

    def download_results(self, task_id, output_dir):
        """ Downloads the results of a task from NodeODM to a specified directory.

        :param task_id: The task ID for the NodeODM process
        :param output_dir: The directory to download the results to
        :return:
        """
        response = self.http_get(f'{self.nodeodm_url}/task/{task_id}/download/all.zip')
        content = response.content
        if response.status_code != 200:
            self.logger.log_warning(f"Error downloading results for task {task_id}: {response.text}")
            return None
        zip_path = os.path.join(output_dir, 'results.zip')
        with open(zip_path, 'wb') as f:
            f.write(content)
        self.logger.log_info(f"Results downloaded to {zip_path}")

    async def process_task(self, task_id, transaction_image_dir):
        """ Processes a task on NodeODM by uploading images, waiting for the task to finish and downloading the results.

        :param task_id: The task ID for the NodeODM process
        :param transaction_image_dir: The directory containing the images for the transaction
        :return:
        """
        try:
            uploaded_successfully = self.task_new_upload(task_id, transaction_image_dir)
            if not uploaded_successfully:
                self.logger.log_warning(f"Uploading images failed for task {task_id}.")
                return None
            self.task_new_commit(task_id)
            status_code = 0
            while status_code != 40 and status_code != 30 and status_code != 50:
                status_code = self.get_task_status(task_id)
                self.logger.log_info(switch_case(status_code))
                if status_code is None:
                    self.logger.log_warning("Error getting task status.")
                    return None
                await asyncio.sleep(60)
            if status_code == 40:
                self.download_results(task_id, transaction_image_dir)
                self.remove_task(task_id)
        except Exception as e:
            self.logger.log_warning(f"An error occurred: {str(e)}")

    async def calculate_orthophoto(self, transaction_id):
        """
        Calculates an orthophoto for a given transaction ID. This function creates a new task on NodeODM and uploads the images.
        The function is not waiting for the task to finish, but returns the task ID.

        :param transaction_id: The transaction ID of the image set to calculate the orthophoto for
        :return: The task ID of the created task or None if an error occurred
        """
        try:
            os.mkdir('logs')
        except FileExistsError:
            pass
        try:
            task_options = [
                {"name": "fast-orthophoto", "value": "true"},
                {"name": "skip-3dmodel", "value": "true"}
            ]
            transaction_image_dir = os.path.join(self.image_dir, transaction_id)
            if not os.path.exists(transaction_image_dir):
                self.logger.log_warning(f"Image directory {transaction_image_dir} does not exist. Exiting.")
                return None
            task_id = self.create_task_new_init(task_options)
            if task_id is None:
                self.logger.log_warning("Calculating the orthophoto failed.")
                return None
            asyncio.create_task(self.process_task(task_id, transaction_image_dir))
            return task_id

        except Exception as e:
            self.logger.log_warning(f"An error occurred: {str(e)}")
