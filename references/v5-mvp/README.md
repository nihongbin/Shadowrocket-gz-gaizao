# V5 MVP Manifests

These files are the maintainable source of the public S5 V5 MVP template.
The verified private V5 config is used only as the bootstrap source; do not commit private nodes or proxy groups.

- `general.txt`: V5 `[General]` settings, without nodes or proxy groups.
- `test-site-proxy-rules.txt`: DNS/IP test sites forced to `PROXY`.
- `overseas-proxy-rules.txt`: overseas account, media, SDK, and common service `PROXY` rules.
- `ai-proxy-rules.txt`: AI and AI-adjacent `PROXY` rules.
- `china-direct-domains.txt`: China App / China service domains allowed to `DIRECT`.
- `china-host-dns.csv`: China Host DNS mapping. Must contain every China DIRECT domain.
- `ruleset-sources.json`: authoritative upstream source, policy, governed URL, semantic hash, rule count, and license registry.
- `remote-rulesets.csv`: generated public `RULE-SET` URL view used by the S5 builder.
- `lazy-body-rules.txt`: full V5 lazy body rule order used by the generated template.
- `candidate-observations.md`: excluded or watch-only items.
- `upstream-sources.md`: upstream attribution, license, and runtime dependency notes.

Build the public template with:

```powershell
python scripts\build-v5-mvp-template.py
```

Verify the public template and local V5 baseline with:

```powershell
python scripts\build-v5-mvp-template.py --check
python scripts\manage-v5-rulesets.py validate
python scripts\check-v5-consistency.py
```

Do not edit snapshot content or hashes by hand. Upstream changes are monitored semantically and only enter a review PR after explicit authorization.
