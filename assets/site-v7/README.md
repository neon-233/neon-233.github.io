# Jisuan V7 bilingual site

V7 adds paired Chinese and English editions of the homepage, research guide,
course overview, and all six course modules. The default homepage is Chinese.
The language switch preserves the current section. Both course languages share
completion IDs and local learning progress.

All English text is built into static HTML. Visitors do not call a translation
service. Navigation, search, diagrams, parameter descriptions, interactive
messages, and example-file instructions are localized. Executable input values
and commands are retained. English examples have their own directory and ZIP.

`templates/` holds the Chinese V7 source pages copied from V6.
`translations/en.json` holds the base translation catalog. The reviewed
`overrides.json`, `headings.json`, `interface.json`, and `parameters-en.json`
provide editorial and scientific terminology corrections. The builder merges
these catalogs, regenerates the English full-text index from translated lesson
content, and emits both language editions and download archives.

From the repository root, before V7 is frozen:

```text
python assets/site-v7/build_bilingual.py
```

The builder refuses to overwrite a V7 recorded as frozen in the local release
registry. Subsequent updates must use a new version, including its own HTML and
changed assets. V1–V6 pages and their referenced assets remain unchanged.

The science and example scope remain those of the source V6 tutorials. This
language release does not represent new VASP numerical validation. Paper figures
are reused unchanged with their existing attribution and licenses.
