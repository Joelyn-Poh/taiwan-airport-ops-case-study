"""Build the Traditional Chinese closeout report, PDF, and English interview summary."""

from __future__ import annotations

import json
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "report"
SUMMARY = json.loads((ROOT / "outputs" / "summary.json").read_text(encoding="utf-8"))
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
CAMPAIGN = CONFIG["campaign"]


def number(value: float | int | None, digits: int = 0) -> str:
    return "-" if value is None else f"{float(value):,.{digits}f}"


def percent(value: float | None) -> str:
    return "-" if value is None else f"{float(value) * 100:.1f}%"


def twd(value: float | None) -> str:
    return "-" if value is None else f"NT${float(value):,.0f}"


def by_key(rows: list[dict], key: str) -> dict:
    return {str(row[key]): row for row in rows}


PIPELINE = by_key(SUMMARY["mart_pipeline_row_counts"], "object_name")
FUNNEL = by_key(SUMMARY["mart_campaign_funnel"], "experiment_arm")
EXPERIMENT = by_key(SUMMARY["mart_experiment_results"], "experiment_arm")
MARKET = by_key(SUMMARY["mart_marketplace_summary"], "service_zone")
GUARDRAILS = by_key(SUMMARY["mart_marketplace_guardrails"], "service_zone")
RAW_CLEAN = by_key(SUMMARY["mart_raw_vs_clean_kpi"], "metric")
BUDGET_DAILY = SUMMARY["mart_campaign_budget_daily"]


