# PBIP, TMDL and PBIR

## PBIP

PBIP means **Power BI Project**. It is the project/folder representation used by Power BI Desktop
developer mode. Instead of treating a `.pbix` binary as the source-controlled artifact, a project
can contain separate semantic-model and report folders.

## TMDL

TMDL means **Tabular Model Definition Language**. It is a text representation of a tabular
semantic model. Typical files include:

```text
definition/
  database.tmdl
  model.tmdl
  relationships.tmdl
  tables/*.tmdl
  roles/*.tmdl
```

TMDL is suitable for Git because relationships, measures, partitions and security roles can be
reviewed as text diffs.

## PBIR

PBIR means **Power BI Enhanced Report Format**. It is the source-control-friendly representation
of a Power BI report. Instead of one opaque `report.json`/PBIX artifact, pages, visuals, bookmarks
and report metadata are represented in separate JSON files.

A PBIR report includes `definition.pbir`, which also contains its semantic-model reference.

V3 rewrites that reference in a build directory to point to the semantic model deployed in the
target environment, leaving the committed source unchanged.
