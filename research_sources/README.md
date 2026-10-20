# Quarantined Research Sources Directory

This directory is designated for cloning third-party candidate open-source repositories for inspection, auditing, and experimentation.

## Isolation Rules
1. **Excluded from Git**: This directory is listed in `.gitignore` to prevent committing upstream code directly into our main repository.
2. **Read-Only Inspection**: Do not modify files directly within upstream clones.
3. **No Unsafe Execution**: Do not execute arbitrary build scripts, bash files, or setup utilities from cloned repositories without a prior security audit.
4. **Audit Requirement**: Every repository cloned here must be cataloged in `docs/SOURCE_REGISTER.md` and audited against the 5-pillar rubric in `docs/REPOSITORY_AUDITS.md`.