def report_markdown() -> str:
    control = EXPERIMENT["control"]
    airport = EXPERIMENT["airport_150"]
    bundle = EXPERIMENT["bundle_100_100"]
    tpe = MARKET["TPE_AIRPORT"]
    tpe_guardrail = GUARDRAILS["TPE_AIRPORT"]
    final_budget = BUDGET_DAILY[-1]
    quality_rows = "\n".join(
        f"| {row['issue_code']} | {row['severity']} | {number(row['affected_trips'])} | {row['disposition']} |"
        for row in SUMMARY["mart_data_quality_report"]
    )
    market_rows = "\n".join(
        f"| {row['service_zone']} | {percent(row['acceptance_rate'])} | {percent(row['cancellation_rate'])} | "
        f"{number(row['p90_of_p90_pickup_eta_min'], 1)} | {number(row['observed_metric_hours'])} | {row['intervention_hours']} |"
        for row in SUMMARY["mart_marketplace_summary"]
    )
    guardrail_rows = "\n".join(
        f"| {row['service_zone']} | {number(row['baseline_avg_p90_pickup_eta_min'], 1)} | "
        f"{number(row['campaign_avg_p90_pickup_eta_min'], 1)} | {percent(row['p90_eta_pct_change_vs_baseline'])} | "
        f"{percent(row['cancellation_rate_pp_change_vs_baseline'])} | {row['guardrail_status']} |"
        for row in SUMMARY["mart_marketplace_guardrails"]
    )
    return f"""# 從雜亂叫車資料到營運決策

## 桃園機場旅遊合作 SQL 專題：完整結案報告

> 專題定位：個人學習資料分析專題；資料完全合成，用於展示叫車平台營運分析所需的 SQL、活動營運與跨部門思維。

## 摘要

本專題模擬旅客抵達桃園機場後，透過虛構旅遊合作夥伴及 CRM 取得叫車優惠的活動。資料從 {number(PIPELINE['raw_trip_orders']['row_count'])} 筆原始訂單開始，經 SQL 去重、事件生命週期重建、座標與付款完整性檢查後，保留 {number(PIPELINE['valid_trip_lifecycle']['row_count'])} 筆可用行程；最終形成 {number(PIPELINE['campaign_cohort']['row_count'])} 位符合資格的活動受眾。

Airport 150 的首次機場完成行程增幅最高（{percent(airport['incremental_conversion_rate'])}，95% CI {percent(airport['incremental_conversion_ci_low'])} 至 {percent(airport['incremental_conversion_ci_high'])}）；Bundle 100+100 的 D7 回訪率最高（{percent(bundle['d7_repeat_rate'])}）。不過以完整七日行程、有效優惠成本與 Control 作比較後，兩個方案的增量貢獻皆未轉正，因此結案建議為：保留 Control、降低補貼或改由夥伴共同出資，並以機場服務品質及預算節奏作為擴量前提。

## 1. 構思：為什麼選這個題目？

這份專題不把問題簡化成「發優惠券後叫車量有沒有上升」。營運角色需要同時處理合作夥伴資料、CRM 資格、優惠規則、供需健康度、預算，以及可落地的跨部門流程。因此本題設定為：在固定八週預算內，旅客抵達桃園機場後，應提供單次機場優惠還是兩段式優惠，才能帶來真正的增量商業價值，而不是只增加補貼支出。

設計原則如下：

1. 用合成資料保護隱私，但保留真實叫車資料常見的品質問題。
2. 用 SQL 把原始資料轉成可解釋、可重跑的決策資料集。
3. 用 Control 和 Intent-to-Treat 避免只看已兌換者造成的偏差。
4. 將 ETA、取消率、供需缺口、預算放進同一個營運決策，而不是只報行銷成效。

## 2. 業務情境與實驗設計

活動期間為 {CAMPAIGN['start_date']} 至 {CAMPAIGN['end_date']}。受眾須具備已確認的合作夥伴抵台訂位、CRM 同意、{CAMPAIGN['prior_trip_exclusion_days']} 天內沒有台灣完成行程，且不在風險排除名單。

| 組別 | 配比 | 方案 |
|---|---:|---|
| Control | 10% | 僅提供旅遊資訊與合作夥伴頁面 |
| Airport 150 | 45% | 首次機場行程折抵 NT$150 |
| Bundle 100+100 | 45% | 首次機場行程 NT$100，{CAMPAIGN['attribution_window_days']} 日內後續當地行程再 NT$100 |

擴量條件：增量貢獻為正、機場轉換率信賴區間排除 0、P90 接車 ETA 相較基準期增加不超過 10%、取消率增加不超過 1 個百分點，且預算不超過按日計畫 15%。

## 3. 資料與 SQL 進行過程

### 3.1 合成髒資料設計

資料包含 Rider、Driver、Partner booking、Trip order、Trip event、Payment、Campaign assignment、Promo redemption、CRM event、Zone-hour supply snapshot。為接近營運現場，刻意混入重複訂單、重複事件、不可解析或未來時間、事件順序倒置、座標缺失或超出台灣範圍、孤兒使用者／司機、負車資、付款高於車資、延遲到貨事件與違反活動資格的兌換紀錄。

### 3.2 SQL 資料流

`raw_*` → `stg_*` 標準化 → 去重 → `trip_quality_issues` → `fct_trip_lifecycle` → 活動 Cohort / 優惠資格 → Funnel / Experiment / Marketplace / Budget Marts。

關鍵控制包括：保留最早入倉的重複紀錄、檢查 `requested ≤ accepted ≤ picked_up ≤ completed`、取消發生時間、平均速度、外鍵、付款、優惠券與 Trip 的使用者一致性、優惠碼與實驗組別一致性、機場首趟與 Bundle 第二趟的七日資格。

### 3.3 清洗結果

| 問題類型 | 嚴重度 | 受影響行程 | 處置 |
|---|---|---:|---|
{quality_rows}

清洗前完成車資為 {twd(RAW_CLEAN['gross_fare_twd']['raw_value'])}，可信車資為 {twd(RAW_CLEAN['gross_fare_twd']['clean_value'])}。這表示若直接使用原始資料，財務判讀將被高估；因此後續 Campaign 與 Marketplace 指標都只使用 `valid_for_trip_kpi = true` 的行程。

## 4. 活動結果與商業判讀

| 組別 | 受眾 | 機場完成率 | D7 回訪率 | 增量機場完成行程 | 增量七日完成行程 | 有效優惠成本 | 增量貢獻 | 決策 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Control | {number(control['assigned_users'])} | {percent(control['airport_conversion_rate'])} | {percent(control['d7_repeat_rate'])} | - | - | {twd(control['reward_cost_twd'])} | - | baseline |
| Airport 150 | {number(airport['assigned_users'])} | {percent(airport['airport_conversion_rate'])} | {percent(airport['d7_repeat_rate'])} | {number(airport['incremental_completed_trips'], 1)} | {number(airport['incremental_7d_completed_trips'], 1)} | {twd(airport['reward_cost_twd'])} | {twd(airport['incremental_contribution_twd'])} | {airport['experiment_decision']} |
| Bundle 100+100 | {number(bundle['assigned_users'])} | {percent(bundle['airport_conversion_rate'])} | {percent(bundle['d7_repeat_rate'])} | {number(bundle['incremental_completed_trips'], 1)} | {number(bundle['incremental_7d_completed_trips'], 1)} | {twd(bundle['reward_cost_twd'])} | {twd(bundle['incremental_contribution_twd'])} | {bundle['experiment_decision']} |

Airport 150 對首趟機場轉換最有力，但單趟補貼成本高。Bundle 的回訪較好，卻同時帶來第二段補貼；完整七日淨貢獻仍不足以覆蓋相較 Control 的成本。因此本次結果不能直接擴量，應進入方案重設。

## 5. Marketplace 與預算治理

### 5.1 活動期服務品質

| 區域 | 接單率 | 取消率 | P90 of P90 ETA（分鐘） | 可觀測小時數 | 需介入小時數 |
|---|---:|---:|---:|---:|---:|
{market_rows}

### 5.2 相對基準期 Guardrail

| 區域 | 基準期平均 P90 ETA | 活動期平均 P90 ETA | ETA 變化 | 取消率變化（百分點） | 狀態 |
|---|---:|---:|---:|---:|---|
{guardrail_rows}

TPE Airport 活動期 P90 ETA 為 {number(tpe['p90_of_p90_pickup_eta_min'], 1)} 分鐘，Guardrail 判定為 `{tpe_guardrail['guardrail_status']}`。沒有實際清洗後行程的 Zone-hour 會標示為 `source_only_no_observed_trip`，不會被誤算成 0% 接單或取消率。

截至結案日，有效優惠累計支出 {twd(final_budget['cumulative_spend_twd'])}／預算 {twd(final_budget['budget_twd'])}（{percent(final_budget['budget_spend_rate'])}），狀態為 `{final_budget['budget_status']}`。每日 Mart 會在累積支出高於按日計畫 15% 時告警，讓 Operations 在 CRM 發送與優惠條件上及早收斂。

## 6. 跨部門執行設計

1. Partnerships / Legal：確認資料使用目的、責任歸屬、優惠成本與取消退款條款。
2. Marketing：準備繁中與英文 CRM、夥伴落地頁、發送時段與版本紀錄。
3. Product / Operations：設定機場區域、首趟與第二趟資格、期限、客服處理規則。
4. Analytics：審查 Cohort SQL、維持 Control、每日刷新 Dashboard 與資料品質測試。
5. Marketplace：在 ETA 或取消率越界時暫停新增發送、調整供給或收窄地理範圍。

對應的 launch checklist、monitoring playbook 與 postmortem 位於 `docs/` 與 `report/`，讓分析結論可以轉換為可執行流程。

## 7. 結案建議與限制

**結案建議：暫不全面擴量。** 保留 Control、將 Bundle 的第二趟補貼改為合作夥伴共同出資或降低金額，並以機場尖峰時段的 ETA、取消率和預算節奏控制 CRM 發送。

本專題的限制是資料全為合成，未納入真實旅客客群差異、價格彈性、合作夥伴實際成本、外部交通或天候因素。若進入正式實驗，下一步應先做樣本數規畫、設定預先註冊的成功門檻，並加入客服、退款與供給誘因資料。

## 8. 可重跑方式

```powershell
python -m pip install -r requirements.txt
npm install
python src/generate_synthetic_data.py --mode sample
python src/run_pipeline.py
node src/build_dashboard.mjs
python src/build_report.py
```

所有資料均為合成資料；市場背景來源與限制請見 `docs/sources.md`，資料清洗與指標定義請見 `docs/cleaning_rules.md`、`docs/metric_definitions.md`。
"""


