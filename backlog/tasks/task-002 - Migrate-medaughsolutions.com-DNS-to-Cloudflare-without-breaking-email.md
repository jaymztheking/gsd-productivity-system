---
id: TASK-002
title: Migrate medaughsolutions.com DNS to Cloudflare without breaking email
status: Done
assignee:
  - '@James'
created_date: '2026-09-25 18:09'
updated_date: '2026-09-26 03:45'
labels:
  - networking
  - dns
  - cloudflare
dependencies: []
references:
  - README.md
documentation:
  - >-
    backlog/docs/dns/doc-001 -
    DNS-Pre-Migration-Snapshot-medaughsolutions.com.md
priority: high
type: chore
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
GSD needs a public hostname so capture and site access work away from the home network. Cloudflare Tunnel requires the zone to be served by Cloudflare nameservers; the partial CNAME setup that would avoid this is Business-plan only (~200 USD/mo), so full nameserver migration is the only viable path.

This changes the DNS provider only. The domain stays registered at Namecheap and renews there, and the Namecheap Private Email subscription is billed separately and is not cancelled by this. A nameserver change is not a registrar transfer: no 60-day lock, no fee, reversible at any time by pointing back at dns1/dns2.registrar-servers.com. Connecting the domain to Cloudflare is the correct action; transferring the domain to Cloudflare Registrar is a different operation and is explicitly not wanted.

The real risk is not billing, it is misconfiguration of mail. If records do not land correctly on the Cloudflare side, Private Email keeps billing while mail silently degrades. Broken DKIM in particular does not bounce: it routes legitimate outbound mail to recipient spam folders, which can go unnoticed for weeks.

**Record inventory: ten records.** The full authoritative zone capture is recorded in doc-001, taken with `dig` against dns1.registrar-servers.com rather than a recursive resolver. An initial recursive pass during task creation missed three records entirely — the `www` CNAME to parkingpage.namecheap.com, the `autoconfig` CNAME to privateemail.com, and the `_autodiscover._tcp` SRV record — and stated the total incorrectly. Two of the three missed records are mail-client autoconfiguration, so migrating the original list would have broken mail client setup while leaving mail flow itself intact, which is exactly the kind of partial failure that is hard to attribute weeks later. Treat the doc-001 table as the authority for what must exist, not any list in this description.

Favourable conditions confirmed at capture: DNSSEC is off, which avoids the worst migration failure mode (DS records left active while nameservers change break resolution of the whole domain until disabled); there is no DMARC record to preserve; and no CAA records restrict certificate issuance, so Cloudflare can issue freely. The subdomain gsd.medaughsolutions.com is unused.

The apex A record and www CNAME both point at Namecheap parking infrastructure, so no real website is at risk. Whether Namecheap Email Forwarding, URL redirect, or Dynamic DNS is enabled cannot be determined from DNS and must be checked in the Namecheap control panel.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A complete authoritative capture of the existing Namecheap DNS zone is stored before any change is made, including the exact DKIM value
- [x] #2 All ten live records (root A, 2x MX, SPF TXT, DKIM TXT, www CNAME, mail CNAME, autodiscover CNAME, autoconfig CNAME, _autodiscover._tcp SRV) are recreated in Cloudflare and verified against doc-001
- [x] #3 The DKIM TXT value is verified after import by comparing the SHA-256 of the concatenated value against the checksum recorded in doc-001, not by visual inspection
- [x] #4 Nameservers are switched at Namecheap to the Cloudflare-assigned pair only after record verification passes
- [x] #5 Inbound mail is verified working after propagation by sending a test message from an external address and confirming receipt
- [x] #6 Outbound mail is verified passing both SPF and DKIM after propagation, checked via received-message headers or an equivalent mail test tool
- [x] #7 DNSSEC is confirmed to remain off during the switchover, and the root A record still serves what it served before
- [x] #8 The Namecheap control panel is checked for Email Forwarding, URL redirect, and Dynamic DNS; any in use has a documented replacement or is confirmed unused
- [x] #9 A rollback procedure is documented, covering nameserver reversion and expected propagation time
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. DONE — Authoritative pre-migration capture stored in doc-001: all nine records, the DKIM value verbatim, SHA-256 checksums of the concatenated DKIM value and of its public-key portion, confirmed-absent record types, and the rollback procedure. Captured via dig against dns1.registrar-servers.com rather than a recursive resolver, which is what surfaced the three records the task originally missed.

