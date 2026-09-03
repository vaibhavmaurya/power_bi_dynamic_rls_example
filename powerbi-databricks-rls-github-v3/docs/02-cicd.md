# Optional CI/CD

V4 CI/CD only industrializes the semantic model/RLS:

`GitHub -> TMDL validation -> OIDC -> Fabric semantic-model API -> Power BI refresh -> RLS test`

PBIR/report deployment and Fabric Connection lifecycle are intentionally outside V4. If PBIX publishing is manual, this CI/CD layer is optional.
