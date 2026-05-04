# Scripts

Automation scripts for validating, generating, or inspecting contracts.

Scripts should support the canonical contracts without making the contracts platform-specific.

## Validation

Validate all contract files:

```bash
python3 scripts/validation/validate-contracts.py
```

Validate one contract while authoring:

```bash
python3 scripts/validation/validate-contracts.py references/odcs/pc/core/party.odcs.yaml
```
