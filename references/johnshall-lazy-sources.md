# Johnshall lazy.conf Source Notes

## Source

- Upstream project: `Johnshall/Shadowrocket-ADBlock-Rules-Forever`
- S1/S2 source file: `lazy.conf`
- URL: `https://johnshall.github.io/Shadowrocket-ADBlock-Rules-Forever/lazy.conf`

## Adopted Scope

- S1 extracts only the active `[Rule]` body.
- S1 keeps lazy `RULE-SET` entries for mature media, AI, overseas service, game, Apple, and China app routing.
- S1 drops lazy `FINAL` and writes its own `FINAL,PROXY`.
- S1 drops lazy `GEOIP,CN,DIRECT` and writes its own `GEOIP,CN,DIRECT` immediately before `FINAL,PROXY`.
- S2 extracts only lazy rules whose policy is `PROXY`.
- S2 uses lazy `PROXY` rules only as an overseas/unknown supplement after local test-site, account, and China-app guards.

## Excluded Scope

- Do not import lazy `[General]`; it includes China DNS, `fallback-dns-server = system`, and `ipv6 = true`, which conflict with current S1 assumptions.
- Do not import lazy `[Host]`; it uses `server:system` for Apple/iCloud, which can reintroduce system DNS.
- Do not import lazy `[URL Rewrite]` or `[MITM]`; they are outside the network-layer routing goal.
- Do not infer S1 `[Host]` from lazy `DIRECT` rules; `[Host]` remains limited to `references/china-local-domain-seeds.txt`.
- Do not import any lazy `DIRECT` rule into S2.
- Do not use `GEOIP,CN,DIRECT` in S2; unknown domains must fall through to `FINAL,PROXY`.

## Risk Notes

- S1 depends on remote `RULE-SET` loading in Shadowrocket. If those URLs fail to load on the phone, S1 may fall back to the local guards plus `FINAL,PROXY`.
- S2 also keeps lazy remote `PROXY` `RULE-SET` entries, but its China direct path does not depend on lazy.
- S0 remains the offline/minimal fallback because it does not keep remote `RULE-SET` dependencies.
- China DNS appearing for China-local seed domains is expected; China DNS appearing for overseas account, AI, unknown, or DNS random test domains is a failure signal.
- In S2, China apps can be slower when domains are missing from `references/china-local-domain-seeds.txt`; add precise China app domains instead of restoring lazy `DIRECT`.

## License

Johnshall upstream uses Creative Commons Attribution-ShareAlike 4.0 International License. If S1 or S2 is shared later, keep attribution and the same license note.
