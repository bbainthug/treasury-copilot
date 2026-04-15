import json
import os
from typing import Any, Dict, List

import requests
import httpx
from dotenv import load_dotenv
from openai import OpenAI
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

load_dotenv()

BASE_URL = os.getenv("LI_FI_EARN_API_BASE", "https://li.quest/v1").rstrip("/")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
DEFAULT_VAULTS = [
    {
        "id": "morpho-base-usdc",
        "vaultAddress": "0x7BfA7C4f149E7415b73bdeDfe609237e29CBF34A",
        "chain": "Base",
        "chainId": 8453,
        "protocol": "Morpho",
        "apy": 0.0,
        "tvl": 0.0,
    },
    {
        "id": "wsteth-mainnet",
        "vaultAddress": "0x7f39c581f595b53c5cb5bbd32bcd5d1a4f57d06b",
        "chain": "Ethereum",
        "chainId": 1,
        "protocol": "Lido",
        "apy": 0.0,
        "tvl": 0.0,
    },
]
HTTP_PROXY = os.getenv("HTTP_PROXY", "").strip() or os.getenv("http_proxy", "").strip()
HTTPS_PROXY = os.getenv("HTTPS_PROXY", "").strip() or os.getenv("https_proxy", "").strip()
CUSTOM_PROXY = os.getenv("LI_FI_PROXY", "").strip()


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


def build_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(total=2, connect=2, read=2, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.mount("http://", HTTPAdapter(max_retries=retry))

    proxy = CUSTOM_PROXY or HTTPS_PROXY or HTTP_PROXY
    if proxy:
        session.proxies.update({"http": proxy, "https": proxy})

    return session


def normalize_vault(vault: Dict[str, Any]) -> Dict[str, Any]:
    vault_id = first_present(vault, ["id", "vaultId", "vault_id"], "")
    vault_address = first_present(vault, ["vaultAddress", "address", "vault", "toToken"], vault_id)
    chain = first_present(vault, ["chain", "chainName", "network", "fromChain"], "Unknown")
    protocol = first_present(vault, ["protocol", "provider", "project", "dex"], "Unknown")
    apy = extract_number(first_present(vault, ["apy", "apr", "netApy", "projectedApy"], 0.0))
    tvl = extract_number(first_present(vault, ["tvl", "tvlUsd", "totalValueLocked", "tvlUSD"], 0.0))
    return {
        **vault,
        "id": vault_id,
        "vaultAddress": vault_address,
        "chain": chain,
        "protocol": protocol,
        "apy": apy,
        "tvl": tvl,
    }


def fetch_vaults() -> List[Dict[str, Any]]:
    session = build_session()
    candidate_urls = [
        f"{BASE_URL}/vaults",
        f"{BASE_URL}/earn/vaults",
        f"{BASE_URL}/earn/v1/vaults",
    ]

    last_error = None
    for url in candidate_urls:
        try:
            response = session.get(url, headers = {"x-lifi-integrator": "yieldrazor"}, timeout=30)
        except requests.RequestException as exc:
            last_error = f"request error on {url}: {exc}"
            continue
        if response.status_code == 404:
            last_error = f"404 from {url}"
            continue
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, list):
            vaults = payload
        elif isinstance(payload, dict):
            vaults = first_present(payload, ["vaults", "data", "items", "results"], [])
        else:
            vaults = []
        return [normalize_vault(v) for v in vaults if isinstance(v, dict)]

    raise RuntimeError(f"vault 请求失败: {last_error}")


def build_prompt(vaults: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    system_prompt = """
你是 YieldRazor 的 AI 收益审计脑。
只输出一个 JSON 对象，不要 markdown，不要解释。
格式必须是：
{
  "recommended_vault_id": "string",
  "protocol": "string",
  "apy": number,
  "chain": "string",
  "audit_report": "string"
}
规则：
1. 只能从提供的 vault 数据中选择。
2. 推荐时优先选择更成熟、TVL 更厚、APY 不离谱的池子。
3. audit_report 必须用中文，带极客感和轻微毒舌。
""".strip()
    user_prompt = {
        "principal_usd": 1000,
        "risk_mode": "稳健",
        "top_vaults": vaults,
        "note": "当前 vault 列表来自官方文档示例地址，用于验证 quote 与 LLM 输出链路。",
    }
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(user_prompt, ensure_ascii=False, indent=2)},
    ]


