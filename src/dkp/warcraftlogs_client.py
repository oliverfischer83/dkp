"""
Client for warcraftlogs.com API
"""
import requests
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

client_id = '9af6b15b-44cb-4872-a9f9-7d0e56aad999'
client_secret = 'oOd6xJib1UsJdocmVxtBcAaavcbWIuuWmuc1XQ0O'
redirect_uri = 'https://www.test.com'

authorize_uri = 'https://www.warcraftlogs.com/oauth/authorize'
token_uri = 'https://www.warcraftlogs.com/oauth/token'

client = BackendApplicationClient(client_id=client_id)
oauth = OAuth2Session(client=client)
token_json = oauth.fetch_token(token_url=token_uri, client_id=client_id, client_secret=client_secret)

access_token = token_json.get('access_token')
api_endpoint = 'https://www.warcraftlogs.com/api/v2/client'
headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
}


def get_data(query: str, **kwargs):
    data = {
        "query": query,
        "variables": kwargs
    }

    try:
        response = requests.get(api_endpoint, headers=headers, json=data)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            print('Request successful!')
            print(response.json())  # Display the response content
        else:
            print(f'Request failed with status code: {response.status_code}')
            print(response.text)  # Display the response content in case of failure

    except requests.exceptions.RequestException as e:
        print(f'Error during the request: {e}')


query_report = """query($code: String) {
    reportData {
        report(code: $code) {
            code
            title
            owner {
                id
                name
            }
            fights {
                startTime
                endTime
                encounterID
                name
                bossPercentage
                fightPercentage
                kill
                difficulty
                size
            }
        }
    }
}

"""
query_master_data = """query($code: String) {
    reportData {
        report(code: $code) {
            code
            title
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
                partitions {
                    id
                    name
                    compactName
                }
            }
            masterData {
                actors(type: "Player") {
                    name
                    server
                }
            }
        }
    }
}
"""

get_data(query_master_data, code='JrYPGF9D1yLqtZhd')
