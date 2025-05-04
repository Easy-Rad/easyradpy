import sqlite3
from firebase_admin import credentials, db, initialize_app
from src.database import FIREBASE_URL
from src.util.format import tokenise_request, encode_key
from urllib.parse import quote

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
        output = {encode_key(row['name']): {'.value': True, '.priority': row['id']} for row in res}
        ref = db.reference('/bodyPart')
        if overwrite: ref.set(output)
        else: ref.update(output)

def update_database_examinations(overwrite=False):
    with sqlite3.connect(SQLITE_DB_PATH) as con:
        con.row_factory = sqlite3.Row
        res = con.execute("select modality.name as modality, code, examination.name, body_part.name as body_part, topic from examination join modality on examination.modality = modality.id join body_part on examination.body_part = body_part.id")
        output = {f'{row['modality']}/{row['code']}': dict(
            name=row['name'],
            tokenised=tokenise_request(row['name']),
            bodyPart=encode_key(row['body_part']),
            topic=row['topic'],
        ) for row in res }
        ref = db.reference('/examination')
        if overwrite: ref.set(output)
        else: ref.update(output)

def update_database_labels(overwrite=False):
    with sqlite3.connect(SQLITE_DB_PATH) as con:
        con.row_factory = sqlite3.Row

        res = con.execute("select modality.name as modality, examination.name, code from examination join modality on examination.modality = modality.id")
        examinations = {f'{row['modality']}/{tokenise_request(row['name'])}': (row['name'], row['code']) for row in res}
        # print(examinations)
        res = con.execute("select modality.name as modality, label.name, examination.code from label join examination on label.examination = examination.id join modality on examination.modality = modality.id")
        output = {}
        for row in res:
            key, code = f'{row['modality']}/{tokenise_request(row['name'])}', row['code']
            try:
                canonical_name, canonical_code = examinations[key]
                assert code == canonical_code
                print(f'"{row['name']}" matches "{canonical_name}" ({canonical_code})')
            except KeyError:
                output[key] = code
        print(output)
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
    tokenised = quote(tokenise_request('CT EXTREMITY - LOWER LIMB C+'))
    print(tokenised)
    result = (
        db.reference('/examination/CT')
        .order_by_child('tokenised')
        .equal_to(tokenised)
        .limit_to_first(1)
        .get()
    )
    print(result)

