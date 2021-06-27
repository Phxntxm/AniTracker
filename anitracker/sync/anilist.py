from typing import Any, Dict, Union
import urllib.parse
import webbrowser

import requests
import json

from anitracker.gql import queries

BASE_URL = "https://anilist.co/api/v2"
GQL_URL = "https://graphql.anilist.co"
REDIRECT_URI = "https://anilist.co/api/v2/oauth/pin"


class AniList:
    def __init__(self) -> None:
        self.__access_token: Union[str, None] = None
        self.id: Union[int, None] = None
        self.name: Union[str, None] = None

    @property
    def headers(self) -> Dict[str, str]:
        h = {"Accept": "application/json", "Content-Type": "application/json"}

        if self.__access_token:
            h["Authorization"] = f"Bearer {self.__access_token}"

        return h

    @property
    def authenticated(self) -> bool:
        return self.__access_token is not None

    def _get_gql_query(self, name: str):
        return getattr(queries, name)

    def from_config(self, config):
        try:
            token = config["access-token"]
        except KeyError:
            return
        else:
            self.__access_token = token

    def gql(self, query_name: str, variables: Dict[str, Any] = None):
        if variables is None:
            variables = {}

        query = self._get_gql_query(query_name)

        with requests.post(
            GQL_URL, json={"query": query, "variables": variables}, headers=self.headers
        ) as r:
            try:
                return r.json()
            except json.JSONDecodeError:
                print(query)
                print(variables)
                raise

    def open_oauth(self):
        payload = {
            "client_id": "5849",
            "response_type": "token",
        }

        url = f"{BASE_URL}/oauth/authorize?{urllib.parse.urlencode(payload)}"
        webbrowser.open(url)

    def get_collection(self):
        ret = self.gql("media_collection", variables={"userName": self.name})

        return ret

    def verify(self):
        ret = self.gql("viewer")

        if ret["data"]["Viewer"] is None:
            return ret

        self.id = ret["data"]["Viewer"]["id"]
        self.name = ret["data"]["Viewer"]["name"]

        return ret

    def store_access(self, access_token: str):
        self.__access_token = access_token
