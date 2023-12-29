"""
Client for warcraftlogs.com API

see WCL OAuth doc: https://www.warcraftlogs.com/api/docs
see WCL GraphQL doc: https://www.warcraftlogs.com/v2-api-docs/warcraft/
see request oauth doc: https://requests-oauthlib.readthedocs.io/en/latest/oauth2_workflow.html#legacy-application-flow
"""

import os
import requests
import datetime
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

# TODO extract to config
client_id = '9af6b15b-44cb-4872-a9f9-7d0e56aad999'
client_secret = os.environ.get("WCL_CLIENT_SECRET")
token_uri = 'https://www.warcraftlogs.com/oauth/token'
api_endpoint = 'https://www.warcraftlogs.com/api/v2/client'

client = BackendApplicationClient(client_id=client_id)
oauth = OAuth2Session(client=client)
token_json = oauth.fetch_token(token_url=token_uri, client_id=client_id, client_secret=client_secret)

access_token = token_json.get('access_token')
headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}


def get_data(query: str, **kwargs):
    data = {"query": query, "variables": kwargs}
    response = requests.get(api_endpoint, headers=headers, json=data)
    return response.json()


def get_raid(report_id):
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
                zone {
                    id
                    name
                    expansion {
                        id
                        name
                        zones {
                            id
                            name
                        }
                    }
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
    response_json = get_data(query, code=report_id)
    # print(response_json)

    timestamp_sec = response_json['data']['reportData']['report']['startTime'] / 1000.0
    date = datetime.datetime.fromtimestamp(timestamp_sec, datetime.UTC).strftime("%Y-%m-%d")

    report_link = f"https://www.warcraftlogs.com/reports/{report_id}"

    all_fights = response_json['data']['reportData']['report']['fights']
    char_id_list = []
    for fight in all_fights:
        char_id_list.extend(fight['friendlyPlayers'])
    char_id_list = list(set(char_id_list))

    all_chars = response_json['data']['reportData']['report']['masterData']['actors']
    char_list = []
    for char in all_chars:
        if char['id'] in char_id_list:
            char_list.append(f"{char['name']}-{char['server']}")

    return date, report_link, char_list

