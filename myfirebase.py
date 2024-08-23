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
    FIRESTORE_PATH = 'https://firestore.googleapis.com/v1/projects/sign-in-eab7e/databases/(default)/documents/'
    PROJECT_ID = "sign-in-eab7e"
    API="AIzaSyCnfut4uNf9BhoVTtxTkT6cb8k57UXwzl8"
    UID="TTm4RVGLbFYFDYmWZHWKD5aSz1q2"
    ACCESS_TOKEN = None


class INTERNAL:
    
    def create(DATA,path):
        url = FIREBASE_GLOBAL_VAR.FIRESTORE_PATH+'reports/'+FIREBASE_GLOBAL_VAR.UID+"/"+path
        headers = {"Authorization":"Bearer " + FIREBASE_GLOBAL_VAR.ACCESS_TOKEN,"Content-Type": "application/json"}
        gc.collect()
        response=urequests.patch(url=url , headers=headers, data=DATA)
        print(response.text)
        del url,headers,DATA
        if response.status_code < 200 or response.status_code > 299:
            raise FirestoreException(response.reason, response.status_code)
        del response
        gc.collect()
        
    def update(url,headers,data):
        print(data)
        response=urequests.patch(url,headers=headers,data=data)
        print(response.text)
        del response
        gc.collect()




def set_access_token(token):
    FIREBASE_GLOBAL_VAR.ACCESS_TOKEN = token
    
def set_uid(uid):
    FIREBASE_GLOBAL_VAR.UID = uid    


def create(data, path=""):
    gc.collect()
    return INTERNAL.create(data, path)
    
def get(slot_name):
    url=FIREBASE_GLOBAL_VAR.FIRESTORE_PATH+slot_name+'/'+FIREBASE_GLOBAL_VAR.UID
    headers = {"Authorization": "Bearer " + FIREBASE_GLOBAL_VAR.ACCESS_TOKEN, "Content-Type": "application/json"}
    response=urequests.get(url,headers=headers)
    print(response.text)
    return parse_doc(ujson.loads(response.text),slot_name)
    
def update(slot_name,count):
    print('Updating '+slot_name)
    url=FIREBASE_GLOBAL_VAR.FIRESTORE_PATH+slot_name+'/'+FIREBASE_GLOBAL_VAR.UID+"?updateMask.fieldPaths=pill_count"
    headers = {"Authorization": "Bearer " + FIREBASE_GLOBAL_VAR.ACCESS_TOKEN, "Content-Type": "application/json"}
    data=ujson.dumps({"fields":{"pill_count":{"integerValue":str(count)}}})
    INTERNAL.update(url,headers,data)

def parse_doc(doc,slot_name):
    
    data=doc['fields']
    parsed_doc={}
    for field,value in data.items():
        for type,val in value.items():
            parsed_doc[field]=val
    del doc
    return parsed_doc
