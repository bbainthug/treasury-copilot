import json
import os
from datetime import datetime
from decimal import Decimal, ROUND_DOWN
from typing import Any, Dict, List, Optional

import requests
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from web3 import Web3

load_dotenv()

EARN_BASE_URL = "https://earn.li.fi/v1"
QUOTE_BASE_URL = "https://li.quest/v1"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
BURNER_PRIVATE_KEY = os.getenv("BURNER_PRIVATE_KEY", "").strip()
PREVIEW_ADDRESS = "0x000000000000000000000000000000000000dEaD"

HEADERS = {"x-lifi-integrator": "yieldrazor"}
TVL_MIN_USD = 5_000_000
TOP_VAULTS_LIMIT = 8
RECOMMENDATION_SCORE_THRESHOLD = 72
DEMO_PROOF_USD_THRESHOLD = 50.0
COST_EFFICIENCY_RATIO_TARGET = 0.02
RISK_MODES = ["稳健", "进攻"]
TREASURY_MODES = ["今天就要用", "可以放一阵子", "尽量赚收益"]
SAFE_CHAINS = {"Base", "Ethereum", "Arbitrum", "Optimism"}
STABLE_SYMBOLS = {"USDC", "USDT", "USDS", "USDe", "DAI", "USD0"}
EXECUTION_MODE_OPTIONS = ["preview", "demo_executor", "user_wallet"]

SETTLEMENT_TOKEN = {
    "chainId": 8453,
    "chain": "Base",
    "symbol": "USDT",
    "address": "0xfde4C96c8593536E31F229EA8f37b2ADa2699bb2",
    "decimals": 6,
}

CHAIN_CONFIG = {
    1: {
        "name": "Ethereum",
        "rpc": os.getenv("ETHEREUM_RPC_URL", "https://ethereum-rpc.publicnode.com"),
    },
    10: {
        "name": "Optimism",
        "rpc": os.getenv("OPTIMISM_RPC_URL", "https://optimism-rpc.publicnode.com"),
    },
    8453: {
        "name": "Base",
        "rpc": os.getenv("BASE_RPC_URL", "https://mainnet.base.org"),
    },
    42161: {
        "name": "Arbitrum",
        "rpc": os.getenv("ARBITRUM_RPC_URL", "https://arbitrum-one-rpc.publicnode.com"),
    },
}

EXPLORER_TX_URLS = {
    1: "https://etherscan.io/tx/{tx_hash}",
    10: "https://optimistic.etherscan.io/tx/{tx_hash}",
    8453: "https://basescan.org/tx/{tx_hash}",
    42161: "https://arbiscan.io/tx/{tx_hash}",
}

PAYMENT_ASSETS = [
    {
        "key": "base-usdc",
        "label": "Base · USDC",
        "chain": "Base",
        "chainId": 8453,
        "symbol": "USDC",
        "address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "decimals": 6,
    },
    {
        "key": "base-eth",
        "label": "Base · ETH",
        "chain": "Base",
        "chainId": 8453,
        "symbol": "ETH",
        "address": "0x0000000000000000000000000000000000000000",
        "decimals": 18,
    },
    {
        "key": "arb-usdc",
        "label": "Arbitrum · USDC",
        "chain": "Arbitrum",
        "chainId": 42161,
        "symbol": "USDC",
        "address": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
        "decimals": 6,
    },
    {
        "key": "eth-usdt",
        "label": "Ethereum · USDT",
        "chain": "Ethereum",
        "chainId": 1,
        "symbol": "USDT",
        "address": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "decimals": 6,
    },
    {
        "key": "eth-eth",
        "label": "Ethereum · ETH",
        "chain": "Ethereum",
        "chainId": 1,
        "symbol": "ETH",
        "address": "0x0000000000000000000000000000000000000000",
        "decimals": 18,
    },
]

LANGUAGE_OPTIONS = {"中文": "zh", "English": "en"}

RISK_MODE_LABELS = {
    "稳健": {"zh": "稳健", "en": "Conservative"},
    "进攻": {"zh": "进取", "en": "Growth"},
}

TREASURY_MODE_LABELS = {
    "今天就要用": {"zh": "短期使用", "en": "Needed soon"},
    "可以放一阵子": {"zh": "中期配置", "en": "Can be parked"},
    "尽量赚收益": {"zh": "收益优先", "en": "Prefer yield"},
}

