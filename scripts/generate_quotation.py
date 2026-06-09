#!/usr/bin/env python3
"""生成项目报价单 Excel 文件。"""

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, Side
from openpyxl.utils import get_column_letter

OUTPUT = Path(__file__).resolve().parent.parent / "报价单.xlsx"

HEADERS = ("需求单", "价格（人民币/元）")

ROWS = [
    ("后端支持OCR图片处理，用户确认后存储到数据库。", 2000),
    (
        "后端支持数据计算，例如涨幅均差等。支持历史记录查询",
        2000,
    ),
    (
        '用户上传图片处理成功后，机器人同步在群内更新"某某已上传当日价格"消息',
        2000,
    ),
    (
        "前端支持用户上传图片，并用户确认。前端支持图表展示（展示内容根据甲方要求改）。前端支持历史记录查看。",
        4000,
    ),
    (
        "集成该应用到钉钉中，能够在工作台找到企业内部应用。",
        4000,
    ),
    ("阿里云服务器采购（可与其他项目共用）", "2190.2 每年"),
]

SUMMARY_ROWS = [
    ("总价", 16190.2),
    (
        "优惠价（钉钉集成已在其他项目付费，阿里云服务器不参与优惠）",
        "9000+2190=11190",
    ),
]


def thin_border() -> Border:
    side = Side(style="thin", color="CCCCCC")
    return Border(left=side, right=side, top=side, bottom=side)


def main() -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "报价单"

    header_font = Font(bold=True, size=11)
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left_wrap = Alignment(horizontal="left", vertical="center", wrap_text=True)
    right_align = Alignment(horizontal="right", vertical="center", wrap_text=True)
    border = thin_border()

    for col, title in enumerate(HEADERS, start=1):
        cell = ws.cell(row=1, column=col, value=title)
        cell.font = header_font
        cell.alignment = center
        cell.border = border

    row_idx = 2
    for requirement, price in ROWS:
        req_cell = ws.cell(row=row_idx, column=1, value=requirement)
        price_cell = ws.cell(row=row_idx, column=2, value=price)
        req_cell.alignment = left_wrap
        price_cell.alignment = right_align
        for cell in (req_cell, price_cell):
            cell.border = border
        row_idx += 1

    summary_font = Font(bold=True, size=11)
    for label, price in SUMMARY_ROWS:
        label_cell = ws.cell(row=row_idx, column=1, value=label)
        price_cell = ws.cell(row=row_idx, column=2, value=price)
        label_cell.font = summary_font
        price_cell.font = summary_font
        label_cell.alignment = left_wrap
        price_cell.alignment = right_align
        for cell in (label_cell, price_cell):
            cell.border = border
        row_idx += 1

    ws.column_dimensions["A"].width = 62
    ws.column_dimensions["B"].width = 22
    for r in range(1, row_idx):
        ws.row_dimensions[r].height = 36

    wb.save(OUTPUT)
    print(f"已生成: {OUTPUT}")


if __name__ == "__main__":
    main()
