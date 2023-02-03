# MLOps-CPD

This documentation describes IBM's MLOps flow implemented using services in IBM's Cloud Pak for Data stack. It therefore describes IBM's narrative of MLOps. The architecture consists of three stages: development, pre-prod, and prod. The process includes: receiving code updates, training, deploying, and monitoring models. The demo uses the German Credit dataset to predict credit risk. The code is written in Python 3.9 and requires access to IBM Watson Studio, Watson Machine Learning, Watson Knowledge Catalog, and Watson OpenScale.

Note: The current implementation has been built on IBM Cloud (CPSaaS). But most of the current implementation barring few changes in authentication, should work well on Cloud Pak for Data on-prem. Based on the users' requests, we may release an on-prem version.

The architecture of the MLOps flow is shown below:
<img src="https://user-images.githubusercontent.com/77606025/205662631-97bb8875-c799-4fd9-9bb0-71c4b0e0be12.png" width="750">

  * [Overview](#overview)
    + [Important consideration: CPDaaS vs. On-Prem](#important-consideration--cpdaas-vs-on-prem)
    + [Prerequisites on IBM Cloud:](#prerequisites-on-ibm-cloud-)
    + [Branch management](#branch-management)
    + [Dataset and data science problem](#dataset-and-data-science-problem)
    + [Process overview](#process-overview)
- [1. Setup](#1-setup)
  * [1.1. Creating a project in Watson Studio](#11-creating-a-project-in-watson-studio)
  * [1.2. Creating the deployment spaces](#12-creating-the-deployment-spaces)
    + [Python environment customisations](#python-environment-customisations)
    + [Pre-requisite before running a notebook or pipeline:](#pre-requisite-before-running-a-notebook-or-pipeline-)
  * [Now if you want to use your own COS.](#now-if-you-want-to-use-your-own-cos)
  * [Github Access Token in Notebooks](#github-access-token-in-notebooks)
      - [How to create a WS Pipeline in CP4D](#how-to-create-a-ws-pipeline-in-cp4d)
      - [NOTE: you will need to save a Jupyter notebook version for WS Pipeline to work](#note--you-will-need-to-save-a-jupyter-notebook-version-for-ws-pipeline-to-work)
      - [To check the log and debug a pipeline](#to-check-the-log-and-debug-a-pipeline)
- [1. Development](#1-development)
  * [Offline modeling](#offline-modeling)
    + [Notebook 1: Connect and validate data](#notebook-1--connect-and-validate-data)
    + [Notebook 2: Data preparation](#notebook-2--data-preparation)
    + [Notebook 3: Model training and evaluation](#notebook-3--model-training-and-evaluation)
    + [Notebook 4: Model deployment](#notebook-4--model-deployment)
- [2. Pre-prod](#2-pre-prod)
  * [Continuous integration](#continuous-integration)
    + [CI tests](#ci-tests)
  * [Recommended CI tests](#recommended-ci-tests)
  * [Continuous delivery - pipeline](#continuous-delivery---pipeline)
    + [Data Extraction and Data Validation](#data-extraction-and-data-validation)
    + [Data preparation](#data-preparation)
    + [Model Training and Model Evaluation](#model-training-and-model-evaluation)
    + [Model Deployment (pre-prod space)](#model-deployment--pre-prod-space-)
    + [Model Monitoring and Model Validation](#model-monitoring-and-model-validation)
    + [Notebook 5: Model monitoring](#notebook-5--model-monitoring)
- [3. Prod](#3-prod)
    + [Deployment Checks](#deployment-checks)
    + [Model deployment (prod space)](#model-deployment--prod-space-)
    + [Model monitoring](#model-monitoring)
    + [Model retraining](#model-retraining)
  * [AI Factsheets](#ai-factsheets)


## Overview

### Important consideration: CPDaaS vs. On-Prem
When this asset was created from scratch, it was laid out for our CPDaaS solution. However, there are slight but - at least here - significant differences between the two including - but not limited to - the absence of a file system and a less refined Git integration in CPDaaS.
We are currently weighing the pros and cons of two approaches: Highlighting points of this documentation where CPDaaS is limited (including a work-around), or offering a separate repository.

### Prerequisites on IBM Cloud:
In order to use the above asset we need to have access to have an IBM environment with authentication.
IBM Cloud Account with following services:
  1. IBM Watson Studio
  2. IBM Watson Machine Learning
  3. IBM Watson Knowledge Catalog with Factsheets and Model Inventory
  4. IBM Watson OpenScale

Please ascertain you have appropriate access in all the services.
  
  The runs are also governed by the amount of capacity unit hours (CUH) you have access to. 
  If you are running on the free plan please refer to the following links:
  
  1. https://cloud.ibm.com/catalog/services/watson-studio
  2. https://cloud.ibm.com/catalog/services/watson-machine-learning
  3. https://cloud.ibm.com/catalog/services/watson-openscale
  4. https://cloud.ibm.com/catalog/services/watson-knowledge-catalog

For OpenScale, we have ml providers:
  1. MLOps_Preprod : To Subscribe to all the models in dev and pre-prod environments.
  2. MLOps_Prod : To Subscribe to all models in the prod environment.

### Branch management
This repo has two branches, `master` and `pre-prod`. The `master` branch is served as the dev branch, and receives direct commits from the linked `CP4D` prject. When a pull request is created to merge the changes into the pre-prod branch, Jenkins will automatically start the CI tests. 

### Dataset and data science problem
In this example we use the German Credit dataset and aim to predict credit risk. The dataset can be downloaded from [here](https://github.com/IBM/watson-openscale-samples/blob/main/Cloud%20Pak%20for%20Data/WML/assets/data/credit_risk/german_credit_data_biased_training.csv).

### Process overview
In this repo we demonstrate three steps in the MLOps process:

1. Development: orchestrated experiments and generate source code for pipelines
2. Pre-prod: receives code updates from dev stage and contain CI tests to make sure the new code/model integrates well, trains, deploys and monitors the model in the pre-prod deployment space to validate the model. The validated model can be deployed to prod once approved by the model validator.
3. Prod: deploys the model in the prod environment and monitors it, triggers retraining jobs (eg. restart pre-prod pipeline or offline modeling)

# 1. Setup

## 1.1. Creating a project in Watson Studio

You create a project to work with data and other resources to achieve a particular goal, such as building a model or integrating data.

⚠️ We plan on offering this asset as a fully pre-built project space demo within the "Create a project from a sample or file" Option. For now, you will have to construct it manually.

1. Click New project on the home page or on your Projects page.
2. Create an empty project.
3. On the New project screen, add a name. Make it short but descriptive.
4. If appropriate for your use case, mark the project as sensitive. The project has a sensitive tag and project collaborators can't move data assets out of the project. You cannot change this setting after the project is created.
5. Choose an existing object storage service instance or create a new one.
Click Create. You can start adding resources to your project.

Along with the creation of a project, a bucket in your object storage instance will be created. This bucket will look like `[PROJECT_NAME]-donotdelete...`. 

## 1.2. Creating the deployment spaces

For IBM WML, We have three spaces:
  1. MLOps_Dev : Dev Space to deploy your models and test before being pushed to the pre-prod
  2. MLOps_preprod : Pre-prod Space to deploy and test and validate your models. The Validator uses this environment before giving a go ahead to                                push the models in production.
  3. MLOps_Prod : Production Space to deploy your validated models and monitor it.

### Python environment customisations

Some of the notebooks require quite a few dependencies, which should not be manually installed via `pip` in each notebook every time. To avoid doing that, we will create custom environments. They are alternatively called `Software Configurations` across Watson Studio Documentation.

---
<details>
<summary><b>⚠️ Click here if you do not know how to customize environments in Watson Studio</b></summary>

1. Under Tool runtimes on the Environments page on the Manage tab of your project, check that no runtime is active for the environment template that you want to change. If a runtime is active, you must stop it before you can change the template.

2. Under Templates on the Environments page, select the template you want to customize and add your changes. You can't change the language of an existing environment template.

3. You can now create a software customization and specify the libraries to add to the standard packages that are available by default. 

(For more details, check out [Adding a customization](https://www.ibm.com/docs/en/cloud-paks/cp-data/4.6.x?topic=environments-adding-customization) in the Documentation)
</details>

---

- Use Python 3.9 
- Modify the `pip` part of the Python environment customisation script below: 

```
# Modify the following content to add a software customization to an environment.
# To remove an existing customization, delete the entire content and click Apply.
# The customizations must follow the format of a conda environment yml file.

# Add conda channels below defaults, indented by two spaces and a hyphen.
channels:
  - defaults

# To add packages through conda or pip, remove the # on the following line.
dependencies:

# Add conda packages here, indented by two spaces and a hyphen.
# Remove the # on the following line and replace sample package name with your package name:
#  - a_conda_package=1.0

# Add pip packages here, indented by four spaces and a hyphen.
# Remove the # on the following lines and replace sample package name with your package name.
  - pip:
    [ADD CUSTOMISATION PACKAGES HERE]
```

Environments used in this asset:

`Custom_python` environment 
```
  - pip:
    - tensorflow-data-validation
    - ibm_watson_studio_pipelines
```



`pipeline_custom` environment
```
  - pip:
    - ibm_watson_studio_pipelines
    - ibm-aigov-facts-client
```
`openscale` environment
```
  - pip:
    - ibm_cloud_sdk_core
    - ibm_watson_openscale
    - ibm_watson_studio_pipelines
    - ibm-aigov-facts-client
```

### Pre-requisite before running a notebook or pipeline:

Before you run a notebook you need to enter the value of following variables.

**a)** The basic requirement is to get your IBM Cloud API Key (`CLOUD_API_KEY`) for all the pipelines.

---
<details>
<summary><b>❓ Where can I create/generate an API Key?</b></summary>

1. Navigate to https://cloud.ibm.com

2. (On the top right) Select Manage > Access(IAM).

<img src="https://user-images.githubusercontent.com/8414621/204450079-c3c315a2-cd37-427d-9188-9eb4518ed37e.png" width="250">

3. Click on the API keys and create new API Key.

<img src="https://user-images.githubusercontent.com/8414621/204450245-3b759195-78ae-4542-bf8f-10553f417706.png" width="700">

4. Name the API Key and Copy or Download it.

</details>

---

**b)** Secondly you will need the following IBM Cloud Object Storage (COS) related variables, which will allow the notebooks to interact with your COS Instance. 

The variables are:
1. `ENDPOINT_URL_MLOPS`
2. `API_KEY_MLOPS`
3. `CRN_MLOPS`
4. `BUCKET_MLOPS`
5. `AUTH_ENDPOINT`

---
<details>
<summary><b>❓ Where can I find these credentials for Cloud Object Storage?</b></summary>

1. Go to cloud.ibm.com and select the account from the drop down.
2. Go to Resource list by either clicking on the left hand side button or https://cloud.ibm.com/resources.
3. Go to Storage and select the Cloud Object Storage instance that you want to use. 

<img src="https://user-images.githubusercontent.com/8414621/204445270-eb9286c0-41e3-4bb9-92fc-0050e6c81661.png" width="250">
  
4. Select  "Service Credentials"  and Click "New Credential:

<img src="https://user-images.githubusercontent.com/8414621/204449450-b49f0e64-f684-4d67-b873-29de89e87759.png" width="600">


5. Name the credential and hit Add.
  
<img src="https://user-images.githubusercontent.com/8414621/204449680-0b85eea4-419d-49b2-9da7-1cc814861149.png" width="600">
  
6. Go to the Saved credential and click to reveal your credential. You can use these values to fill the variables
  
<img src="https://user-images.githubusercontent.com/8414621/204449849-69d23454-675e-421e-8531-2cbed2235e4a.png" width="600">
  
</details>

---

You should set them at the top level of each notebook.
Here is an example:

```python3
ENDPOINT_URL_MLOPS = "https://s3.jp-tok.cloud-object-storage.appdomain.cloud/" # Adjust to your correct regional endpoints (eu-de etc.)
API_KEY_MLOPS = apikey
CRN_MLOPS = resource_instance_id
BUCKET_MLOPS = "" # Name of the Bucket
AUTH_ENDPOINT = "https://iam.cloud.ibm.com/oidc/token"
```

Now if you want to use your own COS.
------------------------------------
1. Navigate to your COS as explain in Step 3 above.
2. Click on buckets. Create a bucket.
 ![Screenshot 2022-11-29 at 1 59 27 PM](https://user-images.githubusercontent.com/8414621/204450694-560792bc-ea54-437c-82c8-f623373a61f8.png)
3. Click "Customise Bucket".
![Screenshot 2022-11-29 at 2 00 11 PM](https://user-images.githubusercontent.com/8414621/204450827-70b032ce-a9b6-436a-963c-802d737009ca.png)
4. Name the Bucket
![Screenshot 2022-11-29 at 2 01 02 PM](https://user-images.githubusercontent.com/8414621/204451007-39aeb731-6933-41d3-8c42-6dd227eb08c3.png)
5. Click create.
![Screenshot 2022-11-29 at 2 01 12 PM](https://user-images.githubusercontent.com/8414621/204451022-c5f33efe-5282-4066-85b0-288b0d59057b.png)

6. Download the data from : https://github.com/IBM/watson-openscale-samples/blob/main/Cloud%20Pak%20for%20Data/WML/assets/data/credit_risk/german_credit_data_biased_training.csv
and place it in the bucket. 


Now you are ready to start!!!!

## Github Access Token in Notebooks 

As the asset was developed in CPDSaaS, the only efficient way to include the utility scripts in the notebook was to use a git clone route with personal access token. So in most notebooks you will see an access token that belongs to Nijesh Or Sherry. We shall modify this and add a better way in the next iteration as the asset is moved to CPD on-prem ; which has file system unlike CPDSaaS. For now if you get an error to Import MLOps_CPD repository , please refresh it with your git access token here.
In the below notebook you can see the accesstoken embeddded : You may need to change that in case of any import errors. You are encouraged to use your personal access token from github.
For now, it has been duly documented in the notebooks as you see in the image below.

<img width="1000" alt="Screenshot 2022-12-06 at 1 54 04 PM" src="https://user-images.githubusercontent.com/8414621/205830002-73375a89-787e-4c1f-814f-f9accd3e566b.png">



#### How to create a WS Pipeline in CP4D

In your CP4D project, click the blue button `New Asset +`. Then find `Pipelines`

<img width="1000" alt="Screenshot 2022-11-25 at 2 05 04 pm" src="https://user-images.githubusercontent.com/77606025/203892669-27589779-ad9f-458b-a0fc-7d6fca728459.png">

Select Pipelines and give the pipeline a name. 

Once the pipeline is created, you will see the pipeline edit menu and the palette on the left.

<img width="500" alt="Screenshot 2022-11-25 at 2 10 16 pm" src="https://user-images.githubusercontent.com/77606025/203892823-e1500928-acc4-4c9f-8165-8c658ae5b5ce.png">

Expand the `Run` section and drag and drop the `Run notebook` block. 

Double click the block to edit the node.

#### NOTE: you will need to save a Jupyter notebook version for WS Pipeline to work

WS Pipeline requires all the Jupyter notebooks to have a version saved before it can run the notebook, failing to do that will result in the below error: 

![Screenshot 2022-11-28 at 8 15 25 pm](https://user-images.githubusercontent.com/77606025/204240070-71ee196e-b653-4b3b-b242-57da12c070a8.png)

To save a version of the notebook, go to the notebook editor model in your CP4D project, select the top right round icon to open the version menu, and click `Save version`.


![Screenshot 2022-11-28 at 8 21 54 pm](https://user-images.githubusercontent.com/77606025/204240804-4996134c-c7db-4dd8-ad9f-84d876cff91d.png)


#### To check the log and debug a pipeline

When the pipeline is running, double click on the node that is currently running to open Node Inspector, as shown in the below image. The log will contain all the notebook run status, the prints and errors where the notebook fails.


![Screenshot 2022-11-28 at 7 45 43 pm](https://user-images.githubusercontent.com/77606025/204234082-95c90b64-a380-4450-887d-a231527ffed7.png)




# 1. Development

## Offline modeling
Offline modeling includes the usually data exploration and data science experiments. In this step, you can try different data manipulation, feature engineering and machine learning models. 

The output of this stage is code assets, for example Python scripts or Jupyter notebooks that can be used as blocks in the pipelines.

In this example, the output scripts are Python scripts in Jupyter notebooks. They are version controled with Git, as shown in this repository, and serve as components in the pre-prod pipeline. 


You can experiment with an orchestrated dev pipeline, which would include 

- Data connection and validation

- Data preparation

- Model training and evaluation

- Model deployment

- Model validation (optional)

Below is a dev pipeline in Watson Studio Pipeline:

<img width="1786" alt="Screenshot 2022-11-25 at 3 18 33 am" src="https://user-images.githubusercontent.com/77606025/203829583-a510f77f-0efa-432e-bac3-c95e9e1e9626.png">

### Notebook 1: Connect and validate data 
This notebook source code can be found in [connect_and_validate_data.ipynb](connect_and_validate_data.ipynb). 

It does the following:
- Load the training data `german_credit_risk.csv` from cloud object storage (COS)
- Data Validation. It comprises of the folllowing steps:
  - Split the Data
  - Generate Training Stats on both Splits
  - Infer Schema on both Splits
  - Check for data anomalies

### Notebook 2: Data preparation

This notebook source code can be found in [data_preparation.ipynb](data_preparation.ipynb), which does the following:

- Load train and test data from COS and split the X and y columns 
- Encode features 
- Save processed train and test data to COS


### Notebook 3: Model training and evaluation

This notebook source code can be found in [train_models.ipynb](train_models.ipynb), which does the following:
- Load train and test data from COS, split train to train and validation data
- Load the pre-processing pipeline
- Train the model 
- Save train and val loss to COS
- Calculate AUC-ROC 
- Store the model in the project
- Track the model runs and stages with AI Factsheets


### Notebook 4: Model deployment
This notebook source code can be found in [deploy_model.ipynb](deploy_model.ipynb), which does the following:
- Load the trained mode from model registry
- Promote the model to a deployment space and deploy the model 
- Test the endpoint

By changing the input to this notebook, the model can be deployed to dev, pre-prod and prod spaces. 


# 2. Pre-prod 

## Continuous integration 

When the Jupyter notebooks have a change commited and a pull request is made, Jenkins will start the CI tests.

The source code is stored in the [jenkins](jenkins) directory and the documentation can be viewed [here](jenkins/README.md)

### CI tests

- Pipeline component integration test: run the pipeline in dev environment to check if it successfully runs
- Model Convergence test: check the training loss to see if it keeps declining

## Recommended CI tests
- Behaviour Tests 
  - Invariance 
  - Directionality
  - Minimum functionality 
- Adversarial Tests 
  - Check to see if the model can be affected by direct adversarial attacks 
- Regression Tests 
  - Check specific groups within the test set to ensure performance is retained in this group after retraining  

- Miscellaneous Tests
  - Test loading artifacts (model into memory)
  - Test input data scheme 
  - Test with unexpected input types (null / Nan) 
  - Test output scheme is as expected 
  - Test output errors are handled correctly 
 




## Continuous delivery - pipeline

After the CI tests passed, the admin/data science lead will merge the changes and Jenkins will trigger the following `pre-prod` pipeline:

<img width="1792" alt="Screenshot 2022-11-25 at 3 22 00 am" src="https://user-images.githubusercontent.com/77606025/203830128-da1b4369-7e2c-44ea-941c-45ca8e0ebcc5.png">



* ### Data Extraction and Data Validation

It runs the notebook [connect_and_validate_data.ipynb](connect_and_validate_data.ipynb) with:

Environment
```
pipeline_custom
```

Input params
```
cloud_api_key, Select from pipeline parameter
training_file_name, String
```

Output params
```
anomaly_status, Bool
files_copied_in_cos, Bool
```

We define a pipeline parameter `cloud_api_key` to avoid having the API key hardcoded in the pipeline: 

[TO DO: insert picture here]

This block is followed by a `Val check` condition:

<img width="1208" alt="Screenshot 2022-11-28 at 5 19 26 am" src="https://user-images.githubusercontent.com/77606025/204152738-21ea961b-1380-4123-8707-758866c6fa52.png">


* ### Data preparation

It runs the notebook [data_preparation.ipynb](data_preparation.ipynb)

Environment
```
pipeline_custom
```

Input params
```
cloud_api_key, Select from pipeline parameter
```

Output params
```
data_prep_done, Bool
```

This block is followed by a `prep check` condition:

<img width="1232" alt="Screenshot 2022-11-28 at 5 20 54 am" src="https://user-images.githubusercontent.com/77606025/204152765-893a8ef7-b4c3-4b5e-ad00-872a916f1d40.png">


* ### Model Training and Model Evaluation

It runs the notebook [train_models.ipynb](train_models.ipynb)

In WS Pipeline you can assign input to be the output from another node. To do this, select the folder icon next to `environment variables`:

<img width="451" alt="Screenshot 2022-11-28 at 4 45 27 am" src="https://user-images.githubusercontent.com/77606025/204152646-8ea26bee-8165-47f2-803e-7ae13222acbc.png">

Then select the node and the output you need 

<img width="454" alt="Screenshot 2022-11-28 at 4 46 13 am" src="https://user-images.githubusercontent.com/77606025/204152670-f2a798cf-01aa-4ebd-a7a9-ffd51d2d5774.png">

Environment
```
pipeline_custom
```

Input params
```
feature_pickle, String
apikey, Select from pipeline parameter
model_name, String
deployment_name, String
```

Output params
```
training_done, Bool
auc_roc, Float
model_name, String
deployment_name, String
model_id, String
project_id, String
```

This block is followed by a `Train check` condition:


<img width="1229" alt="Screenshot 2022-11-28 at 5 21 33 am" src="https://user-images.githubusercontent.com/77606025/204152795-c58ba6f9-3a09-4217-b903-a6ef7ca0e0ae.png">



* ### Model Deployment (pre-prod space)

It runs the notebook [deploy_model.ipynb](deploy_model.ipynb)

By changing the input parameter `space_id`, we can set the model to deploy to the `pre-prod` deployment space in CP4D.

Environment
```
pipeline_custom
```

Input params
```
model_name, Select model_name from Train the Model node
deployment_name, Select deployment_name from Train the Model node
cloud_api_key, Select from pipeline parameter
model_id, Select model_id from Train the Model node
project_id, Select project_id from Train the Model node
space_id, String
```

Output params
```
deployment_status, Bool
deployment_id, String
model_id, String
space_id, String
```

This block is followed by a `deployed?` condition:

<img width="1229" alt="Screenshot 2022-11-28 at 5 22 25 am" src="https://user-images.githubusercontent.com/77606025/204152825-0ff6d425-ecdc-43ba-9cfc-c4a5fc725c91.png">


* ### Model Monitoring and Model Validation

It runs the notebook [monitor_models.ipynb](monitor_models.ipynb):

### Notebook 5: Model monitoring
This notebook source code can be found in [monitor_models.ipynb](monitor_models.ipynb), which does the following:
- Create subscription for the model deployment in Openscale
- Enable quality, fairness, drift, explainability, and MRM in Openscale
- Evaluate the model in Openscale

The trained model is saved to the model registry. 

After the pipeline and model prediction service is verified to be successful in the pre-prod space, We can mannually deploy the model to the production environment.

This node has:

Environment
```
openscale
```

Input params
```
data_mart_id, String
model_name, Select model_name from Train the Model node
deployment_name, Select deployment_name from Train the Model node
cloud_api_key, Select from pipeline parameter
deployment_id, Select deployment_id from Deploy Model - Preprod node
model_id, Select model_id from Deploy Model - Preprod node
space_id, Select space_id from Deploy Model - Preprod node
service_provider_id, String
training_data_reference_file, String
```

Output params
```
None
```


Once the model is validated, and approved by the model validator, the model can be deployed to the prod environment.

# 3. Prod 

In this example we reuse the [deploy_model.ipynb](deploy_model.ipynb) and [monitor_models.ipynb](monitor_models.ipynb) to create the deployment job.

<img width="948" alt="Screenshot 2022-12-06 at 3 35 18 am" src="https://media.github.ibm.com/user/312522/files/c9c2ef22-444b-4152-b9e9-e449eeb191eb">

* ### Deployment Checks

This step checks if the the model is approved for production in Openscale. 

It runs the notebook [Checks for Model Production.ipynb](Checks for Model Production.ipynb)


* ### Model deployment (prod space)

In this step, the validated model from the pre-prod is deployed in the production deployment space.


It runs the notebook [deploy_model.ipynb](deploy_model.ipynb)

The input parameter `space_id` is the prod deployment space ID.

* ### Model monitoring

It runs the notebook [monitor_models.ipynb](monitor_models.ipynb)

The Openscale API does not allow test data upload for Production subscriptions (like you'd upload for Pre-Production subscriptions). Therefore we save the data into Payload Logging and Feedback tables in Openscale and trigger on-demand runs for Fairness, Quality, Drift monitors and MRM. 


* ### Model retraining

Model retraining is governed by the underlying usecase.Following list is by no means exhaustive. Some of the common retraining methods are:
  1. Event based : When a business defined event occurs which explicitly impacts the objective of the model, a retrainig is triggered.
  2. Schedule based : Some of the models always rely on latest data viz: forecasting models. So such kind of retraining is schedule driven.
  3. Metric based : When a defined metric like model quality, bias or even data drift falls below a threshold , a retraining is triggered.

We have implemented the 3rd type of retraining as we are monitoring the data drift and augmenting the training data with the drifted records.

In OpenScale, the flow of the retraining looks like:
- Openscale model monitoring alerts are triggered, and an email is received: manually trigger the retrain job to update the data and restart the pre-prod pipeline
- Openscale model monitoring alerts are triggered, and an email is received: after some investigation, you decide that you want to try different models or features, therefore restart from the offline modeling stage. 

## AI Factsheets

In this project we also demonstrate how we put the model into the a model registry and track the model with [AI Factsheets](https://dataplatform.cloud.ibm.com/docs/content/wsj/analyze-data/factsheets-model-inventory.html)

You can instantiate a Factsheets (as shown in the [train_models](train_models.ipynb) notebook) with 
```
facts_client = AIGovFactsClient(api_key=apikey, experiment_name="CreditRiskModel", container_type="project", container_id=project_id, set_as_current_experiment=True)
```
and log the models in Factsheets with the `save_log_facts()` function in the [notebook](train_models.ipynb)

After the model has been deployed to pre-prod and prod environments, and evaluated by Openscale, the deployments can be seen in the model entry (in Watson Knowledge Catalog):

<img width="1467" alt="Screenshot 2022-11-28 at 4 17 15 am" src="https://user-images.githubusercontent.com/77606025/204152565-b9942c0e-48e7-4412-ac3e-92a4787f1e23.png">
