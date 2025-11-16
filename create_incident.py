import boto3
import os
from datetime import datetime
import uuid

def create_incident(event, context):
    print("Event recibido en create_incident:", event)  # Log en CloudWatch

    try:
        # Obtener el token desde el header Authorization (formato Bearer <token>)
        token = event['headers'].get('Authorization').replace('Bearer ', '')  
        if not token:
            return {
                'statusCode': 400,
                'body': {'error': 'Faltan datos en los headers'}
            }

        # Obtener el nombre de la tabla de tokens desde las variables de entorno
        tokens_table_name = os.environ['DYNAMODB_TABLE_TOKENS']

        dynamodb = boto3.resource('dynamodb')
        tokens_table = dynamodb.Table(tokens_table_name)

        # Buscar el token en la tabla de tokens
        response = tokens_table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('tenant_id').eq(token)
        )

        if 'Items' not in response or len(response['Items']) == 0:
            return {
                'statusCode': 403,
                'body': 'Token no válido o no encontrado'
            }

        token_item = response['Items'][0]
        user_role = token_item['role']

        # Verificar si el usuario es un estudiante
        if user_role != 'estudiante':
            return {
                'statusCode': 403,
                'body': 'Solo los estudiantes pueden crear incidencias'
            }

        # Crear la incidencia
        body = event['body']
        descripcion = body.get('descripcion')
        tipo_incidencia = body.get('tipo_incidencia')
        ubicacion = body.get('ubicacion')
        urgencia = body.get('urgencia')

        if not descripcion or not tipo_incidencia or not ubicacion or not urgencia:
            return {
                'statusCode': 400,
                'body': {'error': 'Faltan datos en el cuerpo de la solicitud'}
            }

        # Generar un ID único para la incidencia
        incidente_id = str(uuid.uuid4())

        # Almacenar la incidencia en DynamoDB
        incidencias_table = dynamodb.Table(os.environ['DYNAMODB_TABLE_INCIDENCIAS'])
        incidencia_data = {
            'incidente_id': incidente_id,
            'descripcion': descripcion,
            'tipo_incidencia': tipo_incidencia,
            'ubicacion': ubicacion,
            'urgencia': urgencia,
            'fecha_creacion': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        incidencias_table.put_item(Item=incidencia_data)

        return {
            'statusCode': 200,
            'body': {'message': 'Incidencia creada con éxito', 'incidente_id': incidente_id}
        }

    except Exception as e:
        print("Error en create_incident:", str(e))  # Log en CloudWatch
        return {
            'statusCode': 500,
            'body': {'error': str(e)}
        }
