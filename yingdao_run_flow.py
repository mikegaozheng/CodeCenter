#!/usr/bin/env python3
"""上传 1.png 并调用影刀 Power 流程。直接运行: python3 yingdao_run_flow.py"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

# 完整 Authorization 值（已含 Bearer，原样填入即可）
YINGDAO_TOKEN = "Bearer AP_VHYbfTUUFYqQNMhw" # <--------TOKEN值
HEADERS = {"Authorization": YINGDAO_TOKEN}

UPLOAD_FILE_URL = "https://power-api.yingdao.com/oapi/power/v1/file/upload"
FLOW_EXECUTE_URL = (
    "https://power-api.yingdao.com/0api/power/v1/rest/flow/"
    "196455ee-441b-449c-8cbc-f74514f926e0/execute"
)

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_IMAGE = SCRIPT_DIR / "1.png" #<-----图片路径


def upload_file(image_path: Path) -> tuple[str, str]:
    """上传图片，返回 (filename, url)。"""
    if not image_path.is_file():
        raise FileNotFoundError(f"找不到图片: {image_path}")

    with image_path.open("rb") as f:
        response = requests.post(
            UPLOAD_FILE_URL,
            headers=HEADERS,
            files={"file": (image_path.name, f)},
            timeout=60,
        )
    response.raise_for_status()
    body = response.json()

    if not body.get("success"):
        raise RuntimeError(f"上传失败: {body}")

    data = body.get("data") or {}
    url = data.get("fileReadUrl") or data.get("url")
    if not url:
        raise RuntimeError(f"上传响应中未找到 url: {json.dumps(body, ensure_ascii=False)}")

    return image_path.name, url


def execute_flow(filename: str, url: str) -> dict:
    """执行流程，返回接口 JSON。"""
    headers = {**HEADERS, "Content-Type": "application/json"}
    payload = {
        "input": {
            "input_image_0": {
                "filename": filename,
                "url": url,
            }
        }
    }
    response = requests.post(
        FLOW_EXECUTE_URL,
        headers=headers,
        json=payload,
        timeout=120,
    )
    response.raise_for_status()
    body = response.json()

    if not body.get("success"):
        raise RuntimeError(f"流程执行失败: {json.dumps(body, ensure_ascii=False)}")

    return body


def main() -> None:
    image_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_IMAGE

    print(f"上传: {image_path}")
    filename, url = upload_file(image_path)
    print(f"  filename: {filename}")
    print(f"  url: {url}")

    print("执行流程...")
    result = execute_flow(filename, url)

    print(json.dumps(result, ensure_ascii=False, indent=2))

    output = (result.get("data") or {}).get("result") or {}
    if output:
        print("\n--- 流程输出 ---")
        print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
