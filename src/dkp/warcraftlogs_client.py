"""
Client for warcraftlogs.com API

see WCL OAuth doc: https://www.warcraftlogs.com/api/docs
see WCL GraphQL doc: https://www.warcraftlogs.com/v2-api-docs/warcraft/
see request oauth doc: https://requests-oauthlib.readthedocs.io/en/latest/oauth2_workflow.html#legacy-application-flow
"""

# pylint: disable=missing-module-docstring,missing-function-docstring,missing-class-docstring

import json
import logging

import requests
from core import FightStats, RaidStats, list_to_csv
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

from github_client import data_to_json

log = logging.getLogger(__name__)


class WclClient:
    def __init__(self, config, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_uri = config.token_url
        self.api_endpoint = config.api_endpoint

        self.client = OAuth2Session(client=BackendApplicationClient(client_id=self.client_id))
        self._headers = None

    @property
    def headers(self):
        if self._headers is None:
            self._headers = self._get_headers()
        return self._headers

    def _get_headers(self):
        token = self.client.fetch_token(token_url=self.token_uri, client_id=self.client_id, client_secret=self.client_secret)
        return {
            "Authorization": f"Bearer {token.get("access_token")}",
            "Content-Type": "application/json",
        }

    def get_data(self, query: str, **kwargs):
        data = {"query": query, "variables": kwargs}
        response = requests.get(self.api_endpoint, headers=self.headers, json=data, timeout=10)
        response_json = response.json()

        try:
            errors = response_json["errors"]
            raise ValueError(list_to_csv([error["message"] for error in errors]))
        except KeyError:
            pass # no errors

        return response_json

    def get_attending_character_list(self, report_id):
        query = """query($code: String) {
            reportData {
                report(code: $code) {
                    fights(translate: true, killType: Encounters) {
                        size
                        friendlyPlayers
                    }
                    masterData(translate: true) {
                        actors(type: "Player") {
                            id
                            name
                            server
                        }
                    }
                }
            }
        }
        """
        response_json = self.get_data(query, code=report_id)

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

        return char_list


    def get_example_for_zones(self):
        query = """query {
            worldData {
                expansions {
                    id
                    name
                    zones {
                        id
                        name
                        difficulties {
                            id
                            name
                            sizes
                        }
                        encounters {
                            id
                            name
                            journalID
                        }
                        brackets {
                            type
                            min
                            max
                            bucket
                        }
                        partitions {
                            id
                            name
                            compactName
                        }
                    }
                }
            }
        }
        """
        save_example_to_file("wcl-zones", self.get_data(query))


    def get_example_for_rate_limits(self):
        query = """query {
            rateLimitData {
                limitPerHour
                pointsSpentThisHour
                pointsResetIn
            }
        }
        """
        save_example_to_file("wcl-rate-limits", self.get_data(query))


    def get_example_for_report(self, report_id):
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
                        averageItemLevel
                        difficulty
                        friendlyPlayers
                        encounterID
                        startTime
                        endTime
                    }
                    masterData(translate: true) {
                        lang
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
        save_example_to_file("wcl-report", self.get_data(query, code=report_id))


    def get_example_for_player_details(self, report_id):
        query = """query($code: String) {
            reportData {
                report(code: $code) {
                    code
                    title
                    startTime
                    playerDetails(fightIDs: [4])
                    fights(translate: true, killType: Encounters) {
                        averageItemLevel
                    }
                    table(fightIDs: [4])
                }
            }
        }
        """
        save_example_to_file("wcl-player_details", self.get_data(query, code=report_id))


    def get_example_for_debugging_report(self, report_id):
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
                        averageItemLevel
                        difficulty
                        friendlyPlayers
                        encounterID
                        startTime
                        endTime
                    }
                    masterData(translate: true) {
                        lang
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

        report = response_json["data"]["reportData"]["report"]
        fights = [fight for fight in report["fights"] if fight["size"] >= 9] # assuming raid size >= 9

        result = RaidStats(
            id=0,
            report_id=report["code"],
            name=report["title"],
            fights=[FightStats(
                id=fight["id"],
                size=fight["size"],
                boss_name=fight["name"],
                item_level=fight["averageItemLevel"],
                difficulty=str(fight["difficulty"]),
                duration=fight["endTime"] - fight["startTime"]
            ) for fight in fights]
        )

        save_example_to_file("statistics", result)



def save_example_to_file(file_name: str, content):
    with open(f"data/example/{file_name}.json", "w", encoding="utf-8") as file:
        json.dump(data_to_json(content, "id"), file)
