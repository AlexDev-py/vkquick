"""
Имплементация HTTP клиентов
"""
import typing as ty

import aiohttp
import requests

from vkquick.base.client import AsyncHTTPClient, SyncHTTPClient
from vkquick.base.json_parser import JSONParser


class AIOHTTPClient(AsyncHTTPClient):
    """
    HTTP клиент, базируемый на `AIOHTTP`
    """

    def __init__(  # noqa
        self, url: str, json_parser: ty.Type[JSONParser],
    ) -> None:
        self.connector = None
        self.session = None
        self.url = url
        self.json_parser = json_parser

    async def send_get_request(
        self, path: str, params: ty.Dict[str, ty.Any]
    ) -> aiohttp.ClientResponse:
        if self.session is None:
            self.connector = aiohttp.TCPConnector(ssl=False)
            self.session = aiohttp.ClientSession(
                connector=self.connector,
                skip_auto_headers={"User-Agent"},
                raise_for_status=True,
                json_serialize=self.json_parser.dumps,
            )
        async with self.session.get(
            f"{self.url}{path}", params=params
        ) as response:
            return response

    async def close(self):
        await self.session.close()
        # Если сессия может делиться коннекторами:
        # await self.connector.close()


class RequestsHTTPClient(SyncHTTPClient):
    """
    HTTP клиент, базируемый на `requests`
    """

    def __init__(  # noqa
        self, url: str, json_parser: ty.Type[JSONParser],
    ) -> None:
        self.session = requests.session()
        self.url = url
        self.json_parser = json_parser

    def send_get_request(
        self, path: str, params: ty.Dict[str, ty.Any]
    ) -> ty.Dict[str, ty.Any]:
        response = self.session.get(f"{self.url}{path}", params=params)
        json_response = self.json_parser.loads(response.content)
        return json_response
