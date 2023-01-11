"""    
__author__ == "Nijesh"

email : knijesh@sg.ibm.com

Jenkins Push Script to run the automated pipeline and push the trained model to registry, deploy and monitor the models.

The Script will be run whenever there is a code changes and a push in the pre-prod branch.

INVOCATION FORMAT:

python push_jenkins_job.py --apikey APIKEY -w --project_id PROJECT_ID --job_name NAME

Job Name is Optional.

"""


import time

import click
from pr_jenkins_job import JobRunner


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
    help="Name of the Preprod Job to be run",
    default="Preprod_Job",
    show_default=True,
)
def push_driver(apikey, project_id, job_name):
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
    push_driver()
