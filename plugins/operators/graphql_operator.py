import json
from typing import Any, Dict, Optional
from itertools import chain
from airflow import AirflowException
from airflow.models import BaseOperator
from airflow.providers.http.hooks.http import HttpHook


class MetadataRetrieverOperator(BaseOperator):

    """
    Will call the GraphQL endpoint to retrieve the metadata
    :param endpoint: The relative part of the full url. (templated)
    :param method: The HTTP method to use, default = "POST"
    :param data: The data to pass. POST-data in POST/PUT and params
        in the URL for a GET request. (templated)
    :param headers: The HTTP headers to be added to the GET request
    """

    def __init__(
        self,
        endpoint: str,
        http_conn_id: str,
        method: str = "GET",
        payload_path: Any = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.endpoint = endpoint
        self.http_conn_id = http_conn_id
        self.method = method
        self.payload_path = payload_path
        self.headers = headers

    def execute(self, context) -> Dict:
        http = HttpHook(self.method, http_conn_id=self.http_conn_id)

        template_env = context["dag"].get_template_env()

        _template = template_env.get_template('retrieve.j2')
        offset = 0
        first = 10
        while True:
            _loop_context = {"OFFSET": offset, "FIRST": first}

            self.log.info(f"Preparing Payload for offset {offset}")

            payload = {"query": _template.render(**_loop_context).replace("\n", " ")}

            self.log.info("Calling HTTP method")
            response = http.run(self.endpoint, json.dumps(payload), self.headers)
            response.raise_for_status()

            if response.json().get("errors", []):
                self.log.error(f"Endpoint return an error: {response.json()}")
                raise AirflowException(f"Endpoint return an error: {response.json()}")
            
            data = response.json().get("data", {}).get("queryDataset", [])
            if not data:
                self.log.info("No data available anymore")
                break

            uuids = list(chain.from_iterable([val.values() for val in data]))
            self.log.info(uuids)
            offset += 10


        return
