import re
from datetime import datetime

from lxml import etree


def date_format(date: datetime) -> str:
    return date.strftime('%a %d %b %Y, %H:%M %Z')

def fee_format(fee: int) -> str:
    return '${:,d}'.format(fee)

def split_name(name: str) -> tuple[str, str]:
    result = re.split(r",\s*", name, maxsplit=1)
    return result[1] if len(result) > 1 else '', result[0]

def parse_comrad_db_object(s: str) -> dict[str, str]:
    return {k:v for k, v in re.findall(r'(rf_exam_type|rf_reason|rf_original_priority)=([^=]+?)(?=]|, \w+=)', s)}


def parse_doctext(html) -> tuple[str | None, int | None]:
    clinical_details = None
    egfr = None
    try:
        doc = etree.fromstring(html)
    except (ValueError, etree.XMLSyntaxError):
        pass
    else:
        xpath_expr = '//p[@id="CLINDETAILS"]/text()|//p[@id="CLINDETAILS"]/following-sibling::p[not(@id) and count(preceding-sibling::p[@id][1]|//p[@id="CLINDETAILS"])=1 and count(preceding-sibling::p[@id and @id!="CLINDETAILS" and position() < count(preceding-sibling::p[@id="CLINDETAILS"]/following-sibling::p)])=0]/text()'
        clinical_details = ' '.join(text.strip() for text in doc.xpath(xpath_expr))[2:]
        if not clinical_details:
            try:
                clinical_details = doc.xpath('./BODY/p/b[contains(text(), "Clinical Notes")]')[0].tail.strip()
            except IndexError:
                pass
        try:
            egfr = int(re.match('([0-9]+) mL/min/1.73m2', doc.find('./BODY/p[@id="EGFRRESULT"]/').tail[2:])[1])
        except (AttributeError, TypeError):
            pass
    # print(clinical_details, egfr)
    return clinical_details, egfr

def tokenise_request(s: str) -> str:
    s = re.sub(
        # remove non-alphanumeric characters except for C- and C+
        # remove irrelevant words including modality
        pattern=r'[^\w+-]|(?<!\bC)[+-]|\b(and|or|with|by|left|right|please|GP|CT|MRI?|US|ultrasound|scan|study|contrast)\b',
        repl=' ',
        string=s,
        flags=re.IGNORECASE|re.ASCII,
    )
    return ' '.join(sorted(re.split(r'\s+', s.lower().strip()))) # remove extra whitespace

def encode_key(s: str) -> str:
    """
    Encode a string by replacing special characters with percent-encoded values.
    Handles ., $, #, [, ], /, and ASCII control characters.
    """
    if not s:
        return s

    result = []
    for c in s:
        # Handle ASCII control characters (0x00-0x1F and 0x7F)
        if ord(c) <= 0x1F or ord(c) == 0x7F:
            result.append(f'%{ord(c):02x}')
        # Handle special characters
        elif c in '.$#[]/':
            result.append(f'%{ord(c):02x}')
        else:
            result.append(c)

    return ''.join(result)


def decode_key(s: str) -> str:
    """
    Decode a string by replacing percent-encoded values back to original characters.
    """
    if not s:
        return s

    result = []
    i = 0
    while i < len(s):
        if s[i] == '%' and i + 2 < len(s):
            try:
                char_code = int(s[i + 1:i + 3], 16)
                result.append(chr(char_code))
                i += 3
            except ValueError:
                result.append(s[i])
                i += 1
        else:
            result.append(s[i])
            i += 1

    return ''.join(result)