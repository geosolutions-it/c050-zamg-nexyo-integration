import os

from datetime import datetime
from airflow import DAG, AirflowException
from operators.uuid_retriever import UUIDRetriever
from operators.detail_retriever import DetailRetriever
from airflow.configuration import conf


default_args = {"owner": "airflow", "start_date": datetime(2022, 4, 12)}

TEMPLATE_PATH = os.getenv("RETRIEVE_QUERY_PAYLOAD", f'{conf.get("core", "dags_folder")}/dag_utils/templates')

MAPPING_QUERY_TEMPLATE_NAME =os.getenv("MAPPING_QUERY_TEMPLATE_NAME", 'mapping.json')
XML_OUTPUT_TEMPLATE_NAME = os.getenv("XML_OUTPUT_TEMPLATE_NAME", 'placeholder.j2')
INITIAL_GATHERING_TEMPLATE_NAME = os.getenv("INITIAL_GATHERING_TEMPLATE_NAME", 'gather.j2')
GET_DETAIL_QUERY_TEMPLATE_NAME = os.getenv("GET_DETAIL_QUERY_TEMPLATE_NAME", 'fetch.j2')

OUTPUT_FOLDER_PATH = os.getenv("OUTPUT_FOLDER_PATH", f'{os.getenv("AIRFLOW_HOME")}/outputs')
API_TOKEN = os.getenv("API_TOKEN")


dag = DAG(
    "import_metadata",
    schedule_interval=None,
    default_args=default_args,
    description="Call the graphql endpoint to retrieve the metadata and then save them as file",
    catchup=False,
    template_searchpath=[
        "dags/dag_utils/templates",
        TEMPLATE_PATH
    ]
)


if API_TOKEN is None:
    raise AirflowException("The API token is not configured")


with dag:
    gather_uuid = UUIDRetriever(
        task_id="gather_uuid",
        endpoint="api/v2/graphql",
        http_conn_id="zamg_connection",
        gathering_template_name=INITIAL_GATHERING_TEMPLATE_NAME,
        method="POST",
        headers={"Content-Type": "application/json", "x-api-key": API_TOKEN},
    )
    
    generate_metadata = DetailRetriever(
        task_id="generate_metadata",
        endpoint="api/v2/graphql",
        http_conn_id="zamg_connection",
        input_uuid="{{ti.xcom_pull(task_ids='gather_uuid')}}",
        output_folder=OUTPUT_FOLDER_PATH,
        detail_template=GET_DETAIL_QUERY_TEMPLATE_NAME,
        xml_template=XML_OUTPUT_TEMPLATE_NAME,
        mapping_template=MAPPING_QUERY_TEMPLATE_NAME,

        method="POST",
        headers={"Content-Type": "application/json", "x-api-key": API_TOKEN},
    )

    gather_uuid >> generate_metadata
