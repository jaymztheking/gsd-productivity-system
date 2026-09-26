---
id: doc-001
title: DNS Pre-Migration Snapshot - medaughsolutions.com
type: specification
created_date: '2026-09-26 02:36'
updated_date: '2026-09-26 03:12'
---
## Purpose

Pre-migration snapshot of the `medaughsolutions.com` DNS zone, captured before moving nameservers to Cloudflare (TASK-002). This is the reference for verifying that every record survives the move, and the source of truth for rollback.

**Captured:** 2026-09-25
**Method:** authoritative `dig` against `dns1.registrar-servers.com`, not a recursive resolver, so these are the zone contents rather than cached answers.
**SOA at capture:** `dns1.registrar-servers.com. hostmaster.registrar-servers.com. 1774308943 43200 3600 604800 3601`
**Zone transfer (AXFR):** refused, as expected — records below were enumerated by type and by probing known hostnames.

## Records that must exist in Cloudflare after migration (10)

Ten records. An earlier recursive-resolver pass missed three of them — the `www` CNAME, the `autoconfig` CNAME, and the `_autodiscover._tcp` SRV — and undercounted the rest; all ten are listed below and this table is the authority.

| Name | Type | TTL | Value | Purpose |
|---|---|---|---|---|
| `@` | A | 1800 | `162.255.119.122` | Namecheap parking page |
| `@` | MX | 1800 | `10 mx1.privateemail.com.` | Inbound mail |
| `@` | MX | 1800 | `10 mx2.privateemail.com.` | Inbound mail |
| `@` | TXT | 1800 | `v=spf1 include:spf.privateemail.com ~all` | SPF, anti-spoofing |
| `default._domainkey` | TXT | 1800 | see below | DKIM signing key |
| `www` | CNAME | 1800 | `parkingpage.namecheap.com.` | Namecheap parking page |
| `mail` | CNAME | 1800 | `privateemail.com.` | Webmail access |
| `autodiscover` | CNAME | 1800 | `privateemail.com.` | Outlook/mail client autoconfig |
| `autoconfig` | CNAME | 1800 | `privateemail.com.` | Thunderbird/mail client autoconfig |
| `_autodiscover._tcp` | SRV | 1800 | `0 0 443 privateemail.com.` | Mail client autodiscovery |

## DKIM record (the fragile one)

Stored at Namecheap as two quoted strings that DNS concatenates into one value. Cloudflare must end up with the identical concatenated result. Importers sometimes mangle this; broken DKIM does not bounce mail, it silently sends it to recipient spam folders.

**As served (two strings):**

```
"v=DKIM1;k=rsa;p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAuK8LDo5FRCrtNBt+P0HZf7mRiAFy1PSEZlEyYlFgt6VAUKyFclGnX1wYS8ArQALGID/2lN9NHNoY2ICZ8e2zGAr31C9OGuinfAgKNJsMd6ugkXS1Mzsr1adSmNPT2VDJmr1GTQeAL6CTFIQvI5nQ0X6ygPuTdlTjKfKAkfdZqYO7j3o4N7RjBzxE/zm9iUjCEmD" "6fLEXk2s9YJJv6a7Fi1QbZLi0dNm74LbhYrMz6fV7TJyWUtI8EcrU8Jnep1jD17MOvFk4PvlVQy1imEIcMLbK91wSqDYMuVH/+WZYzjHc41YwOaBmRUKDk69pqd0x7vdJCTZ0d3aNUE1u2tLpXQIDAQAB"
```

**Concatenated value that must match after migration:**

```
v=DKIM1;k=rsa;p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAuK8LDo5FRCrtNBt+P0HZf7mRiAFy1PSEZlEyYlFgt6VAUKyFclGnX1wYS8ArQALGID/2lN9NHNoY2ICZ8e2zGAr31C9OGuinfAgKNJsMd6ugkXS1Mzsr1adSmNPT2VDJmr1GTQeAL6CTFIQvI5nQ0X6ygPuTdlTjKfKAkfdZqYO7j3o4N7RjBzxE/zm9iUjCEmD6fLEXk2s9YJJv6a7Fi1QbZLi0dNm74LbhYrMz6fV7TJyWUtI8EcrU8Jnep1jD17MOvFk4PvlVQy1imEIcMLbK91wSqDYMuVH/+WZYzjHc41YwOaBmRUKDk69pqd0x7vdJCTZ0d3aNUE1u2tLpXQIDAQAB
```

**SHA-256 of the concatenated value** (compare instead of eyeballing):

```
9581ac785fdf24492f329137f1ac611b329c20f6691c8af88b7db19b1d3fc0de
```

**SHA-256 of the public key portion alone (`p=` onward):**

```
ef0c12ee5b511649be2e6a25b86687bf2eb77533ef017a4c3d42c19fbd073596
```

## Confirmed absent at capture

These carry no migration risk, and their absence is itself useful:

- **DNSSEC / DS records** — none. Removes the worst migration failure mode: DS records left active while nameservers change break resolution of the entire domain until disabled.
- **DMARC** (`_dmarc` TXT) — none.
- **AAAA** (IPv6) — none.
- **CAA** — none, so nothing restricts which authority may issue certificates for the domain. Cloudflare can issue freely.
- **`_domainconnect`, `_acme-challenge`** — none.

## Namecheap DNS-dependent services (AC #8)

The apex `A` record and the `www` CNAME both point at Namecheap parking infrastructure (`162.255.119.122`, `parkingpage.namecheap.com`), so the only thing currently served on this domain over HTTP is a parked placeholder page. There is no real website to preserve.

`parkingpage.namecheap.com` remains resolvable as a CNAME target from any DNS provider, so the record can be carried across unchanged. Whether the parking page still renders depends on Namecheap serving it by `Host` header; if it stops, nothing of value is lost.

Still to confirm in the Namecheap control panel, since none of it is visible from DNS alone: whether **Email Forwarding**, **URL/domain redirect**, or **Dynamic DNS** is enabled. All three are implemented by Namecheap inside their own DNS and stop working the moment nameservers move.

## Rollback procedure (AC #9)

Nothing is destructive until the nameservers are switched, and the switch is reversible.

1. In the Namecheap dashboard: **Domain List → Manage → Nameservers**, set back to **Namecheap BasicDNS**, or enter `dns1.registrar-servers.com` and `dns2.registrar-servers.com` explicitly.
2. Namecheap retains the original zone, so the records in this document return without re-entry. Verify anyway against the table above.
3. **Propagation:** the parent `.com` delegation NS TTL is 1800s (30 min), so most resolvers pick up the change within about 30 minutes; allow up to a few hours for stragglers holding longer-cached delegations.
4. Verify rollback took effect:

```bash
dig +short NS medaughsolutions.com          # expect dns1/dns2.registrar-servers.com
dig +short MX medaughsolutions.com          # expect mx1/mx2.privateemail.com
dig +short TXT default._domainkey.medaughsolutions.com
```

**Mail-specific note:** inbound mail is resilient to a botched cutover. Sending servers retry for days when MX lookups fail, so mail queues rather than bounces and is delivered once records are correct. The unrecoverable risk is not lost mail, it is a wrong-but-valid DKIM record quietly degrading deliverability, which is why the checksums above exist.
