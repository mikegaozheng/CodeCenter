#!/usr/bin/env python3
"""
PDF 拆分工具（内置路径配置）

使用方式：
1. 修改下方 CONFIG 中的路径和页码
2. 执行 `python pdf_splitter.py`

依赖：
    pip install PyPDF2
"""

import sys
from dataclasses import dataclass
from pathlib import Path

try:
    from PyPDF2 import PdfReader, PdfWriter
except ImportError as exc:
    print("错误：未找到 PyPDF2 库。请先运行 `pip install PyPDF2`。")
    raise SystemExit(1) from exc


@dataclass
class SplitConfig:
    """PDF 拆分所需配置"""

    input_pdf: Path
    output_pdf: Path
    start_page: int
    end_page: int


# === 修改这里以适配你的需求 ===
CONFIG = SplitConfig(
    input_pdf=Path("/Users/mikegao/Desktop/2022高校财务制度.pdf"), 
    output_pdf=Path("/Users/mikegao/Desktop/SPLITTED2022高校财务制度.pdf"),
    start_page=1,
    end_page=5,
)


def split_pdf(src: Path, dst: Path, start_page: int, end_page: int) -> None:
    if not src.exists():
        raise FileNotFoundError(f"未找到源文件：{src}")

    if start_page < 1 or end_page < 1:
        raise ValueError("页码必须从 1 开始且为正整数。")

    if start_page > end_page:
        raise ValueError("起始页码不能大于结束页码。")

    reader = PdfReader(src)
    total_pages = len(reader.pages)

    if start_page > total_pages:
        raise ValueError(
            f"起始页码 {start_page} 超过总页数 {total_pages}。"
        )

    if end_page > total_pages:
        raise ValueError(
            f"结束页码 {end_page} 超过总页数 {total_pages}。"
        )

    writer = PdfWriter()
    for page_num in range(start_page - 1, end_page):
        writer.add_page(reader.pages[page_num])

    dst.parent.mkdir(parents=True, exist_ok=True)
    with dst.open("wb") as fh:
        writer.write(fh)


def main() -> int:
    cfg = CONFIG

    try:
        split_pdf(cfg.input_pdf, cfg.output_pdf, cfg.start_page, cfg.end_page)
    except Exception as exc:  # pylint: disable=broad-except
        print(f"❌ 拆分失败：{exc}")
        return 1

    print(
        f"✅ 已成功生成 {cfg.output_pdf}，页码范围：{cfg.start_page} - {cfg.end_page}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())



[{'filename': 'desktop.ini', 'creation_time': '2025-06-03 16:36:21'}, 
{'filename': 'stable_diffusion_极速版.zip', 'creation_time': '2025-07-26 19:07:28'}, 
{'filename':  ’release-standard-standard-shizai-CN-develop-7.1.0-ci-14485.exe', 'creation_time': '2025-07-26 22:01:22'}, 
{'filename': 'Adobe 2025 P s 安装向导.exe', 'creation_time': '2025-09-21 11:15:23'}, 
{'filename': 'AutomaRPA-2.0.2-x64.exe', 'creation_time': '2025-10-29 10:15:37'}, 
{'filename': 'sellersprite-extension-mv3-v4.8.3.zip', 'creation_time': '2025-11-25 17:06:44'}, 
{'filename': '订单数据.xlsx', 'creation_time': '2025-11-28 10:40:46'}]