def english_summary() -> str:
    airport = EXPERIMENT["airport_150"]
    bundle = EXPERIMENT["bundle_100_100"]
    final_budget = BUDGET_DAILY[-1]
    return f"""# Executive Summary

## From Dirty Ride Data to Operations Decisions

An independent, synthetic-data personal learning project about ride-hailing platform operations.

### Decision

Do not fully scale either current reward. Keep a Control holdout, reduce the subsidy or obtain partner co-funding, and pace CRM sends against airport marketplace guardrails.

### Evidence

- SQL cleaning reduced {number(PIPELINE['raw_trip_orders']['row_count'])} raw order rows to {number(PIPELINE['valid_trip_lifecycle']['row_count'])} trusted trip records.
- Airport 150 produced the strongest first-airport-trip lift: {percent(airport['incremental_conversion_rate'])}, with a 95% CI of {percent(airport['incremental_conversion_ci_low'])} to {percent(airport['incremental_conversion_ci_high'])}.
- Bundle 100+100 delivered the highest D7 repeat rate at {percent(bundle['d7_repeat_rate'])}, but both treatments had negative full seven-day incremental contribution after valid reward cost.
- Valid reward spend reached {twd(final_budget['cumulative_spend_twd'])} against a {twd(final_budget['budget_twd'])} budget; the operating dashboard exposes pace alerts and service-quality guardrails.

### Repository guide

- `sql/`: DuckDB transformations, cohort logic, experiment measurement, marketplace and budget marts.
- `tests/`: lifecycle, promotion-integrity, and mart assertions.
- `dashboard/`: Excel operating dashboard.
- `report/`: Traditional Chinese closeout report and PDF.
- `docs/`: campaign brief, launch checklist, monitoring playbook, source notes, and definitions.

All operational records are synthetic and do not represent any real ride-hailing platform.
"""


