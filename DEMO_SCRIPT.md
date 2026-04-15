# Treasury Copilot Demo Script

## 90-second version

This is Treasury Copilot, an AI-powered treasury routing MVP for crypto-native revenue.

Most onchain tools stop at either payments or yield discovery. We focus on the gap after revenue lands in a wallet.

Here, a payer can start with a supported token on Base, Arbitrum, or Ethereum. The first thing we do is normalize that fragmented revenue into one treasury asset: Base USDT.

So instead of leaving teams with random assets across chains, we turn incoming revenue into something standardized and easier to manage.

Then we fetch LI.FI Earn vaults, filter them for stablecoin strategies, and keep only the ones that still have live executable routes right now.

At that point, the AI decision engine steps in. But it is policy-aware and constrained: it does not generate transactions, and it does not invent strategies. It only decides whether funds should stay liquid or be deployed, based on factors like liquidity horizon, risk mode, APY, TVL, chain, and route viability.

If the funds are needed soon, Treasury Copilot recommends keeping Base USDT liquid. If the funds look idle long enough, it recommends a live yield route into a vetted Earn vault.

And if deployment makes sense, we can already inspect the route and broadcast the real transaction.

So the key idea is simple:

Treasury Copilot turns fragmented onchain revenue into standardized stablecoin treasury, then uses AI to recommend whether idle funds should remain liquid or be routed into a live executable yield strategy.

## Demo beats

1. Start with a supported payment asset
2. Show revenue normalization into Base USDT
3. Show the treasury memo: keep vs deploy
4. Open the recommended strategy
5. Show the live executable route
6. End on the execution button

## Final line

Treasury Copilot is the first decision layer between onchain revenue and treasury deployment.