I18N = {
    "zh": {
        "language_label": "语言",
        "language_control_label": "切换语言",
        "topbar_note": "Treasury Copilot 演示",
        "hero_badges": [
            "AI × Earn",
            "Treasury Router",
            "归集至 Base USDT",
            "实时可执行 Route",
        ],
        "hero_title": "Treasury Copilot",
        "hero_body": "链上收入标准化与资金决策入口",
        "input_kicker": "收入接入",
        "source_token_label": "来源资产",
        "amount_label": "输入数量",
        "amount_help": "稳定币建议输入 25 至 100；选择 ETH 时建议使用 0.01 等小额。",
        "risk_mode_label": "风险策略",
        "treasury_mode_label": "资金期限",
        "preview_button": "预览资金路径",
        "preview_caption": "系统将生成收入标准化结果，并输出对应的 Treasury 动作建议。",
        "positioning_kicker": "产品定位",
        "positioning_title": "将链上收入转化为可配置的 Treasury 资产",
        "positioning_body": "产品覆盖收入归集、资产标准化与后续部署建议，适用于链上 Treasury 管理场景。",
        "stat_treasury_asset": "Treasury 资产",
        "stat_revenue_source": "收入来源",
        "stat_origin_chain": "来源链",
        "stat_liquidity_policy": "流动性策略",
        "spinner_payment_quote": "正在获取 Revenue Route Quote...",
        "spinner_vaults": "正在加载 Earn Vault 并校验可执行 Route...",
        "preview_error": "预览生成失败：{error}",
        "step_1_title": "收入接入",
        "step_1_body": "收入自 {chain} 的 {symbol} 进入，并统一标准化为 Base USDT。",
        "step_2_title": "资金决策",
        "step_2_body": "系统仅在已筛选且可执行的候选策略范围内生成 Treasury 建议。",
        "step_3_title": "执行部署",
        "step_3_body": "满足条件时，资金可进一步进入可执行的 Earn Vault Route。",
        "summary_kicker": "收入标准化",
        "summary_title": "{from_amount} {from_token} → {to_amount} {to_token}",
        "label_route": "Route",
        "label_standardized_treasury": "标准化后 Treasury",
        "label_gas": "Gas",
        "label_fees": "Fees",
        "memo_kicker": "决策说明",
        "confidence_label": "决策等级 {value}/100",
        "action_keep": "保留为 Base USDT",
        "action_deposit": "部署至 Earn Vault",
        "label_best_for": "适用情景",
        "label_raw_vaults": "原始 Vault 数",
        "label_live_vetted_vaults": "通过校验的 Vault",
        "standardization_heading": "Treasury 标准化",
        "standardization_text": "资金从 `{chain} · {symbol}` 进入后，先统一转换为 `{settlement_chain} · {settlement_symbol}`，作为后续 Treasury 管理的基础资产。",
        "keep_message": "当前建议保留流动性，不继续执行收益部署。",
        "deploy_message": "当前建议将标准化后的稳定币继续部署至 Earn Vault。",
        "revenue_route_details": "Revenue Route 详情",
        "recommended_action_heading": "推荐资金配置",
        "treasury_route_note": "Treasury 标准资产默认为 Base USDT；若更高评分的可执行策略位于其他链，系统可基于实时 Route 将标准化后的 Treasury 继续路由至目标链策略。",
        "strategy_boundary_note": "当前推荐仅代表在当前输入条件与实时可执行路径下的优先策略，不构成收益保证。",
        "deployment_kicker": "部署预览",
        "label_target_strategy": "目标策略",
        "label_estimated_vault_tokens": "预计获得的 Vault Token",
        "label_deployment_cost": "Deployment 成本",
        "deployment_route_details": "Deployment Route 详情",
        "no_strategy_warning": "当前没有达到推荐阈值的可执行策略，建议暂时保留流动性。",
        "other_strategies_heading": "其他已验证策略",
        "badge_ai_pick": "推荐",
        "badge_backup": "候选",
        "execution_heading": "执行",
        "execution_mode_label": "当前执行模式",
        "execution_mode_selector_label": "执行模式选择",
        "execution_mode_overview_kicker": "模式分层",
        "execution_mode_overview_heading": "执行模式说明",
        "execution_mode_preview_option": "策略预览",
        "execution_mode_demo_option": "演示执行钱包",
        "execution_mode_user_option": "用户钱包执行（即将支持）",
        "execution_mode_preview_title": "策略预览",
        "execution_mode_preview_note": "当前模式仅展示实时路径与策略结果，不发起链上交易。",
        "execution_mode_demo_title": "演示执行钱包（Demo Executor）",
        "execution_mode_demo_note": "当前版本不会调用访问者钱包资产。",
        "execution_mode_user_title": "用户钱包执行（即将支持）",
        "execution_mode_user_note": "当前 hackathon 版本暂未开放用户钱包签名；生产环境将切换为用户钱包签名或托管执行层。",
        "execution_mode_preview_badge": "Preview Mode",
        "execution_mode_demo_badge": "Demo Executor Mode",
        "execution_mode_user_badge": "User Wallet Mode",
        "execution_mode_preview_scope": "展示内容：实时策略、Quote、Route、Route fee、Gas、min received。",
        "execution_mode_demo_scope": "展示内容：在预览基础上，使用本地 burner / Demo Executor 验证链上执行闭环。",
        "execution_mode_user_scope": "展示内容：保留用户钱包执行入口形态，当前仅做产品占位展示。",
        "execution_mode_preview_actions": "按钮状态：仅支持预览，所有交易按钮禁用。",
        "execution_mode_demo_actions": "按钮状态：仅在余额充足时允许执行；余额不足时仅支持预览。",
        "execution_mode_user_actions": "按钮状态：当前不接入真实钱包，所有交易按钮禁用。",
        "execution_mode_value": "演示执行钱包（Demo Executor）",
        "execution_mode_note": "当前版本不会调用访问者钱包资产。",
        "execution_warning": "当前为 Demo Executor Mode。系统将使用执行钱包地址重新请求最新 Quote，并由本地 burner signer 完成签名与广播。当前 demo 通过本地 burner wallet 验证可执行闭环；生产环境建议切换为用户钱包签名或托管执行层。",
        "execution_mode_preview_info": "当前为 Preview Mode，仅展示实时策略、Quote、Route 与资金决策结果，不发起链上交易。",
        "execution_mode_user_info": "当前为 User Wallet Mode 占位。当前 hackathon 版本暂未开放用户钱包签名；生产环境将切换为用户钱包签名或托管执行层。",
        "execution_mode_demo_info": "当前为 Demo Executor Mode，可在余额满足条件时验证真实链上执行闭环。",
        "button_standardization": "用演示钱包执行收入标准化",
        "button_deployment": "用演示钱包执行收益部署",
        "missing_private_key": "未配置 BURNER_PRIVATE_KEY，当前无法启用演示执行钱包。",
        "spinner_live_quote": "正在使用执行钱包地址获取最新 Quote...",
        "spinner_broadcast_standardization": "正在发送标准化交易...",
        "success_standardization": "Demo Executor Mode 交易已发送：{tx_hash}",
        "error_standardization": "标准化交易失败：{error}",
        "no_recommended_vault": "当前没有达到推荐阈值的可执行策略，暂不支持执行收益部署。",
        "spinner_requote_settlement": "正在使用执行钱包地址重新获取标准化 Quote...",
        "spinner_requote_deployment": "正在使用执行钱包地址重新获取部署 Quote...",
        "spinner_broadcast_deployment": "正在发送部署交易...",
        "success_deployment": "Demo Executor Mode 交易已发送：{tx_hash}",
        "error_deployment": "部署交易失败：{error}",
        "execution_success_note": "该交易在 Demo Executor Mode 下用于验证链上执行闭环，不代表访问者钱包资产已被调用。",
        "execution_buttons_preview_note": "当前为 Preview Mode，仅提供实时路径预览，不提供交易广播。",
        "execution_buttons_demo_note": "当前为 Demo Executor Mode，按钮会在余额与路径条件满足时开放。",
        "execution_buttons_user_note": "当前为 User Wallet Mode 占位，暂不开放真实钱包签名与交易按钮。",
        "execution_deployment_locked_note": "当前决策为保留流动性，或候选策略未达到部署阈值，收益部署按钮保持关闭。",
        "threshold_badge": "推荐阈值 {value}",
        "score_heading": "策略评分拆解",
        "score_apy": "APY score",
        "score_tvl": "TVL score",
        "score_route_cost": "Route cost score",
        "score_chain_preference": "Chain fit score",
        "score_time_fit": "Time horizon fit score",
        "score_executable": "Executable status",
        "score_total": "Total score",
        "score_yes": "可执行",
        "score_no": "不可执行",
        "score_threshold_warning": "当前没有达到推荐阈值的可执行策略，建议暂时保留流动性。",
        "below_threshold_heading": "可执行但未达推荐阈值的候选策略",
        "reason_heading_recommended": "推荐原因",
        "reason_heading_candidate": "未优先选择原因",
        "reason_kicker_recommended": "推荐证据",
        "reason_kicker_candidate": "候选说明",
        "reason_position_label": "策略定位",
        "reason_position_recommended": "当前条件下的最优可执行策略",
        "reason_position_top_candidate": "当前策略评分最高的可执行方案",
        "reason_default_recommended": "该方案在当前条件下综合评分最高，且具备明确可执行性。",
        "reason_default_candidate": "该候选在当前条件下可执行，但综合评分低于优先展示方案。",
        "reason_apy_high": "APY 表现较强，当前约为 {apy}。",
        "reason_tvl_high": "TVL 较高，当前约为 {tvl}，容量与流动性更稳健。",
        "reason_route_cost_low": "Route 成本更低，当前估算约为 {cost}。",
        "reason_chain_fit": "链偏好与当前风险策略更匹配，当前更偏向 {chain}。",
        "reason_time_fit": "与当前资金期限更匹配，适合 {horizon} 场景。",
        "reason_executable": "已通过 live quote 校验，可执行性明确。",
        "candidate_reason_lower_tvl": "TVL 更低",
        "candidate_reason_higher_route_cost": "Route 成本更高",
        "candidate_reason_risk_mismatch": "不符合当前风险策略",
        "candidate_reason_time_mismatch": "与资金期限不匹配",
        "candidate_reason_not_executable": "未通过 live quote 校验",
        "candidate_reason_below_threshold": "总评分未达到推荐阈值",
        "candidate_reason_lower_apy": "APY 优势不足",
        "confirmation_heading": "资金确认",
        "confirmation_kicker": "执行前金额确认",
        "confirm_input_amount": "输入资产数量",
        "confirm_standardized_amount": "预计标准化后收到的 Base USDT 数量",
        "confirm_route_fee": "Route fee",
        "confirm_gas": "Gas",
        "confirm_min_received": "最小可接受收到金额（min received）",
        "confirm_deposit_amount": "实际将投入 Vault 的 Base USDT 数量",
        "confirm_vault_tokens": "预计收到的 Vault Token 数量",
        "confirm_target_vault": "目标 Vault",
        "confirm_wallet_type": "执行钱包类型",
        "status_generated_at_unavailable": "当前会话尚未生成策略数据时间",
        "status_amount_estimate_unavailable": "当前未完成路径预览，暂不生成金额估算",
        "confirm_input_amount_unavailable": "当前未完成路径预览，暂不生成输入资产数量",
        "confirm_standardized_amount_unavailable": "当前未完成路径预览，暂不生成标准化金额估算",
        "confirm_min_received_unavailable": "当前未完成路径预览，暂不生成最小可接受收到金额",
        "confirm_deposit_amount_unavailable": "当前建议保留流动性，因此不生成部署预估",
        "confirm_vault_tokens_unavailable": "当前建议保留流动性，因此不生成 Vault 预估数量",
        "confirm_target_vault_unavailable": "当前未进入部署校验阶段，暂不生成目标 Vault 数据",
        "confirm_executor_address": "演示执行钱包地址",
        "confirm_standardization_balance": "演示执行钱包当前余额（收入标准化）",
        "confirm_standardization_required": "本次执行预计所需余额（收入标准化）",
        "confirm_standardization_status": "执行状态（收入标准化）",
        "confirm_deployment_balance": "演示执行钱包当前余额（收益部署）",
        "confirm_deployment_required": "本次执行预计所需余额（收益部署）",
        "confirm_deployment_status": "执行状态（收益部署）",
        "executor_status_ready": "可执行",
        "executor_status_preview_only": "余额不足，仅支持预览",
        "executor_status_preview_mode": "当前为策略预览模式，不进入执行校验",
        "executor_status_user_mode": "当前为用户钱包执行占位模式，不进入执行校验",
        "executor_status_missing_wallet": "当前未配置演示执行钱包，无法进入执行校验",
        "executor_address_unavailable": "当前未配置演示执行钱包地址",
        "executor_address_preview": "当前为策略预览模式，不调用演示执行钱包地址",
        "executor_address_user": "当前为用户钱包执行占位模式，不调用演示执行钱包地址",
        "executor_balance_unavailable": "当前未能读取演示执行钱包余额，请检查 RPC 或网络",
        "executor_balance_preview": "当前为策略预览模式，不读取演示执行钱包余额",
        "executor_balance_user": "当前为用户钱包执行占位模式，不读取演示执行钱包余额",
        "executor_balance_missing_wallet": "当前未配置演示执行钱包，无法读取钱包余额",
        "executor_required_unavailable": "当前未完成执行条件校验，暂不生成本次执行所需金额",
        "executor_required_deployment_keep": "当前建议保留流动性，因此不生成部署所需金额",
        "deployment_path_unavailable": "当前未进入部署校验阶段，暂不生成部署路径数据",
        "deployment_balance_keep": "当前建议保留流动性，因此不进入部署余额校验",
        "deployment_balance_preview": "当前为策略预览模式，不读取演示执行钱包部署侧余额",
        "deployment_balance_user": "当前为用户钱包执行占位模式，不读取演示执行钱包部署侧余额",
        "deployment_balance_missing_wallet": "当前未配置演示执行钱包，无法读取部署侧余额",
        "deployment_balance_unavailable": "当前未能读取演示执行钱包部署侧余额，请检查 RPC 或网络",
        "deployment_status_keep": "当前建议保留流动性，因此不进入部署执行",
        "executor_insufficient_warning": "当前演示执行钱包余额不足，仅支持实时路径预览。",
        "preview_only_amount_note": "当前金额用于展示策略与路径结果，不代表演示钱包已具备等额执行能力。大额场景优先用于实时策略预览，小额场景更适合验证真实链上执行闭环。",
        "transparency_heading": "推荐透明度",
        "transparency_kicker": "推荐依据",
        "transparency_updated_at": "数据更新时间",
        "transparency_filtered_count": "通过筛选数",
        "transparency_validated_count": "通过 live quote 验证数",
        "transparency_total_score": "总评分",
        "transparency_main_reason": "主要推荐原因",
        "transparency_other_reason": "未选其他候选的原因",
        "transparency_other_reason_default": "其他候选的综合评分较低，因此未被优先推荐。",
        "transparency_other_reason_below_threshold": "当前候选策略虽可执行，但总评分均未达到推荐阈值。",
        "transparency_other_reason_keep": "当前决策优先保留流动性，因此未继续执行候选策略。",
        "keep_reason_heading": "为何建议保留流动性",
        "keep_reason_kicker": "拒绝部署说明",
        "keep_reason_note": "保留流动性也是有效决策结果，不会为了展示收益而强行部署。",
        "display_keep_headline": "建议暂时保留流动性",
        "display_keep_rationale": "当前没有达到推荐阈值的可执行策略，因此本次结果以保留流动性为准。",
        "display_keep_risk_note": "保留流动性可避免在成本效率或期限匹配不足时强行部署。",
        "display_keep_best_for": "等待下一次配置窗口",
        "keep_reason_min_threshold": "当前金额是否低于最小部署阈值",
        "keep_reason_standardization_cost": "标准化成本占比",
        "keep_reason_deployment_cost": "预计部署成本占比",
        "keep_reason_payback": "在当前 APY 下预计回本周期",
        "keep_reason_time_fit": "当前资金期限与策略是否匹配",
        "keep_reason_threshold_yes": "是 · 阈值约 {threshold}",
        "keep_reason_threshold_no": "否 · 阈值约 {threshold}",
        "keep_reason_threshold_unknown": "当前成本估算不完整，暂无法判断是否低于最小部署阈值",
        "keep_reason_ratio_value": "{ratio} · {amount}",
        "keep_reason_standardization_unavailable": "当前标准化成本信息不足，无法计算成本占比",
        "keep_reason_deployment_unavailable": "当前未生成部署路径，无法计算部署成本占比",
        "keep_reason_payback_value": "约 {days} 天",
        "keep_reason_payback_unavailable": "当前未生成可参考的部署路径或 APY 数据，无法估算回本周期",
        "keep_reason_time_fit_high": "{mode} · 匹配较高（{score}/100）",
        "keep_reason_time_fit_mid": "{mode} · 基本匹配（{score}/100）",
        "keep_reason_time_fit_low": "{mode} · 匹配不足（{score}/100）",
        "keep_reason_time_fit_unknown": "{mode} · 当前未生成可执行策略参考，暂无法判断期限匹配度",
        "proof_heading": "验证记录 / Execution Proof",
        "proof_note": "大额金额主要用于展示实时策略与可执行路径；链上闭环能力通过 Demo Executor 的小额验证记录展示。",
        "proof_empty": "当前暂无可展示的链上验证记录",
        "proof_action_standardization": "收入标准化",
        "proof_action_deployment": "收益部署",
        "proof_field_type": "验证类型",
        "proof_field_mode": "执行模式",
        "proof_field_chain": "链",
        "proof_field_token": "Token",
        "proof_field_amount": "输入金额",
        "proof_field_hash": "交易哈希",
        "proof_field_time": "时间",
        "proof_field_explorer": "浏览器链接",
        "proof_mode_demo": "Demo Executor",
        "proof_explorer_link": "查看浏览器",
        "proof_explorer_unavailable": "当前交易链未匹配浏览器链接",
        "proof_hash_unavailable": "当前未记录交易哈希",
        "proof_chain_unavailable": "当前未记录链信息",
        "proof_token_unavailable": "当前未记录 Token 信息",
        "proof_amount_unavailable": "当前未记录输入金额",
        "footer_caption": "当前版本仅开放少量已验证的演示资产，用于展示收入进入 Treasury 后的标准化、决策与部署流程。",
        "step_prefix": "步骤",
        "unknown_label": "未知",
        "vault_metric_pack_label": "Pack 数",
    },
    "en": {
        "language_label": "Language",
        "language_control_label": "Switch language",
        "topbar_note": "Treasury Copilot demo",
        "hero_badges": [
            "AI × Earn",
            "Treasury Router",
            "Revenue standardized into Base USDT",
            "Policy-aware idle cash deployment",
        ],
        "hero_title": "Treasury Copilot",
        "hero_body": "Entry point for onchain revenue standardization and treasury decisions.",
        "input_kicker": "Revenue Intake",
        "source_token_label": "Source asset",
        "amount_label": "Amount",
        "amount_help": "For stablecoins, 25 to 100 works well for demo. If you choose ETH, use a small amount such as 0.01.",
        "risk_mode_label": "Risk mode",
        "treasury_mode_label": "Liquidity horizon",
        "preview_button": "Preview Treasury Route",
        "preview_caption": "Revenue is first standardized into Base USDT, then the product recommends whether liquidity should be preserved or deployed.",
        "positioning_kicker": "Positioning",
        "positioning_title": "Turn fragmented onchain revenue into deployable Treasury",
        "positioning_body": "This is not just a payment page or a Vault browser. It is a Treasury Router that aggregates revenue, standardizes assets, and recommends an executable Treasury action.",
        "stat_treasury_asset": "Treasury asset",
        "stat_revenue_source": "Revenue source",
        "stat_origin_chain": "Origin chain",
        "stat_liquidity_policy": "Liquidity policy",
        "spinner_payment_quote": "Fetching Revenue Route Quote...",
        "spinner_vaults": "Loading Earn Vaults and validating executable Routes...",
        "preview_error": "Preview failed: {error}",
        "step_1_title": "Revenue Intake",
        "step_1_body": "Revenue enters from {chain} {symbol} and is first standardized into Base USDT.",
        "step_2_title": "Treasury Decision",
        "step_2_body": "AI only recommends keep or deploy within already-filtered, executable strategies.",
        "step_3_title": "Live Deployment",
        "step_3_body": "If funds are idle long enough, Treasury is routed into a live executable Earn Vault.",
        "summary_kicker": "Revenue Standardization",
        "summary_title": "{from_amount} {from_token} → {to_amount} {to_token}",
        "label_route": "Route",
        "label_standardized_treasury": "Standardized Treasury",
        "label_gas": "Gas",
        "label_fees": "Fees",
        "memo_kicker": "Policy-aware Treasury Memo",
        "confidence_label": "Confidence {value}/100",
        "action_keep": "Keep Base USDT",
        "action_deposit": "Deposit into Earn Vault",
        "label_best_for": "Best for",
        "label_raw_vaults": "Raw Vault count",
        "label_live_vetted_vaults": "Live-vetted Vaults",
        "standardization_heading": "Treasury standardization",
        "standardization_text": "This revenue enters from `{chain} · {symbol}` and is first standardized into `{settlement_chain} · {settlement_symbol}` so it becomes easier to manage as Treasury.",
        "keep_message": "The AI recommends preserving liquidity at this stage to avoid unnecessary execution cost and capital constraints.",
        "deploy_message": "The AI recommends deploying the standardized stablecoin into an Earn Vault so idle Treasury can continue working.",
        "revenue_route_details": "Revenue Route details",
        "recommended_action_heading": "Recommended Treasury Action",
        "treasury_route_note": "The standardized Treasury asset defaults to Base USDT. When a higher-scoring executable strategy is on another chain, the system can continue routing the standardized Treasury into that target-chain strategy through a live Route.",
        "strategy_boundary_note": "The current recommendation only reflects the preferred strategy under the current inputs and live executable routes, and does not imply a yield guarantee.",
        "deployment_kicker": "Deployment Preview",
        "label_target_strategy": "Target strategy",
        "label_estimated_vault_tokens": "Estimated Vault tokens",
        "label_deployment_cost": "Deployment cost",
        "deployment_route_details": "Deployment Route details",
        "no_strategy_warning": "No executable strategy currently reaches the recommendation threshold, so the product suggests preserving liquidity.",
        "other_strategies_heading": "Other Validated Strategies",
        "badge_ai_pick": "AI pick",
        "badge_backup": "Backup",
        "execution_heading": "Execution",
        "execution_mode_label": "Execution mode",
        "execution_mode_selector_label": "Execution mode",
        "execution_mode_overview_kicker": "Mode layers",
        "execution_mode_overview_heading": "Execution mode overview",
        "execution_mode_preview_option": "Strategy preview",
        "execution_mode_demo_option": "Demo Executor",
        "execution_mode_user_option": "User wallet execution (Coming soon)",
        "execution_mode_preview_title": "Strategy preview",
        "execution_mode_preview_note": "This mode only displays live routes and strategy results without sending transactions.",
        "execution_mode_demo_title": "Demo Executor wallet",
        "execution_mode_demo_note": "This version does not use visitor wallet assets.",
        "execution_mode_user_title": "User wallet execution (Coming soon)",
        "execution_mode_user_note": "The hackathon build does not support user wallet signing yet; production deployments will switch to user wallet signing or a managed execution layer.",
        "execution_mode_preview_badge": "Preview Mode",
        "execution_mode_demo_badge": "Demo Executor Mode",
        "execution_mode_user_badge": "User Wallet Mode",
        "execution_mode_preview_scope": "Displays live strategy, Quote, Route, Route fee, Gas, and minimum received only.",
        "execution_mode_demo_scope": "Builds on preview mode and uses the local burner / Demo Executor to validate the onchain execution loop.",
        "execution_mode_user_scope": "Reserves the user-wallet execution entry shape, but remains a UI placeholder in the hackathon build.",
        "execution_mode_preview_actions": "Button state: preview only, all transaction buttons are disabled.",
        "execution_mode_demo_actions": "Button state: execution is allowed only when balance and route conditions are satisfied.",
        "execution_mode_user_actions": "Button state: no real wallet is connected yet, so all transaction buttons remain disabled.",
        "execution_mode_value": "Demo Executor wallet",
        "execution_mode_note": "This version does not use visitor wallet assets.",
        "execution_warning": "Current mode: Demo Executor Mode. The system requests the latest Quote with the executor wallet address, then uses the local burner signer to sign and broadcast. This demo validates the execution loop with a local burner wallet; production deployments should switch to user wallet signing or a managed execution layer.",
        "execution_mode_preview_info": "Current mode: Preview Mode. Only live strategy, Quote, Route, and Treasury decision results are shown, with no transaction broadcast.",
        "execution_mode_user_info": "Current mode: User Wallet Mode placeholder. The hackathon build does not support user wallet signing yet; production deployments will switch to user wallet signing or a managed execution layer.",
        "execution_mode_demo_info": "Current mode: Demo Executor Mode. Real transaction validation is available when balance and route conditions are satisfied.",
        "button_standardization": "Use Demo Executor for revenue standardization",
        "button_deployment": "Use Demo Executor for yield deployment",
        "missing_private_key": "BURNER_PRIVATE_KEY is not configured, so Demo Executor mode is unavailable.",
        "spinner_live_quote": "Fetching the latest Quote with the executor wallet address...",
        "spinner_broadcast_standardization": "Broadcasting revenue standardization...",
        "success_standardization": "Demo Executor Mode transaction sent: {tx_hash}",
        "error_standardization": "Revenue standardization failed: {error}",
        "no_recommended_vault": "No executable strategy currently reaches the recommendation threshold, so yield deployment is unavailable.",
        "spinner_requote_settlement": "Re-requesting the standardization Quote with the executor wallet address...",
        "spinner_requote_deployment": "Re-requesting the deployment Quote with the executor wallet address...",
        "spinner_broadcast_deployment": "Broadcasting Treasury deployment...",
        "success_deployment": "Demo Executor Mode transaction sent: {tx_hash}",
        "error_deployment": "Treasury deployment failed: {error}",
        "execution_success_note": "This transaction is sent in Demo Executor Mode to validate the onchain execution loop and does not imply that visitor wallet assets were used.",
        "execution_buttons_preview_note": "Current mode: Preview Mode. Real-time route preview is available, but transaction broadcasting stays disabled.",
        "execution_buttons_demo_note": "Current mode: Demo Executor Mode. Buttons open only when balance and route conditions are satisfied.",
        "execution_buttons_user_note": "Current mode: User Wallet Mode placeholder. Wallet signing and transaction buttons are not available yet.",
        "execution_deployment_locked_note": "The current decision preserves liquidity, or the candidate did not meet the deployment threshold, so the yield deployment button stays disabled.",
        "threshold_badge": "Threshold {value}",
        "score_heading": "Strategy score breakdown",
        "score_apy": "APY score",
        "score_tvl": "TVL score",
        "score_route_cost": "Route cost score",
        "score_chain_preference": "Chain fit score",
        "score_time_fit": "Time horizon fit score",
        "score_executable": "Executable status",
        "score_total": "Total score",
        "score_yes": "Executable",
        "score_no": "Not executable",
        "score_threshold_warning": "No executable strategy currently reaches the recommendation threshold, so the product suggests preserving liquidity.",
        "below_threshold_heading": "Executable candidates below the recommendation threshold",
        "reason_heading_recommended": "Recommendation reasons",
        "reason_heading_candidate": "Why it was not prioritized",
        "reason_kicker_recommended": "Recommendation evidence",
        "reason_kicker_candidate": "Candidate explanation",
        "reason_position_label": "Strategy position",
        "reason_position_recommended": "Highest-scoring executable strategy under current conditions",
        "reason_position_top_candidate": "Highest-scoring executable candidate under current conditions",
        "reason_default_recommended": "This route has the strongest combined score under the current constraints and remains executable.",
        "reason_default_candidate": "This candidate remains executable, but its combined score is lower than the route shown above.",
        "reason_apy_high": "APY is comparatively strong at around {apy}.",
        "reason_tvl_high": "TVL is stronger at about {tvl}, which improves capacity and stability.",
        "reason_route_cost_low": "Route cost is lower, currently estimated around {cost}.",
        "reason_chain_fit": "Chain fit is stronger for the current risk policy, with a preference toward {chain}.",
        "reason_time_fit": "It better matches the current liquidity horizon for {horizon}.",
        "reason_executable": "It already passed live quote validation, so executability is explicit.",
        "candidate_reason_lower_tvl": "Lower TVL",
        "candidate_reason_higher_route_cost": "Higher Route cost",
        "candidate_reason_risk_mismatch": "Weaker fit for the current risk policy",
        "candidate_reason_time_mismatch": "Weaker fit for the current time horizon",
        "candidate_reason_not_executable": "Did not pass live quote validation",
        "candidate_reason_below_threshold": "Total score remains below the recommendation threshold",
        "candidate_reason_lower_apy": "Less APY advantage",
        "confirmation_heading": "Amount confirmation",
        "confirmation_kicker": "Pre-execution amount check",
        "confirm_input_amount": "Input asset amount",
        "confirm_standardized_amount": "Estimated Base USDT after standardization",
        "confirm_route_fee": "Route fee",
        "confirm_gas": "Gas",
        "confirm_min_received": "Minimum received",
        "confirm_deposit_amount": "Base USDT to be deposited into the Vault",
        "confirm_vault_tokens": "Estimated Vault tokens",
        "confirm_target_vault": "Target Vault",
        "confirm_wallet_type": "Executor wallet type",
        "status_generated_at_unavailable": "No strategy data timestamp is available for the current session yet",
        "status_amount_estimate_unavailable": "Route preview has not completed yet, so no amount estimate is available",
        "confirm_input_amount_unavailable": "Route preview has not completed yet, so the input amount is not available",
        "confirm_standardized_amount_unavailable": "Route preview has not completed yet, so the standardized amount is not available",
        "confirm_min_received_unavailable": "Route preview has not completed yet, so the minimum received amount is not available",
        "confirm_deposit_amount_unavailable": "Liquidity is being preserved, so no deployment estimate is generated",
        "confirm_vault_tokens_unavailable": "Liquidity is being preserved, so no Vault token estimate is generated",
        "confirm_target_vault_unavailable": "The flow has not entered deployment validation yet, so no target Vault is generated",
        "confirm_executor_address": "Demo Executor wallet address",
        "confirm_standardization_balance": "Demo Executor balance (standardization)",
        "confirm_standardization_required": "Required balance for this execution (standardization)",
        "confirm_standardization_status": "Execution status (standardization)",
        "confirm_deployment_balance": "Demo Executor balance (deployment)",
        "confirm_deployment_required": "Required balance for this execution (deployment)",
        "confirm_deployment_status": "Execution status (deployment)",
        "executor_status_ready": "Executable",
        "executor_status_preview_only": "Insufficient balance, preview only",
        "executor_status_preview_mode": "Preview Mode is active, so execution validation is not entered",
        "executor_status_user_mode": "User Wallet Mode placeholder is active, so execution validation is not entered",
        "executor_status_missing_wallet": "The Demo Executor wallet is not configured, so execution validation is unavailable",
        "executor_address_unavailable": "Demo Executor wallet address is not configured",
        "executor_address_preview": "Preview Mode is active, so the Demo Executor wallet address is not used",
        "executor_address_user": "User Wallet Mode placeholder is active, so the Demo Executor wallet address is not used",
        "executor_balance_unavailable": "The Demo Executor balance could not be loaded. Check RPC or network connectivity.",
        "executor_balance_preview": "Preview Mode is active, so the Demo Executor balance is not read",
        "executor_balance_user": "User Wallet Mode placeholder is active, so the Demo Executor balance is not read",
        "executor_balance_missing_wallet": "The Demo Executor wallet is not configured, so balance data cannot be loaded",
        "executor_required_unavailable": "Execution-condition validation has not completed yet, so the required amount is not available",
        "executor_required_deployment_keep": "Liquidity is being preserved, so no deployment amount is generated",
        "deployment_path_unavailable": "The flow has not entered deployment validation yet, so deployment path data is not generated",
        "deployment_balance_keep": "Liquidity is being preserved, so deployment balance checks are skipped",
        "deployment_balance_preview": "Preview Mode is active, so the deployment-side Demo Executor balance is not read",
        "deployment_balance_user": "User Wallet Mode placeholder is active, so the deployment-side Demo Executor balance is not read",
        "deployment_balance_missing_wallet": "The Demo Executor wallet is not configured, so deployment-side balance data cannot be loaded",
        "deployment_balance_unavailable": "The deployment-side Demo Executor balance could not be loaded. Check RPC or network connectivity.",
        "deployment_status_keep": "Liquidity is being preserved, so deployment execution is not entered",
        "executor_insufficient_warning": "The current Demo Executor balance is insufficient, so only live path preview is available.",
        "preview_only_amount_note": "The current amount is used to demonstrate strategy and route results, and does not imply that the Demo Executor wallet can execute at the same notional size. Large amounts are for live strategy preview, while small amounts are better for validating the real onchain execution loop.",
        "transparency_heading": "Recommendation transparency",
        "transparency_kicker": "Recommendation basis",
        "transparency_updated_at": "Data updated at",
        "transparency_filtered_count": "Filtered Vaults",
        "transparency_validated_count": "Live-quoted Vaults",
        "transparency_total_score": "Total score",
        "transparency_main_reason": "Primary recommendation reason",
        "transparency_other_reason": "Why other candidates were not selected",
        "transparency_other_reason_default": "Other candidates were not prioritized because their combined scores were lower.",
        "transparency_other_reason_below_threshold": "The current executable candidates remain below the recommendation threshold.",
        "transparency_other_reason_keep": "The current decision keeps liquidity available, so the validated candidates remain for reference only.",
        "keep_reason_heading": "Why liquidity is being preserved",
        "keep_reason_kicker": "Deployment rejection rationale",
        "keep_reason_note": "Keeping liquidity available is a valid decision outcome. The demo does not force deployment just to showcase yield.",
        "display_keep_headline": "Preserve liquidity for now",
        "display_keep_rationale": "No executable strategy currently reaches the recommendation threshold, so the effective result is to keep liquidity available.",
        "display_keep_risk_note": "Preserving liquidity avoids forcing deployment when cost efficiency or time-horizon fit is still weak.",
        "display_keep_best_for": "Waiting for the next allocation window",
        "keep_reason_min_threshold": "Is the current amount below the minimum deployment threshold",
        "keep_reason_standardization_cost": "Standardization cost ratio",
        "keep_reason_deployment_cost": "Estimated deployment cost ratio",
        "keep_reason_payback": "Estimated payback period at the current APY",
        "keep_reason_time_fit": "Does the current time horizon fit the strategy",
        "keep_reason_threshold_yes": "Yes · threshold around {threshold}",
        "keep_reason_threshold_no": "No · threshold around {threshold}",
        "keep_reason_threshold_unknown": "Cost estimates are incomplete, so the minimum deployment threshold cannot be determined yet",
        "keep_reason_ratio_value": "{ratio} · {amount}",
        "keep_reason_standardization_unavailable": "Standardization cost data is incomplete, so the ratio cannot be calculated",
        "keep_reason_deployment_unavailable": "No deployment route is available yet, so the deployment cost ratio cannot be calculated",
        "keep_reason_payback_value": "Around {days} days",
        "keep_reason_payback_unavailable": "No deployment route or usable APY reference is available yet, so the payback period cannot be estimated",
        "keep_reason_time_fit_high": "{mode} · strong fit ({score}/100)",
        "keep_reason_time_fit_mid": "{mode} · moderate fit ({score}/100)",
        "keep_reason_time_fit_low": "{mode} · weak fit ({score}/100)",
        "keep_reason_time_fit_unknown": "{mode} · no executable strategy reference is available yet, so time-horizon fit cannot be determined",
        "proof_heading": "Validation Record / Execution Proof",
        "proof_note": "Large amounts are used to demonstrate live strategy and executable routes, while the onchain execution loop is proven through small Demo Executor validation records.",
        "proof_empty": "No onchain validation records are available for display yet",
        "proof_action_standardization": "Revenue standardization",
        "proof_action_deployment": "Yield deployment",
        "proof_field_type": "Validation type",
        "proof_field_mode": "Execution mode",
        "proof_field_chain": "Chain",
        "proof_field_token": "Token",
        "proof_field_amount": "Input amount",
        "proof_field_hash": "Transaction hash",
        "proof_field_time": "Time",
        "proof_field_explorer": "Explorer link",
        "proof_mode_demo": "Demo Executor",
        "proof_explorer_link": "Open explorer",
        "proof_explorer_unavailable": "No explorer link is mapped for the recorded chain",
        "proof_hash_unavailable": "Transaction hash was not recorded",
        "proof_chain_unavailable": "Chain data was not recorded",
        "proof_token_unavailable": "Token data was not recorded",
        "proof_amount_unavailable": "Input amount was not recorded",
        "footer_caption": "To keep the demo stable, the current version exposes only a small set of tested demo assets. The product focus is not infinite token support, but a clear Treasury decision and deployment flow after revenue arrives.",
        "step_prefix": "STEP",
        "unknown_label": "Unknown",
        "vault_metric_pack_label": "Pack count",
    },
}

