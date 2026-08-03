# M2 GROBID and pypdf Spike

Date: 2026-08-01

Status: completed implementation spike

## Inputs

- GROBID image: `lfoppiano/grobid:0.8.2`
- Image digest: `sha256:cab12863cab26c818479dbcb6a4f09922ed6caeedfbbf59ef957f52d7195a85d`
- Service version/revision: `0.8.2` / `a91ee48`
- Client comparison source: `grobid-client-python` commit
  `161e0f45189c8592b2e2c58e9638cc6218bc75fb`
- Fixed PDF source: upstream client test resource
  `resources/test_pdf/0046d83a-edd6-4631-b57c-755cdcce8b7f.pdf`
- Fixed PDF size: `955532` bytes

The fixed PDF contains Springer copyright content. It was used temporarily for
the local transport spike and is not committed to RECA. Generated live TEI is
also temporary and is not a reusable corpus asset. RECA tests use synthetic PDF
and RECA-authored TEI fixtures instead.

## Runtime Findings

The pinned image failed on the current Docker Desktop/cgroup v2 environment
with a JDK container-metrics `NullPointerException`. Starting the image with
`JAVA_TOOL_OPTIONS=-XX:-UseContainerSupport` restored a stable service. RECA
Compose therefore records that compatibility option explicitly.

Measured on the local Competition Edition host:

| Check | Result |
| --- | --- |
| Cold service readiness | approximately 10.6 seconds |
| Idle container memory | approximately 3.33 GiB |
| Health response | approximately 0.006 seconds |
| First full-text parse | HTTP 200, 14.49 seconds, 113862 TEI bytes |
| Warm coordinate parse | HTTP 200, 2.97 seconds, 147825 TEI bytes |
| Limited-container readiness | PASS with 2 CPUs and 6 GiB; idle approximately 2.37 GiB |

The coordinate request included `p`, `s`, `head`, `figure`, `table`, `ref` and
`biblStruct`. The returned TEI did not contain page-break elements, but GROBID
`coords` values carried stable physical page numbers such as
`2,64.69,88.76,225.83,8.98`.

## Frozen Boundary

RECA uses a small synchronous `httpx` Adapter rather than installing
`grobid-client-python`. The upstream client is useful research for multipart
options, concurrency and failure behavior, but its directory crawling, batch
filesystem ownership and lossy output conversions do not match Artifact and
Job ownership.

```text
immutable PDF Artifact
-> bounded GROBID HTTP request
-> immutable application/tei+xml Artifact
-> RECA-owned secure TEI Converter
-> atomic DocumentPage and DocumentChunk replacement
```

GROBID TEI remains parser output, not formal evidence. The Converter accepts
only namespace-valid TEI with page-addressable coordinates, rejects unsafe or
malformed XML, and maps coordinates into internal metadata without creating
EvidenceSpan.

## Fallback

`pypdf==6.14.2` is the page-text fallback. It preserves physical page order and
page dimensions but creates no section path or coordinates. Every fallback
result is `PYPDF`, `LOW` confidence and has a ProcessingRun degradation record.
Encrypted, corrupt and scanned/no-text PDFs fail explicitly; M2 does not add
OCR. `defusedxml==0.7.1` protects the TEI XML boundary.

## Resource and Failure Limits

- single GROBID request timeout: 180 seconds;
- Adapter concurrency: 2;
- maximum TEI response: 25 MB;
- GROBID container: 2 CPUs and 6 GiB memory;
- Worker: 1 CPU, 1 GiB memory and 256 MB private temporary filesystem;
- retry eligibility: timeout, 502/503/504, connection and object-storage errors;
- nonretryable: rejected input, empty/malformed TEI, GROBID processing failure,
  encrypted/corrupt/scanned-no-text PDF.

Worker duplicate delivery is controlled by the existing Job claim lock. A
failed document Job does not change or block an independent document Job.

## Deferred Scope

- PDF.js display integration;
- OCR;
- LiteratureReference extraction;
- EvidenceSpan and coordinate validation against rendered PDF pages;
- full ten-field literature extraction and evidence analysis.
