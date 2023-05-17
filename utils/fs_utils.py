"""__author__ == "Nijesh"
email : knijesh@sg.ibm.com

Factsheets and Model Metadata Utility Client


"""


import contextlib
import os
import time
from collections import defaultdict
from dataclasses import dataclass

import requests
from ibm_aigov_facts_client import AIGovFactsClient
from ibm_watson_machine_learning import APIClient


@dataclass
class FSUtils:
    wml_client: APIClient
    catalog_id: str
    project_id: str
    bss_account_id: str
    space_id: str
    facts_client: AIGovFactsClient
    service_url: str = "https://api.dataplatform.cloud.ibm.com"

    def register_new_model_entry(
        self, model_uid, model_entry_name, model_entry_description
    ):
        self.wml_client.set.default_project(self.project_id)
        meta_props = {
            self.wml_client.factsheets.ConfigurationMetaNames.NAME: model_entry_name,
            self.wml_client.factsheets.ConfigurationMetaNames.DESCRIPTION: model_entry_description,
            self.wml_client.factsheets.ConfigurationMetaNames.MODEL_ENTRY_CATALOG_ID: self.catalog_id,
        }
        model_registration = self.wml_client.factsheets.register_model_entry(
            model_id=model_uid, meta_props=meta_props
        )
        return model_registration

    def register_existing_model_entry(self, model_uid, model_entry_asset_id):
        meta_props = {
            self.wml_client.factsheets.ConfigurationMetaNames.ASSET_ID: model_entry_asset_id,
            self.wml_client.factsheets.ConfigurationMetaNames.MODEL_ENTRY_CATALOG_ID: self.catalog_id,
        }
        model_registration = self.wml_client.factsheets.register_model_entry(
            model_id=model_uid, meta_props=meta_props
        )
        return model_registration

    def get_model_entries(self):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": self.wml_client._get_headers()["Authorization"],
        }
        params = {"bss_account_id": self.bss_account_id}
        r = requests.get(
            f"{self.service_url}/v1/aigov/model_inventory/{self.catalog_id}/model_entries",
            headers=headers,
            params=params,
        )
        return r.json()

    def get_model_entry(self, model_entry_asset_id):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": self.wml_client._get_headers()["Authorization"],
        }
        params = {"catalog_id": self.catalog_id}
        r = requests.get(
            f"{self.service_url}/v1/aigov/model_inventory/model_entries/{model_entry_asset_id}",
            headers=headers,
            params=params,
        )
        return r.json()

    def get_model_entry_asset_id_by_name(self, model_entry_name):
        response = self.get_model_entries()
        return next(
            (
                x["metadata"]["asset_id"]
                for x in response["results"]
                if x["metadata"]["name"] == model_entry_name
            ),
            None,
        )

    def prepare_training_reference(
        self, bucket_name, apikey, crn, endpoint, training_file_name
    ):
        """_summary_

        Args:
            bucket_name (str): Bucket_Name
            apikey (str): APIKEY
            crn (str): CRN  Of COS
            endpoint (str): ENDPOINT
            training_file_name (str): Training Data Filename

        Returns:
            list[dict]: Training Data Reference
        """

        self.wml_client.set.default_project(self.project_id)
        datasource_type = self.wml_client.connections.get_datasource_type_uid_by_name(
            "bluemixcloudobjectstorage"
        )
        conn_meta_props = {
            self.wml_client.connections.ConfigurationMetaNames.NAME: "MLOps COS",
            self.wml_client.connections.ConfigurationMetaNames.DATASOURCE_TYPE: datasource_type,
            self.wml_client.connections.ConfigurationMetaNames.DESCRIPTION: "MLOpsCOS COnnection",
            self.wml_client.connections.ConfigurationMetaNames.PROPERTIES: {
                "bucket": bucket_name,
                "api_key": apikey,
                "resource_instance_id": crn,
                "iam_url": "https://iam.ng.bluemix.net/oidc/token",
                "url": endpoint,
            },
        }

        conn_details = self.wml_client.connections.create(meta_props=conn_meta_props)
        connection_id = self.wml_client.connections.get_uid(conn_details)

        training_data_references = [
            {
                "id": "German Credit Risk",
                "type": "connection_asset",
                "connection": {
                    "id": connection_id,
                    "href": "/v2/connections/"
                    + connection_id
                    + "?space_id="
                    + self.space_id,
                },
                "location": {"bucket": bucket_name, "file_name": training_file_name},
            }
        ]
        return training_data_references

    def save_model(
        self,
        model,
        model_name,
        model_entry_description,
        model_entry_name,
        target,
        X,
        y,
        train_data_ref,
        model_type="scikit-learn_1.0"
    ):
        # sourcery skip: use-named-expression
        self.wml_client.set.default_project(self.project_id)
        for x in self.wml_client.repository.get_model_details()["resources"]:
            if x["metadata"]["name"] == model_name:
                self.wml_client.repository.delete(x["metadata"]["id"])

        run_id = self.facts_client.runs.get_current_run_id()

        self.facts_client.export_facts.export_payload(run_id)

        software_spec_uid = self.wml_client.software_specifications.get_id_by_name(
            "runtime-22.2-py3.10"
        )

        meta_props = {
            self.wml_client.repository.ModelMetaNames.NAME: model_name,
            self.wml_client.repository.ModelMetaNames.TYPE: model_type,
            self.wml_client.repository.ModelMetaNames.SOFTWARE_SPEC_UID: software_spec_uid,
            self.wml_client.repository.ModelMetaNames.LABEL_FIELD: target,
            self.wml_client._models.ConfigurationMetaNames.TRAINING_DATA_REFERENCES: train_data_ref,
            self.wml_client.repository.ModelMetaNames.INPUT_DATA_SCHEMA: [
                {
                    "id": "input_data_schema",
                    "type": "list",
                    "fields": [
                        {"name": index, "type": value}
                        for index, value in X.dtypes.astype(str).items()
                    ],
                },
            ],
        }

        self.facts_client.export_facts.prepare_model_meta(
            wml_client=self.wml_client, meta_props=meta_props
        )

        model_details = self.wml_client.repository.store_model(
            model=model, meta_props=meta_props, training_data=X, training_target=y
        )
        model_uid = self.wml_client.repository.get_model_id(model_details)
        model_entry_asset_id = self.get_model_entry_asset_id_by_name(model_entry_name)
        if model_entry_asset_id:
            self.register_existing_model_entry(model_uid, model_entry_asset_id)
        else:
            self.register_new_model_entry(
                model_uid, model_entry_name, model_entry_description
            )
        return model_uid

    def save_custom_model(
        self,
        model,
        model_name,
        model_entry_description,
        model_entry_name,
        X,
        y,
        model_type="scikit-learn_1.0"
    ):
        # sourcery skip: use-named-expression
        self.wml_client.set.default_project(self.project_id)
        for x in self.wml_client.repository.get_model_details()["resources"]:
            if x["metadata"]["name"] == model_name:
                self.wml_client.repository.delete(x["metadata"]["id"])

        run_id = self.facts_client.runs.get_current_run_id()

        self.facts_client.export_facts.export_payload(run_id)

        software_spec_uid = self.wml_client.software_specifications.get_id_by_name(
            "runtime-22.2-py3.10"
        )

        meta_props = {
            self.wml_client.repository.ModelMetaNames.NAME: model_name,
            self.wml_client.repository.ModelMetaNames.TYPE: model_type,
            self.wml_client.repository.ModelMetaNames.SOFTWARE_SPEC_UID: software_spec_uid,
        }
        
        self.facts_client.export_facts.prepare_model_meta(
            wml_client=self.wml_client, meta_props=meta_props
        )

        model_details = self.wml_client.repository.store_model(
            model=model, meta_props=meta_props#, training_data=X, training_target=y
        )
        model_uid = self.wml_client.repository.get_model_id(model_details)
        model_entry_asset_id = self.get_model_entry_asset_id_by_name(model_entry_name)
        if model_entry_asset_id:
            self.register_existing_model_entry(model_uid, model_entry_asset_id)
        else:
            self.register_new_model_entry(
                model_uid, model_entry_name, model_entry_description
            )
        return model_uid



    def promote_model(self, model_uid, model_name):
        """

        Promote the model to deployment Space by checking duplicate deployments and
        model assets in the space repository

        Args:
            model_uid (str): Model_ID
            model_name (str): Name of the Model

        Returns:
            json: model saved result in json
        """
        self.wml_client.set.default_space(self.space_id)

        to_delete = defaultdict(list)

        model_ids = [
            model["metadata"]["id"]
            for model in self.wml_client.repository.get_model_details()["resources"]
            if model["metadata"]["name"] == model_name
        ]

        for model in self.wml_client.deployments.get_details()["resources"]:
            if (
                model["entity"]["asset"]["id"] in model_ids
                and "WOS-INTERNAL" not in model["metadata"]["name"]
            ):
                to_delete[model["entity"]["asset"]["id"]].append(
                    model["metadata"]["id"]
                )

        # to_delete = {
        #     model["entity"]["asset"]["id"]: model["metadata"]["id"]
        #     for model in self.wml_client.deployments.get_details()["resources"]
        #     if model["entity"]["asset"]["id"] in model_ids
        #     and "WOS-INTERNAL" not in model["metadata"]["name"]
        # }

        print(to_delete)

        ## Delete Deployment IDs and Duplicate Assets

        with contextlib.suppress(Exception):
            for key, value in to_delete.items():
                for each in value:
                    print(f"Deleting {each}")
                    self.wml_client.deployments.delete(each)
                time.sleep(3)
                print(f"Deleting {key}")
                self.wml_client.repository.delete(key)

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": self.wml_client._get_headers()["Authorization"],
        }
        params = {"project_id": self.project_id}
        data = {"mode": 0, "space_id": self.space_id}
        r = requests.post(
            f"{self.service_url}/v2/assets/{model_uid}/promote",
            headers=headers,
            params=params,
            json=data,
        )
        return r.json()

    def deploy_model(self, space_id, deployment_name, model_uid):
        self.wml_client.set.default_space(space_id)
        # with contextlib.suppress(Exception):
        #     for x in self.wml_client.deployments.get_details()["resources"]:
        #         if x["metadata"]["name"] == deployment_name:
        #             self.wml_client.deployments.delete(x["metadata"]["id"])
        meta_props = {
            self.wml_client.deployments.ConfigurationMetaNames.NAME: deployment_name,
            self.wml_client.deployments.ConfigurationMetaNames.ONLINE: {},
        }
        deployment_details = self.wml_client.deployments.create(
            model_uid, meta_props=meta_props
        )
        deployment_uid = self.wml_client.deployments.get_uid(deployment_details)
        return deployment_uid
