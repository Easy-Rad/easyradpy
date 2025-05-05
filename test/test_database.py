import unittest

from src.autotriage import Request, Modality, BodyPart, Examination
from src.database import Database, ExaminationNotFoundError


class TestDatabase(unittest.TestCase):

    database = Database()

    canonical_request: tuple[Request, Examination] = Request(
        Modality.Ultrasound,
        'US Aortic Surveillance',
    ), (BodyPart.ABDO_PELV, 'U89')
    reordered_request: tuple[Request, Examination] = Request(
        Modality.CT,
        'CT LUMBAR SPINE',  # canonical = CT SPINE LUMBAR
    ), (BodyPart.SPINE, 'Q81')
    special_chars_request: tuple[Request, Examination] = Request(
        Modality.CT,
        'CT EXTREMITY - LOWER LIMB C+',
    ), (BodyPart.LOWERLIMB, 'Q108C')
    alias_request: tuple[Request, Examination] = Request(
        Modality.CT,
        'CT Parathyroids',
    ), (BodyPart.NECK, 'Q113')
    not_in_database = Request(
        Modality.CT,
        'Impossible request',
    )

    def test_canonical(self):
        self.assertEqual(self.canonical_request[1], self.database.get_examination(self.canonical_request[0]))
    def test_reordered_request(self):
        self.assertEqual(self.reordered_request[1], self.database.get_examination(self.reordered_request[0]))
    def test_special_chars_request(self):
        self.assertEqual(self.special_chars_request[1], self.database.get_examination(self.special_chars_request[0]))
    def test_alias_request(self):
        self.assertEqual(self.alias_request[1], self.database.get_examination(self.alias_request[0]))
    def test_impossible_request(self):
        self.assertRaises(ExaminationNotFoundError, self.database.get_examination, self.not_in_database)


if __name__ == '__main__':
    unittest.main()
