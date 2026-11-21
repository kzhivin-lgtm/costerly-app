# Accepted UI behavior and publication

Before changing navigation, callbacks/reruns, shared layout, authentication,
saved-estimate persistence, cache identity/invalidation or their dependencies,
read the accepted behavior contract in `notes/UI_GUIDELINES.md` and the
verification procedure in `tests/ui/README.md`.

Preserve the accepted V1.3.3 checkpoint. Intentional changes to protected
behavior require an owner-approved before/after impact report, alternatives,
verification and rollback. Routine feature changes that preserve the contract
do not require another approval. Do not weaken or remove the contract, tests,
workflow or remote publication rule just to make a failing candidate pass.

Run `tools/run_ui_contract.py` for local verification. Publish runtime changes
through `tools/promote_ui_release.py COMMIT --publish` after the exact commit
passes `UI release gate` in GitHub Actions. Do not directly push an unchecked
runtime commit to main or bypass the remote rule. Existing Core and wrapper
build/version checks still apply after deployment. Report test evidence and
the actual remote enforcement state separately; a local hook or CI file alone
does not establish an obligatory remote barrier.

Standing owner rule,21November2026: every release preserves all previously
accepted behavior and checkpoints, not only the feature being added. New
requirements are additive unless the owner explicitly approves a before/after
change. Identify protected behavior and its regression evidence before editing;
do not weaken or omit an existing check to publish a candidate. Verify the exact
published Core/wrapper versions after rollout. The owner does not need to repeat
this requirement for each deployment.
