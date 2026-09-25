---
id: TASK-002
title: Migrate medaughsolutions.com DNS to Cloudflare without breaking email
status: To Do
assignee: []
created_date: '2026-09-25 18:09'
labels:
  - networking
  - dns
  - cloudflare
dependencies: []
references:
  - README.md
priority: high
type: chore
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
GSD needs a public hostname so capture and site access work away from the home network. Cloudflare Tunnel requires the zone to be served by Cloudflare nameservers; the partial CNAME setup that would avoid this is Business-plan only (~200 USD/mo), so full nameserver migration is the only viable path.

This changes the DNS provider only. The domain stays registered at Namecheap and renews there, and the Namecheap Private Email subscription is billed separately and is not cancelled by this. A nameserver change is not a registrar transfer: no 60-day lock, no fee, reversible at any time by pointing back at dns1/dns2.registrar-servers.com.

The real risk is not billing, it is misconfiguration of mail. If records do not land correctly on the Cloudflare side, Private Email keeps billing while mail silently degrades. Broken DKIM in particular does not bounce: it routes legitimate outbound mail to recipient spam folders, which can go unnoticed for weeks.

Live records as observed on 2026-09-25, all of which must survive the move:

- MX 10 mx1.privateemail.com and 10 mx2.privateemail.com (inbound mail)
- TXT @ `v=spf1 include:spf.privateemail.com ~all` (anti-spoofing)
- TXT default._domainkey (DKIM, roughly 400 characters, stored as two quoted strings that concatenate)
- CNAME autodiscover -> privateemail.com (mail client autoconfiguration)
- CNAME mail -> privateemail.com
- A @ -> 162.255.119.122 (Namecheap parking/hosting)

Favourable conditions confirmed at the same time: DNSSEC is off, which avoids the worst migration failure mode (leaving DS records active breaks resolution entirely until disabled), and there is no DMARC record to preserve. The subdomain gsd.medaughsolutions.com is currently unused.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A complete export or screenshot of the existing Namecheap DNS zone is captured and stored before any change is made
- [ ] #2 All six live records (2x MX, SPF TXT, DKIM TXT, autodiscover CNAME, mail CNAME, root A) are recreated in Cloudflare and verified against the pre-migration export
- [ ] #3 The DKIM TXT value is verified character-for-character after import, with the concatenated two-part string matching the original exactly
- [ ] #4 Nameservers are switched at Namecheap to the Cloudflare-assigned pair only after record verification passes
- [ ] #5 Inbound mail is verified working after propagation by sending a test message from an external address and confirming receipt
- [ ] #6 Outbound mail is verified passing both SPF and DKIM after propagation, checked via received-message headers or an equivalent mail test tool
- [ ] #7 DNSSEC is confirmed to remain off during the switchover, and the root A record still serves what it served before
- [ ] #8 Confirmed whether any Namecheap DNS-dependent free service is in use (email forwarding, URL redirect, dynamic DNS); any that is has a documented replacement or is confirmed unused
- [ ] #9 A rollback procedure is documented: reverting nameservers to dns1/dns2.registrar-servers.com and expected propagation time
<!-- AC:END -->
