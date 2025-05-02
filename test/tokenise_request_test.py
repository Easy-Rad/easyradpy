import unittest
from src.util.format import tokenise_request


class TestTokeniser(unittest.TestCase):

    def tokenise(self, expected, input_string):
        self.assertEqual(expected, tokenise_request(input_string))

    def test_strip_whitespace(self):
        self.tokenise('abdomen adrenal', '  CT   ABDOMEN  ADRENAL  ')
        self.tokenise('', '  CT    please  ')

    def test_distinguish_between_hyphens_and_c_plus_c_minus(self):
        self.tokenise('abdomen c+ c- cardiac chest', 'c- CT chest- -abdomen-and cardiac- C+ MR')

    # def test_preserve_non_contrast(self):
    #     self.tokenise( 'non-contrast', 'non-contrast')


if __name__ == '__main__':
    unittest.main()
