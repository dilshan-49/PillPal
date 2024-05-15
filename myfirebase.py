import ujson
import urequests
import _thread


class FirestoreException(Exception):
    def __init__(self, message, code=400):
        super().__init__()
        self.message = message
        self.code = code

    def __str__(self):
        return f"{self.code}: {self.message}"


class FIREBASE_GLOBAL_VAR:
    FIRESTORE_PATH = 'https://firestore.googleapis.com/v1/projects/pillpal-fb/databases/(default)/documents/SN00001'
    FIREBASE_PATH = "https://pillpal-fb-default-rtdb.asia-southeast1.firebasedatabase.app/user1.json"
    PROJECT_ID = "pillpal-fb"
    DATABASE_ID = "(default)"
    ACCESS_TOKEN = None

class INTERNAL:
    
    def create(DOC,document_id=None):
        url = FIREBASE_GLOBAL_VAR.FIRESTORE_PATH
        if document_id:
            url=url+'?documentId={}'.format(document_id)
        DATA = DOC.process()
        headers = {"Authorization":"Bearer " + FIREBASE_GLOBAL_VAR.ACCESS_TOKEN}
        
        response=urequests.post(url , headers=headers, json=DATA)
        
        if response.status_code < 200 or response.status_code > 299:
            print(response.text)
            raise FirestoreException(response.reason, response.status_code)
    

def set_access_token(token):
    FIREBASE_GLOBAL_VAR.ACCESS_TOKEN = token


def create(DOC, document_id=None, bg=True):
    if bg:
        _thread.start_new_thread(
            INTERNAL.create, [DOC, document_id])
    else:
        return INTERNAL.create(DOC, document_id)
    
def get():
    url=FIREBASE_GLOBAL_VAR.FIREBASE_PATH+"?auth="+FIREBASE_GLOBAL_VAR.ACCESS_TOKEN
    response=urequests.get(url)
    return ujson.loads(response.text)
    