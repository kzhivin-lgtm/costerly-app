# DOCUMENT IDENTITY V1 - TITLE-BLOCK EVIDENCE ONLY

Extract document-level metadata from the supplied title-block candidate crops.
This is a post-Detection administrative task. It cannot identify, create,
merge, split, name, or otherwise affect commercial objects.

Read the visible source language directly. The document may use a language
outside Costerly's primary English, Hebrew and Russian workflows. Do not need a
language whitelist and do not translate a role speculatively: populate a field
only when its label or role and value are visibly bound in the same title-block
entry.

Return `unknown` for a field unless the role and value are visibly explicit.
For every populated field, cite the page, crop corner, and exact visible field
label or role in `source_label`.

- `project_name` is only a value explicitly labelled Project, Project Name, or
  an unambiguous local-language equivalent.
- `client` is only a value explicitly labelled Client, Owner, Customer, or an
  unambiguous equivalent.
- `design_partner` is only an explicitly labelled design office, architect
  office, designer, or issuing design firm. A file name, drawing number,
  generic logo, contractor, or manufacturer is never a partner by itself.
- `author` is only an explicitly credited person, for example Architect,
  Chief Architect, Drawn by, or Author. A firm is not an author.
- `document_date` is only a value explicitly labelled Date, Issue Date,
  Revision Date, or an unambiguous equivalent.

Do not infer a missing Client or Partner from a logo, file name, address,
telephone number, title-block position, drawing name, or document subject.
