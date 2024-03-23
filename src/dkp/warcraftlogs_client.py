"""
Client for warcraftlogs.com API

see WCL OAuth doc: https://www.warcraftlogs.com/api/docs
see WCL GraphQL doc: https://www.warcraftlogs.com/v2-api-docs/warcraft/
see request oauth doc: https://requests-oauthlib.readthedocs.io/en/latest/oauth2_workflow.html#legacy-application-flow
"""

# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring

import datetime
import logging
import os

import requests
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

log = logging.getLogger(__name__)


class WclClient:
    def __init__(self, wcl_client):
        self.client_id = os.environ.get("WCL_CLIENT_ID", wcl_client.client_id)
        self.client_secret = os.environ.get("WCL_CLIENT_SECRET", wcl_client.client_secret)
        self.token_uri = wcl_client.token_url
        self.api_endpoint = wcl_client.api_endpoint

        self.client = BackendApplicationClient(client_id=self.client_id)
        self.oauth = OAuth2Session(client=self.client)
        self.token_json = self.oauth.fetch_token(
            token_url=self.token_uri,
            client_id=self.client_id,
            client_secret=self.client_secret,
        )

        self.access_token = self.token_json.get("access_token")
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def get_data(self, query: str, **kwargs):
        log.debug("get_data")
        data = {"query": query, "variables": kwargs}
        response = requests.get(self.api_endpoint, headers=self.headers, json=data, timeout=10)
        return response.json()

    def get_raid_details(self, report_id):
        log.debug("get_raid_details")
        # TODO test report having m+ fights, expect m+ fights not considered
        query = """query($code: String) {
            reportData {
                report(code: $code) {
                    code
                    title
                    startTime
                    fights(translate: true, killType: Encounters) {
                        id
                        size
                        name
                        difficulty
                        friendlyPlayers
                        encounterID
                        startTime
                        endTime
                    }
                    masterData {
                        actors(type: "Player") {
                            name
                            server
                            id
                        }
                    }
                }
            }
        }
        """
        response_json = self.get_data(query, code=report_id)

        timestamp_sec = response_json["data"]["reportData"]["report"]["startTime"] / 1000.0
        date = datetime.datetime.fromtimestamp(timestamp_sec, datetime.UTC).strftime("%Y-%m-%d")

        report_url = f"https://www.warcraftlogs.com/reports/{report_id}"

        all_fights = response_json["data"]["reportData"]["report"]["fights"]
        char_id_list = []
        for fight in all_fights:
            char_id_list.extend(fight["friendlyPlayers"])
        char_id_list = list(set(char_id_list))  # distinct

        all_chars = response_json["data"]["reportData"]["report"]["masterData"]["actors"]
        char_list = []
        for char in all_chars:
            if char["id"] in char_id_list:
                char_list.append(f"{char['name']}-{char['server']}")

        return date, report_url, char_list
