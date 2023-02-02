"""    
This script is used to run a watson studio pipeline job using the Watson Data API. 
https://dataplatform.cloud.ibm.com/docs/content/wsj/analyze-data/ml-orchestration-overview.html
TODO: use ibm-watson-pipelines python package instead of the API --> more reliable and convenient
https://pypi.org/project/ibm-watson-pipelines/

python start_and_monitor_pipeline_job_run.py.py --apikey APIKEY -w --project_id PROJECT_ID --job_name NAME
"""

import json
import os
import time
from dataclasses import dataclass
from datetime import date
from pprint import pprint

import click
import requests
from tqdm import tqdm

# explanation of the JobRunner class

@dataclass
class JobRunner:
    """
    Class Encapsulating Job methods in CPD using Watson Data API.
    """

    api_key: str
    project_id: str
    URL: str = "https://api.dataplatform.cloud.ibm.com"
    identity_url: str = "https://iam.cloud.ibm.com/identity/token"

    def create_access_token(self):
        """
        creates an access token for the user based on his/her API key

        Returns:
            str: the access token
        """
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = (
            f"grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey={self.api_key}"
        )

        response = requests.post(self.identity_url, headers=headers, data=data)

        return response.json()["access_token"]



    def list_jobs(self) -> dict:
        """
        gets the list of all jobs in the project

        Returns:
            dict: json object containing the list of jobs in the project
        """
        access_token = self.create_access_token()
        headers = {
            "authorization": f"Bearer {access_token}",
            "cache-control": "no-cache",
        }

        params = {
            "project_id": self.project_id,
            "limit": "100",
            "userfs": "false",
        }
        response = requests.get(f"{self.URL}/v2/jobs", params=params, headers=headers)

        return response.json()

    def retrieve_job_id(self, name: str) -> str:
        """
        gets the job id of the job with the given name

        Args:
            name (str): name of the job

        Returns:
            str: id of the job
        """
        job_json = self.list_jobs()
        job_list = [
            job_json["results"][i]
            for i, job in enumerate(job_json["results"])
            if job_json["results"][i]["metadata"]["name"] == name
        ]
        try: 
            if len(job_list) == 1:
                return job_list[0]["metadata"]["asset_id"]
            else:
                return job_list[-1]["metadata"]["asset_id"]
        except IndexError:
            raise Exception("No job with the given name "+name+" found")

    def run_pipeline_job(self, job_id: str) -> dict:
        """
        starts a new run for the job with the given id 
        https://cloud.ibm.com/apidocs/watson-data-api#job-runs-create
        NOTE: It seems like the API has to belong to the person who created the job. This seems to differ from the behavior of the UI :-/

        Args:
            job_id (str): job id

        Returns:
            dict : full json response from the API
        """
        
        access_token = self.create_access_token()
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {access_token}",
        }

        params = {
            "project_id": self.project_id,
            "userfs": "false",
        }

        json_data = {
            "job_run": {
                "name": f"API_Run_{date.today()}",
                "description": "Description",
            },
        }

        response = requests.post(
            f"{self.URL}/v2/jobs/{job_id}/runs",
            params=params,
            headers=headers,
            json=json_data,
        )
        
        # raise an exception if the response is not 200 or 201
        if response.status_code not in [200, 201]:
            raise Exception(f"Error: {response.status_code} {response.text}")
        
        return response.json()



    def get_runs_of_job(self, job_id: str) -> dict:
        """
        gets the list of runs for the job with the given id

        Args:
            job_id (str): job id

        Returns:
            dict: json object containing the list of runs for the job
        """
        access_token = self.create_access_token()
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {access_token}",
        }

        params = {
            "project_id": self.project_id,
            "limit": "100",
            "userfs": "false",
        }

        response = requests.get(
            f"{self.URL}/v2/jobs/{job_id}/runs", params=params, headers=headers
        )
        return response.json()

    def get_run_ids(self, job_id: str):
        """_summary_

        Args:
            job_id (str): _description_

        Returns:
            _type_: _description_
        """
        result = self.get_runs_of_job(job_id=job_id)
        run_ids = {
            each["metadata"]["asset_id"]: each["metadata"]["created_at"]
            for each in result["results"]
        }
        run_ids = dict(sorted(run_ids.items(), key=lambda item: item[1], reverse=True))
        return run_ids

    def get_runs_by_runid(self, job_id, run_id):
        access_token = self.create_access_token()
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {access_token}",
        }

        params = {
            "project_id": self.project_id,
            "userfs": "false",
        }

        response = requests.get(
            f"{self.URL}/v2/jobs/{job_id}/runs/{run_id}", params=params, headers=headers
        )

        return response.json()


# this is needed to run the script from a terminal 
@click.command()
@click.option(
    "--apikey",
    prompt="Enter your API Key",
    required=True,
    help="API Key of the user for running the CPD Job/WS Pipeline",
)
@click.option(
    "--project_id",
    prompt="Enter your Project ID",
    required=True,
    help="Project ID of the project where WS Pipeline should run",
)
@click.option(
    "--job_name",
    help="Name of the Job to be run",
    default="Dev_Pipeline",
    show_default=True,
)

def driver(apikey, project_id, job_name):
    """
    Starts a new run for the given job name and checks if it runs successfully

    Args:
        apikey (str): Key that identifies the user. NOTE: It seems like it has to be the user who created the job
        project_id (str): ID of the watson studio project
        job_name (str): the name of the job

    Raises:
        Exception: if the job run fails

    Returns:
        bool: true if the job runs successfully
    """
    jobrun = JobRunner(apikey, project_id)
    job_id = jobrun.retrieve_job_id(name=job_name)
    print(f" Job ID is -->{job_id}")

    ##Start the Pipeline Run

    jobrun.run_pipeline_job(job_id)

    job_runs = jobrun.get_run_ids(job_id)

    latest_job_run_id = list(job_runs.keys())[0]

    print(f"Latest Job RUN ID is -->{latest_job_run_id}")

    # check the status of the newest run if it is completed or failed
    try:
        while True:
            result = jobrun.get_runs_by_runid(job_id=job_id, run_id=latest_job_run_id)
            state = result["entity"]["job_run"]["state"]
            if state == "Completed":
                break
            elif state == "Failed":
                raise Exception("Job Run Failed")
            print(state)
            time.sleep(120)
    except Exception as e:
        print(e)

    print(
        f"Job {job_id} with latest run {latest_job_run_id} done with status--> {state}"
    )

    return True


if __name__ == "__main__":
    driver()
