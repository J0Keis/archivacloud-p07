# =============================================================================
#  gestionar.py  —  CRUD sobre la tabla DynamoDB "database_dynamo"
# -----------------------------------------------------------------------------
#  La tabla usa CLAVE COMPUESTA:
#    - Partition key (HASH):  id_tabla
#    - Sort key (RANGE):      nombre_proyecto
#  Por eso 'editar' y 'borrar' necesitan AMBOS valores para identificar el item.
#  'editar' solo cambia la descripcion (el nombre_proyecto es parte de la clave
#  y no se puede modificar; para cambiarlo hay que borrar y volver a agregar).
#
#  Uso:
#    python dynamodb/gestionar.py agregar <id> <nombre> <descripcion>
#    python dynamodb/gestionar.py editar  <id> <nombre> <nueva_descripcion>
#    python dynamodb/gestionar.py borrar  <id> <nombre>
#    python dynamodb/gestionar.py listar
# =============================================================================
import os
import sys
from pathlib import Path

import boto3
from dotenv import load_dotenv

#  Credenciales desde el .env (control SEC-01: nunca en el código).
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

session = boto3.Session(
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
    region_name=os.getenv("AWS_REGION", "us-east-1"),
)
table = session.resource("dynamodb").Table("database_dynamo")


def agregar(id_tabla, nombre, descripcion):
    """Inserta (o reemplaza) un item completo."""
    table.put_item(
        Item={"id_tabla": id_tabla, "nombre_proyecto": nombre, "descripcion": descripcion}
    )
    print(f"[OK] Agregado -> id={id_tabla}, nombre={nombre}, desc={descripcion}")


def editar(id_tabla, nombre, descripcion):
    """Cambia la descripcion de un item existente (clave = id_tabla + nombre)."""
    table.update_item(
        Key={"id_tabla": id_tabla, "nombre_proyecto": nombre},
        UpdateExpression="SET descripcion = :d",
        ExpressionAttributeValues={":d": descripcion},
    )
    print(f"[OK] Editado -> id={id_tabla}, nombre={nombre}, nueva desc={descripcion}")


def borrar(id_tabla, nombre):
    """Elimina un item por su clave compuesta (id_tabla + nombre)."""
    table.delete_item(Key={"id_tabla": id_tabla, "nombre_proyecto": nombre})
    print(f"[OK] Borrado -> id={id_tabla}, nombre={nombre}")


def listar():
    """Muestra todos los items de la tabla (scan)."""
    resp = table.scan()
    print(f"Total items: {resp['Count']}")
    for item in sorted(resp["Items"], key=lambda x: x["id_tabla"]):
        print(f"  {item['id_tabla']} | {item.get('nombre_proyecto')} | {item.get('descripcion')}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__)
    elif args[0] == "agregar" and len(args) == 4:
        agregar(args[1], args[2], args[3])
    elif args[0] == "editar" and len(args) == 4:
        editar(args[1], args[2], args[3])
    elif args[0] == "borrar" and len(args) == 3:
        borrar(args[1], args[2])
    elif args[0] == "listar":
        listar()
    else:
        print("Uso incorrecto.")
        print(__doc__)
