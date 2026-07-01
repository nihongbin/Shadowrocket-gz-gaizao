# S2 Strict App Whitelist Source Notes

## Source

- Upstream project: `Johnshall/Shadowrocket-ADBlock-Rules-Forever`
- S2 source file: `lazy.conf`
- URL: `https://johnshall.github.io/Shadowrocket-ADBlock-Rules-Forever/lazy.conf`

## Adopted Scope

- S2 extracts only active lazy rules whose policy is `PROXY`.
- S2 keeps lazy `RULE-SET` entries for overseas apps, media, AI, games, and global services when those entries are `PROXY`.
- S2 uses `references/china-local-domain-seeds.txt` as the only source for China App `[Host]` and `DIRECT` rules.

## Excluded Scope

- Do not import lazy `[General]`, `[Host]`, `[URL Rewrite]`, or `[MITM]`.
- Do not import any lazy `DIRECT` rule.
- Do not import `GEOIP,CN,DIRECT`.
- Do not infer China App Host entries from lazy, Johnshall, `.cn`, or GEOIP.
- S2 intentionally excludes ambiguous cross-border domains from China direct handling: `bytedance.com`, `byteimg.com`, `snssdk.com`.

## Risk Notes

- S2 is stricter than S1. Unknown domains go to `FINAL,PROXY`.
- A China App may be slower if one of its domains is missing from the seed file.
- If a China App is slow or logs show `PROXY`, add the observed China-local domain to `references/china-local-domain-seeds.txt` after confirming it is not shared with overseas account traffic.
- Do not fix China App speed by restoring lazy `DIRECT` or `GEOIP,CN,DIRECT`; that would weaken the S2 safety boundary.

## License

Johnshall upstream uses Creative Commons Attribution-ShareAlike 4.0 International License. If S2 is shared later, keep attribution and the same license note.
