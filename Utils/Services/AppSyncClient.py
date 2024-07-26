import boto3
import requests
import json
from requests_aws4auth import AWS4Auth


class AppSyncClient:
    def __init__(self, aws_access_key, aws_secret_key, region, api_url, api_key=None):
        self.api_url = api_url
        self.api_key = api_key

        # Create a Boto3 session
        session = boto3.Session(
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region
        )

        # Fetch credentials from the session
        credentials = session.get_credentials().get_frozen_credentials()
        self.auth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            region,
            'appsync',
            session_token=credentials.token
        )

    def execute_query(self, query):
        headers = {
            'Content-Type': 'application/json',
        }

        if self.api_key:
            headers['x-api-key'] = self.api_key

        response = requests.post(
            self.api_url, json={'query': query}, headers=headers, auth=self.auth)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(
                f"Query failed to run with a {response.status_code}.")

    def test(self, client):
        query = """
        getScheduledJobs
        """

        try:
            response = client.execute_query(query)
            print(json.dumps(response, indent=2))
        except Exception as e:
            print(f"An error occurred: {e}")
