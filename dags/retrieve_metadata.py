import os

from datetime import datetime
from airflow import DAG
from operators.uuid_retriever import UUIDRetriever
from operators.detail_retriever import DetailRetriever
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
    gather_uuid = UUIDRetriever(
        task_id="gather_uuid",
        endpoint="api/v2/graphql",
        http_conn_id="zamg_connection",
        method="POST",
        headers={"Content-Type": "application/json", "x-api-key": os.getenv("API_TOKEN")},
    )
    
    generate_metadata = DetailRetriever(
        task_id="generate_metadata",
        endpoint="api/v2/graphql",
        http_conn_id="zamg_connection",
        input_uuid="{{ti.xcom_pull(task_ids='gather_uuid')}}",
        method="POST",
        headers={"Content-Type": "application/json", "x-api-key": os.getenv("API_TOKEN")},
    )

    gather_uuid >> generate_metadata
