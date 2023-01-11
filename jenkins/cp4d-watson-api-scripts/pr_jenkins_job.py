"""    
__author__ == "Nijesh"

email : knijesh@sg.ibm.com

 Jenkins PR Script Job Runner Client

 The Script is used to test a dev orchestrated pipeline before accepting a pull request

INVOCATION FORMAT:

python pr_jenkins_job.py --apikey APIKEY -w --project_id PROJECT_ID --job_name NAME

Job Name is Optional.

All the tests in Watson Studio especially on CPDSaaS has to be run via jobs.. This is the template to be followed.

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
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = (
            f"grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey={self.api_key}"
        )

        response = requests.post(self.identity_url, headers=headers, data=data)

        return response.json()["access_token"]

    def list_jobs(self):

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

    def retrieve_job_id(self, name):
        job_json = self.list_jobs()
        job_list = [
            job_json["results"][i]
            for i, job in enumerate(job_json["results"])
            if job_json["results"][i]["metadata"]["name"] == name
        ]
        if len(job_list) == 1:
            return job_list[0]["metadata"]["asset_id"]
        else:
            return job_list[-1]["metadata"]["asset_id"]

    def run_pipeline_job(self, job_id):
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

        return response.json()

    def get_status_job(self, job_id):
        access_token = self.create_access_token()
        headers = {
            "accept": "application/json",
            "Authorization": f"Bearer {access_token}",
        }

        params = {
            "project_id": "416c3bc7-c5c2-4ec6-88fd-521714fed6bb",
            "userfs": "false",
        }

        response = requests.get(
            f"https://api.dataplatform.cloud.ibm.com/v2/jobs/{job_id}",
            params=params,
            headers=headers,
        )

        return response

    def get_runs_of_job(self, job_id):
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

    def get_run_ids(self, job_id):
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
    jobrun = JobRunner(apikey, project_id)
    job_id = jobrun.retrieve_job_id(name=job_name)
    print(f" Job ID is -->{job_id}")

    ##Start the Pipeline Run

    jobrun.run_pipeline_job(job_id)

    job_runs = jobrun.get_run_ids(job_id)

    latest_job_run_id = list(job_runs.keys())[0]

    print(f"Latest Job RUN ID is -->{latest_job_run_id}")

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
    # pprint(jobrun.get_runs_by_runid(job_id=job_id, run_id=latest_job_id))

    return True


if __name__ == "__main__":
    driver()
