"""__author__ == "Nijesh"
email : knijesh@sg.ibm.com

WKC and Model Inventory Utility Client


"""

import json
import os
from dataclasses import dataclass
from operator import itemgetter

import numpy as np
import pandas as pd
import requests
from ibm_watson_machine_learning import APIClient
from requests.structures import CaseInsensitiveDict


@dataclass
class CatalogUtils:
    """
    Encapsulated Catalog Utils Class to enable the use of WKC via Watson Data API.

    """

    service_url: str
    auth_url: str
    api_key: str
    project_id: str

    def get_wml_client(self):

        wml_credentials = {
            "url": "https://us-south.ml.cloud.ibm.com",
            "apikey": self.api_key,
        }
        wml_client = APIClient(wml_credentials)
        return wml_client

    def create_access_token(self):
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = (
            f"grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey={self.api_key}"
        )

        response = requests.post(self.auth_url, headers=headers, data=data)

        return response.json()["access_token"]

    def list_catalogs(self):
        access_token = self.create_access_token()
        headers = CaseInsensitiveDict()
        headers["Accept"] = "application/json"
        headers["Authorization"] = f"Bearer {access_token}"
        list_catalogs = requests.get(self.service_url + "/v2/catalogs", headers=headers)
        return list_catalogs.json()

    def get_catalog_id_map(self):
        result = self.list_catalogs()
        asset_map = {}
        for keys, values in result.items():
            if type(values) == list:
                for each in values:
                    asset_map[each["entity"]["name"]] = each["metadata"]["guid"]
        return asset_map

    def get_latest_asset_id(self, name):

        wml_client = self.get_wml_client()
        wml_client.set.default_project(self.project_id)
        result = wml_client.repository.get_model_details()
        result_meta = [
            each["metadata"]
            for each in result["resources"]
            if each["metadata"]["name"] == name
        ]

        my_asset_list = sorted(result_meta, key=itemgetter("created_at"), reverse=True)
        return my_asset_list[0]["id"]

    def get_revisions_asset(self, catalog_id, asset_id):
        access_token = self.create_access_token()
        headers = CaseInsensitiveDict()
        headers["Accept"] = "application/json"
        headers["Authorization"] = f"Bearer {access_token}"
        search_asset = requests.get(
            self.service_url
            + f"/v2/assets/{asset_id}/revisions?catalog_id={catalog_id}",
            headers=headers,
        )
        return search_asset.json()

    def publish_asset(self, catalog_id, asset_id, name, desc, tags):
        """Publish Assets to Catalog

        Args:
            catalog_id (str): catalog id
            asset_id (str): Id of the asset to be published
            name (str): name of the asset
            desc (str): description
            tags (str): asset tag
        """
        access_token = self.create_access_token()
        url = f"{self.service_url}/v2/assets/{asset_id}/publish?project_id={self.project_id}"

        payload = json.dumps(
            {
                "catalog_id": catalog_id,
                "mode": 0,
                "metadata": {
                    "name": name,
                    "description": desc,
                    "tags": tags,
                },
            }
        )
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        print(response.text)

    def get_model_from_registry(self, name):
        """Get latest model from registry

        Args:
            name (str): name of the Model

        Returns:
            str: model id
        """
        access_token = self.create_access_token()

        url = "https://api.dataplatform.cloud.ibm.com/v1/aigov/model_inventory/model_entries?bss_account_id=27ff418fedd6aedffb8dc6ae4164a1d2"

        payload = {}
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        response = requests.request("GET", url, headers=headers, data=payload)

        result = response.json()

        for each in result["results"]:
            for item in each["entity"]["modelfacts_global"]["physical_models"]:
                if (
                    item["name"] == name
                    and item["container_id"] == self.project_id
                    and item["is_deleted"] == False
                ):
                    return item["id"]
