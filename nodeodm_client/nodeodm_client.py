import os
import requests
import time
import json
import zipfile


class NodeodmClient:
    """ A class to interact with the NodeODM API.

    """

    def __init__(self):
        self.project_dir = os.path.dirname(os.path.abspath(__file__))
        self.local_image_dir = os.path.join(self.project_dir, 'images')
        self.odm_output_dir = os.path.join(self.project_dir, 'odm_output')
        self.nodeodm_url = 'http://192.168.2.39:4000'

    # Function to create a new task in NodeODM
    def create_task(self, images_path, options):
        files = [(f'images', open(os.path.join(images_path, f), 'rb')) for f in os.listdir(images_path) if
                 os.path.isfile(os.path.join(images_path, f))]
        response = requests.post(f'{self.nodeodm_url}/task/new', files=files, data=options)
        response.raise_for_status()
        response_json = json.loads(response.text)
        task_id = response_json['uuid']
        return task_id

    def remove_task(self, task_id):
        # sends a post request to remove the task. The Body contains the task id
        response = requests.post(f'{self.nodeodm_url}/task/remove', data={'uuid': task_id})
        response.raise_for_status()
        print(response.text)
        print(f"Task {task_id} removed.")

    # Function to check task status
    def get_task_status(self, task_id):
        response = requests.get(f'{self.nodeodm_url}/task/{task_id}/info')
        response.raise_for_status()
        response_json = json.loads(response.text)
        status_code = response_json['status']['code']
        return status_code

    # Function to download results
    def download_results(self, task_id, output_dir):
        response = requests.get(f'{self.nodeodm_url}/task/{task_id}/download/all.zip')
        response.raise_for_status()
        zip_path = os.path.join(output_dir, 'results.zip')
        with open(zip_path, 'wb') as f:
            f.write(response.content)
        print(f"Results downloaded to {zip_path}")
        # extract the zip file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(output_dir)
        print(f"Results extracted to {output_dir}")
        # remove the zip file
        os.remove(zip_path)

    def switch_case(self,status_code):
        switcher = {
            10: "Task queued.",
            20: "Task running.",
            30: "Task failed.",
            40: "Task completed.",
            50: "Task canceled."
        }
        return switcher.get(status_code, "Invalid status code")

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
            print(f"Task created with ID: {task_id}")
            status_code = 0
            while status_code != 40 and status_code != 30 and status_code != 50:
                status_code = self.get_task_status(task_id)
                # switch case for status code
                status = self.switch_case(status_code)
                print(status)
                time.sleep(5)  # Wait for 30 seconds before polling again

            # Download the results
            # Ensure output directory exists
            os.makedirs(self.odm_output_dir, exist_ok=True)
            self.download_results(task_id, self.odm_output_dir)
            self.remove_task(task_id)

        except requests.HTTPError as e:
            print(f"HTTP error occurred: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")
