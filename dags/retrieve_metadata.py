import os

from datetime import datetime
from airflow import DAG
from operators.graphql_operator import MetadataRetrieverOperator
from airflow.configuration import conf


default_args = {"owner": "airflow", "start_date": datetime(2022, 4, 12)}

RETRIEVE_QUERY_PAYLOAD = os.getenv("RETRIEVE_QUERY_PAYLOAD", f'{conf.get("core", "dags_folder")}/dag_utils/templates/gather.j2')

dag = DAG(
    "import_metadata",
    schedule_interval=None,
    default_args=default_args,
    description="Call the graphql endpoint to retrieve the metadata and then save them as file",
    catchup=False,
    template_searchpath=[
        "dags/dag_utils/templates",
        os.path.dirname(RETRIEVE_QUERY_PAYLOAD)
    ]
)

with dag:
    MetadataRetrieverOperator(
        task_id="create_metadata_file",
        endpoint="api/v2/graphql",
        http_conn_id="zamg_connection",
        method="POST",
        headers={"Content-Type": "application/json", "x-api-key": os.getenv("API_TOKEN")},
    )
