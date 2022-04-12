import os

from datetime import datetime
from airflow import DAG
from operators.graphql_operator import MetadataRetrieverOperator


default_args = {"owner": "airflow", "start_date": datetime(2022, 4, 12)}


dag = DAG(
    "import_metadata",
    schedule_interval=None,
    default_args=default_args,
    description="Call the graphql endpoint to retrieve the metadata and then save them as file",
    catchup=False,
    template_searchpath=[
        "dags/dag_utils/templates"
    ]
)

with dag:
    MetadataRetrieverOperator(
        task_id="create_metadata_file",
        endpoint="api/v2/graphql",
        http_conn_id="zamg_connection",
        method="POST",
        payload_path=os.getenv("RETRIEVE_QUERY_PAYLOAD"),
        headers={"Content-Type": "application/json", "x-api-key": os.getenv("API_TOKEN")},
    )
