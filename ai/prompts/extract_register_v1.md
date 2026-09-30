# extract_register_v1: handwritten stock register photo → table rows

The attached image is a photo of a handwritten stock register page from an Indian Primary Health Centre.

## Rules
- Extract every table row: medicine, opening balance, received, issued, closing balance.
- Mark any cell you cannot read with certainty as null and list its name in `illegible_cells`.
  NEVER guess a number. An illegible cell is better than a wrong number.
- Do not compute missing values from other columns; report only what is written.
- Match each medicine to one `drug_code` from the medicine master below, with `match_confidence`.
  If there is no confident match (< 0.5), set `drug_code` to null and add the text to `unrecognised`.
- `register_date`: the date written on the page, as written, or null.
- Always set `requires_confirmation` to true.

## Medicine master (JSON)
{{medicine_master}}

Return JSON matching the response schema only.
