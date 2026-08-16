# 從雜亂叫車資料到營運決策

## 桃園機場旅遊合作 SQL 專題：完整結案報告

> 專題定位：大學期間製作的個人資料分析專題；資料完全合成，用於展示叫車平台營運分析所需的 SQL、活動營運與跨部門思維。

## 摘要

本專題模擬旅客抵達桃園機場後，透過虛構旅遊合作夥伴及 CRM 取得叫車優惠的活動。資料從 52,222 筆原始訂單開始，經 SQL 去重、事件生命週期重建、座標與付款完整性檢查後，保留 48,347 筆可用行程；最終形成 6,824 位符合資格的活動受眾。

Airport 150 的首次機場完成行程增幅最高（8.7%，95% CI 5.5% 至 11.9%）；Bundle 100+100 的 D7 回訪率最高（8.3%）。不過以完整七日行程、有效優惠成本與 Control 作比較後，兩個方案的增量貢獻皆未轉正，因此結案建議為：保留 Control、降低補貼或改由夥伴共同出資，並以機場服務品質及預算節奏作為擴量前提。

## 1. 構思：為什麼選這個題目？

這份專題不把問題簡化成「發優惠券後叫車量有沒有上升」。營運角色需要同時處理合作夥伴資料、CRM 資格、優惠規則、供需健康度、預算，以及可落地的跨部門流程。因此本題設定為：在固定八週預算內，旅客抵達桃園機場後，應提供單次機場優惠還是兩段式優惠，才能帶來真正的增量商業價值，而不是只增加補貼支出。

設計原則如下：

1. 用合成資料保護隱私，但保留真實叫車資料常見的品質問題。
2. 用 SQL 把原始資料轉成可解釋、可重跑的決策資料集。
3. 用 Control 和 Intent-to-Treat 避免只看已兌換者造成的偏差。
4. 將 ETA、取消率、供需缺口、預算放進同一個營運決策，而不是只報行銷成效。

## 2. 業務情境與實驗設計

活動期間為 2025-09-01 至 2025-10-26。受眾須具備已確認的合作夥伴抵台訂位、CRM 同意、180 天內沒有台灣完成行程，且不在風險排除名單。

| 組別 | 配比 | 方案 |
|---|---:|---|
| Control | 10% | 僅提供旅遊資訊與合作夥伴頁面 |
| Airport 150 | 45% | 首次機場行程折抵 NT$150 |
| Bundle 100+100 | 45% | 首次機場行程 NT$100，7 日內後續當地行程再 NT$100 |

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
| future_or_unparseable_event_time | hard_invalid | 1,968 | quarantined |
| non_monotonic_event_steps | hard_invalid | 1,819 | quarantined |
| invalid_event_sequence | hard_invalid | 1,424 | quarantined |
| invalid_coordinates | hard_invalid | 513 | quarantined |
| payment_exceeds_gross_fare | hard_invalid | 304 | quarantined |
| negative_fare | hard_invalid | 178 | quarantined |
| orphan_user | hard_invalid | 104 | quarantined |
| orphan_driver | hard_invalid | 104 | quarantined |
| implausible_speed | hard_invalid | 25 | quarantined |
| late_arriving_event | warning | 4,522 | kept_with_warning |

清洗前完成車資為 NT$21,979,956，可信車資為 NT$20,505,068。這表示若直接使用原始資料，財務判讀將被高估；因此後續 Campaign 與 Marketplace 指標都只使用 `valid_for_trip_kpi = true` 的行程。

## 4. 活動結果與商業判讀

| 組別 | 受眾 | 機場完成率 | D7 回訪率 | 增量機場完成行程 | 增量七日完成行程 | 有效優惠成本 | 增量貢獻 | 決策 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Control | 683 | 16.4% | 2.8% | - | - | NT$0 | - | baseline |
| Airport 150 | 3,053 | 25.1% | 5.0% | 265.4 | 329.9 | NT$112,500 | NT$-42,480 | hold_or_redesign |
| Bundle 100+100 | 3,088 | 23.5% | 8.3% | 218.6 | 397.4 | NT$96,400 | NT$-25,592 | hold_or_redesign |

Airport 150 對首趟機場轉換最有力，但單趟補貼成本高。Bundle 的回訪較好，卻同時帶來第二段補貼；完整七日淨貢獻仍不足以覆蓋相較 Control 的成本。因此本次結果不能直接擴量，應進入方案重設。

## 5. Marketplace 與預算治理

### 5.1 活動期服務品質

| 區域 | 接單率 | 取消率 | P90 of P90 ETA（分鐘） | 可觀測小時數 | 需介入小時數 |
|---|---:|---:|---:|---:|---:|
| TPE_AIRPORT | 94.3% | 12.8% | 21.2 | 1,293 | 551 |
| TAIPEI_MAIN | 94.7% | 13.8% | 20.6 | 669 | 252 |
| TAIPEI_101 | 94.5% | 11.0% | 20.5 | 727 | 256 |
| XIMENDING | 94.9% | 12.1% | 20.9 | 705 | 253 |

### 5.2 相對基準期 Guardrail

| 區域 | 基準期平均 P90 ETA | 活動期平均 P90 ETA | ETA 變化 | 取消率變化（百分點） | 狀態 |
|---|---:|---:|---:|---:|---|
| TPE_AIRPORT | 15.2 | 17.5 | 15.0% | 0.6% | guardrail_breach |
| TAIPEI_101 | 15.5 | 15.2 | -1.7% | -0.7% | pass |
| XIMENDING | 15.1 | 15.4 | 1.4% | 1.7% | guardrail_breach |
| TAIPEI_MAIN | 15.7 | 15.1 | -3.4% | -1.1% | pass |

TPE Airport 活動期 P90 ETA 為 21.2 分鐘，Guardrail 判定為 `guardrail_breach`。沒有實際清洗後行程的 Zone-hour 會標示為 `source_only_no_observed_trip`，不會被誤算成 0% 接單或取消率。

截至結案日，有效優惠累計支出 NT$208,900／預算 NT$150,000（139.3%），狀態為 `alert_over_budget`。每日 Mart 會在累積支出高於按日計畫 15% 時告警，讓 Operations 在 CRM 發送與優惠條件上及早收斂。

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
