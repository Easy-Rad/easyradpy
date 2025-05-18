import csv
from os import environ

import psycopg
from lxml import etree
from psycopg.rows import dict_row

from src.util.format import tokenise_request, parse_doctext

E_REFERRAL_REQUEST_KEY = 'e_request'
E_REFERRAL_REQUEST_TOKENISED_KEY = 'e_request_tokenised'
E_REFERRAL_CLINICAL_DETAILS_KEY = 'e_clinical_details'
TRIAGE_HISTORY_FILENAME = 'triage_history.csv'
TRIAGE_RECORDS_START_OFFSET = 0
TRIAGE_RECORDS_CHUNK_SIZE = 1000
TRIAGE_RECORDS_CHUNK_COUNT = 100

def get_referral_data(connection: psycopg.Connection) -> list[dict]:
    data = []
    with connection.cursor() as cur:
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
    return data

def get_reports(connection: psycopg.Connection):
    with connection.cursor() as cur:
        cur.execute("""
                    select pa_nhi::text,
                           ce_description,
                           re_status_change,
                           te_text
                    from reports
                             join doctext on te_key = re_serial and te_key_type = 'R'
                             join case_event on re_event_serial = ce_serial
                             join case_main on ce_cs_serial = cs_serial
                             join patient on cs_pno = pa_pno
                    where re_status_change is not null
                    order by re_status_change desc
                    limit 500
        """)
        for record in cur:
            print(record)


def get_triage_records(connection: psycopg.Connection):
    with open(TRIAGE_HISTORY_FILENAME, mode='a', encoding='utf-8') as psv, connection.cursor() as cur:
        psv_writer = csv.writer(psv, delimiter='|', lineterminator='\n')
        count = TRIAGE_RECORDS_START_OFFSET
        for chunk in range(TRIAGE_RECORDS_CHUNK_COUNT):
            print(
                f'limit={TRIAGE_RECORDS_CHUNK_SIZE}, offset={TRIAGE_RECORDS_START_OFFSET + chunk * TRIAGE_RECORDS_CHUNK_SIZE}')
            cur.execute("""
                        select rf_serial,
                               rf_date,
                               rf_reason                           exam,
                               extract(year from age(pa_dob))::int age,
                               codes,
                               te_text
                        from case_referral
                                 join (select rfe_reg_serial               rf_registered_id,
                                              array_agg(distinct rfe_exam) codes
                                       from case_referral_exam
                                       where rfe_exam <> 0
                                         and rfe_status = 'A'
                                       group by rfe_reg_serial
                                       order by rfe_reg_serial desc) codes using (rf_registered_id)
                                 join patient on rf_pno = pa_pno
                                 left join notes on no_key = rf_serial and no_type = 'F' and no_category = 'Q' and
                                                    no_sub_category = 'R' and no_status = 'A'
                                 left join doctext on te_key = no_serial and te_key_type = 'N'
                        where rf_new_rf_serial = 0
                          and rf_site in ('CDHB', 'EMER', 'PARK', 'CWHO', 'BURW', 'NUC', 'ASH')
                          and rf_exam_type = 'CT'
                        limit %(limit)s offset %(offset)s
                        """, params=dict(
                limit=TRIAGE_RECORDS_CHUNK_SIZE,
                offset=TRIAGE_RECORDS_START_OFFSET + chunk * TRIAGE_RECORDS_CHUNK_SIZE
            ), prepare=True)
            for record in cur:
                count += 1
                age = record['age']
                clinical_details, egfr = parse_doctext(record['te_text'])
                data = [
                    record['rf_serial'],
                    record['rf_date'],
                    record['exam'],
                    age,
                    record['codes'],
                    clinical_details or '',
                    egfr or (140 - age),
                ]
                print(count, data)
                psv_writer.writerow(data)

if __name__ == '__main__':
    username = environ['db_username']
    password = environ['db_password']
    with psycopg.connect(
            f'postgresql://{username}:{password}@159.117.39.229:5432/prod_cdhb',
            row_factory=dict_row,
    ) as conn:
        # get_triage_records(conn)
        # referrals = get_referral_data(conn)
        # print(json.dumps(referrals, indent=2))
        # print(f'Parsed {len(referrals)} referrals')
        get_reports(conn)
