import json
from os import environ

import psycopg
from lxml import etree
from psycopg.rows import dict_row

from src.util.format import tokenise_request

E_REFERRAL_REQUEST_KEY = 'e_request'
E_REFERRAL_REQUEST_TOKENISED_KEY = 'e_request_tokenised'
E_REFERRAL_CLINICAL_DETAILS_KEY = 'e_clinical_details'

if __name__ == '__main__':
    username = environ['db_username']
    password = environ['db_password']
    data = []
    with psycopg.connect(f'postgresql://{username}:{password}@159.117.39.229:5432/prod_cdhb',
                         row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("""select rf_serial      serial,
                                  rf_dor         date,
                                  rf_triage_team team,
                                  rf_exam_type   modality,
                                  rf_reason      request,
                                  te_text        eref
                           from case_referral
                                    -- join patient on rf_pno = patient.pa_pno
                                    left join notes on no_key = rf_serial and no_type = 'F' and no_category = 'Q' and
                                                       no_sub_category = 'R' and no_status = 'A'
                                    left join doctext on te_key = no_serial and te_key_type = 'N'
                           where (rf_new_rf_serial IS NULL OR rf_new_rf_serial = 0)
                             and rf_status = 'W'
                             and coalesce(rf_triage_status, 'N') = 'I'
                             and rf_site in ('CDHB', 'EMER', 'CWHO', 'BURW', 'ASH', 'NUC', 'VASC')
                             -- and rf_triage_team='AB'
                             and rf_exam_type in ('CT', 'MR', 'US', 'SC')
                           order by rf_dor desc
                           limit 1000""")
            for record in cur:
                entry = dict(
                    id=record['serial'],
                    date=str(record['date']),
                    team=record['team'],
                    modality=record['modality'],
                    request=record['request'],
                    tokenised=tokenise_request(record['request']),
                )
                if (e_referral := record['eref']) is not None:
                    for e in etree.fromstring(e_referral).findall('./BODY/p/b'):
                        if e.text == 'Examination requested' or (
                                E_REFERRAL_REQUEST_KEY not in entry and e.text == 'Reason For Study:'):
                            r = e.tail[1:].strip()
                            entry[E_REFERRAL_REQUEST_KEY] = r
                            entry[E_REFERRAL_REQUEST_TOKENISED_KEY] = tokenise_request(r)
                        elif E_REFERRAL_CLINICAL_DETAILS_KEY not in entry and e.text in ('Clinical Details',
                                                                                         'Clinical Notes:'):
                            entry[E_REFERRAL_CLINICAL_DETAILS_KEY] = e.tail[1:].strip()
                    if E_REFERRAL_REQUEST_KEY not in entry or E_REFERRAL_CLINICAL_DETAILS_KEY not in entry:
                        raise Exception(f'Could not find request and clinical details in e-referral {e_referral}')
                    if entry[E_REFERRAL_REQUEST_TOKENISED_KEY] == entry['tokenised']:
                        del entry[E_REFERRAL_REQUEST_TOKENISED_KEY]
                        if entry[E_REFERRAL_REQUEST_KEY].lower() == entry['request'].lower():
                            del entry[E_REFERRAL_REQUEST_KEY]
                data.append(entry)
    print(json.dumps(data, indent=2))
    print(f'Parsed {len(data)} referrals')