2. Namecheap panel audit (AC #8). In the Namecheap dashboard check whether Email Forwarding, URL/domain redirect, or Dynamic DNS is enabled. None of these is visible from DNS, and all three are implemented inside Namecheap DNS and stop working when nameservers move. Record the finding either way.

3. OPTIONAL, recommended — lower record TTLs at Namecheap to 300s and wait 30 minutes before proceeding. Does not speed up the nameserver switch itself (the parent .com delegation TTL governs that) but it shortens how long a rollback takes to take effect.

4. Create a free Cloudflare account and add medaughsolutions.com as a zone on the Free plan. Cloudflare scans the existing zone and pre-populates what it finds. Do NOT change nameservers at this stage; Namecheap remains authoritative and live throughout steps 4 to 6.

5. Reconcile the imported records against the doc-001 table. Add anything missing, correct anything altered, delete anything invented. Set proxy status deliberately: mail, autodiscover, and autoconfig must be DNS-only (grey cloud), because proxying them routes traffic through Cloudflare HTTP/HTTPS and breaks IMAP/SMTP/autodiscovery. MX and SRV records are never proxied. Leave the apex A and www as DNS-only for now to keep this step a pure like-for-like migration; revisit when TASK-004 introduces the tunnel.

6. Verify the zone BEFORE delegating — this is the step that removes most of the risk. Cloudflare assigns two nameservers and will answer authoritatively for the zone as soon as records exist, even though the world is still being served by Namecheap. Query the assigned Cloudflare nameservers directly and diff against doc-001, including a DKIM checksum comparison. A mistake caught here costs nothing because no live traffic is using those answers yet.

7. Switch nameservers at Namecheap to the Cloudflare-assigned pair (AC #4), only once step 6 is clean. Confirm DNSSEC remains off.

8. Confirm propagation, then re-verify all nine records against doc-001 through both the authoritative path and a public recursive resolver.

9. Mail verification (AC #5, #6), the acceptance gate for this task. Inbound: send from an external address and confirm receipt. Outbound: send to an external mailbox and inspect Authentication-Results headers for spf=pass and dkim=pass, or use an equivalent mail-test service. Inbound mail is resilient to a botched cutover because sending servers retry for days, so mail queues rather than bounces; a wrong-but-valid DKIM record is the failure that does real damage, hence the checksum comparison rather than eyeballing.

10. Confirm the apex A still serves what it served before (AC #7), record results in implementation notes, then finalize per backlog instructions task-finalization.

Division of labour: steps 2, 4, 5 and 7 are dashboard work only James can do. Steps 6, 8 and parts of 9 and 10 are dig-based verification that can be run and interpreted here.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Pre-migration capture complete (doc-001). Authoritative dig against dns1.registrar-servers.com found TEN records; the task was created from a recursive-resolver pass that missed the www CNAME, the autoconfig CNAME, and the _autodiscover._tcp SRV, and stated the count wrong. Description, AC #2 and doc-001 corrected to ten. Record contents in doc-001 were correct throughout; only the headline count was wrong.

DKIM stored verbatim (408 chars) with SHA-256 checksums of both the full concatenated value and the p= portion, so post-import verification is a hash comparison rather than visual inspection.

Confirmed absent and therefore not migration risks: DNSSEC/DS, DMARC, AAAA, CAA, _domainconnect, _acme-challenge.

Cloudflare data-entry notes surfaced while working through the records: MX priority is 10 for BOTH mx1 and mx2 (equal-priority peers, not primary/backup); the SRV is priority 0, weight 0, port 443; DKIM must be pasted unquoted as one continuous line with the name as default._domainkey rather than the FQDN; TTL Auto (300s) is correct and preferable to reproducing the old 1800s values.

PRE-DELEGATION VERIFICATION PASSED (plan step 6), 2026-09-25. Cloudflare zone validated on the wire while Namecheap is still authoritative, so any error found here was free to correct.

Assigned Cloudflare nameservers: vera.ns.cloudflare.com, yahir.ns.cloudflare.com. Zone mode: Full (correct; Partial/CNAME setup is Business-plan only).

All 10 records queried directly against vera.ns.cloudflare.com and diffed against dns1.registrar-servers.com: 9 checks, 0 failures (the MX check covers both records). A, both MX with priority 10, SPF TXT, DKIM TXT, www/mail/autodiscover/autoconfig CNAMEs, and the _autodiscover._tcp SRV all match the pre-migration values.

Both Cloudflare nameservers serve an identical zone (matching hash 8d71396d00aa6b25), so there is no partial-propagation risk between them.

DKIM verified twice by SHA-256 rather than inspection: once as pasted into the dashboard, once as served on the wire. Both 9581ac785fdf24492f329137f1ac611b329c20f6691c8af88b7db19b1d3fc0de, matching doc-001.

DNSSEC confirmed still off at the .com parent (no DS records), so the delegation change carries no DNSSEC breakage risk. All records are DNS-only (grey cloud), which is required for mail, autodiscover and autoconfig since proxying would route them through the HTTP layer and break IMAP/SMTP and client autodiscovery.

Delegation at time of writing still points at dns1/dns2.registrar-servers.com. Nameserver switch (AC #4) not yet performed. AC #8 (Namecheap Email Forwarding / URL redirect / Dynamic DNS audit) still outstanding.

POST-DELEGATION VERIFICATION PASSED, 2026-09-25. Nameservers switched to vera/yahir.ns.cloudflare.com.

Delegation confirmed at the .com parent (a.gtld-servers.net returns the Cloudflare pair) and seen by 1.1.1.1, 8.8.8.8 and 9.9.9.9. The local resolver briefly still returned the Namecheap pair from cache, which is expected TTL expiry and not a fault.

All 10 records re-verified end to end through public resolver 1.1.1.1: 9 checks, 0 failures. DKIM re-hashed through the new delegation at 408 chars, SHA-256 9581ac785fdf24492f329137f1ac611b329c20f6691c8af88b7db19b1d3fc0de, matching doc-001 for the third time (dashboard paste, authoritative wire pre-flip, public resolver post-flip). DNSSEC confirmed still off at the parent.

AC #8 partial findings from the Namecheap panel: Email Forwarding is NOT in use. Namecheap now shows the Redirect Email feature as unavailable with the notice that nameservers must be returned to Namecheap default to use it, and mail is served by Namecheap Private Email (1 of 1 mailbox in use, subscription valid Mar 23 2026 to Apr 23 2027) which is mutually exclusive with Email Forwarding. Private Email confirmed unaffected by the DNS move, as predicted. Dynamic DNS state still to be confirmed on the Advanced DNS tab.

Remaining: AC #5 inbound mail test, AC #6 outbound SPF/DKIM test, AC #8 Dynamic DNS confirmation.

AC #6 PASSED, 2026-09-26. Outbound mail verified through Gmail after the delegation change.

Authentication-Results from mx.google.com: dkim=pass header.i=@medaughsolutions.com header.s=default header.b=VeT8QQDy; spf=pass (198.54.127.74 designated permitted sender) smtp.mailfrom=james@medaughsolutions.com.

The selector is header.s=default, so Gmail validated against the default._domainkey record migrated in this task. Signature b=VeT8QQDy verified against the published 408-char key, which is cryptographic proof the DKIM record is functionally correct rather than merely textually identical to the capture. SPF passed via include:spf.privateemail.com. Message routed through smtp.privateemail.com over TLSv1.3, confirming Private Email is unaffected by the DNS move.

Remaining: AC #5 inbound mail test, AC #8 Dynamic DNS toggle state.

AC #8 COMPLETE, 2026-09-26. All three Namecheap DNS-dependent services confirmed not in use.

Email Forwarding: not in use. Namecheap reports the Redirect Email feature as unavailable under Custom DNS, and mail is served by Private Email, which is mutually exclusive with forwarding.

URL/domain redirect: not in use. The apex A record pointed at the Namecheap parking IP 162.255.119.122 and www at parkingpage.namecheap.com, both default parking rather than a configured redirect. Redirect management is likewise gated behind BasicDNS.

Dynamic DNS: not in use. The Advanced DNS tab no longer lists a Dynamic DNS section at all, since Namecheap hides it under Custom DNS because it cannot function without their nameservers. Corroborated by the pre-migration capture, which probed www, mail, autodiscover, autoconfig, ftp, cpanel, webmail, smtp, imap, pop and gsd and found no dynamically-updated host; the only A record was the static parking IP. A DDNS configuration would have left a residential-IP record behind.

No replacement work is required for any of the three. Remaining: AC #5 inbound mail test.

AC #5 PASSED, 2026-09-26. Inbound mail from Gmail to james@medaughsolutions.com delivered to the Private Email INBOX. The delay was greylisting: Private Email temporarily rejects a first attempt from an unfamiliar sender and accepts the retry, which presents exactly as a missing message. No bounce was ever issued, consistent with a queued rather than rejected message. Worth noting the MX records were byte-identical before and after the migration, so inbound routing was never altered by this work.

FINAL VERIFICATION 2026-09-26 03:45 UTC: delegation at the .com parent returns vera/yahir.ns.cloudflare.com; 18/18 record checks passed covering all 10 records across two independent public resolvers (1.1.1.1 and 8.8.8.8); DKIM re-hashed at 408 chars matching doc-001; no DS records at the parent so DNSSEC remains off; root A still 162.255.119.122 as before.

DKIM was verified four separate ways across the task: as pasted into the dashboard, on the authoritative wire before delegation, through a public resolver after delegation, and cryptographically by Gmail validating signature b=VeT8QQDy against selector default.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Moved medaughsolutions.com DNS from Namecheap BasicDNS to Cloudflare (vera/yahir.ns.cloudflare.com, Free plan, Full setup) with no loss of mail service, providing the zone control that TASK-004 needs to publish gsd.medaughsolutions.com through Cloudflare Tunnel. Registration remains at Namecheap and Private Email is unaffected.

All 10 records were migrated: root A, both MX at priority 10, SPF TXT, DKIM TXT, four CNAMEs (www, mail, autodiscover, autoconfig) and the _autodiscover._tcp SRV. An authoritative dig capture taken before any change (doc-001) found three records that the recursive-resolver pass at task creation had missed — the www CNAME, the autoconfig CNAME, and the SRV — two of which are mail-client autoconfiguration, so migrating the original list would have broken client setup while leaving mail flow intact.

Verified by: 18/18 record checks across two independent public resolvers after delegation; the zone validated against Cloudflare nameservers BEFORE delegating, while Namecheap was still authoritative, so errors could be corrected at zero cost; DKIM confirmed four ways, ending with Gmail cryptographically validating signature b=VeT8QQDy against selector default; outbound mail showing spf=pass and dkim=pass in Gmail Authentication-Results; and inbound mail from Gmail delivered to the Private Email INBOX after an initial greylisting delay. DNSSEC confirmed off at the parent throughout, and all records left DNS-only since proxying the mail hostnames would break IMAP/SMTP and autodiscovery.

Namecheap Email Forwarding, URL redirect and Dynamic DNS all confirmed unused, so no replacement work was needed. Rollback procedure documented in doc-001.
<!-- SECTION:FINAL_SUMMARY:END -->
