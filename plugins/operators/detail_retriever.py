import ast
import json
import os
from typing import Dict, Optional

import jmespath
from airflow.models import BaseOperator
from airflow.providers.http.hooks.http import HttpHook


class DetailRetriever(BaseOperator):

    """
    Will call the GraphQL endpoint to retrieve the metadata
    :param endpoint: The relative part of the full url. (templated)
    :param method: The HTTP method to use, default = "POST"
    :param data: The data to pass. POST-data in POST/PUT and params
        in the URL for a GET request. (templated)
    :param headers: The HTTP headers to be added to the GET request
    """

    template_fields = ("input_uuid",)

    def __init__(
        self,
        endpoint: str,
        http_conn_id: str,
        input_uuid: str,
        output_folder: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.endpoint = endpoint
        self.http_conn_id = http_conn_id
        self.method = method
        self.headers = headers
        self.input_uuid = input_uuid
        self.output_folder = output_folder

    def execute(self, context) -> Dict:

        uuid_found = ast.literal_eval(self.input_uuid)
        self.log.info(f"UUID found {len(uuid_found)}")
        # converting uuid into a generator for memory usage
        uuid_as_gen = (y for y in uuid_found)
        # clean-up memory
        del uuid_found
        self.input_uuid = None

        http = HttpHook(self.method, http_conn_id=self.http_conn_id)        
        template_env = context["dag"].get_template_env()
        _search_paths = ast.literal_eval(template_env.get_template('mapping.json').render())
        _template = template_env.get_template('fetch.j2')
        for el in uuid_as_gen:
            _loop_context = {"UUID": el}
            payload = {"query": _template.render(**_loop_context).replace("\n", " ")}

            self.log.info(f"Calling HTTP method for UUID: {el}")
            response = http.run(self.endpoint, json.dumps(payload), self.headers)
            response.raise_for_status()

            if response.json().get("errors", []):
                self.log.error(f"Endpoint return an error: {response.json().get('errors')}")
                context["ti"].xcom_push(key=el, value=response.json().get('errors'))
                continue

            self._save_file(
                uuid=el,
                data=self._parse_detail(databox=response.json(), _search_paths=_search_paths),
                output=self.output_folder
            )

    def _parse_detail(self, databox, _search_paths):
        values = {}
        for key, _path in _search_paths.items():
            values[key] = jmespath.search(
                expression=_path,
                data=databox
            )
        yield values

    def _save_file(self, uuid, data, output):
        _path = f"{output}/{uuid}"
        if not os.path.exists(_path):
            os.makedirs(_path, exist_ok=True)
        with open(f"{_path}/{uuid}.txt", 'w+') as _file:
            _file.writelines(json.dumps([x for x in data][0]))

