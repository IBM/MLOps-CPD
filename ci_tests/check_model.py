import pandas as pd

import credentials

import os
import sys
import pickle
from ibm_watson_studio_pipelines import WSPipelines
from botocore.client import Config
from ibm_botocore.client import Config
import ibm_boto3
import sklearn.metrics as metrics

params = {}

## Get Cloud API Key from Global Pipeline Parameters
CLOUD_API_KEY = os.getenv('cloud_api_key')

# At this point, the filename of the binary is hardcoded.
# With increasing complexity of your MLOps flow, you may want to add the filename as a pipeline parameter.
FILENAME = "model_pipeline.pkl"

## Retrieve cos credentials from pipeline parameters
import json

# Get json from environment and convert to string
project_cos_credentials = json.loads(os.environ['project_cos_credentials'])
mlops_cos_credentials = json.loads(os.getenv('mlops_cos_credentials'))

## PROJECT COS
AUTH_ENDPOINT = project_cos_credentials['AUTH_ENDPOINT']
ENDPOINT_URL = project_cos_credentials['ENDPOINT_URL']
API_KEY_COS = project_cos_credentials['API_KEY']
# BUCKET_PROJECT_COS = project_cos_credentials['BUCKET']

## MLOPS COS
ENDPOINT_URL_MLOPS = mlops_cos_credentials['ENDPOINT_URL']
API_KEY_MLOPS = mlops_cos_credentials['API_KEY']
CRN_MLOPS = mlops_cos_credentials['CRN']
BUCKET_MLOPS = mlops_cos_credentials['BUCKET']

cos = ibm_boto3.resource(service_name='s3',
                         ibm_api_key_id=API_KEY_MLOPS,
                         ibm_service_instance_id=CRN_MLOPS,
                         ibm_auth_endpoint=AUTH_ENDPOINT,
                         config=Config(signature_version='oauth'),
                         endpoint_url=ENDPOINT_URL_MLOPS)


# Reusable methods for COS operations and reading
def read_data_from_mlops_cos(key):
    def __iter__(self): return 0

    MLOPS_DATA_STORE_client = ibm_boto3.client(
        service_name='s3',
        ibm_api_key_id=API_KEY_MLOPS,
        ibm_service_instance_id=CRN_MLOPS,
        ibm_auth_endpoint=AUTH_ENDPOINT,
        config=Config(signature_version='oauth'),
        endpoint_url=ENDPOINT_URL_MLOPS)

    body = MLOPS_DATA_STORE_client.get_object(Bucket=BUCKET_MLOPS, Key=key)['Body']
    # add missing __iter__ method, so pandas accepts body as file-like object
    if not hasattr(body, "__iter__"): body.__iter__ = types.MethodType(__iter__, body)

    gcf_df = pd.read_csv(body)
    return gcf_df


def download_file_cos(local_file_name, key):
    cos = ibm_boto3.client(service_name='s3',
                           ibm_api_key_id=API_KEY_MLOPS,
                           ibm_service_instance_id=CRN_MLOPS,
                           ibm_auth_endpoint=AUTH_ENDPOINT,
                           config=Config(signature_version='oauth'),
                           endpoint_url=ENDPOINT_URL_MLOPS)
    try:
        res = cos.download_file(Bucket=BUCKET_MLOPS, Key=key, Filename=local_file_name)
    except Exception as e:
        print(Exception, e)
    else:
        print('File Downloaded')


def get_file_size_cos(local_file_name, key):
    cos = ibm_boto3.resource(service_name='s3',
                             ibm_api_key_id=API_KEY_MLOPS,
                             ibm_service_instance_id=CRN_MLOPS,
                             ibm_auth_endpoint=AUTH_ENDPOINT,
                             config=Config(signature_version='oauth'),
                             endpoint_url=ENDPOINT_URL_MLOPS)
    try:
        # size = cos.ObjectSummary(local_file_name, key).size ### this doesnt work for some reason
        size = cos.Bucket(BUCKET_MLOPS).Object(key).content_length
        return size
    except Exception as e:
        print(Exception, e)


def load_model(key, filename):
    download_file_cos(key, filename)
    with open(filename, "rb") as f:
        artifact = pickle.load(f)
    return artifact


from lightgbm import LGBMClassifier

model_pipeline = load_model(FILENAME, FILENAME)

# Download test_data from cos
test_data = read_data_from_mlops_cos('test_tfr.csv')

# Drop only 'Risk'
y_test = test_data[test_data.columns[-1]]
X_test = test_data.drop(list(test_data.columns)[-1:], axis=1)

### MEMORY FOOTPRINTS ###
# for checking max memory thresholds
binary_cos_footprint = get_file_size_cos(FILENAME, FILENAME)
memory_footprint = sys.getsizeof(model_pipeline)

### DATA FORMAT ###
# for checking if input column names equal to the ones expected by the model?
n_input_columns = len(X_test.columns)
n_model_columns = model_pipeline.n_features_in_

input_columns = set(X_test.columns)
model_columns = set(model_pipeline.steps[0][1].feature_names_in_)

### METRICS ###
# for checking certain metric thresholds
pred = model_pipeline.predict(X_test)
roc_auc = metrics.roc_auc_score(y_test, pred)
f1 = metrics.f1_score(y_test, pred)
acc = metrics.accuracy_score(y_test, pred)
specificity = metrics.recall_score(y_test, pred, pos_label=0)
sensitivity = metrics.recall_score(y_test, pred, pos_label=1)

params['metrics'] = {'roc_auc': roc_auc,
                     'f1': f1,
                     'acc': acc,
                     'specificity': specificity,
                     'sensitivity': sensitivity}
params['memory_footprint'] = memory_footprint
params['binary_footprint'] = binary_cos_footprint
params['n_columns_input_vs_expected'] = (n_input_columns, n_model_columns)
params['columns_input_vs_expected'] = (input_columns, model_columns)

# pipelines_client = WSPipelines.from_apikey(apikey=CLOUD_API_KEY)
# pipelines_client.store_results(params)
