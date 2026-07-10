# V5 Governed RULE-SET Snapshots

This directory freezes the 33 blackmatrix7 Shadowrocket lists used by public S5.

- Source identity, policy, semantic hash, and rule count are registered in `references/v5-mvp/ruleset-sources.json`.
- Snapshot rules are normalized by removing comments, blanks, duplicates, and order-only differences.
- No runtime timestamp is stored.
- S5 reads these snapshots instead of tracking upstream `master` at runtime.
- Upstream semantic changes require a GitHub Issue, explicit authorization, a tested PR, and manual merge.

The snapshot contents are derived from `blackmatrix7/ios_rule_script` under GPL-2.0. See `LICENSE.blackmatrix7-GPL-2.0.txt`. Project-authored configuration and documentation have their own CC BY-SA 4.0 notice at the repository root.
