import firebase_admin
from firebase_admin import credentials, firestore
import os
import base64
import json

# Inicializar Firestore
def init_firestore():
    try:
        # Leer credenciales desde base64
        encoded_creds = os.getenv('FIRESTORE_CREDENTIALS')
        if not encoded_creds:
            raise ValueError("FIRESTORE_CREDENTIALS no está configurado en las variables de entorno.")
        
        # Decodificar base64 y convertir a diccionario
        firestore_creds = base64.b64decode(encoded_creds).decode("utf-8")
        creds_dict = json.loads(firestore_creds)
        
        # Inicializar Firebase Admin con las credenciales
        cred = credentials.Certificate(creds_dict)
        firebase_admin.initialize_app(cred)
        
        # Retornar cliente de Firestore
        return firestore.client()
    except Exception as e:
        raise RuntimeError(f"Error al inicializar Firestore: {str(e)}")

# Instancia global de Firestore
db = init_firestore()
