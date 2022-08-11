import os

from datetime import datetime
from airflow import DAG, AirflowException
from operators.uuid_retriever import UUIDRetriever
from operators.detail_retriever import DetailRetriever
from airflow.configuration import conf


default_args = {"owner": "airflow", "start_date": datetime(2022, 4, 12)}

TEMPLATES_PATH_INTERNAL = os.getenv("TEMPLATES_PATH_INTERNAL", f'{os.getenv("AIRFLOW_HOME")}/templates')
OUTPUT_PATH_INTERNAL = os.getenv("OUTPUT_PATH_INTERNAL", f'{os.getenv("AIRFLOW_HOME")}/output')

GATHER_QUERY_TEMPLATE_NAME = os.getenv("GATHER_QUERY_TEMPLATE_NAME", '10_gather.j2')
FETCH_QUERY_TEMPLATE_NAME = os.getenv("FETCH_QUERY_TEMPLATE_NAME", '20_fetch.j2')

MAPPING_FILE_NAME = os.getenv("MAPPING_FILE_NAME", '30_mapping.json')
ISO_TEMPLATE_NAME = os.getenv("ISO_TEMPLATE_NAME", '40_iso_template.j2')


API_TOKEN = os.getenv("API_TOKEN")


dag = DAG(
    "import_metadata",
    schedule_interval=None,
    default_args=default_args,
    description="Call the graphql endpoint to retrieve the metadata and then save them as file",
    catchup=False,
    template_searchpath=[
        "templates",
        TEMPLATES_PATH_INTERNAL
    ]
)


if API_TOKEN is None:
    raise AirflowException("The API token is not configured")


with dag:
    gather_uuid = UUIDRetriever(
        task_id="gather_uuid",
        endpoint="api/v2/graphql",
        http_conn_id="zamg_connection",
        gathering_template_name=GATHER_QUERY_TEMPLATE_NAME,
        method="POST",
        headers={"Content-Type": "application/json", "x-api-key": API_TOKEN},
    )
    
    generate_metadata = DetailRetriever(
        task_id="generate_metadata",
        endpoint="api/v2/graphql",
        http_conn_id="zamg_connection",
        input_uuid="{{ti.xcom_pull(task_ids='gather_uuid')}}",
        output_folder=OUTPUT_PATH_INTERNAL,
        detail_template=FETCH_QUERY_TEMPLATE_NAME,
        xml_template=ISO_TEMPLATE_NAME,
        mapping_template=MAPPING_FILE_NAME,

        method="POST",
        headers={"Content-Type": "application/json", "x-api-key": API_TOKEN},
    )

    gather_uuid >> generate_metadata