def get_sample_vaults() -> List[Dict[str, Any]]:
    return DEFAULT_VAULTS


def run_llm_audit(vaults: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not OPENAI_API_KEY or OPENAI_API_KEY.startswith("YOUR_"):
        selected = vaults[0]
        return {
            "recommended_vault_id": selected.get("id", ""),
            "protocol": selected.get("protocol", ""),
            "apy": selected.get("apy", 0.0),
            "chain": selected.get("chain", ""),
            "audit_report": "未检测到有效 LLM Key，先走本地降级推荐。Morpho 这池子是官方文档样本，路径最清晰，先拿它做 quote 验证，别像无头苍蝇一样乱扎。",
        }

    proxy = CUSTOM_PROXY or HTTPS_PROXY or HTTP_PROXY
    http_client = httpx.Client(proxy=proxy) if proxy else httpx.Client()
    client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL, http_client=http_client)
    completion = client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=build_prompt(vaults),
    )
    content = completion.choices[0].message.content or "{}"
    return json.loads(content)


def build_quote_params(vault: Dict[str, Any]) -> Dict[str, str]:
    chain_id = str(vault.get("chainId", 8453))
    return {
        "fromChain": chain_id,
        "fromToken": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913" if chain_id == "8453" else "0x0000000000000000000000000000000000000000",
        "toChain": chain_id,
        "toToken": vault["vaultAddress"],
        "fromAmount": str(1000 * 1_000_000) if chain_id == "8453" else str(10**17),
        "fromAddress": "0x000000000000000000000000000000000000dEaD",
    }


def fetch_quote(vault: Dict[str, Any]) -> Dict[str, Any]:
    session = build_session()
    candidate_urls = [
        f"{BASE_URL}/quote",
    ]

    last_error = None
    for url in candidate_urls:
        try:
            response = session.get(
                url,
                headers = {"x-lifi-integrator": "yieldrazor"},
                params=build_quote_params(vault),
                timeout=30,
            )
        except requests.RequestException as exc:
            last_error = f"request error on {url}: {exc}"
            continue
        response.raise_for_status()
        return response.json()

    raise RuntimeError(f"quote 请求失败: {last_error}")


def main() -> None:
    print("\n[env] BASE_URL:", BASE_URL)
    proxy = CUSTOM_PROXY or HTTPS_PROXY or HTTP_PROXY
    print("[env] Proxy:", proxy if proxy else "<none>")
    masked_key = "<missing>"
    if OPENAI_API_KEY:
        masked_key = OPENAI_API_KEY[:8] + "..." if not OPENAI_API_KEY.startswith("YOUR_") else "<placeholder>"
    print("[env] OPENAI_API_KEY:", masked_key)
    print("\n[1/4] Preparing documented sample vaults...")
    vaults = get_sample_vaults()

    sample_vaults = vaults[:2]
    print("\n[2/4] First 2 vaults sample JSON:\n")
    print(json.dumps(sample_vaults, ensure_ascii=False, indent=2))

    print("\n[3/4] Running LLM audit...\n")
    llm_result = run_llm_audit(sample_vaults)
    print(json.dumps(llm_result, ensure_ascii=False, indent=2))

    recommended_id = llm_result.get("recommended_vault_id", "")
    matched = next((vault for vault in sample_vaults if vault.get("id") == recommended_id), None)
    if not matched:
        raise RuntimeError(f"LLM 推荐的 vault id 未在样本中命中: {recommended_id}")

    print("\n[4/4] Fetching quote with documented vault token...\n")
    quote = fetch_quote(matched)
    print(json.dumps(quote, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
