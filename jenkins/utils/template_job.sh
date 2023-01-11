#!/bin/bash

set -e
set +x

# This assumes the virtual env called jenkins-env found in /var/jenkins_home is actually created. 
# The command we had to run was: python3 -m venv name_of_env_here

echo "Activating Virtual Env..."
source /var/jenkins_home/jenkins-env/bin/activate

echo "Installing dependencies"
pip install -r requirements.txt

# TODO: Wrap this in a try catch and deactivate on failure. Right now this deactivates only on success but we want to do it in failure events too.
echo "Executing script"
python3 pr_jenkins_job.py --apikey $KEY --project_id $PROJECT --job_name $JOB

deactivate