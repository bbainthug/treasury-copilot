# Treasury Copilot Submission Copy

## One-liner

Treasury Copilot turns fragmented onchain revenue into standardized stablecoin treasury, then uses AI to recommend whether idle funds should remain liquid or be routed into a live executable yield strategy.

## Hackathon submission paragraph

Treasury Copilot is an AI-powered treasury routing MVP for crypto-native teams, creators, and small protocols. Instead of stopping at payment collection or yield discovery, it focuses on the operational gap after revenue lands onchain. A payer can send a supported token, the system standardizes that revenue into Base USDT through LI.FI routing, fetches candidate Earn vaults, filters them by liquidity and live route availability, and then uses a policy-aware AI decision engine to recommend whether the funds should stay liquid or be deployed into a validated yield strategy. If deployment makes sense, the user can inspect a live executable route and broadcast the transaction. The key idea is not “AI chooses a vault,” but “AI helps turn fragmented revenue into deployable treasury.”

## Short version

Treasury Copilot is a crypto-native treasury autopilot entry point. It standardizes fragmented revenue into Base USDT, evaluates whether idle funds should remain liquid or be deployed, and only recommends yield strategies that already have live executable routes.

## Problem

- Onchain revenue is fragmented across chains and tokens
- Teams often lack a standard treasury asset
- Idle funds sit in wallets because deployment requires too many manual steps
- Most products solve only payments or only yield, not the decision layer in between

## Solution

- Normalize incoming revenue into Base USDT
- Discover candidate Earn vaults from LI.FI
- Filter to live-vetted, executable strategies
- Use AI with explicit policy inputs to recommend keep vs deploy
- Let users inspect and optionally broadcast the route

## Why AI belongs here

The AI is constrained and policy-aware. It does not generate raw transaction logic. It only explains and recommends between already-vetted treasury actions based on:

- liquidity horizon
- risk mode
- vault APY
- vault TVL
- destination chain
- route executability

## Recommended category

AI × Earn
