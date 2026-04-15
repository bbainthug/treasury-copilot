# Treasury Copilot

An `AI × Earn` MVP for crypto-native revenue routing and treasury decisions.

`Treasury Copilot` is not a payment page and not a vault picker. It is the first decision layer after onchain revenue lands in a wallet:

`Revenue in -> standardize into Base USDT -> decide keep vs deploy -> execute a live yield route`
## Demo Video
[X](https://x.com/BBainthug/status/2044305023258243477?s=20)

## What problem it solves

Crypto-native teams, creators, contributors, and small protocols often receive fragmented onchain income:

- different chains
- different tokens
- no standard treasury asset
- no clear rule for whether idle funds should remain liquid or be deployed

Most tools stop at either:

- payment collection
- yield discovery
- AI chat

`Treasury Copilot` fills the operational gap in between:

it turns fragmented revenue into a standardized treasury asset, then recommends whether that cash should stay liquid or move into a live executable Earn strategy.

## Product flow

1. A payer sends one of the supported demo assets
2. Revenue is normalized into `Base USDT`
3. LI.FI Earn vaults are fetched and filtered
4. Only vaults with live executable quote paths are kept
5. AI makes a policy-aware treasury recommendation:
   - `Keep Base USDT`
   - `Deploy to yield`
6. The user can inspect the live route and optionally broadcast a real transaction

## Why this is different

- It standardizes treasury assets, not just payments
- AI does not invent transactions or calldata
- Yield recommendations are constrained to already-vetted, executable routes
- The product is about idle cash deployment, not APY browsing

## Supported demo assets

To keep the demo stable, the current version uses a curated set of assets:

- Base USDC
- Base ETH
- Arbitrum USDC
- Ethereum USDT
- Ethereum ETH

Treasury is standardized into:

- `Base USDT`

## Architecture

The app is a single Streamlit interface with four layers:

1. Revenue intake layer
   Accepts a supported source token and builds a LI.FI quote into Base USDT.

2. Treasury standardization layer
   Converts fragmented revenue into one treasury asset for easier downstream decisions.

3. Decision layer
   Uses policy inputs such as liquidity horizon, risk mode, vault APY, TVL, chain, and live route availability to recommend `keep` or `deploy`.

4. Execution layer
   Re-quotes with a real wallet address and broadcasts the resulting transaction when requested.

## Key implementation details

- LI.FI Quote / Composer API is used for revenue standardization and vault deployment
- LI.FI Earn API is used to discover candidate vaults
- AI only evaluates constrained candidate strategies
- Real transactions are signed locally for demo purposes
- The current demo can later be upgraded to wallet signing or managed execution

## Local setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the app:

```bash
streamlit run app.py
```

## Environment variables

Recommended configuration:

```env
OPENAI_API_KEY=your_openai_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

BURNER_PRIVATE_KEY=your_wallet_private_key

BASE_RPC_URL=https://mainnet.base.org
ARBITRUM_RPC_URL=https://arbitrum-one-rpc.publicnode.com
ETHEREUM_RPC_URL=https://ethereum-rpc.publicnode.com
OPTIMISM_RPC_URL=https://optimism-rpc.publicnode.com
```

Notes:

- `OPENAI_API_KEY` powers the treasury decision engine
- `BURNER_PRIVATE_KEY` is only used for demo transaction broadcasting
- Without `OPENAI_API_KEY`, the app falls back to deterministic local decision rules

## Repo guide

- [app.py](/Users/a123/监控脚本/app.py): main product flow, UI, LI.FI integration, AI decision logic, and execution
- [test_lifi.py](/Users/a123/监控脚本/test_lifi.py): early integration script for endpoint checks
- [SUBMISSION.md](/Users/a123/监控脚本/SUBMISSION.md): hackathon submission-ready project description
- [DEMO_SCRIPT.md](/Users/a123/监控脚本/DEMO_SCRIPT.md): 90-second demo script

## Demo framing

The cleanest demo story is:

1. someone pays in a supported token
2. revenue is standardized into Base USDT
3. the system decides whether funds should remain liquid or be deployed
4. if deployment makes sense, the route is already executable

## Risk note

This project can generate and broadcast real onchain transactions.

- yield is not risk-free
- routing costs, bridge paths, and exit timing matter
- use burner wallets or test funds for demos
