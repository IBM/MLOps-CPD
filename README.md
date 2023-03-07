# MLOps-CPD

This documentation describes IBM's MLOps flow implemented using services in IBM's Cloud Pak for Data stack. It therefore describes IBM's narrative of MLOps. The architecture consists of three stages: development, pre-prod, and prod. The process includes: receiving code updates, training, deploying, and monitoring models. The demo uses the German Credit dataset to predict credit risk. The code is written in Python 3.9 and requires access to IBM Watson Studio, Watson Machine Learning, Watson Knowledge Catalog, and Watson OpenScale.

Note: The current implementation has been built on IBM Cloud (CPSaaS). But most of the current implementation barring few changes in authentication, should work well on Cloud Pak for Data on-prem. Based on the users' requests, we may release an on-prem version.

<p align="center">
  <img src="https://user-images.githubusercontent.com/77606025/205662631-97bb8875-c799-4fd9-9bb0-71c4b0e0be12.png" width="750">
</p>

<p align="center">
  <em>Fig. 1.: Architecture of the MLOps flow</em>
</p>

  * [Overview](#overview)
    + [Important consideration: CPDaaS vs. On-Prem](#important-consideration--cpdaas-vs-on-prem)
    + [Prerequisites on IBM Cloud](#prerequisites-on-ibm-cloud)
    + [Branch management](#branch-management)
    + [Dataset and data science problem](#dataset-and-data-science-problem)
    + [Process overview](#process-overview)
- [1. Setup](#1-setup)
  * [1.1. Creating a project in Watson Studio](#11-creating-a-project-in-watson-studio)
  * [1.2. Creating the deployment spaces](#12-creating-the-deployment-spaces)
  * [1.3. Preparing the Notebooks](#13-preparing-the-notebooks)
    + [Python environment customisations](#python-environment-customisations)
    + [Retrieving required credentials (IBM Cloud API key and COS credentials)](#retrieving-required-credentials--ibm-cloud-api-key-and-cos-credentials-)
    + [Adding the Notebooks (CPDaaS)](#adding-the-notebooks--cpdaas-)
    + [Adding the Notebooks (On-Prem)](#adding-the-notebooks--on-prem-)
      - [How to create a WS Pipeline](#how-to-create-a-ws-pipeline)
      - [How to create a WS Notebook Job](#how-to-create-a-ws-notebook-job)
      - [To check the log and debug a pipeline](#to-check-the-log-and-debug-a-pipeline)
- [2. Pipeline Setup](#2-pipeline-setup)
  * [2.1. Development](#21-development)
    + [Offline modeling](#offline-modeling)
    + [Notebook 1: Connect and validate data](#notebook-1--connect-and-validate-data)
    + [Notebook 2: Data preparation](#notebook-2--data-preparation)
    + [Notebook 3: Model training and evaluation](#notebook-3--model-training-and-evaluation)
    + [Notebook 4: Model deployment](#notebook-4--model-deployment)
  * [2.2. Pre-prod](#22-pre-prod)
    + [Continuous integration](#continuous-integration)
    + [CI tests](#ci-tests)
    + [Recommended CI tests](#recommended-ci-tests)
    + [Continuous delivery - pipeline](#continuous-delivery---pipeline)
    + [Data Extraction and Data Validation](#data-extraction-and-data-validation)
    + [Data preparation](#data-preparation)
    + [Model Training and Model Evaluation](#model-training-and-model-evaluation)
    + [Model Deployment (pre-prod space)](#model-deployment--pre-prod-space-)
    + [Model Monitoring and Model Validation](#model-monitoring-and-model-validation)
    + [Notebook 5: Model monitoring](#notebook-5--model-monitoring)
  * [2.3. Prod](#23-prod)
    + [Deployment Checks](#deployment-checks)
    + [Model deployment (prod space)](#model-deployment--prod-space-)
    + [Model monitoring](#model-monitoring)
    + [Model retraining](#model-retraining)
  * [2.4. AI Factsheets](#24-ai-factsheets)


## Overview

### Important consideration: CPDaaS vs. On-Prem
When this asset was created from scratch, it was laid out for our CPDaaS solution. However, there are slight but - at least here - significant differences between the two including - but not limited to - the absence of a file system and a less refined Git integration in CPDaaS.
We are currently weighing the pros and cons of two approaches: Highlighting points of this documentation where CPDaaS is limited (including a work-around), or offering a separate repository.

### Prerequisites on IBM Cloud
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

### Branch management
This repo has two branches, `master` and `pre-prod`. The `master` branch is served as the dev branch, and receives direct commits from the linked `CP4D` project. When a pull request is created to merge the changes into the pre-prod branch, Jenkins will automatically start the CI tests. 

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
You can use this bucket through out this project, however we recommend creating a separate bucket in which we will store the dataset, train/test split et cetera.

---
<details>
<summary><b>🪣 See how you can setup your own Bucket in COS</b></summary>

1. Navigate to your COS as explain in Step 3 above.

2. Click on buckets. Create a bucket.

<img width="1000" src="https://user-images.githubusercontent.com/8414621/204450694-560792bc-ea54-437c-82c8-f623373a61f8.png">


3. Click "Customise Bucket".

<img width="1000" src="https://user-images.githubusercontent.com/8414621/204450827-70b032ce-a9b6-436a-963c-802d737009ca.png">

4. Name the Bucket

<img width="1000" src="https://user-images.githubusercontent.com/8414621/204451007-39aeb731-6933-41d3-8c42-6dd227eb08c3.png">

5. Click create.
<img width="1000" s
rc="https://user-images.githubusercontent.com/8414621/204451022-c5f33efe-5282-4066-85b0-288b0d59057b.png">

</details>


---

Now download the dataset ([german_credit_data_biased_training.csv](https://github.com/IBM/watson-openscale-samples/blob/main/Cloud%20Pak%20for%20Data/WML/assets/data/credit_risk/german_credit_data_biased_training.csv)) and place it in the bucket you chose to use for the rest of this tutorial.


## 1.2. Creating the deployment spaces

For IBM WML, We have three spaces:
  1. MLOps_Dev : Dev Space to deploy your models and test before being pushed to the pre-prod
  2. MLOps_preprod : Pre-prod Space to deploy and test and validate your models. The Validator uses this environment before giving a go ahead to                                push the models in production.
  3. MLOps_Prod : Production Space to deploy your validated models and monitor it.

## 1.3. Preparing the Notebooks

In this section, we will first setup the custom Python environments, collect necessary credentials, upload the notebooks, and modify them. The pre-defined environments (henceforth called `software configuration`) do not contain all the Python packages we require. Therefore we will create custom software configurations prior to adding the notebooks.

### Python environment customisations

Some of the notebooks require quite a few dependencies, which should not be manually installed via `pip` in each notebook every time. To avoid doing that, we will create software configurations.

---
<details>
<summary><b>⚠️ Click here if you do not know how to customize environments in Watson Studio</b></summary>

1. Navigate to your Project overview, select the "Manage" tab and select "Environments" in the left-hand menu.
Here, check that no runtime is active for the environment template that you want to change. If a runtime is active, you must stop it before you can change the template.

<img width="1000" alt="software_config-create-button" src="https://user-images.githubusercontent.com/15169745/220061624-7ef06389-8dd2-4d06-8a16-5e2e6d440eb5.png">

2. Under Templates click `New template +` and give it a name (for the pipeline preferably one of those described below), specify a hardware configuration (we recommend `2vCPU and 8GB RAM` for this project, but you can scale up or down depending on your task). When you are done click `Create`.

<img width="1000" alt="software_config-create-window" src="https://user-images.githubusercontent.com/15169745/220061273-598b8754-5bff-4049-b654-e3f7d371cc4a.png">

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

### Retrieving required credentials (IBM Cloud API key and COS credentials)

Before you run a notebook you need to obtain the following credentials and add the COS credentials to the beginning of each notebook. The Cloud API key must not be added to the notebooks since it is passed through the pipeline later.

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

**Universal**
- `AUTH_ENDPOINT` = "https://iam.cloud.ibm.com/oidc/token"

**Project Bucket (auto-generated e.g. `"mlops-donotdelete-pr-qxxcecxi1d"`)** 
- `ENDPOINT_URL` = "https://s3.private.us.cloud-object-storage.appdomain.cloud"
- `API_KEY_COS` = "xx"
- `BUCKET_PROJECT_COS` = "mlops-donotdelete-pr-qxxcecxi1dtw94"


**MLOps Bucket (e.g. `"mlops-asset"`)** 
- `ENDPOINT_URL_MLOPS` = "https://s3.jp-tok.cloud-object-storage.appdomain.cloud"
- `API_KEY_MLOPS` = "xx"
- `CRN_MLOPS` = "xx"
- `BUCKET_MLOPS`  = "mlops-asset"

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

You will need to define those variables at the top level of each notebook.
Here is an example:

```python3
## PROJECT COS 
AUTH_ENDPOINT = "https://iam.cloud.ibm.com/oidc/token"
ENDPOINT_URL = "https://s3.private.us.cloud-object-storage.appdomain.cloud"
API_KEY_COS = "xyz"
BUCKET_PROJECT_COS = "mlops-donotdelete-pr-qxxcecxi1dtw94"


##MLOPS COS
ENDPOINT_URL_MLOPS = "https://s3.jp-tok.cloud-object-storage.appdomain.cloud"
API_KEY_MLOPS = "xyz"
CRN_MLOPS = "xyz"
BUCKET_MLOPS  = "mlops-asset"
```

**However**, to make things easier, you may set them as Global Pipeline Parameters later on.
This will allow you to e.g. switch the COS Bucket you are using without having to edit mulitple notebooks. Instead, you will only have to edit the parameter. Taking advantage of this feature will prove itself useful when using multiple pipelines later on.

The parameter strings should look like the example below in order for the notebooks to extract the correct values. Prepare one for your manually created Bucket and one for the Bucket attached to the project space.
```json
{"API_KEY": "abc", "CRN": null, "AUTH_ENDPOINT": "https://iam.cloud.ibm.com/oidc/token", "ENDPOINT_URL": "https://s3.private.us.cloud-object-storage.appdomain.cloud", "BUCKET": "mlopsshowcaseautoai-donotdelete-pr-diasjjegeind"}
```

Now you are ready to start!

### Adding the Notebooks (CPDaaS)

The Git integration within CPDaaS is not as advanced as that found in our On-Prem solution. As long as that is the case, the notebooks found in the repository must be manually added to the project space. 

<details>
<summary><b>💻 Manually adding a notebook to the project space</b></summary>

Download the repository to your local machine and navigate to your project space. On the asset tab, click `New Asset +`.

<img width="1000" alt="mlops-new_notebook" src="https://user-images.githubusercontent.com/15169745/219624292-1fa33065-767e-40ab-9ea5-787d1d078014.png">

In the tool selection, select `Jupyter notebook editor`. Upload the desired notebook. A name will automatically be assigned based on the filename. Make sure to select our previously added Software Configuration `Custom_python` as the environment to be used for the notebook.
<img width="1000" alt="mlops-new_notebook_env" src="https://user-images.githubusercontent.com/15169745/219624258-61830dc2-bb8d-4204-a8ad-9b905df970a3.png">

**Repeat this procedure for all notebooks.**

</details>
<br>

**Note**: As previously mentioned, CPDaaS does not come with a filesystem. The only efficient way to include utility scripts (see [utility scripts](utils)) to e.g. handle catalog operations is to clone the repository manually from the notebook. This has been documented in each notebook. The corresponding cells are commented out at the top level of each notebook and must only be uncommented when operating on CPDaaS.

<img width="1048" alt="load_utils" src="https://user-images.githubusercontent.com/15169745/221542329-3e8b59ad-518e-48ce-ba3b-e4692de10817.png">


### Adding the Notebooks (On-Prem)

tbd


# 2. Pipeline Setup

For this section you need to know how to create a WS Pipeline and how to correctly setup `Notebook Jobs`, which you will need to add Notebooks to a Pipeline. Check out the following toggleable sections to learn how to do that.

---
<details>
<summary><b>⚠️ How to create a WS Pipeline</b></summary>

In your CP4D project, click the blue button `New Asset +`. Then find `Pipelines`

<img width="1000" alt="Screenshot 2022-11-25 at 2 05 04 pm" src="https://user-images.githubusercontent.com/77606025/203892669-27589779-ad9f-458b-a0fc-7d6fca728459.png">

Select Pipelines and give the pipeline a name. 

Once the pipeline is created, you will see the pipeline edit menu and the palette on the left.

<img width="500" alt="Screenshot 2022-11-25 at 2 10 16 pm" src="https://user-images.githubusercontent.com/77606025/203892823-e1500928-acc4-4c9f-8165-8c658ae5b5ce.png">

Expand the `Run` section and drag and drop the `Run notebook` block. 

Double click the block to edit the node.

</details>

---

<details>
<summary><b>⚠️ How to create a WS Notebook Job</b></summary>

In an earlier version of Watson Studio Pipelines, you were able to drag a `Run notebook` block into the canvas to use as pipeline node. This functionality has been replaced with the `Run notebook job` block.

Prior to selecting a Notebook within the Settings of the `Run notebook job` block, you have to create a notebook job from the Project Space View under the Assets tab.

![notebook-job_create](https://user-images.githubusercontent.com/15169745/218707846-70dfe420-dbc8-4022-afd7-dfe2defaf61b.png)

For the MLOps workflow to work as intended, it is important that you select `Latest` as the notebook Version for your notebook job. Otherwise, the notebook job block in your pipeline will be set to a specific previous version of the notebook, therefore changes in your code would not affect your pipeline.

![notebook-job_versioning](https://user-images.githubusercontent.com/15169745/218708971-24130964-632a-4e37-b988-6429f6a83be3.png)

However, even when having selected `Latest` as the notebook version to use for your notebook job, you will have to select `File` > `Save Version` after performing code changes in your notebook. Only then will the notebook register the changes.

#### To check the log and debug a pipeline

When the pipeline is running, double click on the node that is currently running to open Node Inspector, as shown in the below image. The log will contain all the notebook run status, the prints and errors where the notebook fails.

![Screenshot 2022-11-28 at 7 45 43 pm](https://user-images.githubusercontent.com/77606025/204234082-95c90b64-a380-4450-887d-a231527ffed7.png)

</details>

---

## 2.1. Development

### Offline modeling
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


## 2.2. Pre-prod 

### Continuous integration 

When the Jupyter notebooks have a change committed and a pull request is made, Jenkins will start the CI tests.

The source code is stored in the [jenkins](jenkins) directory and the documentation can be viewed [here](jenkins/README.md)

### CI Test Notebooks

As with any other MLOps pipeline, you should rigorously check whether or not your current model meets all the requirements you defined. In order to test this, we added a folder containing a small repertoire of CI tests which you can find [here](ci_tests/).

It is the overarching idea that a Data Scientist works primarily with the Notebooks themselves and manually invokes the development pipeline in order to initially test their work. The updated Notebooks should only be committed and pushed to the repository if the development pipeline completes successfully. 

Therefore we suggest that you use the CI test repertoire to the extend that you can. Add tests that you would like to have to the end of your development pipeline in a plug&play manner. 
You may of course want to edit those CI test notebooks to set certain thresholds or even write your own tests.

Examples:

- Pipeline component integration test: run the pipeline in dev environment to check if it successfully runs.
- [deserialize_artifact.ipynb](ci_tests/deserialize_artifact.ipynb) will download the model stored in your COS Bucket. It will be deserialized and loaded into memory which is tested by scoring a few rows of your test data. This test is thus ensuring successful serialization. You may extend this test by checking the size of the model in memory or the size of the serialized model in storage and set a threshold, in order for the pipeline to fail when your model exceeds a certain size.
- [model_convergence](ci_tests/model_convergence.ipynb) will download the pickled training and validation loss data from your COS Bucket. It ensures that the training loss is continuously decreasing. You may extend this test by analysing training and validation loss to e.g. avoid serious underfitting or overfitting of the model.

### Further recommended CI tests
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
 

### Continuous delivery - pipeline

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

## 2.3. Prod 

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

## 2.4. AI Factsheets

In this project we also demonstrate how we put the model into the a model registry and track the model with [AI Factsheets](https://dataplatform.cloud.ibm.com/docs/content/wsj/analyze-data/factsheets-model-inventory.html)

You can instantiate a Factsheets (as shown in the [train_models](train_models.ipynb) notebook) with 
```
facts_client = AIGovFactsClient(api_key=apikey, experiment_name="CreditRiskModel", container_type="project", container_id=project_id, set_as_current_experiment=True)
```
and log the models in Factsheets with the `save_log_facts()` function in the [notebook](train_models.ipynb)

After the model has been deployed to pre-prod and prod environments, and evaluated by Openscale, the deployments can be seen in the model entry (in Watson Knowledge Catalog):

<img width="1467" alt="Screenshot 2022-11-28 at 4 17 15 am" src="https://user-images.githubusercontent.com/77606025/204152565-b9942c0e-48e7-4412-ac3e-92a4787f1e23.png">

.
