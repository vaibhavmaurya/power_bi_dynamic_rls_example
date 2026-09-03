# Bootstrap Existing Power BI Content

## Semantic model

Authenticate and run:

```bash
python scripts/export_semantic_model.py   --environment dev   --semantic-model-id <SEMANTIC_MODEL_GUID>
```

This retrieves the public TMDL definition into `semantic-model/`.

Then verify:

- `definition.pbism`
- `database.tmdl`
- `model.tmdl`
- table definitions
- relationships
- partitions
- measures
- roles

Run the RLS renderer after bootstrap so the governed role is restored.

## Report

```bash
python scripts/export_report.py   --environment dev   --report-id <REPORT_GUID>
```

This retrieves the PBIR definition into `report/`.

Do not start production CI/CD with the skeletal sample report bundled in the reference package.
Bootstrap your actual report.


## Fail-safe validation

The reference repository intentionally contains `BOOTSTRAP_REQUIRED.txt` markers.
CI validation fails while these markers exist. The export scripts remove them when the real
semantic model/report definitions are bootstrapped. This prevents accidental deployment of
the skeletal reference artifacts.
