# 從雜亂叫車資料到營運決策

## 桃園機場旅遊合作 SQL 專題

這是一份以 Uber Taiwan Mobility Operations Specialist 職務為目標的個人大學專題。專題以合成資料模擬「旅客抵達桃園機場後，透過旅遊合作夥伴與 CRM 取得叫車優惠」的真實營運情境，從資料清洗、受眾圈選、活動評估到供需風險控管，產出可重跑的 SQL、Excel Dashboard 與完整結案報告。

> 核心問題：在固定八週預算下，應該提供哪一種機場叫車優惠，才能增加完成行程與後續回訪，同時不犧牲機場接送品質？

## 專題展示的能力

- SQL 資料清洗：重複訂單與事件、無效座標、時間序錯置、孤兒關聯、付款異常、延遲到貨資料。
- 活動受眾：以合作夥伴訂位、CRM 同意、180 天無完成行程、風險排除建立 Cohort。
- 活動量測：Control、Airport 150、Bundle 100+100 的 Intent-to-Treat 成效比較。
- 營運決策：機場 P90 接車 ETA、取消率、供需缺口、基準期比較與預算節奏告警。
- 跨部門執行：Campaign brief、launch checklist、monitoring playbook、postmortem。

## 快速開始

```powershell
python -m pip install -r requirements.txt
npm install
python src/generate_synthetic_data.py --mode sample
python src/run_pipeline.py
node src/build_dashboard.mjs
python src/build_report.py
```

需要 Python 3.12、Node.js 20+、DuckDB、ReportLab 與 `@oai/artifact-tool`。若本機無法使用 Excel 產製套件，仍可執行 SQL Pipeline，直接閱讀 `outputs/data/` 的 CSV 分析表。

## 專案導覽

| 路徑 | 內容 |
|---|---|
| `src/` | 合成資料、SQL Pipeline、Dashboard、報告產製程式 |
| `sql/` | 從 Raw、Staging、Fact 到 Mart 的 DuckDB SQL |
| `tests/` | 交易生命週期、優惠資格、行銷與營運品質檢核 |
| `dashboard/` | Excel Dashboard 與預覽圖 |
| `report/` | 繁中完整報告、PDF、英文摘要 |
| `docs/` | 資料模型、清洗規則、指標、活動與營運文件 |
| `data/` | 合成原始資料、資料字典與髒資料清單 |

## 重要說明

所有人、司機、行程、合作夥伴與結果皆為合成資料。本專題不代表 Uber，也不使用任何 Uber 內部資料或真實業績。
