# Detection V8.4.29 Ada checkpoint

The owner accepted the Ada fix on 2026-11-13 after four Adda repeats.
Haiku 4.5 again classifies and describes Islands in Ada Discovery.
Sonnet 4.6 receives those descriptions and groups the fixed Views using
the V8.4.8 citation contract. Each successful run used the same saved
PDF and OCR with fresh provider replies.

| Benchmark | Run | Detection time | Outcome |
| --- | --- | ---: | --- |
| Adda 1 | `run_943e832d05074310baccbcc16745aa70` | 39.27 s | 01/04/06/08 and 02/03/05/07 |
| Adda 2 | `run_6fb60a33b6f34d84b04bb0438a7a26e2` | 40.17 s | Same exact partition |
| Adda 3 | `run_be30ba54f20645739f91e30eecfe5837` | 47.82 s | Same exact partition |
| Adda 4 | `run_bd3cadaad25840829fd0b92ea3e752d0` | 42.12 s | Same exact partition |
| Lev1 | `run_1205c1e09d4e43e398a600b263a76c87` | 38.38 s | One object with all six Views |
| Lev2 | `run_3013e57350b449d7b47cd368fc5acd7d` | 32.91 s | One kitchen with all four Views and its render |

All eight Adda bounding boxes matched across the four repeats. The
runtime passed 193 focused tests. Offline replay matched all 18 saved
request hashes, exact memberships, evidence regions, and Lev2 render
attachment across the six runs.

Runtime commit `420a7e4d61cfc3dca740b820fe884a3a91bb7e01`.
Checkpoint tag `detection-v8.4.29-ada-haiku45-checkpoint-2026-11-13`.
Rollback reference `a420198d8d367224c487da260a1e40bf4eac1c08`.

Private replay archive
`backups/detection-v8.4.29-ada-haiku45-checkpoint-2026-11-13/`
contains the PDFs, OCR, replies, evidence regions, Git bundle,
restore instructions, and checksums.

## Production release

GitHub main advanced to `534abf4df1f1c78b138aa07c1f493548c2ad41b6`
on 2026-11-13. Railway deployment
`28884ea7-c138-4cd5-adbf-6584f5e3cc14` reported success for that commit.
The Cloudflare wrapper and Streamlit Core both reported
`estimation-v9.6-detection-v8.4.29`. Core health returned HTTP 200.
The next authenticated Adda Upload will verify Detection and the
Estimation result in Objects.

## Return to Estimation

Production Adda `run_3aa7bc04987e442fb8c2fdf691e22fee` gave V01 to
the straight object. Estimation 9.6 Parts Check ran on that 5+3
partition. The resulting worksheet and pricing cannot verify the
correct two-object estimate. The saved correct-input pricing replay
accounts for 149 identified part rows. Fresh recognition can change
the row count, so compare source coverage, dimensions, quantities and
costs.

The owner will upload Adda on this release and start Estimation. First
verify the two exact File Review groups. Then reconcile each Parts
Check report with Material Demand and the allocated Material Engine
costs. Verify units, Company Catalog or Israel Reference matches,
Assumption Fallback and the amount displayed in Objects. A Review
status can accompany a provisional amount when all requirements
have prices and findings remain open.
