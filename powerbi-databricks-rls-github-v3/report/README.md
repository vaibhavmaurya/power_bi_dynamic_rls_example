# Power BI Report PBIR source

Bootstrap this directory from your existing Fabric/Power BI report:

```bash
python scripts/export_report.py --environment dev --report-id <REPORT_GUID>
```

A real PBIR report contains `definition.pbir` plus a `definition/` folder with report, page,
visual, bookmark and related JSON files. Do not hand-author a fake report for production.
