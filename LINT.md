# GenVM lint and SDK validation

- Source: `contracts/roll_call_latch.py`
- SHA-256: `c10f00e7dfcf9fe533499f46312653515123ccddf1ec315f819da195e9f4c9f7`
- Official tool: `genvm-linter==0.11.0`
- Official runner bundle: GenVM `v0.2.16`
- SDK resolved from the declared header: `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`
- The runner resolved its standard library from its own manifest. No SDK override was used.

```sh
python -m pip install genvm-linter==0.11.0
env -u GENVMROOT GENVM_VERSION=v0.2.16 genvm-lint check contracts/roll_call_latch.py --json
```

[Raw output](LINT.json) records both AST lint and SDK semantic validation. The read-only chain verifier compares the deployed bytes against this source file.
