#!/usr/bin/env python3
"""
XPath 优化工具 - 后端服务

功能：
1. 接收前端请求，抓取网页内容
2. 调用大模型 API 分析网页结构
3. 返回优化的 XPath 表达式

依赖：
    pip install flask flask-cors requests beautifulsoup4 lxml openai

使用方式：
    python xpath_optimizer_server.py
"""

import os
import json
import re
from typing import Dict, Optional, Any
from pathlib import Path

try:
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    import requests
    from bs4 import BeautifulSoup
except ImportError as exc:
    print("错误：缺少必要的依赖库。请运行：")
    print("pip install flask flask-cors requests beautifulsoup4 lxml")
    raise SystemExit(1) from exc

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 配置
CONFIG_FILE = Path(__file__).parent / "xpath_config.json"


def load_config() -> Dict:
    """加载配置文件"""
    default_config = {
        # Power API 配置
        "power_api_url": "https://power-api.yingdao.com/oapi/power/v1/rest/flow/12b4db3e-43cf-4cf2-a520-f68205623b44/execute",
        "power_api_token": "Bearer AP_Tdvgn24JBhG9BDS3",
        # 通用配置
        "timeout": 30,
        "max_retries": 3
    }
    
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        except Exception as e:
            print(f"警告：读取配置文件失败，使用默认配置：{e}")
    
    # 优先使用环境变量
    if os.getenv("POWER_API_TOKEN"):
        default_config["power_api_token"] = os.getenv("POWER_API_TOKEN")
    
    return default_config


CONFIG = load_config()