DECISION_COPY = {
    "zh": {
        "immediate": {
            "headline": "优先保留流动性",
            "rationale": "该笔资金期限较短，保留 Base USDT 更符合当前 Treasury 目标，并可避免额外 Route 成本与策略暴露。",
            "risk_note": "短期资金应优先保证可用性。",
            "best_for": "短期支出 / 运营周转",
        },
        "no_vaults": {
            "headline": "暂不执行部署",
            "rationale": "当前没有同时满足筛选条件且具备实时可执行 Route 的 Stablecoin Vault，因此不建议执行部署。",
            "risk_note": "候选策略不足时，保留流动性更符合风险控制要求。",
            "best_for": "等待后续配置窗口",
        },
        "small_amount": {
            "headline": "优先控制执行成本",
            "rationale": "当前金额较小，额外 Route、Gas 与执行复杂度可能显著压缩收益空间，因此更适合保留 Base USDT。",
            "risk_note": "小额资金应优先考虑成本效率。",
            "best_for": "小额结算 / 高频收款",
        },
        "deploy": {
            "headline": "建议部署至 {protocol}",
            "rationale": "该 Vault 位于 {chain}，TVL 为 {tvl}，APY 约为 {apy}，与当前风险策略和资金期限更匹配。",
            "risk_note": "部署至 Stablecoin Vault 仍需关注协议风险、Route 风险与退出时点。",
            "best_for": "7 天以上闲置 Treasury",
        },
    },
    "en": {
        "immediate": {
            "headline": "Preserve liquidity first",
            "rationale": "These funds may be needed soon, so keeping Base USDT is more aligned with the current Treasury objective and avoids additional Route cost and strategy risk.",
            "risk_note": "Short-duration funds should prioritize availability over nominal yield.",
            "best_for": "Short-term operations / working capital",
        },
        "no_vaults": {
            "headline": "Do not deploy yet",
            "rationale": "No Stablecoin Vault currently passes the filter and still has a live executable Route. Forcing deployment would increase both product and risk friction.",
            "risk_note": "When candidate strategies are weak, preserving liquidity is the more disciplined choice.",
            "best_for": "Waiting for a better deployment window",
        },
        "small_amount": {
            "headline": "Keep the path simple for small amounts",
            "rationale": "The amount is small enough that extra Route cost, Gas, and execution complexity could eat too much of the potential yield, so keeping Base USDT is more efficient.",
            "risk_note": "For small amounts, execution cost matters more than headline APY.",
            "best_for": "Small payments / frequent settlement",
        },
        "deploy": {
            "headline": "Deploy into {protocol}",
            "rationale": "This Vault is on {chain}, with TVL of {tvl} and APY around {apy}, which is a better fit for the current liquidity horizon and risk preference.",
            "risk_note": "Stablecoin Vaults still carry protocol risk, Route risk, and exit timing risk.",
            "best_for": "Idle Treasury for 7+ days",
        },
    },
}


def extract_number(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(",", "").replace("%", "").strip())
        except ValueError:
            return default
    return default


def first_present(payload: Dict[str, Any], keys: List[str], fallback: Any = None) -> Any:
    for key in keys:
        if key in payload and payload[key] not in (None, ""):
            return payload[key]
    return fallback


def nested_get(payload: Dict[str, Any], path: List[str], fallback: Any = None) -> Any:
    current: Any = payload
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return fallback
        current = current[key]
    return current


def to_units(amount: float, decimals: int) -> str:
    scaled = Decimal(str(amount)) * (Decimal(10) ** decimals)
    return str(int(scaled.quantize(Decimal("1"), rounding=ROUND_DOWN)))


def from_units(raw_amount: str, decimals: int) -> float:
    return float(Decimal(raw_amount) / (Decimal(10) ** decimals))


def format_amount(value: float, digits: int = 2) -> str:
    return f"{value:,.{digits}f}"


def format_compact_number(value: float, digits: int = 2) -> str:
    abs_value = abs(value)
    if abs_value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.{digits}f}B"
    if abs_value >= 1_000_000:
        return f"{value / 1_000_000:.{digits}f}M"
    if abs_value >= 1_000:
        return f"{value / 1_000:.{digits}f}K"
    return format_amount(value, digits)


def amount_display_digits(value: Optional[float], min_digits: int = 2, max_digits: int = 4) -> int:
    if value is None:
        return max_digits
    abs_value = abs(value)
    if abs_value >= 100:
        return min_digits
    if abs_value >= 1:
        return min(min_digits + 1, max_digits)
    return max_digits


def format_display_amount(
    value: Optional[float],
    min_digits: int = 2,
    max_digits: int = 4,
    empty_text: str = "",
) -> str:
    if value is None:
        fallback_digits = max(min_digits, 2)
        return empty_text or format_amount(0.0, fallback_digits)
    digits = amount_display_digits(value, min_digits=min_digits, max_digits=max_digits)
    return format_amount(value, digits)


def format_usd(value: float) -> str:
    return f"${format_compact_number(value, 2)}"


def format_percent(value: Optional[float], digits: int = 2, empty_text: str = "") -> str:
    if value is None:
        return empty_text or "0.00%"
    return f"{value:.{digits}f}%"


def clamp(value: float, lower: float = 0.0, upper: float = 100.0) -> float:
    return max(lower, min(upper, value))


def format_token_amount(amount: Optional[float], symbol: str, digits: int = 4, empty_text: str = "") -> str:
    if amount is None:
        fallback_digits = max(2, digits)
        return empty_text or format_amount(0.0, fallback_digits)
    return f"{format_display_amount(amount, min_digits=2, max_digits=max(2, digits))} {symbol}".strip()


ERC20_BALANCE_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    }
]


def is_native_asset(asset: Dict[str, Any]) -> bool:
    return asset.get("address", "").lower() == "0x0000000000000000000000000000000000000000"


def get_asset_balance(asset: Dict[str, Any], wallet_address: str) -> Optional[float]:
    try:
        w3 = Web3(Web3.HTTPProvider(get_rpc_url(int(asset["chainId"]))))
        if is_native_asset(asset):
            raw_balance = w3.eth.get_balance(wallet_address)
        else:
            token_contract = w3.eth.contract(address=Web3.to_checksum_address(asset["address"]), abi=ERC20_BALANCE_ABI)
            raw_balance = token_contract.functions.balanceOf(wallet_address).call()
        return from_units(str(raw_balance), int(asset["decimals"]))
    except Exception:
        return None


def execution_status_label(executable: bool, lang: str) -> str:
    return tr(lang, "executor_status_ready") if executable else tr(lang, "executor_status_preview_only")


def execution_mode_label(mode: str, lang: str) -> str:
    key_map = {
        "preview": "execution_mode_preview_option",
        "demo_executor": "execution_mode_demo_option",
        "user_wallet": "execution_mode_user_option",
    }
    return tr(lang, key_map.get(mode, "execution_mode_preview_option"))


def execution_mode_title(mode: str, lang: str) -> str:
    key_map = {
        "preview": "execution_mode_preview_title",
        "demo_executor": "execution_mode_demo_title",
        "user_wallet": "execution_mode_user_title",
    }
    return tr(lang, key_map.get(mode, "execution_mode_preview_title"))


def execution_mode_note(mode: str, lang: str) -> str:
    key_map = {
        "preview": "execution_mode_preview_note",
        "demo_executor": "execution_mode_demo_note",
        "user_wallet": "execution_mode_user_note",
    }
    return tr(lang, key_map.get(mode, "execution_mode_preview_note"))


def execution_mode_badge(mode: str, lang: str) -> str:
    key_map = {
        "preview": "execution_mode_preview_badge",
        "demo_executor": "execution_mode_demo_badge",
        "user_wallet": "execution_mode_user_badge",
    }
    return tr(lang, key_map.get(mode, "execution_mode_preview_badge"))


def execution_mode_scope(mode: str, lang: str) -> str:
    key_map = {
        "preview": "execution_mode_preview_scope",
        "demo_executor": "execution_mode_demo_scope",
        "user_wallet": "execution_mode_user_scope",
    }
    return tr(lang, key_map.get(mode, "execution_mode_preview_scope"))


def execution_mode_actions(mode: str, lang: str) -> str:
    key_map = {
        "preview": "execution_mode_preview_actions",
        "demo_executor": "execution_mode_demo_actions",
        "user_wallet": "execution_mode_user_actions",
    }
    return tr(lang, key_map.get(mode, "execution_mode_preview_actions"))


def executor_address_status(mode: str, executor_account: Optional[Any], lang: str) -> str:
    if mode == "preview":
        return tr(lang, "executor_address_preview")
    if mode == "user_wallet":
        return tr(lang, "executor_address_user")
    if not executor_account:
        return tr(lang, "executor_address_unavailable")
    return format_address(executor_account.address, empty_text=tr(lang, "executor_address_unavailable"))


def standardization_balance_status(
    mode: str,
    executor_account: Optional[Any],
    balance: Optional[float],
    symbol: str,
    lang: str,
) -> str:
    if mode == "preview":
        return tr(lang, "executor_balance_preview")
    if mode == "user_wallet":
        return tr(lang, "executor_balance_user")
    if not executor_account:
        return tr(lang, "executor_balance_missing_wallet")
    if balance is None:
        return tr(lang, "executor_balance_unavailable")
    return format_token_amount(balance, symbol, 4, empty_text=tr(lang, "executor_balance_unavailable"))


def deployment_balance_status(
    mode: str,
    executor_account: Optional[Any],
    balance: Optional[float],
    symbol: str,
    show_keep_liquidity_analysis: bool,
    execution_vault: Optional[Dict[str, Any]],
    lang: str,
) -> str:
    if show_keep_liquidity_analysis:
        return tr(lang, "deployment_balance_keep")
    if mode == "preview":
        return tr(lang, "deployment_balance_preview")
    if mode == "user_wallet":
        return tr(lang, "deployment_balance_user")
    if not execution_vault:
        return tr(lang, "deployment_path_unavailable")
    if not executor_account:
        return tr(lang, "deployment_balance_missing_wallet")
    if balance is None:
        return tr(lang, "deployment_balance_unavailable")
    return format_token_amount(balance, symbol, 4, empty_text=tr(lang, "deployment_balance_unavailable"))


