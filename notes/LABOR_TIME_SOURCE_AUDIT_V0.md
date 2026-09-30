# Labor Time Source Audit v0

Status: research ledger. No source below is production-ready without an
operation-to-unit mapping and applicability review.

## Research rule

The work catalog is editable. New evidence may split, merge, add, re-scope, or
deprecate an operation. Every change must name the source, the affected recipe,
the formula effect, and the migration impact before the catalog is changed.

## Current evidence

| Source | Scope | Useful evidence | Limitation | Proposed use |
| --- | --- | --- | --- | --- |
| Figurić, 1975, `Standard operation time system on some machines for furniture manufacture`, https://drvnaindustrija.com/archive/volume-1975-issue-9-10/standard-operation-time-system-on-some-machines-for-furniture-manufacture/ | Furniture-machine operations | States that standards were built from observations and simple functions of operation inputs. | Historic machinery. | Methodology and formula structure only. |
| Gawroński et al., 2012, `Optimization of setup times in the furniture industry`, https://link.springer.com/article/10.1007/s10479-012-1233-z | Made-to-order solid-wood cabinet doors, 24 variants. | Setup is a finite sum of tool, fixture, and adjustment activities; setup is sequence dependent. | Schedules a factory, not quote-time norms. | Require shared work sessions and component-level setup records. |
| `Machining Operations for Components in Kitchen Furniture`, 2019, https://www.sciencedirect.com/science/article/pii/S2351978919310534 | Custom kitchen components in agglomerate, plywood, and MDF. | Separating cutting and later machining lowered total machining time by 38% in the studied factory. | Relative outcome, not transferable minute coefficients. | Preserve separate routing recipes for cutting and machining. |
| Wiranata et al., 2023, `Pengukuran waktu standar proses kerja mesin bandsaw dan cross cut`, https://ojs.uajy.ac.id/index.php/JTIMR/article/view/7034 | Raw solid-timber preparation for garden furniture. | 18 observed work elements, motion study, standard time 4.92 minutes for the study's defined unit. | The public abstract does not define the exact unit or machine context sufficiently. | Inspect PDF before using any numeric value. |
| Yücel and Dilik, 2021, `Time study and an example of application in wood urban furniture`, https://dergipark.org.tr/tr/pub/mamad/article/940285 | Wood urban-furniture assembly. | Ten observations per stage, 95% confidence and 5% error margin; reported product-specific assembly standards. | Picnic table and bench are not cabinet or custom interior furniture. | Validate time-study method only, not transfer minutes. |
| `Modeling and Simulation of Cabinet Manufacturing Processes`, 2018, https://www.msc-les.org/proceedings/mas/2018/MAS2018.pdf | Cabinet-line cutting, edge banding, CNC/drilling, sorting, assembly, QC, sanding, finishing. | Published triangular durations for individual production stations. | Entity unit and automation level must be recovered from paper before mapping. | Candidate direct benchmark after unit inspection. |

## Taxonomy effects found so far

1. `cnc_router_profile_cutting`, `cnc_vertical_drilling`, `cnc_grooving`, and
   `cnc_pocketing` remain separate operation identities. They must share one
   `cnc_router_session` calculation group for compatible work, so setup and
   sheet handling are not duplicated.
2. `manual_drilling` and `manual_routing` remain separate identities. They may
   share one manual-panel session when they occur on the same compatible batch.
3. No source yet supports adding, merging, or removing a global operation.
   The correct current action is to improve grouping and formula semantics,
   not mutate the 77-operation catalog prematurely.

## Next bounded extraction

1. Recover the unit, machine configuration, batch basis, and exact table
   semantics from the 2018 cabinet-manufacturing paper.
2. Recover the 18 work elements and unit from the 2023 solid-timber paper.
3. Map only exact compatible measurements to the current recipes.
4. Record all non-compatible evidence as methodology or sanity-check evidence,
   never as a numeric baseline.
