#!/bin/bash

set -e
set +x

# This needs to be added to the jenkins job as a "build step". Consult readme.md for details
# This assumes the virtual env called jenkins-env found in /var/jenkins_home is actually created. 
# The command we had to run was: python3 -m venv name_of_env_here

echo "Activating Virtual Env..."
source /var/jenkins_home/jenkins-env/bin/activate


echo "Installing dependencies"
pip install -r jenkins/cp4d-watson-api-scripts/requirements.txt

# TODO: Wrap this in a try catch and deactivate on failure. Right now this deactivates only on success but we want to do it in failure events too.
echo "Executing script"
python3 jenkins/cp4d-watson-api-scripts/start_and_monitor_pipeline_job_run.py --apikey $KEY --project_id $PROJECT --job_name $JOB

deactivate
