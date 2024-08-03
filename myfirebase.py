import ujson
import urequests
import gc


class FirestoreException(Exception):
    def __init__(self, message, code=400):
        super().__init__()
        self.message = message
        self.code = code

    def __str__(self):
        return f"{self.code}: {self.message}"


class FIREBASE_GLOBAL_VAR:
    FIRESTORE_PATH = 'https://firestore.googleapis.com/v1/projects/<project_id>/databases/(default)/documents/'
    PROJECT_ID = "<project_id>"
    API="<WEB API key in Project Settings>"
    UID=None
    ACCESS_TOKEN = None


class INTERNAL:
    def get(url):
        headers = {"Authorization": "Bearer " + FIREBASE_GLOBAL_VAR.ACCESS_TOKEN, "Content-Type": "application/json"}
        response=urequests.get(url,headers=headers)
        return(response.text)
        
    def create(DATA,url):
        headers = {"Authorization":"Bearer " + FIREBASE_GLOBAL_VAR.ACCESS_TOKEN}
        gc.collect()
        response=urequests.post(url , headers=headers, data=DATA)
        print(response.text)
        del url,headers,DATA
        if response.status_code < 200 or response.status_code > 299:
            raise FirestoreException(response.reason, response.status_code)
        del response
        gc.collect()
        
    def update(url,headers,data):
        response=urequests.patch(url,headers=headers,data=json_data)
        print(response.text)
        del response

def set_access_token(token):
    FIREBASE_GLOBAL_VAR.ACCESS_TOKEN = token
    
def set_uid(uid):
    FIREBASE_GLOBAL_VAR.UID = uid    


def create(doc, path=None):
    url = FIREBASE_GLOBAL_VAR.FIRESTORE_PATH
    if path:
        url=url+path
    data=process_doc(doc)
    return INTERNAL.create(data, url)
    
def get(path): #path=slot_name
    url=FIREBASE_GLOBAL_VAR.FIRESTORE_PATH+path
    raw_doc=INTERNAL.get(url)
    data=parse_doc(ujson.loads(raw_doc))
    del raw_doc
    gc.collect()
    return data
    
def update(doc,fields):
    print('Updating '+slot_name)
    url=FIREBASE_GLOBAL_VAR.FIRESTORE_PATH+slot_name+'/'+FIREBASE_GLOBAL_VAR.UID+"?updateMask.fieldPaths="+fields
    headers = {"Authorization": "Bearer " + FIREBASE_GLOBAL_VAR.ACCESS_TOKEN, "Content-Type": "application/json"}
    data=process_doc(doc)
    INTERNAL.update(url,headers,data)

def parse_doc(doc):
    fields=doc.get('fields',{})
    parsed_doc={}
    for field,value in fields.items():
        for type,val in value.items():
            parsed_doc[field]=val
    return parsed_doc


def process_doc(doc):
    '''Converting Python Dictionary to Json object with the format required by REST API'''
    #Only Basic object types are defined here
    formatted_data = {"fields": {}}
    for key, value in data.items():
        if isinstance(value, str):
            formatted_data["fields"][key] = {"stringValue": value}
        elif isinstance(value, bool):
            formatted_data["fields"][key] = {"booleanValue": value}
        elif isinstance(value, int):
            formatted_data["fields"][key] = {"integerValue": value}
        elif isinstance(value, float):
            formatted_data["fields"][key] = {"doubleValue": value}
        
        #add more types as required

        else:
            raise ValueError(f"Type of value for {key} is not supported.")
    return ujson.dumps(formatted_data) 
    
