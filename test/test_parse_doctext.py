import unittest

from src.util.format import parse_doctext


class TestParser(unittest.TestCase):
    strings = ['malformed'
        ,
               '<HTML><BODY><p><b>Reason For Study:</b> CT - Computerised tomography</p><p><b>Order Number:</b> 276196777477000</p><p><b>Order Group:</b> 2761967</p><p> <b>Ordered at:</b> 18/05/2025 10:13 </p><p> <b>Required at:</b> 18/05/2025 10:11 <b>Priority: &lt;4 hours</b></p><p></p><p><b>Referred by: </b>  RESPIRATORY 1 TEAM ( - 683RQ)</p><p><b>Actually Ordered by: </b>DR TEURAI CHIKURA ( - 18BPEZ)</p><p id="ROLE"><b>Role</b>: SMO</p><p><b>Callback number:</b> 0211465691</p><p><b>Entered by:</b>  (TEUURAC)</p><p></p><p id="EXAMREQUESTED"><b>Examination requested</b>: Abdomen</p><p id="CLINURGENCY"><b>Clinical urgency</b>: &lt;4 hours</p><p id="INFECTIOUS"><b>Infection</b>: No</p><p id="ACCREL"><b>ACC related visit</b>: No</p><p id="CLINDETAILS"><b>Clinical Details</b>: Likely malignant ascites from ovarian primary, drain placed yesterday, significant suprapubic pain ? perforation</p><p id="CONSENTQUESTION"><b>Patient consent</b>: Yes</p><p id="EGFRRESULT"><b>eGFR result</b>: 38 mL/min/1.73m2 (Ref Range 80-120) 15-May-2025 12:10</p><p id="PATACUTE"><b>Acute kidney injury</b>: No</p><p id="PATHOSPITALSTAY"><b>Hospital admission in the last 6 weeks</b>: No</p><p id="SERUMCREATRESULT"><b>Serum creatinine result</b>: 121 umol/L (Ref Range 45-90) 15-May-2025 12:10</p></BODY></HTML>'
        ,
               '<HTML><BODY><p><b>Reason For Study:</b> CT - Computerised tomography</p><p><b>Order Number:</b> 276218777477000</p><p><b>Order Group:</b> 2762187</p><p> <b>Ordered at:</b> 18/05/2025 15:52 </p><p> <b>Required at:</b> 18/05/2025 15:48 <b>Priority: &lt;4 hours</b></p><p></p><p><b>Referred by: </b>  TEAM EMERGENCY MEDICINE, TEAM ( - 441YT)</p><p><b>Actually Ordered by: </b> SU-ANN YEE ( - 27HLTD)</p><p id="ROLE"><b>Role</b>: House Surgeon</p><p><b>Callback number:</b> 0277494821</p><p><b>Entered by:</b>  (SU-ANNY)</p><p></p><p id="EXAMREQUESTED"><b>Examination requested</b>: CT Head Neck Chest/Abdomen Trauma</p><p id="CLINURGENCY"><b>Clinical urgency</b>: &lt;4 hours</p><p id="INFECTIOUS"><b>Infection</b>: No</p><p id="ACCREL"><b>ACC related visit</b>: No</p><p id="CLINDETAILS"><b>Clinical Details</b>: 79F. </p><p>Unwitnessed fall x2, unclear mechanism and limited history. Found prone, possible long lie. </p><p>Vomiting x2 post fall, now settled. </p><p>Mild tenderness RLQ no guarding. Mild pain in coccyx</p><p>Background dementia, on aspirin. Also ILD</p><p id="CONSENTQUESTION"><b>Patient consent</b>: Attending medical practitioner consent</p><p id="EGFRRESULT"><b>eGFR result</b>: 26 mL/min/1.73m2 (Ref Range 80-120) 18-May-2025 12:12</p><p id="PATACUTE"><b>Acute kidney injury</b>: Yes</p><p id="PATHOSPITALSTAY"><b>Hospital admission in the last 6 weeks</b>: No</p><p id="SERUMCREATRESULT"><b>Serum creatinine result</b>: 163 umol/L (Ref Range 45-90) 18-May-2025 12:12</p></BODY></HTML>'
        ,
               '<HTML><BODY><b>Modality:</b> US <b>Body part:</b> BONY PELVIS/HIP/THIGH <b>Clinical Category:</b> 4 Weeks <p><b>Clinical Notes:</b> Born by C-section. x2 cousins have congenital hip dislocation, one had complications from late diagnosis. Normal initial examination today. To rule out hip congenital hip dislocation based on risk factors (FH) please.</p><p><b>Reason For Study:</b> Ultrasound - Hip (GP)</p><p><b>Order Number:</b> ERMS-8327872</p><p> <b>Ordered at:</b> 16/05/2025 13:11 </p><p> <b>Required at:</b> 16/05/2025 13:11 <b>Priority: 4 Weeks</b></p><p></p><p><b>Referred by: </b> ROBERT ELLUL ( - 23HCJH)</p><p></p></BODY></HTML>'
        , '<html> <head>  </head> <body> <p> DR Ngaire cancelled scan </p> </body> </html>'
               ]

    def test_parse_malformed(self):
        clinical_details, egfr = parse_doctext(self.strings[0])
        self.assertIsNone(clinical_details)
        self.assertIsNone(egfr)

    def test_parse_common(self):
        clinical_details, egfr = parse_doctext(self.strings[1])
        self.assertIsNotNone(clinical_details)
        self.assertIsNotNone(egfr)

    def test_parse_rare(self):
        clinical_details, egfr = parse_doctext(self.strings[2])
        self.assertIsNotNone(clinical_details)
        self.assertNotEqual('79F. ', clinical_details)
        self.assertIsNotNone(egfr)

    def test_parse_alt(self):
        clinical_details, egfr = parse_doctext(self.strings[3])
        self.assertIsNotNone(clinical_details)
        # self.assertNotEqual('79F. ', clinical_details)
        self.assertIsNone(egfr)


if __name__ == '__main__':
    unittest.main()
