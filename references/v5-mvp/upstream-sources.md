# V5 MVP Upstream Sources

## Johnshall

- Project: `Johnshall/Shadowrocket-ADBlock-Rules-Forever`
- Adopted scope: the mature `lazy.conf` rule ordering inherited by the verified V5 baseline.
- Excluded scope: upstream `[General]`, `[Host]`, `[URL Rewrite]`, and `[MITM]` sections.
- License: Creative Commons Attribution-ShareAlike 4.0 International.

## blackmatrix7

- Project: `blackmatrix7/ios_rule_script`
- Adopted scope: the Shadowrocket `RULE-SET` URLs listed in `remote-rulesets.csv`.
- Runtime note: these URLs currently point to the upstream `master` branch and can change without a local template commit.
- Maintenance boundary: an upstream change is not automatically considered verified for V5; phone behavior must be reviewed before changing local manifests.

## Project License

The public S5 template is distributed under CC BY-SA 4.0. Keep this attribution and the repository `LICENSE` notice when redistributing an adapted template.
