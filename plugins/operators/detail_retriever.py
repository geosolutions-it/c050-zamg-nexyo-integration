import ast, json
from typing import Dict, Optional
from airflow import AirflowException
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

    def execute(self, context) -> Dict:
        uuid_found = ast.literal_eval(self.input_uuid)
        self.log.info(len(uuid_found))
        http = HttpHook(self.method, http_conn_id=self.http_conn_id)        
        template_env = context["dag"].get_template_env()
        _template = template_env.get_template('fetch.j2')
        for el in uuid_found:
            _loop_context = {"UUID": el}
            payload = {"query": _template.render(**_loop_context).replace("\n", " ")}

            self.log.info("Calling HTTP method")
            response = http.run(self.endpoint, json.dumps(payload), self.headers)
            response.raise_for_status()

            if response.json().get("errors", []):
                self.log.error(f"Endpoint return an error: {response.json()}")
                raise AirflowException(f"Endpoint return an error: {response.json()}")
