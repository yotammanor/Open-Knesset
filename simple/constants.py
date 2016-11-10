# -*- coding: utf-8 -*
SPECIAL_COMMITTEES_NAMES = [u"הוועדה המשותפת לנושא סביבה ובריאות", ]

SECOND_AND_THIRD_READING_LAWS_URL = 'http://www.knesset.gov.il/privatelaw/plaw_display.asp?LawTp=2'
PRIVATE_LAWS_URL = r"http://www.knesset.gov.il/privatelaw/Plaw_display.asp?lawtp=1"
KNESSET_LAWS_URL = r"http://www.knesset.gov.il/laws/heb/template.asp?Type=3"
GOV_LAWS_URL = r"http://www.knesset.gov.il/laws/heb/template.asp?Type=4"

# some party names appear in the knesset website in several forms.
# this dictionary is used to transform them to canonical form.
CANONICAL_PARTY_ALIASES = {'עבודה': 'העבודה',
                           'ליכוד': 'הליכוד',
                           'ש"ס-התאחדות ספרדים שומרי תורה': 'ש"ס',
                           'יחד (ישראל חברתית דמוקרטית) והבחירה הדמוקרטית': 'יחד (ישראל חברתית דמוקרטית) והבחירה הדמוקרטית',
                           'בל"ד-ברית לאומית דמוקרטית': 'בל"ד',
                           'אחריות לאומית': 'קדימה',
                           'יחד (ישראל חברתית דמוקרטית) והבחירה הדמוקרטית': 'מרצ-יחד והבחירה הדמוקרטית',
                           'יחד והבחירה הדמוקרטית': 'מרצ-יחד והבחירה הדמוקרטית',
                           'יחד והבחירה הדמוקרטית (מרצ לשעבר)': 'מרצ-יחד והבחירה הדמוקרטית',
                           'יחד (ישראל חברתית דמוקרטית) והבחירה הדמוקרטית': 'מרצ-יחד והבחירה הדמוקרטית',
                           'יחד  (ישראל חברתית דמוקרטית) והבחירה הדמוקרטית': 'מרצ-יחד והבחירה הדמוקרטית',
                           }
GOVT_INFO_PAGE = r"http://www.knesset.gov.il/mk/heb/MKIndex_Current.asp?view=4"
KNESSET_INFO_PAGE = r"http://www.knesset.gov.il/mk/heb/MKIndex_Current.asp?view=7"
MK_HTML_INFO_PAGE = r"http://www.knesset.gov.il/mk/heb/mk_print.asp?mk_individual_id_t="
KNESSET_COMMITTEES_AGENDA_PAGE = 'http://knesset.gov.il/agenda/heb/CommitteesByDate.asp'
