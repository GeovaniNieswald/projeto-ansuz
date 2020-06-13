import firebase_admin
import json

from firebase_admin import credentials
from firebase_admin import db

firebase_sdk_path = "ansuz/odin/config/projeto-ansuz-firebase-adminsdk-9xff1-ed81f64f90.json"
    
class Firebase():

    def __init__(self):
        self.cred = credentials.Certificate(firebase_sdk_path)
        firebase_admin.initialize_app(self.cred, { 'databaseURL': 'https://projeto-ansuz.firebaseio.com/' })

    def gravar_conf_inicial(self, uuid, conf_local):
        self.sucesso = False

        ref = db.reference("usuarios") 

        uuid_ref = ref.child(uuid) 
        uuid_ref.set(conf_local)

        self.sucesso = True

        return self.sucesso

    def obter_conf(self, uuid):
        self.conf = None

        ref = db.reference("usuarios/" + uuid) 
        
        self.conf = ref.get()

        return self.conf