def fetch_webpage(url: str) -> tuple[Optional[str], Optional[str]]:
    """
    抓取网页内容
    
    Returns:
        (html_content, error_message)
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=CONFIG.get("timeout", 30))
        response.raise_for_status()
        response.encoding = response.apparent_encoding or 'utf-8'
        return response.text, None
    except requests.exceptions.RequestException as e:
        return None, f"无法访问网页：{str(e)}"


def extract_html_structure(html: str, max_length: int = 8000) -> str:
    """
    提取 HTML 结构信息（用于发送给大模型）
    只保留关键的结构信息，避免内容过长
    """
    soup = BeautifulSoup(html, 'lxml')
    
    # 移除脚本和样式
    for script in soup(["script", "style", "noscript"]):
        script.decompose()
    
    # 提取关键信息
    structure_info = []
    
    # 提取所有元素的标签名、类名、ID、文本片段
    for tag in soup.find_all():
        attrs = {}
        if tag.get('id'):
            attrs['id'] = tag.get('id')
        if tag.get('class'):
            attrs['class'] = ' '.join(tag.get('class'))
        if tag.get('name'):
            attrs['name'] = tag.get('name')
        
        text = tag.get_text(strip=True)
        if text and len(text) > 50:
            text = text[:50] + "..."
        
        if attrs or text:
            structure_info.append({
                'tag': tag.name,
                'attrs': attrs,
                'text': text[:100] if text else None
            })
    
    # 转换为文本格式
    result = []
    for item in structure_info[:200]:  # 限制数量
        line = f"<{item['tag']}"
        if item['attrs']:
            attrs_str = ' '.join([f'{k}="{v}"' for k, v in item['attrs'].items()])
            line += f" {attrs_str}"
        line += ">"
        if item['text']:
            line += f" {item['text']}"
        result.append(line)
    
    structure_text = '\n'.join(result)
    
    # 如果太长，截断
    if len(structure_text) > max_length:
        structure_text = structure_text[:max_length] + "\n... (内容已截断)"
    
    return structure_text


def _find_first_value(data: Any, keys: tuple[str, ...]) -> Optional[str]:
    """在嵌套结构中按优先级寻找值"""
    if isinstance(data, dict):
        for k in keys:
            if k in data and isinstance(data[k], (str, int, float)):
                return str(data[k])
        for v in data.values():
            found = _find_first_value(v, keys)
            if found is not None:
                return found
    elif isinstance(data, list):
        for item in data:
            found = _find_first_value(item, keys)
            if found is not None:
                return found
    return None


def call_llm_api(html_structure: str, target: str, target_type: str, api_key: Optional[str] = None) -> Dict:
    """
    调用 power-api 接口生成 XPath
    """
    raw_token = (api_key or CONFIG.get("power_api_token") or "").strip()
    # 允许两种写法：直接填 "Bearer xxx" 或仅填 token
    if raw_token.lower().startswith("bearer "):
        auth_header = raw_token  # 已包含 Bearer
    else:
        auth_header = f"Bearer {raw_token}" if raw_token else ""

    api_url = CONFIG.get("power_api_url")

    if not auth_header or not api_url:
        return generate_mock_xpath(target, target_type)

    try:
        payload = {
            "input": {
                "input_text_0": html_structure,
                "input_text_1": target
            }
        }
        headers = {
            "Authorization": auth_header,
            "Content-Type": "application/json"
        }
        resp = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=CONFIG.get("timeout", 30)
        )
        resp.raise_for_status()
        resp_json = resp.json()

        xpath = _find_first_value(resp_json, ("output_text_0", "xpath", "result", "output"))
        explanation = _find_first_value(resp_json, ("output_text_1", "explanation", "desc", "message"))

        if not xpath:
            raise ValueError(f"模型返回格式无法解析：{resp_json}")

        return {
            "xpath": xpath,
            "explanation": explanation or "已生成最稳定的 XPath 表达式（来自模型）"
        }

    except Exception as e:
        # 输出更详细的错误信息，便于对照示例排查
        err_msg = str(e)
        try:
            err_body = resp.text  # type: ignore[arg-type]
            err_msg += f" | response={err_body[:500]}"
        except Exception:
            pass
        print(f"调用大模型 API 失败：{err_msg}")
        return generate_mock_xpath(target, target_type)


def generate_mock_xpath(target: str, target_type: str) -> Dict:
    """
    生成模拟的 XPath（当无法调用 API 时使用）
    """
    if target_type == 'text':
        # 基于文本内容生成 XPath
        xpath = f"//*[contains(text(), '{target[:30]}')]"
        explanation = f"基于文本内容 '{target[:30]}...' 生成的 XPath。建议：如果可能，请使用更具体的属性（如 ID 或 class）来定位元素。"
    elif target_type == 'xpath':
        # 优化现有 XPath
        xpath = target
        # 简单的优化：移除位置索引
        xpath = re.sub(r'\[\d+\]', '', xpath)
        explanation = "已移除位置索引以提高稳定性。建议：使用 ID、class 或其他稳定属性来定位元素。"
    else:  # selector
        # CSS 选择器转 XPath（简单转换）
        selector = target.strip()
        if selector.startswith('#'):
            id_val = selector[1:]
            xpath = f"//*[@id='{id_val}']"
        elif selector.startswith('.'):
            class_val = selector[1:].replace('.', ' ')
            xpath = f"//*[contains(@class, '{class_val}')]"
        else:
            xpath = f"//{selector}"
        explanation = f"已将 CSS 选择器 '{selector}' 转换为 XPath。建议：测试并验证该 XPath 是否准确。"
    
    return {
        'xpath': xpath,
        'explanation': explanation
    }


@app.route('/api/optimize-xpath', methods=['POST'])
def optimize_xpath():
    """API 端点：优化 XPath"""
    try:
        data = request.get_json()
        
        url = data.get('url')
        target = data.get('target')
        target_type = data.get('type', 'text')
        api_key = data.get('api_key')
        
        if not url or not target:
            return jsonify({'error': '缺少必要参数：url 和 target'}), 400
        
        # 抓取网页
        html, error = fetch_webpage(url)
        if error:
            return jsonify({'error': error}), 400
        
        # 提取结构信息
        html_structure = extract_html_structure(html)
        
        # 调用大模型分析
        result = call_llm_api(html_structure, target, target_type, api_key)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'服务器错误：{str(e)}'}), 500


@app.route('/api/health', methods=['GET'])
def health():
    """健康检查端点"""
    return jsonify({
        'status': 'ok',
        'has_power_token': bool(CONFIG.get("power_api_token")),
        'api_url': CONFIG.get("power_api_url")
    })


@app.route('/', methods=['GET'])
def index():
    """返回前端页面"""
    html_path = Path(__file__).parent / "xpath_optimizer.html"
    if html_path.exists():
        return open(html_path, 'r', encoding='utf-8').read()
    return "XPath 优化工具后端服务正在运行", 200


if __name__ == '__main__':
    print("=" * 60)
    print("XPath 优化工具 - 后端服务")
    print("=" * 60)
    print(f"Power API URL : {CONFIG.get('power_api_url')}")
    print(f"Token 配置   : {'已配置' if CONFIG.get('power_api_token') else '未配置（将使用模拟结果）'}")
    print("\n访问地址: http://localhost:8080")
    print("API 端点: http://localhost:8080/api/optimize-xpath")
    print("\n提示：")
    print("1. 在 xpath_config.json 中配置 power_api_token，或设置环境变量 POWER_API_TOKEN")
    print("2. 也可以在前端界面直接输入 Token（API Key）")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=8080, debug=True)