def execution_readiness_status(
    mode: str,
    executor_account: Optional[Any],
    executable: bool,
    *,
    show_keep_liquidity_analysis: bool = False,
    for_deployment: bool = False,
    execution_vault: Optional[Dict[str, Any]] = None,
    execution_metrics: Optional[Dict[str, Any]] = None,
    lang: str,
) -> str:
    if for_deployment and show_keep_liquidity_analysis:
        return tr(lang, "deployment_status_keep")
    if mode == "preview":
        return tr(lang, "executor_status_preview_mode")
    if mode == "user_wallet":
        return tr(lang, "executor_status_user_mode")
    if not executor_account:
        return tr(lang, "executor_status_missing_wallet")
    if for_deployment and (not execution_vault or not execution_metrics):
        return tr(lang, "deployment_path_unavailable")
    return execution_status_label(executable, lang)


def ratio_percent(numerator: float, denominator: float) -> Optional[float]:
    denominator = extract_number(denominator)
    if denominator <= 0:
        return None
    return (extract_number(numerator) / denominator) * 100.0


def estimate_payback_days(cost_usd: float, deployed_amount_usd: float, apy: float) -> Optional[float]:
    annual_yield_usd = extract_number(deployed_amount_usd) * max(extract_number(apy), 0.0) / 100.0
    if annual_yield_usd <= 0 or extract_number(cost_usd) <= 0:
        return None
    return (extract_number(cost_usd) / annual_yield_usd) * 365.0


def keep_time_fit_text(score: Optional[float], treasury_mode: str, lang: str) -> str:
    mode_text = mode_label(TREASURY_MODE_LABELS, treasury_mode, lang)
    if score is None:
        return tr(lang, "keep_reason_time_fit_unknown", mode=mode_text)
    rounded = int(round(score))
    if rounded >= 80:
        return tr(lang, "keep_reason_time_fit_high", mode=mode_text, score=rounded)
    if rounded >= 60:
        return tr(lang, "keep_reason_time_fit_mid", mode=mode_text, score=rounded)
    return tr(lang, "keep_reason_time_fit_low", mode=mode_text, score=rounded)


def build_keep_liquidity_items(
    payment_metrics: Dict[str, Any],
    treasury_mode: str,
    reference_vault: Optional[Dict[str, Any]],
    reference_deposit_metrics: Optional[Dict[str, Any]],
    lang: str,
) -> List[tuple[str, str]]:
    standardized_usd = extract_number(payment_metrics.get("toAmountUSD")) or extract_number(payment_metrics.get("toAmount"))
    standardization_cost_usd = extract_number(payment_metrics.get("gasUSD")) + extract_number(payment_metrics.get("feeUSD"))
    deployment_metrics = reference_deposit_metrics or (reference_vault or {}).get("previewMetrics") or {}
    has_deployment_metrics = bool(deployment_metrics)
    deployment_cost_usd = extract_number(deployment_metrics.get("gasUSD")) + extract_number(deployment_metrics.get("feeUSD"))
    total_cost_usd = standardization_cost_usd + deployment_cost_usd if has_deployment_metrics else None
    min_deploy_threshold_usd = (
        (total_cost_usd / COST_EFFICIENCY_RATIO_TARGET)
        if total_cost_usd is not None and total_cost_usd > 0
        else None
    )

    if min_deploy_threshold_usd is None:
        threshold_text = tr(lang, "keep_reason_threshold_unknown")
    elif standardized_usd < min_deploy_threshold_usd:
        threshold_text = tr(lang, "keep_reason_threshold_yes", threshold=format_usd(min_deploy_threshold_usd))
    else:
        threshold_text = tr(lang, "keep_reason_threshold_no", threshold=format_usd(min_deploy_threshold_usd))

    standardization_ratio = ratio_percent(standardization_cost_usd, standardized_usd)
    if standardization_ratio is None:
        standardization_ratio_text = tr(lang, "keep_reason_standardization_unavailable")
    else:
        standardization_ratio_text = tr(
            lang,
            "keep_reason_ratio_value",
            ratio=format_percent(standardization_ratio, empty_text=tr(lang, "keep_reason_standardization_unavailable")),
            amount=format_usd(standardization_cost_usd),
        )

    deployment_ratio = ratio_percent(deployment_cost_usd, standardized_usd)
    if has_deployment_metrics and deployment_ratio is not None:
        deployment_ratio_text = tr(
            lang,
            "keep_reason_ratio_value",
            ratio=format_percent(deployment_ratio, empty_text=tr(lang, "keep_reason_deployment_unavailable")),
            amount=format_usd(deployment_cost_usd),
        )
    else:
        deployment_ratio_text = tr(lang, "keep_reason_deployment_unavailable")

    apy = extract_number((reference_vault or {}).get("apy"))
    payback_days = estimate_payback_days(total_cost_usd or 0.0, standardized_usd, apy) if has_deployment_metrics else None
    payback_text = (
        tr(lang, "keep_reason_payback_value", days=int(round(payback_days)))
        if payback_days is not None
        else tr(lang, "keep_reason_payback_unavailable")
    )

    time_fit_score = None
    if reference_vault:
        time_fit_score = extract_number((reference_vault.get("scoreBreakdown") or {}).get("timeFit"))
    time_fit_text = keep_time_fit_text(time_fit_score, treasury_mode, lang)

    return [
        (tr(lang, "keep_reason_min_threshold"), threshold_text),
        (tr(lang, "keep_reason_standardization_cost"), standardization_ratio_text),
        (tr(lang, "keep_reason_deployment_cost"), deployment_ratio_text),
        (tr(lang, "keep_reason_payback"), payback_text),
        (tr(lang, "keep_reason_time_fit"), time_fit_text),
    ]


def tr(lang: str, key: str, **kwargs: Any) -> Any:
    value = I18N[lang][key]
    if isinstance(value, str):
        return value.format(**kwargs)
    return value


def mode_label(mapping: Dict[str, Dict[str, str]], value: str, lang: str) -> str:
    return mapping.get(value, {}).get(lang, value)


def decision_copy(lang: str, scenario: str, **kwargs: Any) -> Dict[str, str]:
    bundle = DECISION_COPY[lang][scenario]
    return {
        key: value.format(**kwargs) if isinstance(value, str) else value
        for key, value in bundle.items()
    }


def shorten(address: str) -> str:
    if len(address) < 12:
        return address
    return f"{address[:6]}...{address[-4:]}"


def format_address(address: Optional[str], empty_text: str = "") -> str:
    if not address:
        return empty_text
    return shorten(address)


def explorer_tx_url(chain_id: Optional[int], tx_hash: str) -> Optional[str]:
    if chain_id is None:
        return None
    template = EXPLORER_TX_URLS.get(int(chain_id))
    if not template:
        return None
    return template.format(tx_hash=tx_hash)


def proof_explorer_markup(url: Optional[str], label: str, empty_text: str) -> str:
    if not url:
        return empty_text
    return f'<a href="{url}" target="_blank">{label}</a>'


def parse_int(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned.startswith("0x"):
            return int(cleaned, 16)
        return int(cleaned)
    return int(value)


def normalize_vault(vault: Dict[str, Any]) -> Dict[str, Any]:
    protocol = first_present(vault, ["protocol", "provider", "project", "dex"], "Unknown")
    if isinstance(protocol, dict):
        protocol = first_present(protocol, ["name", "slug"], "Unknown")

    asset = first_present(vault, ["asset", "symbol", "depositTokenSymbol", "token", "name"], "Unknown")
    underlying_symbol = ""
    underlying_tokens = vault.get("underlyingTokens")
    if isinstance(underlying_tokens, list) and underlying_tokens:
        underlying_symbol = first_present(underlying_tokens[0], ["symbol", "name"], "")
        if asset == "Unknown":
            asset = underlying_symbol or asset

    tags = vault.get("tags", [])
    if not isinstance(tags, list):
        tags = []

    return {
        **vault,
        "id": first_present(vault, ["id", "vaultId", "vault_id", "slug"], ""),
        "vaultAddress": first_present(vault, ["vaultAddress", "address", "vault", "toToken"], ""),
        "chain": first_present(vault, ["chain", "chainName", "network", "fromChain"], "Unknown"),
        "chainId": first_present(vault, ["chainId"], None),
        "protocol": protocol,
        "apy": extract_number(
            first_present(vault, ["apy", "apr", "netApy", "projectedApy"], nested_get(vault, ["analytics", "apy", "total"], 0.0))
        ),
        "tvl": extract_number(
            first_present(vault, ["tvl", "tvlUsd", "totalValueLocked", "tvlUSD"], nested_get(vault, ["analytics", "tvl", "usd"], 0.0))
        ),
        "asset": asset,
        "underlyingSymbol": underlying_symbol,
        "tags": tags,
        "isTransactional": bool(vault.get("isTransactional")),
        "isRedeemable": bool(vault.get("isRedeemable")),
        "depositPacks": vault.get("depositPacks", []),
    }


def fetch_vaults() -> List[Dict[str, Any]]:
    response = requests.get(f"{EARN_BASE_URL}/earn/vaults", headers=HEADERS, timeout=30)
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, list):
        vaults = payload
    elif isinstance(payload, dict):
        vaults = first_present(payload, ["vaults", "data", "items", "results"], [])
    else:
        vaults = []
    return [normalize_vault(v) for v in vaults if isinstance(v, dict)]


def is_stable_vault(vault: Dict[str, Any]) -> bool:
    if "stablecoin" in vault.get("tags", []):
        return True
    if vault.get("asset") in STABLE_SYMBOLS:
        return True
    if vault.get("underlyingSymbol") in STABLE_SYMBOLS:
        return True
    return False


def clean_vaults(vaults: List[Dict[str, Any]], risk_mode: str) -> List[Dict[str, Any]]:
    filtered = [
        vault for vault in vaults
        if vault.get("chain") in SAFE_CHAINS
        and vault.get("vaultAddress")
        and vault.get("chainId")
        and vault.get("isTransactional")
        and is_stable_vault(vault)
        and extract_number(vault.get("tvl")) >= TVL_MIN_USD
        and extract_number(vault.get("apy")) >= 1.0
    ]

    if risk_mode == "稳健":
        filtered.sort(
            key=lambda vault: (
                extract_number(vault.get("tvl")),
                extract_number(vault.get("apy")),
                1 if vault.get("chain") == "Base" else 0,
            ),
            reverse=True,
        )
    else:
        filtered.sort(
            key=lambda vault: (
                extract_number(vault.get("apy")),
                extract_number(vault.get("tvl")),
                1 if vault.get("chain") == "Base" else 0,
            ),
            reverse=True,
        )

    return filtered[:TOP_VAULTS_LIMIT]


