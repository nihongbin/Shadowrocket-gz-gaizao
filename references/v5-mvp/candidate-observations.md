# V5 MVP Candidate Observations

- Do not add `itdog.cn`, `ip.cn`, DNS leak test sites, or IP lookup sites to China DIRECT.
- Do not use DNS B Google fallback as a V5 baseline; the fallback was not triggered in the test logs.
- Do not use QUIC allow as a V5 baseline; it did not prove a speed improvement.
- If an overseas App is slow only on first open and fast on second open, prefer network/node/time-window checks before rules.
- If a new China App domain is added to DIRECT, add the same root domain to `china-host-dns.csv`.
