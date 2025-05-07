import unittest
from src.util.format import parse_comrad_db_object


class TestParser(unittest.TestCase):

    obj = 'DBObject(case_referral, rf_serial v0) [rf_serial=19911796, rf_pno=1085841, rf_dor=05/05/2025 09:35, rf_do_serial=212818, rf_reason=MRI WHOLE ABDOMEN, PANCREAS, rf_referral_type=CO, rf_priority=U, rf_ambulatory=A0, rf_site=XXXX, rf_staff=7752, rf_exam_type=MR, rf_status=W, rf_referrers_code=2745714113091000, rf_printed=null, rf_case=0, rf_after=null, rf_before=null, rf_target_date=19/05/2025, rf_target_time=114, rf_cs_type=GN, rf_auth_code=XXX-RAD, rf_date=05/05/2025, rf_status_change=05/05/2025 10:36, rf_prep_code=0, rf_pat_type=OUT, rf_pat_location=null, rf_body_part=AB, rf_rp_batchid=0, rf_new_rf_serial=0, rf_do_ad_serial=4334075, rf_case_key=N, rf_cti_rmt=null, rf_registered_id=19910999, rf_ex_sub_type=MRZ, rf_waiting_list_target=05/05/2025, rf_can_reason=null, rf_doc_letter_type=null, rf_pat_letter_type=null, rf_doc_letter_printed=null, rf_hospital=null, rf_grouping=2745714, rf_original_code=113091000, rf_original_description=Magnetic resonance imaging, rf_original_location=OUT-PATIENT, rf_encounter=null, rf_original_priority=<2 weeks, rf_triage_team=AB, rf_triage_team_allocated=05/05/2025 10:36, rf_triage_due=05/05/2025 13:36, rf_triage_complete=null, rf_triage_completed_staff=0, rf_triage_assigned_staff=0, rf_triage_disagreement=N, rf_triage_disagreement_notes=null, rf_triage_status=I, rf_original_source=EOE, rf_original_orderer_code=17HQHP, rf_original_orderer_description=SMITH,JOHN DR, rf_cancer_suspicion=null, rf_tumour_stream=null, rf_row_last_changed=05/05/2025 10:35, rf_row_version=0, rf_triage_rank=0, do_short=SMITH], isNewRecord=false'

    def test_parse(self):
        parsed = parse_comrad_db_object(self.obj)
        self.assertDictEqual(dict(
            rf_exam_type='MR',
            rf_original_priority='<2 weeks',
            rf_reason='MRI WHOLE ABDOMEN, PANCREAS',
        ), parsed)

if __name__ == '__main__':
    unittest.main()