def fetch_quote(params: Dict[str, str]) -> Dict[str, Any]:
    response = requests.get(f"{QUOTE_BASE_URL}/quote", headers=HEADERS, params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_payment_quote(source_asset: Dict[str, Any], amount: float, from_address: str = PREVIEW_ADDRESS) -> Dict[str, Any]:
    params = {
        "fromChain": str(source_asset["chainId"]),
        "fromToken": source_asset["address"],
        "toChain": str(SETTLEMENT_TOKEN["chainId"]),
        "toToken": SETTLEMENT_TOKEN["address"],
        "fromAmount": to_units(amount, source_asset["decimals"]),
        "fromAddress": from_address,
    }
    return fetch_quote(params)


def fetch_deposit_quote(vault: Dict[str, Any], settle_amount_raw: str, from_address: str = PREVIEW_ADDRESS) -> Dict[str, Any]:
    params = {
        "fromChain": str(SETTLEMENT_TOKEN["chainId"]),
        "fromToken": SETTLEMENT_TOKEN["address"],
        "toChain": str(vault["chainId"]),
        "toToken": vault["vaultAddress"],
        "fromAmount": settle_amount_raw,
        "fromAddress": from_address,
    }
    return fetch_quote(params)


def quote_to_metrics(quote: Dict[str, Any]) -> Dict[str, Any]:
    action = quote.get("action", {})
    estimate = quote.get("estimate", {})
    from_token = action.get("fromToken", {})
    to_token = action.get("toToken", {})
    gas_costs = estimate.get("gasCosts", []) or []
    fee_costs = estimate.get("feeCosts", []) or []

    gas_usd = sum(extract_number(cost.get("amountUSD")) for cost in gas_costs)
    fee_usd = sum(extract_number(cost.get("amountUSD")) for cost in fee_costs)

    to_amount = 0.0
    raw_to_amount = estimate.get("toAmount")
    if raw_to_amount and to_token.get("decimals") is not None:
        to_amount = from_units(str(raw_to_amount), int(to_token["decimals"]))

    from_amount = 0.0
    raw_from_amount = action.get("fromAmount") or estimate.get("fromAmount")
    if raw_from_amount and from_token.get("decimals") is not None:
        from_amount = from_units(str(raw_from_amount), int(from_token["decimals"]))

    raw_min_received = (
        estimate.get("toAmountMin")
        or estimate.get("minAmountOut")
        or quote.get("toAmountMin")
        or quote.get("minAmountOut")
        or action.get("toAmountMin")
        or action.get("minAmountOut")
    )
    min_received = None
    if raw_min_received and to_token.get("decimals") is not None:
        try:
            min_received = from_units(str(raw_min_received), int(to_token["decimals"]))
        except Exception:
            min_received = None
    if min_received is None and to_amount:
        min_received = to_amount

    return {
        "tool": first_present(quote, ["tool"], "unknown"),
        "toolName": nested_get(quote, ["toolDetails", "name"], first_present(quote, ["tool"], "unknown")),
        "fromToken": from_token.get("symbol", ""),
        "toToken": to_token.get("symbol", ""),
        "fromChainId": action.get("fromChainId"),
        "toChainId": action.get("toChainId"),
        "fromAmount": from_amount,
        "toAmount": to_amount,
        "fromAmountUSD": extract_number(estimate.get("fromAmountUSD")),
        "toAmountUSD": extract_number(estimate.get("toAmountUSD")),
        "gasUSD": gas_usd,
        "feeUSD": fee_usd,
        "minReceived": min_received,
        "rawMinReceived": str(raw_min_received or ""),
        "rawToAmount": str(raw_to_amount or "0"),
    }


def score_vault_candidates(
    vaults: List[Dict[str, Any]],
    payment_metrics: Dict[str, Any],
    risk_mode: str,
    treasury_mode: str,
) -> List[Dict[str, Any]]:
    if not vaults:
        return []

    apys = [extract_number(vault.get("apy")) for vault in vaults]
    tvls = [max(extract_number(vault.get("tvl")), TVL_MIN_USD) for vault in vaults]
    max_apy = max(max(apys), 1.0)
    min_tvl = min(tvls)
    max_tvl = max(tvls)
    settle_usd = max(payment_metrics.get("toAmountUSD") or 0.0, payment_metrics.get("toAmount") or 0.0, 1.0)

    conservative_chain_scores = {"Base": 100, "Ethereum": 88, "Arbitrum": 74, "Optimism": 70}
    growth_chain_scores = {"Base": 92, "Ethereum": 82, "Arbitrum": 86, "Optimism": 84}

    scored: List[Dict[str, Any]] = []
    for vault in vaults:
        preview_metrics = vault.get("previewMetrics", {})
        route_cost_usd = extract_number(preview_metrics.get("gasUSD")) + extract_number(preview_metrics.get("feeUSD"))
        route_cost_ratio = route_cost_usd / settle_usd if settle_usd else 0.0

        apy_score = clamp((extract_number(vault.get("apy")) / max_apy) * 100.0)
        if max_tvl == min_tvl:
            tvl_score = 100.0
        else:
            tvl_score = clamp(((max(extract_number(vault.get("tvl")), TVL_MIN_USD) - min_tvl) / (max_tvl - min_tvl)) * 100.0)

        if route_cost_ratio <= 0.003:
            route_cost_score = 100.0
        elif route_cost_ratio <= 0.01:
            route_cost_score = 86.0
        elif route_cost_ratio <= 0.02:
            route_cost_score = 68.0
        elif route_cost_ratio <= 0.05:
            route_cost_score = 42.0
        else:
            route_cost_score = 18.0

        chain_score_table = conservative_chain_scores if risk_mode == "稳健" else growth_chain_scores
        chain_score = float(chain_score_table.get(vault.get("chain"), 60))

        if treasury_mode == "今天就要用":
            base_time_score = {"Base": 26, "Ethereum": 20, "Arbitrum": 14, "Optimism": 12}
        elif treasury_mode == "可以放一阵子":
            base_time_score = {"Base": 90, "Ethereum": 82, "Arbitrum": 74, "Optimism": 72}
        else:
            base_time_score = {"Base": 96, "Ethereum": 88, "Arbitrum": 84, "Optimism": 82}
        time_fit_score = float(base_time_score.get(vault.get("chain"), 68))
        if route_cost_ratio > 0.02:
            time_fit_score -= 14
        if route_cost_ratio > 0.05:
            time_fit_score -= 18
        time_fit_score = clamp(time_fit_score)

        executable = bool(vault.get("previewQuote"))
        executable_score = 100.0 if executable else 0.0
        total_score = round(
            (
                apy_score * 0.18
                + tvl_score * 0.24
                + route_cost_score * 0.18
                + chain_score * 0.16
                + time_fit_score * 0.24
            )
            * (executable_score / 100.0)
        )

        scored.append(
            {
                **vault,
                "scoreBreakdown": {
                    "apy": round(apy_score),
                    "tvl": round(tvl_score),
                    "routeCost": round(route_cost_score),
                    "chainPreference": round(chain_score),
                    "timeFit": round(time_fit_score),
                    "executable": executable,
                    "executableScore": round(executable_score),
                    "total": int(total_score),
                },
                "routeCostUSD": route_cost_usd,
                "thresholdMet": executable and total_score >= RECOMMENDATION_SCORE_THRESHOLD,
            }
        )

    return sorted(
        scored,
        key=lambda vault: (
            vault["thresholdMet"],
            vault["scoreBreakdown"]["total"],
            extract_number(vault.get("apy")),
            extract_number(vault.get("tvl")),
        ),
        reverse=True,
    )


def render_score_breakdown(vault: Dict[str, Any], lang: str) -> None:
    scores = vault.get("scoreBreakdown", {})
    executable_text = tr(lang, "score_yes") if scores.get("executable") else tr(lang, "score_no")
    rows = [
        (tr(lang, "score_apy"), f"{scores.get('apy', 0)}/100"),
        (tr(lang, "score_tvl"), f"{scores.get('tvl', 0)}/100"),
        (tr(lang, "score_route_cost"), f"{scores.get('routeCost', 0)}/100"),
        (tr(lang, "score_chain_preference"), f"{scores.get('chainPreference', 0)}/100"),
        (tr(lang, "score_time_fit"), f"{scores.get('timeFit', 0)}/100"),
        (tr(lang, "score_executable"), executable_text),
        (tr(lang, "score_total"), f"{scores.get('total', 0)}/100"),
    ]
    rows_html = "".join(
        f"""
        <div class="score-row">
          <span>{label}</span>
          <strong>{value}</strong>
        </div>
        """
        for label, value in rows
    )
    st.markdown(
        f"""
        <div class="score-card">
          <div class="score-card-top">
            <div class="mini-kicker">{tr(lang, "score_heading")}</div>
            <span class="vault-badge">{tr(lang, "threshold_badge", value=RECOMMENDATION_SCORE_THRESHOLD)}</span>
          </div>
          <div class="score-grid">
            {rows_html}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_recommendation_reasons(vault: Dict[str, Any], risk_mode: str, treasury_mode: str, lang: str) -> List[str]:
    reasons: List[str] = []
    scores = vault.get("scoreBreakdown", {})
    if scores.get("executable"):
        reasons.append(tr(lang, "reason_executable"))
    if scores.get("tvl", 0) >= 75:
        reasons.append(tr(lang, "reason_tvl_high", tvl=format_usd(extract_number(vault.get("tvl")))))
    if scores.get("routeCost", 0) >= 70:
        reasons.append(tr(lang, "reason_route_cost_low", cost=format_usd(extract_number(vault.get("routeCostUSD")))))
    if scores.get("chainPreference", 0) >= 80:
        reasons.append(tr(lang, "reason_chain_fit", chain=vault.get("chain", "Unknown")))
    if scores.get("timeFit", 0) >= 75:
        reasons.append(tr(lang, "reason_time_fit", horizon=mode_label(TREASURY_MODE_LABELS, treasury_mode, lang)))
    if scores.get("apy", 0) >= 75:
        reasons.append(tr(lang, "reason_apy_high", apy=f"{format_amount(extract_number(vault.get('apy')), 2)}%"))
    if not reasons:
        reasons.append(tr(lang, "reason_default_recommended"))
    return reasons[:3]


def build_candidate_reasons(
    vault: Dict[str, Any],
    reference_vault: Optional[Dict[str, Any]],
    lang: str,
) -> List[str]:
    reasons: List[str] = []
    scores = vault.get("scoreBreakdown", {})
    reference_scores = (reference_vault or {}).get("scoreBreakdown", {})

    if not scores.get("executable"):
        reasons.append(tr(lang, "candidate_reason_not_executable"))
    if reference_vault:
        if scores.get("tvl", 0) < reference_scores.get("tvl", 0):
            reasons.append(tr(lang, "candidate_reason_lower_tvl"))
        if extract_number(vault.get("routeCostUSD")) > extract_number(reference_vault.get("routeCostUSD")):
            reasons.append(tr(lang, "candidate_reason_higher_route_cost"))
        if scores.get("chainPreference", 0) < reference_scores.get("chainPreference", 0):
            reasons.append(tr(lang, "candidate_reason_risk_mismatch"))
        if scores.get("timeFit", 0) < reference_scores.get("timeFit", 0):
            reasons.append(tr(lang, "candidate_reason_time_mismatch"))
        if scores.get("apy", 0) < reference_scores.get("apy", 0):
            reasons.append(tr(lang, "candidate_reason_lower_apy"))
    else:
        if scores.get("tvl", 0) < 70:
            reasons.append(tr(lang, "candidate_reason_lower_tvl"))
        if scores.get("routeCost", 0) < 70:
            reasons.append(tr(lang, "candidate_reason_higher_route_cost"))
        if scores.get("chainPreference", 0) < 75:
            reasons.append(tr(lang, "candidate_reason_risk_mismatch"))
        if scores.get("timeFit", 0) < 75:
            reasons.append(tr(lang, "candidate_reason_time_mismatch"))
    if not vault.get("thresholdMet"):
        reasons.append(tr(lang, "candidate_reason_below_threshold"))
    if not reasons:
        reasons.append(tr(lang, "reason_default_candidate"))
    return reasons[:3]


def render_reason_list(
    heading: str,
    kicker: str,
    reasons: List[str],
    lang: str,
    position_text: Optional[str] = None,
) -> None:
    safe_reasons = reasons or [tr(lang, "reason_default_candidate")]
    items_html = "".join(f"<li>{reason}</li>" for reason in safe_reasons)
    position_html = ""
    if position_text:
        position_html = f"""
        <div class="reason-position">
          <span>{tr(lang, "reason_position_label")}</span>
          <strong>{position_text}</strong>
        </div>
        """
    st.markdown(
        f"""
        <div class="reason-card">
          <div class="score-card-top">
            <div class="mini-kicker">{kicker}</div>
            <span class="vault-badge">{heading}</span>
          </div>
          {position_html}
          <ul class="reason-list">
            {items_html}
          </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def summarize_other_candidates(
    scored_vaults: List[Dict[str, Any]],
    selected_vault: Optional[Dict[str, Any]],
    lang: str,
) -> str:
    if not scored_vaults:
        return tr(lang, "transparency_other_reason_default")
    if not selected_vault:
        return tr(lang, "transparency_other_reason_below_threshold")

    others = [vault for vault in scored_vaults if vault.get("id") != selected_vault.get("id")]
    if not others:
        return tr(lang, "transparency_other_reason_default")

    metric_counts = {
        tr(lang, "score_route_cost"): 0,
        tr(lang, "score_tvl"): 0,
        tr(lang, "score_chain_preference"): 0,
        tr(lang, "score_time_fit"): 0,
        tr(lang, "score_apy"): 0,
    }
    selected_scores = selected_vault.get("scoreBreakdown", {})
    for vault in others:
        scores = vault.get("scoreBreakdown", {})
        if scores.get("routeCost", 0) < selected_scores.get("routeCost", 0):
            metric_counts[tr(lang, "score_route_cost")] += 1
        if scores.get("tvl", 0) < selected_scores.get("tvl", 0):
            metric_counts[tr(lang, "score_tvl")] += 1
        if scores.get("chainPreference", 0) < selected_scores.get("chainPreference", 0):
            metric_counts[tr(lang, "score_chain_preference")] += 1
        if scores.get("timeFit", 0) < selected_scores.get("timeFit", 0):
            metric_counts[tr(lang, "score_time_fit")] += 1
        if scores.get("apy", 0) < selected_scores.get("apy", 0):
            metric_counts[tr(lang, "score_apy")] += 1

    top_reasons = [label for label, count in sorted(metric_counts.items(), key=lambda item: item[1], reverse=True) if count > 0][:2]
    if not top_reasons:
        return tr(lang, "transparency_other_reason_default")
    joined = "、".join(top_reasons) if lang == "zh" else ", ".join(top_reasons)
    if lang == "zh":
        return f"其他候选的综合评分较低，主要体现在 {joined}。"
    return f"Other candidates scored lower overall, mainly due to weaker {joined}."


def record_execution_proof(
    action: str,
    tx_hash: str,
    amount_usd: float,
    *,
    chain_id: Optional[int] = None,
    chain_name: str = "",
    token: str = "",
    input_amount: Optional[float] = None,
    mode: str = "demo_executor",
) -> None:
    records = st.session_state.get("execution_proof_records", [])
    records.insert(
        0,
        {
            "action": action,
            "tx_hash": tx_hash,
            "amount_usd": amount_usd,
            "chain_id": chain_id,
            "chain_name": chain_name,
            "token": token,
            "input_amount": input_amount,
            "mode": mode,
            "explorer_url": explorer_tx_url(chain_id, tx_hash),
            "proof_eligible": amount_usd <= DEMO_PROOF_USD_THRESHOLD,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
    )
    st.session_state["execution_proof_records"] = records[:12]


def render_step_card(step: str, title: str, body: str, accent: str, lang: str) -> None:
    st.markdown(
        f"""
        <div class="step-card">
          <div class="step-chip" style="border-color:{accent}; color:{accent};">{tr(lang, "step_prefix")} {step}</div>
          <h3>{title}</h3>
          <p>{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_vault_card(vault: Dict[str, Any], badge: str = "", lang: str = "zh") -> None:
    badge_html = f'<span class="vault-badge">{badge}</span>' if badge else ""
    unknown = tr(lang, "unknown_label")
    protocol = vault.get("protocol")
    asset = vault.get("asset")
    chain = vault.get("chain")
    protocol = unknown if protocol in (None, "", "Unknown") else protocol
    asset = unknown if asset in (None, "", "Unknown") else asset
    chain = unknown if chain in (None, "", "Unknown") else chain
    st.markdown(
        f"""
        <div class="vault-card">
          <div class="vault-top">
            <div>
              <div class="vault-title">{protocol} · {asset}</div>
              <div class="vault-sub">{chain} · {format_address(vault.get("vaultAddress", ""))}</div>
            </div>
            {badge_html}
          </div>
          <div class="vault-metrics">
            <div><span>APY</span><strong>{format_amount(extract_number(vault.get("apy")), 2)}%</strong></div>
            <div><span>TVL</span><strong>{format_usd(extract_number(vault.get("tvl")))}</strong></div>
            <div><span>{tr(lang, "vault_metric_pack_label")}</span><strong>{len(vault.get("depositPacks", [])) or 1}</strong></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def deterministic_decision(vaults: List[Dict[str, Any]], settle_amount: float, risk_mode: str, treasury_mode: str, lang: str = "zh") -> Dict[str, Any]:
    unknown = tr(lang, "unknown_label")
    if treasury_mode == "今天就要用":
        copy = decision_copy(lang, "immediate")
        return {
            "action": "keep_usdt",
            "recommended_vault_id": "",
            "headline": copy["headline"],
            "rationale": copy["rationale"],
            "risk_note": copy["risk_note"],
            "best_for": copy["best_for"],
            "confidence": 82,
        }

    if not vaults:
        copy = decision_copy(lang, "no_vaults")
        return {
            "action": "keep_usdt",
            "recommended_vault_id": "",
            "headline": copy["headline"],
            "rationale": copy["rationale"],
            "risk_note": copy["risk_note"],
            "best_for": copy["best_for"],
            "confidence": 78,
        }

    if settle_amount < 50 and treasury_mode != "尽量赚收益":
        copy = decision_copy(lang, "small_amount")
        return {
            "action": "keep_usdt",
            "recommended_vault_id": "",
            "headline": copy["headline"],
            "rationale": copy["rationale"],
            "risk_note": copy["risk_note"],
            "best_for": copy["best_for"],
            "confidence": 76,
        }

    preferred = next((vault for vault in vaults if vault.get("chain") == "Base"), vaults[0])
    if risk_mode == "进攻":
        preferred = sorted(vaults, key=lambda vault: (extract_number(vault.get("apy")), extract_number(vault.get("tvl"))), reverse=True)[0]
    elif treasury_mode == "可以放一阵子":
        preferred = sorted(
            vaults,
            key=lambda vault: (vault.get("chain") == "Base", extract_number(vault.get("tvl")), extract_number(vault.get("apy"))),
            reverse=True,
        )[0]

    copy = decision_copy(
        lang,
        "deploy",
        protocol=preferred.get("protocol") if preferred.get("protocol") not in (None, "", "Unknown") else unknown,
        chain=preferred.get("chain") if preferred.get("chain") not in (None, "", "Unknown") else unknown,
        tvl=format_usd(extract_number(preferred.get("tvl"))),
        apy=f"{format_amount(extract_number(preferred.get('apy')), 2)}%",
    )
    return {
        "action": "deposit",
        "recommended_vault_id": preferred.get("id", ""),
        "headline": copy["headline"],
        "rationale": copy["rationale"],
        "risk_note": copy["risk_note"],
        "best_for": copy["best_for"],
        "confidence": 84,
    }


def run_ai_treasury_decision(vaults: List[Dict[str, Any]], settle_amount: float, risk_mode: str, treasury_mode: str, lang: str = "zh") -> Dict[str, Any]:
    fallback = deterministic_decision(vaults, settle_amount, risk_mode, treasury_mode, lang=lang)
    if not OPENAI_API_KEY or OPENAI_API_KEY.startswith("YOUR_"):
        return fallback

    brief_vaults = [
        {
            "id": vault.get("id"),
            "chain": vault.get("chain"),
            "protocol": vault.get("protocol"),
            "asset": vault.get("asset"),
            "apy": round(extract_number(vault.get("apy")), 4),
            "tvl": round(extract_number(vault.get("tvl")), 2),
        }
        for vault in vaults[:5]
    ]

    client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
    if lang == "zh":
        system_prompt = """你是 Treasury Copilot 的 AI treasury decision engine。
只输出一个 JSON 对象，不要 markdown，不要解释。
格式必须是：
{"action":"keep_usdt|deposit","recommended_vault_id":"string","headline":"string","rationale":"string","risk_note":"string","best_for":"string","confidence":number}
规则：
1. 只能在给定 vault 列表中选，或者选择 keep_usdt。
2. 今天就要用的钱优先 keep_usdt。
3. 稳健模式优先 Base / Ethereum / TVL 更厚的池子。
4. 进攻模式可以追 APY，但不要忽略 TVL。
5. 文案必须中文，语气简洁、稳定、专业，适合正式产品 demo。
6. AI 负责解释决策，不要伪造链上执行细节。"""
    else:
        system_prompt = """You are Treasury Copilot's AI treasury decision engine.
Output one JSON object only, with no markdown and no explanation outside the JSON.
Required format:
{"action":"keep_usdt|deposit","recommended_vault_id":"string","headline":"string","rationale":"string","risk_note":"string","best_for":"string","confidence":number}
Rules:
1. Choose only from the provided vault list, or choose keep_usdt.
2. If the funds are needed soon, prefer keep_usdt.
3. In conservative mode, prefer Base or Ethereum and thicker TVL.
4. In growth mode, higher APY is acceptable, but do not ignore TVL.
5. Use concise professional English product copy.
6. Explain the decision, but do not invent execution details."""

    try:
        completion = client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "settlement_asset": "Base USDT",
                            "settlement_amount": settle_amount,
                            "risk_mode": mode_label(RISK_MODE_LABELS, risk_mode, lang),
                            "treasury_mode": mode_label(TREASURY_MODE_LABELS, treasury_mode, lang),
                            "vaults": brief_vaults,
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
        )
        parsed = json.loads(completion.choices[0].message.content or "{}")
        if parsed.get("action") not in {"keep_usdt", "deposit"}:
            return fallback
        if parsed.get("action") == "deposit" and parsed.get("recommended_vault_id"):
            matched = next((vault for vault in vaults if vault.get("id") == parsed.get("recommended_vault_id")), None)
            if not matched:
                return fallback
        return {
            "action": parsed.get("action", fallback["action"]),
            "recommended_vault_id": parsed.get("recommended_vault_id", ""),
            "headline": parsed.get("headline", fallback["headline"]),
            "rationale": parsed.get("rationale", fallback["rationale"]),
            "risk_note": parsed.get("risk_note", fallback["risk_note"]),
            "best_for": parsed.get("best_for", fallback["best_for"]),
            "confidence": int(extract_number(parsed.get("confidence"), fallback["confidence"])),
        }
    except Exception:
        return fallback


def select_quotable_vaults(vaults: List[Dict[str, Any]], settle_amount_raw: str, limit: int = 3) -> List[Dict[str, Any]]:
    selected: List[Dict[str, Any]] = []
    for vault in vaults:
        try:
            quote = fetch_deposit_quote(vault, settle_amount_raw)
            enriched = {**vault, "previewQuote": quote, "previewMetrics": quote_to_metrics(quote)}
            selected.append(enriched)
        except Exception:
            continue
        if len(selected) >= limit:
            break
    return selected


def get_account() -> Optional[Any]:
    if not BURNER_PRIVATE_KEY:
        return None
    return Web3().eth.account.from_key(BURNER_PRIVATE_KEY)


def get_rpc_url(chain_id: int) -> str:
    config = CHAIN_CONFIG.get(chain_id)
    if not config or not config.get("rpc"):
        raise RuntimeError(f"缺少 chainId={chain_id} 的 RPC 配置。")
    return config["rpc"]


def broadcast_tx(quote: Dict[str, Any]) -> str:
    tx_req = quote.get("transactionRequest", {})
    if not tx_req:
        raise RuntimeError("quote 中没有 transactionRequest，无法广播。")

    chain_id = parse_int(tx_req.get("chainId") or nested_get(quote, ["action", "fromChainId"]) or 8453)
    w3 = Web3(Web3.HTTPProvider(get_rpc_url(chain_id)))
    account = w3.eth.account.from_key(BURNER_PRIVATE_KEY)

    tx = {
        "from": account.address,
        "to": Web3.to_checksum_address(tx_req["to"]),
        "data": tx_req["data"],
        "value": parse_int(tx_req.get("value", "0x0")),
        "chainId": chain_id,
        "nonce": w3.eth.get_transaction_count(account.address),
    }

    if tx_req.get("gasLimit"):
        tx["gas"] = parse_int(tx_req["gasLimit"])
    if tx_req.get("gasPrice"):
        tx["gasPrice"] = parse_int(tx_req["gasPrice"])
    if tx_req.get("maxFeePerGas"):
        tx["maxFeePerGas"] = parse_int(tx_req["maxFeePerGas"])
    if tx_req.get("maxPriorityFeePerGas"):
        tx["maxPriorityFeePerGas"] = parse_int(tx_req["maxPriorityFeePerGas"])

    signed = w3.eth.account.sign_transaction(tx, BURNER_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    return tx_hash.hex()


def payment_option_by_label(label: str) -> Dict[str, Any]:
    return next(asset for asset in PAYMENT_ASSETS if asset["label"] == label)


def render_styles() -> None:
    st.markdown(
        """
        <style>
          @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

          :root {
            --bg: #f4efe6;
            --ink: #1f1d1a;
            --muted: #6f665e;
            --card: rgba(255, 252, 246, 0.84);
            --line: rgba(45, 40, 34, 0.12);
            --field-bg: rgba(255, 252, 247, 0.98);
            --field-bg-hover: rgba(255, 250, 243, 1);
            --field-border: rgba(45, 40, 34, 0.18);
            --field-border-strong: rgba(239, 108, 52, 0.45);
            --field-text: #1f1d1a;
            --field-label: #5d554d;
            --field-placeholder: #8c837a;
            --orange: #ef6c34;
            --teal: #0f766e;
            --gold: #c28f2c;
            --plum: #6f4ca5;
          }

          .stApp {
            background:
              radial-gradient(circle at 8% 8%, rgba(239, 108, 52, 0.16), transparent 28%),
              radial-gradient(circle at 92% 12%, rgba(15, 118, 110, 0.16), transparent 24%),
              linear-gradient(180deg, #f5f0e7 0%, #efe7dc 48%, #ece2d4 100%);
            color: var(--ink);
          }

          .block-container {
            padding-top: 1.15rem;
            padding-bottom: 2.75rem;
            max-width: 1180px;
          }

          html, body, [class*="css"] {
            font-family: 'Space Grotesk', sans-serif;
            color: var(--ink);
          }

          [data-testid="stSelectbox"] label p,
          [data-testid="stNumberInput"] label p,
          [data-testid="stTextInput"] label p,
          [data-testid="stTextArea"] label p {
            color: var(--field-label) !important;
            font-weight: 600 !important;
            letter-spacing: 0.01em;
          }

          [data-testid="stSelectbox"] [data-baseweb="select"] > div,
          [data-testid="stNumberInput"] input,
          [data-testid="stTextInput"] input,
          [data-testid="stTextArea"] textarea {
            background: var(--field-bg) !important;
            color: var(--field-text) !important;
            -webkit-text-fill-color: var(--field-text) !important;
            border-radius: 16px !important;
            border: 1.5px solid var(--field-border) !important;
            box-shadow: 0 1px 0 rgba(255, 255, 255, 0.65) inset, 0 8px 18px rgba(77, 59, 37, 0.05) !important;
            transition: border-color 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
          }

          [data-testid="stSelectbox"] [data-baseweb="select"] > div:hover,
          [data-testid="stNumberInput"] input:hover,
          [data-testid="stTextInput"] input:hover,
          [data-testid="stTextArea"] textarea:hover {
            background: var(--field-bg-hover) !important;
            border-color: rgba(45, 40, 34, 0.26) !important;
          }

          [data-testid="stSelectbox"] [data-baseweb="select"] > div:focus-within,
          [data-testid="stNumberInput"] input:focus,
          [data-testid="stTextInput"] input:focus,
          [data-testid="stTextArea"] textarea:focus {
            background: #fffdf9 !important;
            border-color: var(--field-border-strong) !important;
            box-shadow: 0 0 0 3px rgba(239, 108, 52, 0.12), 0 10px 22px rgba(77, 59, 37, 0.08) !important;
            outline: none !important;
          }

          [data-testid="stSelectbox"] [data-baseweb="select"] input,
          [data-testid="stSelectbox"] [data-baseweb="select"] span,
          [data-testid="stSelectbox"] [data-baseweb="select"] div,
          [data-testid="stNumberInput"] input,
          [data-testid="stTextInput"] input,
          [data-testid="stTextArea"] textarea,
          div[data-baseweb="popover"] *,
          div[role="listbox"] * {
            color: var(--field-text) !important;
            -webkit-text-fill-color: var(--field-text) !important;
          }

          [data-testid="stSelectbox"] [data-baseweb="select"] > div > div,
          [data-testid="stSelectbox"] [data-baseweb="select"] span,
          [data-testid="stNumberInput"] input,
          [data-testid="stTextInput"] input,
          [data-testid="stTextArea"] textarea {
            font-weight: 600 !important;
          }

          [data-testid="stNumberInput"] input::placeholder,
          [data-testid="stTextInput"] input::placeholder,
          [data-testid="stSelectbox"] [data-baseweb="select"] input::placeholder,
          [data-testid="stTextArea"] textarea::placeholder {
            color: var(--field-placeholder) !important;
            -webkit-text-fill-color: var(--field-placeholder) !important;
            opacity: 1 !important;
            font-weight: 500 !important;
          }

          div[data-baseweb="popover"],
          div[role="listbox"] {
            background: #fffaf3 !important;
            border: 1px solid rgba(45, 40, 34, 0.12) !important;
            box-shadow: 0 18px 34px rgba(77, 59, 37, 0.14) !important;
          }

          div[role="option"],
          li[role="option"] {
            color: var(--field-text) !important;
            background: #fffaf3 !important;
            font-weight: 500 !important;
          }

          div[role="option"][aria-selected="true"],
          li[role="option"][aria-selected="true"] {
            background: rgba(239, 108, 52, 0.14) !important;
            color: #1a1714 !important;
            font-weight: 700 !important;
          }

          div[role="option"]:hover,
          li[role="option"]:hover {
            background: rgba(15, 118, 110, 0.08) !important;
          }

          label p,
          .stCaption,
          .stMarkdown p {
            color: var(--ink) !important;
          }

          .topbar-note {
            padding-top: 0.45rem;
            color: var(--muted);
            font-size: 0.86rem;
          }

          .lang-kicker {
            text-align: right;
            color: var(--muted);
            font-size: 0.72rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            margin-bottom: 0.25rem;
          }

          [data-testid="stRadio"] > div {
            justify-content: flex-end;
            gap: 0.45rem;
          }

          [data-testid="stRadio"] label {
            background: rgba(255,255,255,0.80);
            border: 1px solid var(--line);
            padding: 0.28rem 0.8rem;
            border-radius: 999px;
          }

          [data-testid="stRadio"] label p {
            font-size: 0.9rem !important;
          }

          .hero {
            background: linear-gradient(145deg, rgba(255,248,239,0.90), rgba(255,245,235,0.70));
            border: 1px solid rgba(45,40,34,0.09);
            border-radius: 24px;
            padding: 14px 18px;
            box-shadow: 0 14px 36px rgba(77, 59, 37, 0.07);
            margin-bottom: 12px;
          }

          .hero-grid {
            display: grid;
            grid-template-columns: minmax(0, 1.1fr) minmax(260px, 0.9fr);
            gap: 16px;
            align-items: end;
          }

          .hero h1 {
            margin: 0;
            font-size: 2.08rem;
            line-height: 0.96;
            letter-spacing: -0.04em;
          }

          .hero p {
            margin: 0;
            color: var(--muted);
            max-width: 640px;
            font-size: 0.92rem;
            line-height: 1.55;
          }

          .badge-row {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-bottom: 8px;
          }

          .badge {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 6px 11px;
            font-size: 0.76rem;
            background: rgba(255,255,255,0.74);
            border: 1px solid rgba(45,40,34,0.10);
            color: var(--ink);
          }

          .aside-card, .step-card, .decision-card, .summary-card, .vault-card {
            background: var(--card);
            border: 1px solid rgba(45,40,34,0.08);
            border-radius: 24px;
            box-shadow: 0 18px 44px rgba(77, 59, 37, 0.09);
          }

          .aside-card {
            padding: 16px 18px;
            min-height: unset;
            background: rgba(255, 251, 245, 0.72);
            box-shadow: 0 12px 28px rgba(77, 59, 37, 0.06);
          }

          .aside-card h3 {
            font-size: 1.08rem;
            line-height: 1.22;
          }

          [data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(255, 252, 246, 0.88);
            border: 1px solid rgba(45, 40, 34, 0.10);
            border-radius: 24px;
            box-shadow: 0 20px 46px rgba(77, 59, 37, 0.10);
            padding: 0.25rem 0.15rem;
          }

          .panel-kicker-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 0.1rem;
          }

          .panel-note {
            color: var(--muted);
            font-size: 0.84rem;
            line-height: 1.45;
            margin: 0 0 0.3rem;
          }

          .mini-kicker {
            font-size: 0.74rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: var(--muted);
            margin-bottom: 8px;
          }

          .stat-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 12px;
            margin-top: 16px;
          }

          .stat {
            background: rgba(255,255,255,0.56);
            border-radius: 18px;
            padding: 14px;
            border: 1px solid rgba(45,40,34,0.06);
          }

          .stat span {
            display: block;
            color: var(--muted);
            font-size: 0.78rem;
            margin-bottom: 6px;
          }

          .stat strong {
            font-size: 1.05rem;
            white-space: nowrap;
            font-variant-numeric: tabular-nums;
          }

          .step-card {
            padding: 16px 18px 18px;
            height: 100%;
          }

          .step-chip, .vault-badge {
            display: inline-block;
            border-radius: 999px;
            padding: 5px 11px;
            font-size: 0.72rem;
            border: 1px solid rgba(45,40,34,0.16);
          }

          .step-card h3 {
            margin: 10px 0 8px;
          }

          .step-card p {
            margin: 0;
            color: var(--muted);
          }

          .decision-card, .summary-card {
            padding: 20px;
          }

          .score-card,
          .confirmation-card,
          .reason-card {
            background: rgba(255, 251, 245, 0.9);
            border: 1px solid rgba(45, 40, 34, 0.09);
            border-radius: 22px;
            box-shadow: 0 14px 30px rgba(77, 59, 37, 0.07);
            padding: 18px;
            margin-top: 12px;
          }

          .score-card-top {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            margin-bottom: 10px;
          }

          .score-grid,
          .confirmation-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 10px 12px;
          }

          .score-row,
          .confirmation-item {
            background: rgba(255, 255, 255, 0.6);
            border: 1px solid rgba(45, 40, 34, 0.06);
            border-radius: 16px;
            padding: 12px 14px;
          }

          .score-row span,
          .confirmation-item span {
            display: block;
            color: var(--muted);
            font-size: 0.76rem;
            margin-bottom: 4px;
          }

          .score-row strong,
          .confirmation-item strong {
            font-size: 0.96rem;
            overflow-wrap: anywhere;
            word-break: break-word;
            font-variant-numeric: tabular-nums;
            line-height: 1.35;
          }

          .reason-position {
            background: rgba(255, 255, 255, 0.6);
            border: 1px solid rgba(45, 40, 34, 0.06);
            border-radius: 16px;
            padding: 12px 14px;
            margin-bottom: 12px;
          }

          .reason-position span {
            display: block;
            color: var(--muted);
            font-size: 0.76rem;
            margin-bottom: 4px;
          }

          .reason-position strong {
            font-size: 0.96rem;
            overflow-wrap: anywhere;
            word-break: break-word;
          }

          .reason-list {
            margin: 0;
            padding-left: 1.1rem;
            color: var(--ink);
          }

          .reason-list li {
            margin: 0 0 0.45rem;
            line-height: 1.5;
          }

          .execution-status {
            background: rgba(255, 251, 245, 0.88);
            border: 1px solid rgba(45, 40, 34, 0.10);
            border-radius: 20px;
            box-shadow: 0 12px 28px rgba(77, 59, 37, 0.06);
            padding: 16px 18px;
            margin-bottom: 12px;
          }

          .execution-status-label {
            display: inline-block;
            color: var(--muted);
            font-size: 0.78rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 6px;
          }

          .execution-status strong {
            display: block;
            font-size: 1.02rem;
            margin-bottom: 4px;
          }

          .execution-status p {
            margin: 0;
            color: var(--muted);
            font-size: 0.92rem;
            line-height: 1.5;
          }

          .mode-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 12px;
            margin: 12px 0 14px;
          }

          .mode-card {
            background: rgba(255, 251, 245, 0.88);
            border: 1px solid rgba(45, 40, 34, 0.09);
            border-radius: 20px;
            box-shadow: 0 12px 28px rgba(77, 59, 37, 0.06);
            padding: 16px;
          }

          .mode-card.active {
            border-color: rgba(239, 108, 52, 0.32);
            box-shadow: 0 16px 34px rgba(239, 108, 52, 0.10);
          }

          .mode-card h4 {
            margin: 8px 0 8px;
            font-size: 1rem;
          }

          .mode-card p {
            margin: 0 0 8px;
            color: var(--muted);
            line-height: 1.5;
            font-size: 0.9rem;
          }

          .mode-meta {
            font-size: 0.82rem;
            color: var(--ink);
            line-height: 1.45;
          }

          .decision-head {
            display: flex;
            justify-content: space-between;
            gap: 16px;
            align-items: start;
          }

          .decision-head h2 {
            margin: 7px 0 10px;
            font-size: 1.72rem;
          }

          .confidence {
            font-family: 'IBM Plex Mono', monospace;
            color: var(--teal);
            font-size: 0.88rem;
            white-space: nowrap;
          }

          .note {
            border-left: 4px solid rgba(15,118,110,0.35);
            padding-left: 14px;
            color: var(--muted);
          }

          .vault-card {
            padding: 18px;
            margin-bottom: 12px;
          }

          .vault-top {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            align-items: start;
            margin-bottom: 14px;
          }

          .vault-title {
            font-size: 1rem;
            font-weight: 700;
          }

          .vault-sub {
            color: var(--muted);
            font-size: 0.84rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
          }

          .vault-metrics {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 10px;
          }

          .vault-metrics div {
            background: rgba(255,255,255,0.58);
            border-radius: 16px;
            padding: 10px 12px;
          }

          .vault-metrics span {
            display: block;
            color: var(--muted);
            font-size: 0.75rem;
            margin-bottom: 4px;
          }

          .vault-metrics strong {
            font-size: 0.98rem;
            white-space: nowrap;
            font-variant-numeric: tabular-nums;
          }

          .proof-stack .confirmation-card {
            margin-top: 12px;
          }

          .proof-stack a {
            color: var(--teal);
            text-decoration: none;
            font-weight: 600;
          }

          .proof-stack a:hover {
            text-decoration: underline;
          }

          .streamlit-expanderHeader {
            font-weight: 600;
          }

          .section-gap-sm {
            height: 0.45rem;
          }

          .section-gap-md {
            height: 0.9rem;
          }

          [data-testid="stButton"] button {
            background: linear-gradient(135deg, #ef6c34, #df8f22);
            color: white;
            border: 1px solid rgba(179, 91, 41, 0.28);
            border-radius: 18px;
            padding: 0.82rem 1.08rem;
            font-weight: 700;
            box-shadow: 0 16px 32px rgba(239, 108, 52, 0.22);
          }

          [data-testid="stButton"] button:hover {
            filter: brightness(1.02);
            transform: translateY(-1px);
          }

          @media (max-width: 960px) {
            .hero-grid {
              grid-template-columns: 1fr;
              gap: 8px;
            }

            .hero h1 {
              font-size: 1.82rem;
            }

            .block-container {
              padding-top: 0.9rem;
            }

            .score-grid,
            .confirmation-grid {
              grid-template-columns: 1fr;
            }
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(page_title="Treasury Copilot", page_icon=":material/account_balance_wallet:", layout="wide")

if "lang" not in st.session_state:
    st.session_state["lang"] = "zh"
if "language_selector" not in st.session_state:
    st.session_state["language_selector"] = next(
        label for label, code in LANGUAGE_OPTIONS.items() if code == st.session_state["lang"]
    )
if "execution_mode" not in st.session_state:
    st.session_state["execution_mode"] = "preview"

render_styles()

preview_lang = LANGUAGE_OPTIONS.get(st.session_state.get("language_selector"), st.session_state["lang"])
top_left, top_right = st.columns([0.74, 0.26], gap="small")
with top_left:
    st.markdown(f'<div class="topbar-note">{tr(preview_lang, "topbar_note")}</div>', unsafe_allow_html=True)
with top_right:
    language_labels = list(LANGUAGE_OPTIONS.keys())
    current_language_label = next(label for label, code in LANGUAGE_OPTIONS.items() if code == st.session_state["lang"])
    st.markdown(f'<div class="lang-kicker">{tr(preview_lang, "language_label")}</div>', unsafe_allow_html=True)
    selected_language_label = st.radio(
        tr(preview_lang, "language_control_label"),
        options=language_labels,
        index=language_labels.index(current_language_label),
        horizontal=True,
        label_visibility="collapsed",
        key="language_selector",
    )
    lang = LANGUAGE_OPTIONS[selected_language_label]
    st.session_state["lang"] = lang

hero_badges = "".join(f'<span class="badge">{badge}</span>' for badge in tr(lang, "hero_badges"))
st.markdown(
    f"""
    <div class="hero">
      <div class="hero-grid">
        <div>
          <div class="badge-row">
            {hero_badges}
          </div>
          <h1>{tr(lang, "hero_title")}</h1>
        </div>
        <p>{tr(lang, "hero_body")}</p>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="section-gap-sm"></div>', unsafe_allow_html=True)

left, right = st.columns([1.18, 0.82], gap="large")

with left:
    with st.container(border=True):
        st.markdown(
            f"""
            <div class="panel-kicker-row">
              <div class="mini-kicker">{tr(lang, "input_kicker")}</div>
            </div>
            <p class="panel-note">{tr(lang, "preview_caption")}</p>
            """,
            unsafe_allow_html=True,
        )
        source_col, amount_col = st.columns([0.58, 0.42], gap="medium")
        with source_col:
            source_label = st.selectbox(
                tr(lang, "source_token_label"),
                options=[asset["label"] for asset in PAYMENT_ASSETS],
                index=0,
            )
        with amount_col:
            amount = st.number_input(
                tr(lang, "amount_label"),
                min_value=0.001,
                value=25.0,
                step=0.01,
                format="%.4f",
                help=tr(lang, "amount_help"),
            )

        risk_col, treasury_col = st.columns(2, gap="medium")
        with risk_col:
            risk_mode = st.selectbox(
                tr(lang, "risk_mode_label"),
                options=RISK_MODES,
                index=0,
                format_func=lambda value: mode_label(RISK_MODE_LABELS, value, lang),
            )
        with treasury_col:
            treasury_mode = st.selectbox(
                tr(lang, "treasury_mode_label"),
                options=TREASURY_MODES,
                index=1,
                format_func=lambda value: mode_label(TREASURY_MODE_LABELS, value, lang),
            )

        preview = st.button(tr(lang, "preview_button"), use_container_width=True)

with right:
    source_asset = payment_option_by_label(source_label)
    st.markdown(
        f"""
        <div class="aside-card">
          <div class="mini-kicker">{tr(lang, "positioning_kicker")}</div>
          <h3 style="margin:0 0 8px;">{tr(lang, "positioning_title")}</h3>
          <p style="margin:0; color:#6f665e;">{tr(lang, "positioning_body")}</p>
          <div class="stat-grid">
            <div class="stat"><span>{tr(lang, "stat_treasury_asset")}</span><strong>Base USDT</strong></div>
            <div class="stat"><span>{tr(lang, "stat_revenue_source")}</span><strong>{source_asset['symbol']}</strong></div>
            <div class="stat"><span>{tr(lang, "stat_origin_chain")}</span><strong>{source_asset['chain']}</strong></div>
            <div class="stat"><span>{tr(lang, "stat_liquidity_policy")}</span><strong>{mode_label(TREASURY_MODE_LABELS, treasury_mode, lang)}</strong></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

if preview:
    source_asset = payment_option_by_label(source_label)
    try:
        with st.spinner(tr(lang, "spinner_payment_quote")):
            payment_quote = fetch_payment_quote(source_asset, amount)
            payment_metrics = quote_to_metrics(payment_quote)

        with st.spinner(tr(lang, "spinner_vaults")):
            raw_vaults = fetch_vaults()
            cleaned_vaults = clean_vaults(raw_vaults, risk_mode)
            quotable_vaults = select_quotable_vaults(cleaned_vaults, payment_metrics["rawToAmount"])

        settle_amount = payment_metrics["toAmount"]
        decision = run_ai_treasury_decision(quotable_vaults, settle_amount, risk_mode, treasury_mode, lang=lang)
        recommended_vault = next((vault for vault in quotable_vaults if vault.get("id") == decision.get("recommended_vault_id")), None)

        deposit_quote = None
        deposit_metrics = None
        if decision.get("action") == "deposit" and recommended_vault:
            deposit_quote = recommended_vault.get("previewQuote")
            deposit_metrics = recommended_vault.get("previewMetrics")

        st.session_state["results"] = {
            "source_asset": source_asset,
            "payment_quote": payment_quote,
            "payment_metrics": payment_metrics,
            "raw_vault_count": len(raw_vaults),
            "filtered_vault_count": len(cleaned_vaults),
            "validated_vault_count": len(quotable_vaults),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "vaults": quotable_vaults,
            "decision": decision,
            "decision_lang": lang,
            "risk_mode": risk_mode,
            "treasury_mode": treasury_mode,
            "recommended_vault": recommended_vault,
            "deposit_quote": deposit_quote,
            "deposit_metrics": deposit_metrics,
        }
    except Exception as exc:
        st.error(tr(lang, "preview_error", error=exc))

results = st.session_state.get("results")

if results and results.get("decision_lang") != lang:
    refreshed_decision = run_ai_treasury_decision(
        results["vaults"],
        results["payment_metrics"]["toAmount"],
        results["risk_mode"],
        results["treasury_mode"],
        lang=lang,
    )
    refreshed_vault = next((vault for vault in results["vaults"] if vault.get("id") == refreshed_decision.get("recommended_vault_id")), None)
    results["decision"] = refreshed_decision
    results["decision_lang"] = lang
    results["recommended_vault"] = refreshed_vault
    results["deposit_quote"] = refreshed_vault.get("previewQuote") if refreshed_vault else None
    results["deposit_metrics"] = refreshed_vault.get("previewMetrics") if refreshed_vault else None
    st.session_state["results"] = results

if results:
    payment_metrics = results["payment_metrics"]
    decision = results["decision"]
    executor_vault = results["recommended_vault"]
    deposit_metrics = results["deposit_metrics"]
    source_asset = results["source_asset"]
    current_execution_mode = st.session_state.get("execution_mode", "preview")
    demo_mode_prefetch = current_execution_mode == "demo_executor"
    executor_account = get_account() if BURNER_PRIVATE_KEY and demo_mode_prefetch else None
    executor_address = executor_account.address if executor_account else ""
    standardization_balance = get_asset_balance(source_asset, executor_address) if executor_account else None
    settlement_asset = SETTLEMENT_TOKEN
    deployment_balance = get_asset_balance(settlement_asset, executor_address) if executor_account else None
    scored_vaults = score_vault_candidates(results["vaults"], payment_metrics, results["risk_mode"], results["treasury_mode"])
    threshold_met_vaults = [vault for vault in scored_vaults if vault.get("thresholdMet")]
    top_scored_vault = scored_vaults[0] if scored_vaults else None
    scored_vault_map = {vault.get("id"): vault for vault in scored_vaults if vault.get("id")}
    executor_scored_vault = scored_vault_map.get(executor_vault.get("id")) if executor_vault else None
    display_recommended_vault = (
        executor_scored_vault
        if decision["action"] == "deposit" and executor_scored_vault and executor_scored_vault.get("thresholdMet")
        else None
    )
    execution_vault = display_recommended_vault
    execution_deposit_metrics = deposit_metrics if display_recommended_vault else None
    required_standardization = payment_metrics.get("fromAmount")
    required_deployment = execution_deposit_metrics.get("fromAmount") if execution_deposit_metrics else None
    can_execute_standardization = bool(
        executor_account
        and standardization_balance is not None
        and required_standardization is not None
        and standardization_balance >= required_standardization
    )
    can_execute_deployment = bool(
        executor_account
        and execution_vault
        and deployment_balance is not None
        and required_deployment is not None
        and deployment_balance >= required_deployment
    )
    insufficient_executor_balance = not can_execute_standardization or (execution_vault is not None and not can_execute_deployment)
    preview_only_amount = extract_number(payment_metrics.get("toAmountUSD")) > DEMO_PROOF_USD_THRESHOLD
    transparency_reference_vault = display_recommended_vault or top_scored_vault
    threshold_warning_needed = bool(scored_vaults) and not threshold_met_vaults
    show_keep_liquidity_analysis = decision["action"] == "keep_usdt" or display_recommended_vault is None
    keep_liquidity_items = build_keep_liquidity_items(
        payment_metrics,
        results["treasury_mode"],
        transparency_reference_vault,
        execution_deposit_metrics,
        lang,
    )
    display_headline = decision["headline"]
    display_rationale = decision["rationale"]
    display_risk_note = decision["risk_note"]
    display_best_for = decision["best_for"]
    if show_keep_liquidity_analysis and decision["action"] != "keep_usdt":
        display_headline = tr(lang, "display_keep_headline")
        display_rationale = tr(lang, "display_keep_rationale")
        display_risk_note = tr(lang, "display_keep_risk_note")
        display_best_for = tr(lang, "display_keep_best_for")
    candidate_heading = (
        tr(lang, "other_strategies_heading")
        if display_recommended_vault
        else tr(lang, "below_threshold_heading")
        if threshold_warning_needed
        else tr(lang, "other_strategies_heading")
    )
    candidate_vaults = [
        vault for vault in scored_vaults
        if not (
            (display_recommended_vault and vault.get("id") == display_recommended_vault.get("id"))
            or (not display_recommended_vault and top_scored_vault and vault.get("id") == top_scored_vault.get("id"))
        )
    ]

    st.markdown('<div class="section-gap-md"></div>', unsafe_allow_html=True)
    step1, step2, step3 = st.columns(3, gap="medium")
    with step1:
        render_step_card("01", tr(lang, "step_1_title"), tr(lang, "step_1_body", chain=source_asset["chain"], symbol=source_asset["symbol"]), "#ef6c34", lang)
    with step2:
        render_step_card("02", tr(lang, "step_2_title"), tr(lang, "step_2_body"), "#0f766e", lang)
    with step3:
        render_step_card("03", tr(lang, "step_3_title"), tr(lang, "step_3_body"), "#6f4ca5", lang)

    st.markdown('<div class="section-gap-md"></div>', unsafe_allow_html=True)
    result_left, result_right = st.columns([1.08, 0.92], gap="large")

    with result_left:
        st.markdown(
            f"""
            <div class="summary-card">
              <div class="mini-kicker">{tr(lang, "summary_kicker")}</div>
              <h3 style="margin:0 0 14px;">{tr(lang, "summary_title", from_amount=format_display_amount(payment_metrics['fromAmount'], min_digits=2, max_digits=4), from_token=payment_metrics['fromToken'], to_amount=format_display_amount(payment_metrics['toAmount'], min_digits=2, max_digits=4), to_token=payment_metrics['toToken'])}</h3>
              <div class="stat-grid">
                <div class="stat"><span>{tr(lang, "label_route")}</span><strong>{payment_metrics['toolName']}</strong></div>
                <div class="stat"><span>{tr(lang, "label_standardized_treasury")}</span><strong>{format_usd(payment_metrics['toAmountUSD'])}</strong></div>
                <div class="stat"><span>{tr(lang, "label_gas")}</span><strong>{format_usd(payment_metrics['gasUSD'])}</strong></div>
                <div class="stat"><span>{tr(lang, "label_fees")}</span><strong>{format_usd(payment_metrics['feeUSD'])}</strong></div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with result_right:
        action_label = tr(lang, "action_keep") if show_keep_liquidity_analysis else tr(lang, "action_deposit")
        st.markdown(
            f"""
            <div class="decision-card">
              <div class="decision-head">
                <div>
                  <div class="mini-kicker">{tr(lang, "memo_kicker")}</div>
                  <h2>{display_headline}</h2>
                </div>
                <div class="confidence">{tr(lang, "confidence_label", value=decision['confidence'])}</div>
              </div>
              <p style="margin-top:0;">{display_rationale}</p>
              <p class="note">{display_risk_note}</p>
              <div class="badge-row" style="margin-top:14px;">
                <span class="badge">{action_label}</span>
                <span class="badge">{tr(lang, "label_best_for")}: {display_best_for}</span>
                <span class="badge">{tr(lang, "label_raw_vaults")}: {results['raw_vault_count']}</span>
                <span class="badge">{tr(lang, "label_live_vetted_vaults")}: {len(results['vaults'])}</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    detail_left, detail_right = st.columns([1.0, 1.0], gap="large")

    with detail_left:
        st.subheader(tr(lang, "standardization_heading"))
        st.write(
            tr(
                lang,
                "standardization_text",
                chain=source_asset["chain"],
                symbol=source_asset["symbol"],
                settlement_chain=SETTLEMENT_TOKEN["chain"],
                settlement_symbol=SETTLEMENT_TOKEN["symbol"],
            )
        )
        if show_keep_liquidity_analysis:
            st.success(tr(lang, "keep_message"))
        else:
            st.info(tr(lang, "deploy_message"))
        if preview_only_amount:
            st.caption(tr(lang, "preview_only_amount_note"))

        with st.expander(tr(lang, "revenue_route_details")):
            st.json(results["payment_quote"])

    with detail_right:
        st.subheader(tr(lang, "recommended_action_heading"))
        st.caption(tr(lang, "treasury_route_note"))
        if display_recommended_vault:
            recommended_reasons = build_recommendation_reasons(
                display_recommended_vault,
                results["risk_mode"],
                results["treasury_mode"],
                lang,
            )
            render_vault_card(display_recommended_vault, badge=tr(lang, "badge_ai_pick"), lang=lang)
            render_score_breakdown(display_recommended_vault, lang)
            render_reason_list(
                tr(lang, "reason_heading_recommended"),
                tr(lang, "reason_kicker_recommended"),
                recommended_reasons,
                lang,
                position_text=tr(lang, "reason_position_recommended"),
            )
            transparency_items = [
                (tr(lang, "transparency_updated_at"), results.get("generated_at") or tr(lang, "status_generated_at_unavailable")),
                (tr(lang, "label_raw_vaults"), str(results.get("raw_vault_count", 0))),
                (tr(lang, "transparency_filtered_count"), str(results.get("filtered_vault_count", 0))),
                (tr(lang, "transparency_validated_count"), str(results.get("validated_vault_count", 0))),
                (tr(lang, "transparency_total_score"), f"{display_recommended_vault.get('scoreBreakdown', {}).get('total', 0)}/100"),
                (tr(lang, "transparency_main_reason"), display_rationale),
                (tr(lang, "transparency_other_reason"), summarize_other_candidates(scored_vaults, display_recommended_vault, lang)),
            ]
            transparency_rows = "".join(
                f"""
                <div class="confirmation-item">
                  <span>{label}</span>
                  <strong>{value}</strong>
                </div>
                """
                for label, value in transparency_items
            )
            st.markdown(
                f"""
                <div class="confirmation-card">
                  <div class="score-card-top">
                    <div class="mini-kicker">{tr(lang, "transparency_kicker")}</div>
                    <span class="vault-badge">{tr(lang, "transparency_heading")}</span>
                  </div>
                  <div class="confirmation-grid">
                    {transparency_rows}
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if execution_deposit_metrics:
                st.markdown(
                    f"""
                    <div class="summary-card">
                      <div class="mini-kicker">{tr(lang, "deployment_kicker")}</div>
                      <div class="stat-grid">
                        <div class="stat"><span>{tr(lang, "label_target_strategy")}</span><strong>{display_recommended_vault['protocol']} · {display_recommended_vault['chain']}</strong></div>
                        <div class="stat"><span>{tr(lang, "label_estimated_vault_tokens")}</span><strong>{format_display_amount(execution_deposit_metrics['toAmount'], min_digits=2, max_digits=4)} {execution_deposit_metrics['toToken']}</strong></div>
                        <div class="stat"><span>{tr(lang, "label_route")}</span><strong>{execution_deposit_metrics['toolName']}</strong></div>
                        <div class="stat"><span>{tr(lang, "label_deployment_cost")}</span><strong>{format_usd(execution_deposit_metrics['gasUSD'] + execution_deposit_metrics['feeUSD'])}</strong></div>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with st.expander(tr(lang, "deployment_route_details")):
                st.json(results["deposit_quote"])
            st.caption(tr(lang, "strategy_boundary_note"))
        elif threshold_warning_needed:
            st.warning(tr(lang, "score_threshold_warning"))
            if transparency_reference_vault:
                top_candidate_reasons = build_candidate_reasons(transparency_reference_vault, None, lang)
                render_vault_card(transparency_reference_vault, badge=tr(lang, "badge_backup"), lang=lang)
                render_score_breakdown(transparency_reference_vault, lang)
                render_reason_list(
                    tr(lang, "reason_heading_candidate"),
                    tr(lang, "reason_kicker_candidate"),
                    top_candidate_reasons,
                    lang,
                    position_text=tr(lang, "reason_position_top_candidate"),
                )
                transparency_items = [
                    (tr(lang, "transparency_updated_at"), results.get("generated_at") or tr(lang, "status_generated_at_unavailable")),
                    (tr(lang, "label_raw_vaults"), str(results.get("raw_vault_count", 0))),
                    (tr(lang, "transparency_filtered_count"), str(results.get("filtered_vault_count", 0))),
                    (tr(lang, "transparency_validated_count"), str(results.get("validated_vault_count", 0))),
                    (tr(lang, "transparency_total_score"), f"{transparency_reference_vault.get('scoreBreakdown', {}).get('total', 0)}/100"),
                    (tr(lang, "transparency_main_reason"), display_rationale),
                    (tr(lang, "transparency_other_reason"), summarize_other_candidates(scored_vaults, None, lang)),
                ]
                transparency_rows = "".join(
                    f"""
                    <div class="confirmation-item">
                      <span>{label}</span>
                      <strong>{value}</strong>
                    </div>
                    """
                    for label, value in transparency_items
                )
                st.markdown(
                    f"""
                    <div class="confirmation-card">
                      <div class="score-card-top">
                        <div class="mini-kicker">{tr(lang, "transparency_kicker")}</div>
                        <span class="vault-badge">{tr(lang, "transparency_heading")}</span>
                      </div>
                      <div class="confirmation-grid">
                        {transparency_rows}
                      </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )
                st.caption(tr(lang, "strategy_boundary_note"))
        elif transparency_reference_vault:
            top_candidate_reasons = build_candidate_reasons(transparency_reference_vault, None, lang)
            st.info(tr(lang, "keep_message"))
            render_vault_card(transparency_reference_vault, badge=tr(lang, "badge_backup"), lang=lang)
            render_score_breakdown(transparency_reference_vault, lang)
            render_reason_list(
                tr(lang, "reason_heading_candidate"),
                tr(lang, "reason_kicker_candidate"),
                top_candidate_reasons,
                lang,
                position_text=tr(lang, "reason_position_top_candidate"),
            )
            transparency_items = [
                (tr(lang, "transparency_updated_at"), results.get("generated_at") or tr(lang, "status_generated_at_unavailable")),
                (tr(lang, "label_raw_vaults"), str(results.get("raw_vault_count", 0))),
                (tr(lang, "transparency_filtered_count"), str(results.get("filtered_vault_count", 0))),
                (tr(lang, "transparency_validated_count"), str(results.get("validated_vault_count", 0))),
                (tr(lang, "transparency_total_score"), f"{transparency_reference_vault.get('scoreBreakdown', {}).get('total', 0)}/100"),
                (tr(lang, "transparency_main_reason"), display_rationale),
                (tr(lang, "transparency_other_reason"), tr(lang, "transparency_other_reason_keep")),
            ]
            transparency_rows = "".join(
                f"""
                <div class="confirmation-item">
                  <span>{label}</span>
                  <strong>{value}</strong>
                </div>
                """
                for label, value in transparency_items
            )
            st.markdown(
                f"""
                <div class="confirmation-card">
                  <div class="score-card-top">
                    <div class="mini-kicker">{tr(lang, "transparency_kicker")}</div>
                    <span class="vault-badge">{tr(lang, "transparency_heading")}</span>
                  </div>
                  <div class="confirmation-grid">
                    {transparency_rows}
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.caption(tr(lang, "strategy_boundary_note"))
        else:
            st.warning(tr(lang, "no_strategy_warning"))
        if show_keep_liquidity_analysis:
            keep_rows = "".join(
                f"""
                <div class="confirmation-item">
                  <span>{label}</span>
                  <strong>{value}</strong>
                </div>
                """
                for label, value in keep_liquidity_items
            )
            st.markdown(
                f"""
                <div class="confirmation-card">
                  <div class="score-card-top">
                    <div class="mini-kicker">{tr(lang, "keep_reason_kicker")}</div>
                    <span class="vault-badge">{tr(lang, "keep_reason_heading")}</span>
                  </div>
                  <p class="note">{tr(lang, "keep_reason_note")}</p>
                  <div class="confirmation-grid">
                    {keep_rows}
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if candidate_vaults:
        st.subheader(candidate_heading)
        vault_columns = st.columns(min(3, max(1, len(candidate_vaults))), gap="medium")
        for index, vault in enumerate(candidate_vaults):
            with vault_columns[index % len(vault_columns)]:
                render_vault_card(vault, badge=tr(lang, "badge_backup"), lang=lang)
                render_score_breakdown(vault, lang)
                render_reason_list(
                    tr(lang, "reason_heading_candidate"),
                    tr(lang, "reason_kicker_candidate"),
                    build_candidate_reasons(vault, transparency_reference_vault, lang),
                    lang,
                )

    st.subheader(tr(lang, "execution_heading"))
    mode_cards_html = "".join(
        f"""
        <div class="mode-card{' active' if st.session_state.get('execution_mode') == mode else ''}">
          <span class="vault-badge">{execution_mode_badge(mode, lang)}</span>
          <h4>{execution_mode_title(mode, lang)}</h4>
          <p>{execution_mode_scope(mode, lang)}</p>
          <div class="mode-meta">{execution_mode_actions(mode, lang)}</div>
        </div>
        """
        for mode in EXECUTION_MODE_OPTIONS
    )
    st.markdown(
        f"""
        <div class="confirmation-card">
          <div class="score-card-top">
            <div class="mini-kicker">{tr(lang, "execution_mode_overview_kicker")}</div>
            <span class="vault-badge">{tr(lang, "execution_mode_overview_heading")}</span>
          </div>
          <div class="mode-grid">
            {mode_cards_html}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(tr(lang, "execution_mode_selector_label"))
    selected_execution_mode = st.radio(
        tr(lang, "execution_mode_selector_label"),
        options=EXECUTION_MODE_OPTIONS,
        format_func=lambda mode: execution_mode_label(mode, lang),
        horizontal=True,
        label_visibility="collapsed",
        key="execution_mode",
    )
    selected_execution_title = execution_mode_title(selected_execution_mode, lang)
    selected_execution_note = execution_mode_note(selected_execution_mode, lang)
    preview_mode_active = selected_execution_mode == "preview"
    demo_mode_active = selected_execution_mode == "demo_executor"
    user_wallet_mode_active = selected_execution_mode == "user_wallet"
    st.markdown(
        f"""
        <div class="execution-status">
          <span class="execution-status-label">{tr(lang, "execution_mode_label")}</span>
          <strong>{selected_execution_title}</strong>
          <p>{selected_execution_note}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if demo_mode_active:
        st.info(tr(lang, "execution_mode_demo_info"))
        st.warning(tr(lang, "execution_warning"))
    elif preview_mode_active:
        st.info(tr(lang, "execution_mode_preview_info"))
    elif user_wallet_mode_active:
        st.info(tr(lang, "execution_mode_user_info"))
    if demo_mode_active and insufficient_executor_balance:
        st.info(tr(lang, "executor_insufficient_warning"))
    if preview_only_amount:
        st.caption(tr(lang, "preview_only_amount_note"))
    if show_keep_liquidity_analysis:
        st.caption(tr(lang, "execution_deployment_locked_note"))
    target_vault_label = (
        f"{execution_vault['protocol']} · {execution_vault['chain']}"
        if execution_vault
        else tr(lang, "confirm_target_vault_unavailable")
    )
    executor_address_display = executor_address_status(selected_execution_mode, executor_account, lang)
    standardization_balance_display = standardization_balance_status(
        selected_execution_mode,
        executor_account,
        standardization_balance,
        source_asset.get("symbol", ""),
        lang,
    )
    standardization_required_display = (
        format_token_amount(
            required_standardization,
            source_asset.get("symbol", ""),
            4,
            empty_text=tr(lang, "executor_required_unavailable"),
        )
        if required_standardization is not None
        else tr(lang, "executor_required_unavailable")
    )
    deployment_balance_display = deployment_balance_status(
        selected_execution_mode,
        executor_account,
        deployment_balance,
        settlement_asset.get("symbol", ""),
        show_keep_liquidity_analysis,
        execution_vault,
        lang,
    )
    deployment_required_display = (
        format_token_amount(
            required_deployment,
            settlement_asset.get("symbol", ""),
            4,
            empty_text=tr(lang, "executor_required_deployment_keep" if show_keep_liquidity_analysis else "deployment_path_unavailable"),
        )
        if execution_vault and execution_deposit_metrics and required_deployment is not None
        else tr(lang, "executor_required_deployment_keep" if show_keep_liquidity_analysis else "deployment_path_unavailable")
    )
    confirmation_items = [
        (
            tr(lang, "confirm_input_amount"),
            format_token_amount(
                payment_metrics.get("fromAmount"),
                payment_metrics.get("fromToken", ""),
                4,
                empty_text=tr(lang, "confirm_input_amount_unavailable"),
            ),
        ),
        (
            tr(lang, "confirm_standardized_amount"),
            format_token_amount(
                payment_metrics.get("toAmount"),
                SETTLEMENT_TOKEN["symbol"],
                4,
                empty_text=tr(lang, "confirm_standardized_amount_unavailable"),
            ),
        ),
        (tr(lang, "confirm_route_fee"), format_usd(payment_metrics.get("feeUSD", 0.0))),
        (tr(lang, "confirm_gas"), format_usd(payment_metrics.get("gasUSD", 0.0))),
        (
            tr(lang, "confirm_min_received"),
            format_token_amount(
                payment_metrics.get("minReceived"),
                SETTLEMENT_TOKEN["symbol"],
                4,
                empty_text=tr(lang, "confirm_min_received_unavailable"),
            ),
        ),
        (tr(lang, "confirm_executor_address"), executor_address_display),
        (tr(lang, "confirm_standardization_balance"), standardization_balance_display),
        (tr(lang, "confirm_standardization_required"), standardization_required_display),
        (
            tr(lang, "confirm_standardization_status"),
            execution_readiness_status(
                selected_execution_mode,
                executor_account,
                can_execute_standardization,
                lang=lang,
            ),
        ),
        (tr(lang, "confirm_deployment_balance"), deployment_balance_display),
        (tr(lang, "confirm_deployment_required"), deployment_required_display),
        (
            tr(lang, "confirm_deployment_status"),
            execution_readiness_status(
                selected_execution_mode,
                executor_account,
                can_execute_deployment,
                show_keep_liquidity_analysis=show_keep_liquidity_analysis,
                for_deployment=True,
                execution_vault=execution_vault,
                execution_metrics=execution_deposit_metrics,
                lang=lang,
            ),
        ),
        (
            tr(lang, "confirm_deposit_amount"),
            format_token_amount(
                execution_deposit_metrics.get("fromAmount"),
                execution_deposit_metrics.get("fromToken", SETTLEMENT_TOKEN["symbol"]),
                4,
                empty_text=tr(lang, "confirm_deposit_amount_unavailable"),
            )
            if execution_deposit_metrics
            else tr(lang, "confirm_deposit_amount_unavailable"),
        ),
        (
            tr(lang, "confirm_vault_tokens"),
            format_token_amount(
                execution_deposit_metrics.get("toAmount"),
                execution_deposit_metrics.get("toToken", ""),
                4,
                empty_text=tr(lang, "confirm_vault_tokens_unavailable"),
            )
            if execution_deposit_metrics
            else tr(lang, "confirm_vault_tokens_unavailable"),
        ),
        (tr(lang, "confirm_target_vault"), target_vault_label),
        (tr(lang, "confirm_wallet_type"), selected_execution_title),
    ]
    confirmation_rows = "".join(
        f"""
        <div class="confirmation-item">
          <span>{label}</span>
          <strong>{value}</strong>
        </div>
        """
        for label, value in confirmation_items
    )
    st.markdown(
        f"""
        <div class="confirmation-card">
          <div class="score-card-top">
            <div class="mini-kicker">{tr(lang, "confirmation_kicker")}</div>
            <span class="vault-badge">{tr(lang, "confirmation_heading")}</span>
          </div>
          <div class="confirmation-grid">
            {confirmation_rows}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    exec_left, exec_right = st.columns(2, gap="medium")
    with exec_left:
        if st.button(
            tr(lang, "button_standardization"),
            use_container_width=True,
            disabled=(not demo_mode_active) or (not can_execute_standardization),
        ):
            if not BURNER_PRIVATE_KEY:
                st.error(tr(lang, "missing_private_key"))
            else:
                try:
                    with st.spinner(tr(lang, "spinner_live_quote")):
                        account = get_account()
                        live_payment_quote = fetch_payment_quote(source_asset, amount, from_address=account.address)
                    with st.spinner(tr(lang, "spinner_broadcast_standardization")):
                        tx_hash = broadcast_tx(live_payment_quote)
                    st.success(tr(lang, "success_standardization", tx_hash=tx_hash))
                    st.caption(tr(lang, "execution_success_note"))
                    record_execution_proof(
                        "standardization",
                        tx_hash,
                        extract_number(payment_metrics.get("toAmountUSD")),
                        chain_id=parse_int(live_payment_quote.get("action", {}).get("fromChainId") or source_asset.get("chainId")),
                        chain_name=source_asset.get("chain", ""),
                        token=source_asset.get("symbol", ""),
                        input_amount=payment_metrics.get("fromAmount"),
                    )
                except Exception as exc:
                    st.error(tr(lang, "error_standardization", error=exc))

    with exec_right:
        if st.button(
            tr(lang, "button_deployment"),
            use_container_width=True,
            disabled=(not demo_mode_active) or (not can_execute_deployment),
        ):
            if not execution_vault:
                st.error(tr(lang, "no_recommended_vault"))
            elif not BURNER_PRIVATE_KEY:
                st.error(tr(lang, "missing_private_key"))
            else:
                try:
                    account = get_account()
                    with st.spinner(tr(lang, "spinner_requote_settlement")):
                        live_payment_quote = fetch_payment_quote(source_asset, amount, from_address=account.address)
                        live_payment_metrics = quote_to_metrics(live_payment_quote)
                    with st.spinner(tr(lang, "spinner_requote_deployment")):
                        live_deposit_quote = fetch_deposit_quote(execution_vault, live_payment_metrics["rawToAmount"], from_address=account.address)
                    with st.spinner(tr(lang, "spinner_broadcast_deployment")):
                        tx_hash = broadcast_tx(live_deposit_quote)
                    st.success(tr(lang, "success_deployment", tx_hash=tx_hash))
                    st.caption(tr(lang, "execution_success_note"))
                    record_execution_proof(
                        "deployment",
                        tx_hash,
                        extract_number(payment_metrics.get("toAmountUSD")),
                        chain_id=parse_int(live_deposit_quote.get("action", {}).get("fromChainId") or SETTLEMENT_TOKEN.get("chainId")),
                        chain_name=SETTLEMENT_TOKEN.get("chain", ""),
                        token=live_payment_metrics.get("toToken", SETTLEMENT_TOKEN["symbol"]),
                        input_amount=live_payment_metrics.get("toAmount"),
                    )
                except Exception as exc:
                    st.error(tr(lang, "error_deployment", error=exc))

    if preview_mode_active:
        st.caption(tr(lang, "execution_buttons_preview_note"))
    elif demo_mode_active:
        st.caption(tr(lang, "execution_buttons_demo_note"))
    elif user_wallet_mode_active:
        st.caption(tr(lang, "execution_buttons_user_note"))

    proof_records = [record for record in st.session_state.get("execution_proof_records", []) if record.get("proof_eligible")]
    st.subheader(tr(lang, "proof_heading"))
    st.caption(tr(lang, "proof_note"))
    if proof_records:
        proof_rows = "".join(
            f"""
            <div class="confirmation-card">
              <div class="score-card-top">
                <div class="mini-kicker">{tr(lang, f"proof_action_{record.get('action')}")}</div>
                <span class="vault-badge">{tr(lang, "proof_mode_demo")}</span>
              </div>
              <div class="confirmation-grid">
                <div class="confirmation-item">
                  <span>{tr(lang, "proof_field_type")}</span>
                  <strong>{tr(lang, f"proof_action_{record.get('action')}")}</strong>
                </div>
                <div class="confirmation-item">
                  <span>{tr(lang, "proof_field_mode")}</span>
                  <strong>{tr(lang, "proof_mode_demo")}</strong>
                </div>
                <div class="confirmation-item">
                  <span>{tr(lang, "proof_field_chain")}</span>
                  <strong>{record.get('chain_name') or tr(lang, "proof_chain_unavailable")}</strong>
                </div>
                <div class="confirmation-item">
                  <span>{tr(lang, "proof_field_token")}</span>
                  <strong>{record.get('token') or tr(lang, "proof_token_unavailable")}</strong>
                </div>
                <div class="confirmation-item">
                  <span>{tr(lang, "proof_field_amount")}</span>
                  <strong>{format_token_amount(record.get('input_amount'), record.get('token', ''), 4, empty_text=tr(lang, "proof_amount_unavailable"))}</strong>
                </div>
                <div class="confirmation-item">
                  <span>{tr(lang, "proof_field_time")}</span>
                  <strong>{record.get('timestamp')}</strong>
                </div>
                <div class="confirmation-item">
                  <span>{tr(lang, "proof_field_hash")}</span>
                  <strong>{format_address(record.get('tx_hash', ''), empty_text=tr(lang, "proof_hash_unavailable"))}</strong>
                </div>
                <div class="confirmation-item">
                  <span>{tr(lang, "proof_field_explorer")}</span>
                  <strong>{proof_explorer_markup(record.get("explorer_url"), tr(lang, "proof_explorer_link"), tr(lang, "proof_explorer_unavailable"))}</strong>
                </div>
              </div>
            </div>
            """
            for record in proof_records[:6]
        )
        st.markdown(
            f"""
            <div class="proof-stack">
              {proof_rows}
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.info(tr(lang, "proof_empty"))

    st.caption(tr(lang, "footer_caption"))
