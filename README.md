# RollCallLatch

RollCallLatch publishes one-shot policy flags keyed to official U.S. House roll calls. A sponsor can bind an application rule to an exact vote and a minimum number of affirmative votes. Consumers share a machine-readable decision and cannot be given different counts by different operators.

## Protocol

1. The deploying sponsor calls `bind(key, year, roll, min_yea)`. The rule is immutable and starts in `PENDING`.
2. Any wallet may call `settle(key)`. Validators independently fetch the fixed [House Clerk XML](https://xml.house.gov/) from the locked year and roll number. They check chamber, roll number, action year, vote type and official result, then agree exactly on the normalized yea/nay/result tuple. Absent, malformed or unsupported evidence aborts without moving the rule out of `PENDING`.
3. Through deterministic code, a passed vote meeting the sponsor's minimum becomes `ACTIVATED`. All other supported outcomes become `CLOSED`. Both states are terminal. Consumers read `get_rule(key)`, which includes the threshold and evidence, from finalized state.

Only official yea-and-nay results marked Passed or Failed are supported. A flag identifies that roll call and its configured threshold. It does not determine whether a bill became law, interpret the substance of the vote, or infer votes from news. The sponsor chooses the mapping from an application rule to a roll call. The archive fixture exercises this workflow against historical official records.

## Stable Studionet

Chain 61999, RPC `https://studio.genlayer.com/api`, Node.js 24, `genlayer-js@2.0.0`.

```sh
npm ci
python -m unittest discover -s tests
STUDIONET_FAUCET=1 npm run deploy
STUDIONET_FAUCET=1 npm run test:studionet
```

Save the JSON object from the smoke test’s `EVIDENCE` output and run `npm run verify -- evidence.json` for read-only verification. The last two commands deploy independent test instances. The acceptance script shows the exact argument order, separate sponsor and resolver signers, and finalized `get_rule` calls. Use `STUDIONET_PRIVATE_KEY` for a funded sponsor account and opt into the test faucet for disposable callers.

[Official lint results](LINT.md)
