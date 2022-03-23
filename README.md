# C050-ZAMG-NEXYO-INTEGRATION

**Run with Docker:**

A simple docker-compose is provived to setup the environment. For run it is enough to use the following command:

```
sudo chmod 777 ./logs # first time only
docker-compose up
```

The first time may take a while before let the docker build the images.

During the development is not needed to restart the docker (unless new library are installed), because the main volume (logs, tests, dags and plugins) are mounted inside the docker.

When up airflow will be available at http://localhost:9000/airflow/home

Default user:
```
username: airflow
password: airflow
```


**Run in local environment:**

Create virtual environment for example: 
```
conda create --name zamg python=3.8
conda activate zamg
```

Install the requirements: 
```
pip install -r develop-requirements.txt
```

Create a postgres database for airflow: 
```
sudo -u postgres createdb zamg_airflow
```

Update the `dev.env` file by changing the database connection and folder path
```
AIRFLOW_HOME=/path/to/the/project/folder
AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql://geonode:geonode@localhost:5434/zamg_airflow
```

Set the new environment variables
```
set -a
. ./dev.env
set +a
```

Initialize the airflow database:
```
airflow db init
```

Create default user
```
airflow users create --username airflow --firstname airflow -lastname airflow --role Admin --email airflow@example.org --password airflow
```

Run the webserver and the scheduler:
```
airflow scheduler -D # will run as daemon
airflow webserver -p 9000
```

When up airflow will be available at http://localhost:9000/airflow/home
