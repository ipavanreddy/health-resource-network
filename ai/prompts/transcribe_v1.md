# transcribe_v1: voice stock report audio → verbatim transcript

The attached audio is a short spoken stock report from a health worker at an Indian Primary Health Centre.
Expected language: {{language}} (it may be mixed with English medicine names).

## Rules
- Transcribe verbatim in the spoken language and script. Do not translate.
- Write numbers as digits.
- Do not add anything that was not said. If the audio is inaudible, return an empty transcript.

Return JSON matching the response schema only.
