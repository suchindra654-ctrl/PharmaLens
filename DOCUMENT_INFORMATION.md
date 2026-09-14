# Document Age / Publication Information

The existing source-answer engine is unchanged. This is an additive metadata layer.

- publication.py: detect explicitly labeled publication dates on the first two
  pages, then revision/update/issue dates, then an explicit PublicationDate tag in
  PDF subject metadata, then catalog publication_date/publication_year/revision.
  CreationDate, ModDate, copyright years and filesystem timestamps are not evidence
  of publication. Conflicting same-priority dates remain unknown.
- catalog.py: expose publication information alongside existing revision metadata.
- rag.py: append a separate Document information section after the existing answer;
  expose newer_information_requested and the check_current_information flag.
- reference_views.py and portal_admin.py: display publication and document age.
- tests/test_publication.py: known, unknown, competing dates, age precision, current
  year, older and future dates, catalog fallback, explicit/normal requests.

Age uses datetime.date.today() on each calculation. A year-only date reports the
current year minus publication year, labeled Approximately; month/day precision
allows approximate completed months. A revision fallback is explicitly identified
as a revision date, not presented as a proven original publication date.

Example as of 2026-09-13 (example only, not a hardcoded clock):

Publication: 2021

Document age: Approximately 5 years

Date source: Publication stated in PDF

Document age alone does not establish whether its contents are current. If you
need current recommendations, consider checking newer publications or guidelines.
No newer-source check was performed.

Normal questions do not trigger any newer-information web search. An explicit
currency request or check_current_information=True marks eligibility only. No
external-search provider is implemented here: the user sees a clear notice that
newer sources have not been checked. PDF and external evidence are never merged.

Limitations: conservative first-two-page detection can miss publication dates
elsewhere, scanned text without OCR, non-English labels and unsupported date
formats. Most generic PDF timestamps are intentionally ignored. No claim is made
that a document is obsolete, correct, or latest solely from its age. Existing
medical disclaimers and source passages are preserved.
