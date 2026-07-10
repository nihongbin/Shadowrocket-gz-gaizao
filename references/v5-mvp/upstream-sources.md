# V5 MVP Upstream Sources

## Johnshall

- Project: `Johnshall/Shadowrocket-ADBlock-Rules-Forever`
- Adopted scope: the mature `lazy.conf` rule ordering inherited by the verified V5 baseline.
- Excluded scope: upstream `[General]`, `[Host]`, `[URL Rewrite]`, and `[MITM]` sections.
- License: Creative Commons Attribution-ShareAlike 4.0 International.

## blackmatrix7

- Project: `blackmatrix7/ios_rule_script`
- Adopted scope: the 33 Shadowrocket lists registered in `ruleset-sources.json`.
- Upstream license: GNU General Public License v2.0 (`GPL-2.0`).
- Redistribution: canonical snapshots are stored separately in `rulesets/v5/`; their license copy is `rulesets/v5/LICENSE.blackmatrix7-GPL-2.0.txt`.
- Runtime boundary: S5 references this repository's snapshots, not blackmatrix7 `master` directly.
- Maintenance boundary: daily monitoring compares effective rule semantics. Upstream changes require an Issue, explicit authorization, a tested PR, manual review, and manual merge.

## Project License

The public S5 template and project-authored manifests are distributed under CC BY-SA 4.0. The separately stored blackmatrix7 snapshot contents remain GPL-2.0. Keep both notices when redistributing the corresponding files.
