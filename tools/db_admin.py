import sqlite3
from firebase_admin import credentials, db, initialize_app
from src.database import FIREBASE_URL
from src.util.format import tokenise_request

FIREBASE_ADMIN_UID = 'db-admin'
SERVICE_ACCOUNT_KEY_PATH = 'serviceAccountKey.json'
SQLITE_DB_PATH = 'AutoTriage.sqlite3'

def update_database_modalities(overwrite=False):
    with sqlite3.connect(SQLITE_DB_PATH) as con:
        con.row_factory = sqlite3.Row
        res = con.execute("SELECT id, name from modality")
        output = {row['name']: {'.value': True, '.priority': row['id']} for row in res}
        ref = db.reference('/modality')
        if overwrite: ref.set(output)
        else: ref.update(output)

def update_database_body_parts(overwrite=False):
    with sqlite3.connect(SQLITE_DB_PATH) as con:
        con.row_factory = sqlite3.Row
        res = con.execute("select id, name from body_part")
        output = {row['name'].replace('/','_'): {'.value': True, '.priority': row['id']} for row in res}
        ref = db.reference('/bodyPart')
        if overwrite: ref.set(output)
        else: ref.update(output)

def update_database_examinations(overwrite=False):
    with sqlite3.connect(SQLITE_DB_PATH) as con:
        con.row_factory = sqlite3.Row
        res = con.execute("select modality.name as modality, code, examination.name, body_part.name as body_part, topic from examination join modality on examination.modality = modality.id join body_part on examination.body_part = body_part.id")
        output = {f'{row['modality']}/{row['code']}': dict(
            name=row['name'],
            bodyPart=row['body_part'],
            topic=row['topic'],
        ) for row in res }
        ref = db.reference('/examination')
        if overwrite: ref.set(output)
        else: ref.update(output)

def update_database_labels(overwrite=False):
    with sqlite3.connect(SQLITE_DB_PATH) as con:
        con.row_factory = sqlite3.Row
        res = con.execute("select modality.name as modality, u.name, body_part.name as body_part, code from (select "
                          "label.name, examination, code, modality, body_part from label join examination on "
                          "examination.id = label.examination union select name, id as examination, code, modality, "
                          "body_part from examination) as u join modality on u.modality = modality.id join body_part "
                          "on u.body_part = body_part.id")
        output = {f'{row['modality']}/{tokenise_request(row['name'])}': dict(bodyPart=row['body_part'], code=row['code']) for row in res}
        ref = db.reference('/label')
        if overwrite: ref.set(output)
        else: ref.update(output)

if __name__ == '__main__':
    cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
    default_app = initialize_app(cred, dict(
        databaseURL=FIREBASE_URL,
        databaseAuthVariableOverride=dict(uid=FIREBASE_ADMIN_UID),
    ))
    # update_database_modalities()
    # update_database_body_parts()
    # update_database_examinations()
    # update_database_labels()
    tokenised = tokenise_request('CT EXTREMITY - LOWER LIMB C+')
    result = db.reference(f'/label/CT/{tokenised}').get()
    print(result)