def styles() -> dict[str, ParagraphStyle]:
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    base = getSampleStyleSheet()
    return {
        "cover": ParagraphStyle("cover", parent=base["Title"], fontName="STSong-Light", fontSize=23, leading=33, alignment=TA_CENTER, textColor=colors.HexColor("#102A43")),
        "subtitle": ParagraphStyle("subtitle", parent=base["BodyText"], fontName="STSong-Light", fontSize=11, leading=18, alignment=TA_CENTER, textColor=colors.HexColor("#486581")),
        "h1": ParagraphStyle("h1", parent=base["Heading1"], fontName="STSong-Light", fontSize=16, leading=23, textColor=colors.HexColor("#102A43"), spaceBefore=10, spaceAfter=8),
        "body": ParagraphStyle("body", parent=base["BodyText"], fontName="STSong-Light", fontSize=9.3, leading=15, textColor=colors.HexColor("#212529"), spaceAfter=7),
        "table": ParagraphStyle("table", parent=base["BodyText"], fontName="STSong-Light", fontSize=7.5, leading=10, textColor=colors.HexColor("#212529")),
    }


def paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(text).replace("\n", "<br/>"), style)


def table(headers: list[str], rows: list[list[str]], widths: list[float], s: dict[str, ParagraphStyle]) -> Table:
    data = [[paragraph(item, s["table"]) for item in headers]]
    data.extend([[paragraph(str(item), s["table"]) for item in row] for row in rows])
    result = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    result.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0B7285")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D9E2EC")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F9FA")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return result


def footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#627D98"))
    canvas.drawString(18 * mm, 10 * mm, "Taiwan Airport Ride-Hailing Operations SQL Case Study | Synthetic educational data")
    canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def build_pdf() -> None:
    s = styles()
    output = REPORT_DIR / "final_report.pdf"
    doc = SimpleDocTemplate(output.as_posix(), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm, topMargin=18 * mm, bottomMargin=18 * mm)
    airport = EXPERIMENT["airport_150"]
    bundle = EXPERIMENT["bundle_100_100"]
    final_budget = BUDGET_DAILY[-1]
    story = [
        Spacer(1, 45 * mm),
        paragraph("從雜亂叫車資料到營運決策", s["cover"]),
        Spacer(1, 7 * mm),
        paragraph("桃園機場旅遊合作 SQL 專題｜完整結案報告", s["subtitle"]),
        Spacer(1, 12 * mm),
        paragraph("個人學習專題｜合成資料｜台灣機場叫車平台營運分析", s["subtitle"]),
        PageBreak(),
        paragraph("摘要與結論", s["h1"]),
        paragraph("本案以髒資料模擬機場旅客叫車活動。經 SQL 清洗、Cohort 圈選、優惠資格核驗與 Intent-to-Treat 比較後，兩個現行優惠方案均不適合直接全面擴量。建議保留 Control、降低補貼或爭取合作夥伴共同出資，並對機場 ETA、取消率與預算建立每日監控。", s["body"]),
        table(["組別", "機場轉換", "D7 回訪", "增量貢獻", "決策"], [
            ["Control", percent(EXPERIMENT["control"]["airport_conversion_rate"]), percent(EXPERIMENT["control"]["d7_repeat_rate"]), "-", "baseline"],
            ["Airport 150", percent(airport["airport_conversion_rate"]), percent(airport["d7_repeat_rate"]), twd(airport["incremental_contribution_twd"]), airport["experiment_decision"]],
            ["Bundle 100+100", percent(bundle["airport_conversion_rate"]), percent(bundle["d7_repeat_rate"]), twd(bundle["incremental_contribution_twd"]), bundle["experiment_decision"]],
        ], [32 * mm, 30 * mm, 30 * mm, 38 * mm, 35 * mm], s),
        paragraph("構思與資料流程", s["h1"]),
        paragraph("設計重點是把活動成效、優惠成本與市場供需放在同一個營運問題。資料流由 Raw、Staging、去重、品質問題表、可信 Trip Lifecycle，到活動、實驗、Marketplace 與 Budget Marts；每一步皆可以由 SQL 重跑與測試驗證。", s["body"]),
        paragraph("資料清洗", s["h1"]),
        paragraph(f"原始訂單 {number(PIPELINE['raw_trip_orders']['row_count'])} 筆，最後可信行程 {number(PIPELINE['valid_trip_lifecycle']['row_count'])} 筆。清洗會檢查重複、時間、事件順序、座標、外鍵、付款與優惠資格；硬性異常隔離，延遲到貨事件保留警示。", s["body"]),
        PageBreak(),
        paragraph("活動與 Marketplace 結果", s["h1"]),
        paragraph(f"Airport 150 的增量機場轉換為 {percent(airport['incremental_conversion_rate'])}，95% 信賴區間為 {percent(airport['incremental_conversion_ci_low'])} 至 {percent(airport['incremental_conversion_ci_high'])}。Bundle 100+100 的 D7 回訪率是 {percent(bundle['d7_repeat_rate'])}，但計入完整七日行程及有效優惠成本後，兩案的增量貢獻仍為負。", s["body"]),
        paragraph(f"截至結案，有效優惠支出 {twd(final_budget['cumulative_spend_twd'])}／預算 {twd(final_budget['budget_twd'])}，狀態為 {final_budget['budget_status']}。系統將缺少觀測行程的 Zone-hour 明確標示，不把它誤算成 0% 接單或取消。", s["body"]),
    ]
    preview = ROOT / "dashboard" / "screenshots" / "dashboard_preview.png"
    if preview.exists():
        story.extend([Spacer(1, 4 * mm), Image(preview.as_posix(), width=170 * mm, height=85 * mm)])
    story.extend([
        paragraph("跨部門執行與結案", s["h1"]),
        paragraph("Partnerships / Legal 負責合作條款與成本責任；Marketing 管理雙語 CRM；Product / Operations 落實優惠條件與客服流程；Analytics 維護 Cohort、Control 與 Dashboard；Marketplace 依 Guardrail 調整供給或暫停發送。完整檢核表、監控規則與限制已記錄在 docs/。", s["body"]),
    ])
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


def main() -> None:
    REPORT_DIR.mkdir(exist_ok=True)
    (REPORT_DIR / "final_report.md").write_text(report_markdown(), encoding="utf-8")
    (REPORT_DIR / "executive_summary_en.md").write_text(english_summary(), encoding="utf-8")
    (ROOT / "docs" / "postmortem.md").write_text(
        "# Postmortem\n\n## Decision\n\nDo not fully scale either current reward. Retain a Control holdout, reduce the subsidy or obtain partner co-funding, and pace CRM sends against Marketplace and budget guardrails.\n\n## What changed after analysis\n\nThe first version over-simplified Marketplace hours without observed trips and calculated contribution from first-trip conversion only. The final pipeline labels non-observed hours explicitly, validates reward eligibility end to end, and compares full seven-day net contribution per assigned user against Control.\n\n## Next experiment\n\nTest a lower second-trip reward with partner funding, pre-register the causal and service-quality decision gates, and add customer-support, refund, and supply-incentive data.\n",
        encoding="utf-8",
    )
    build_pdf()
    print(f"Generated report artifacts in {REPORT_DIR}")


if __name__ == "__main__":
    main()
