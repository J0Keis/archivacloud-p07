# =============================================================================
#  main.py  —  Sube datos de ejemplo a la tabla DynamoDB "database_dynamo"
# -----------------------------------------------------------------------------
#  Versión mejorada del ejemplo del profesor: en lugar de escribir las
#  credenciales DENTRO del código (mala práctica), las lee del archivo .env
#  (control SEC-01: secretos fuera del código y del repositorio).
# =============================================================================
import os
from pathlib import Path

import boto3
from dotenv import load_dotenv

#  Carga el .env de la raíz del proyecto (mismas credenciales de AWS Academy).
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")


def upload_dynamodb(data):
    #  Sesión de AWS con las credenciales temporales leídas del .env.
    session = boto3.Session(
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )

    #  Recurso DynamoDB y referencia a la tabla ya creada en AWS.
    dynamodb = session.resource("dynamodb")
    table = dynamodb.Table("database_dynamo")

    #  Inserta cada registro en la tabla (put_item).
    for item in data:
        table.put_item(
            Item={
                "id_tabla": item["id_tabla"],
                "nombre_proyecto": item["nombre_proyecto"],
                "descripcion": item["descripcion"],
            }
        )
    print(f"{len(data)} registros subidos a 'database_dynamo' correctamente.")


#  Datos de ejemplo a subir.
data_to_upload = [
    {"id_tabla": "1", "nombre_proyecto": "Item1", "descripcion": "Description1"},
    {"id_tabla": "2", "nombre_proyecto": "Item2", "descripcion": "Description2"},
]


if __name__ == "__main__":
    upload_dynamodb(data_to_upload)
