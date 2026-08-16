# 從雜亂的叫車資料找到營運答案

## 桃園機場旅客叫車優惠分析：大學專題報告

> 本專題是個人學習作品，所有乘客、司機、行程、合作夥伴及優惠資料皆為合成資料，並非任何真實叫車平台的內部資料。

---

## 專題摘要

我把自己設定成叫車平台的營運分析人員，模擬平台和旅遊業者合作，向抵達桃園機場的旅客發送叫車優惠。

這份專題想回答一個簡單的問題：發優惠是否真的能增加旅客叫車，而且不會造成虧損、超支或服務品質下降？

我先建立一批合成資料，並刻意加入重複訂單、錯誤時間、異常座標、付款錯誤等問題。接著使用 SQL 清理資料、找出符合活動資格的旅客，再比較三種活動方案的結果。

最後得到以下結論：

- 兩種優惠都能增加機場叫車完成率。
- `Airport 150` 對第一次機場叫車最有效。
- `Bundle 100+100` 對七天內再次叫車最有效。
- 兩種方案的優惠成本都高於帶來的額外收益。
- 活動總支出超過預算，而且桃園機場的等車時間變差。
- 因此不建議立刻全面推出，應先降低優惠金額、控制發送人數，並改善機場尖峰時段的司機供給。

---

## 1. 專題構想

### 1.1 為什麼選擇這個題目？

叫車平台的活動不能只看「訂單有沒有增加」。如果平台發出大量優惠，訂單可能變多，但同時也可能發生三個問題：

1. 優惠成本太高，增加的收入無法補回支出。
2. 旅客同時叫車，司機數量不足，等車時間變長。
3. 原始資料有錯誤，造成分析結果不可信。

因此，我把專題設計成一個完整的營運問題，而不是單純計算訂單量。

### 1.2 假設情境

假設叫車平台與一間旅遊合作夥伴合作。合作夥伴提供即將抵達桃園機場的旅客名單，平台透過 CRM 訊息向旅客介紹叫車服務及優惠。

活動期間設定為 2025 年 9 月 1 日至 10 月 26 日，預算為 NT$150,000。旅客抵達後七天內的叫車行為會被納入觀察。

### 1.3 三個比較組別

| 組別 | 人數比例 | 內容 |
|---|---:|---|
| Control | 10% | 不提供車資優惠，作為比較基準 |
| Airport 150 | 45% | 第一次機場行程折抵 NT$150 |
| Bundle 100+100 | 45% | 第一次機場行程折抵 NT$100，七天內第二次一般行程再折 NT$100 |

保留 Control 組的原因，是要知道「沒有優惠時，原本就會有多少人叫車」。如果只觀察使用優惠的人，就無法判斷這些人是否本來就會叫車。

---

## 2. 專題目標

本專題設定五個目標：

1. 建立接近真實叫車情境的合成資料。
2. 使用 SQL 找出並處理無效資料。
3. 比較三個組別的機場叫車完成率及七天內再次叫車率。
4. 檢查活動是否超過預算，以及是否影響等車時間與取消率。
5. 根據分析結果提出可以執行的營運建議。

### 2.1 判斷活動是否成功的標準

活動不能只通過一項指標，而要同時符合以下條件：

- 優惠組的機場叫車完成率高於 Control 組。
- 增加的收益高於優惠成本。
- 桃園機場的 P90 接車時間增加不超過 10%。
- 取消率增加不超過 1 個百分點。
- 活動支出沒有超過預算。

P90 接車時間可以白話理解成：100 趟行程中，大約有 90 趟能在這個時間內接到乘客。這比只看平均時間更能反映等很久的旅客。

---

## 3. 資料設計

### 3.1 使用的資料表

| 資料表 | 內容 | 在專題中的用途 |
|---|---|---|
| `raw_users` | 乘客基本資料與 CRM 同意狀態 | 判斷乘客是否可以收到活動訊息 |
| `raw_drivers` | 司機資料 | 確認行程中的司機是否存在 |
| `raw_partner_bookings` | 旅遊合作夥伴的抵台訂位 | 確認旅客抵達時間 |
| `raw_trip_orders` | 叫車訂單 | 取得乘客、司機、車資、上下車地點及訂單狀態 |
| `raw_trip_events` | 行程事件 | 重建 requested、accepted、picked up、completed 等時間 |
| `raw_payments` | 付款及退款紀錄 | 檢查付款是否合理 |
| `raw_campaign_assignments` | 活動分組結果 | 確認乘客屬於 Control 或優惠組 |
| `raw_promo_redemptions` | 優惠使用紀錄 | 計算有效優惠成本 |
| `raw_crm_events` | 訊息發送、開啟及點擊紀錄 | 建立活動漏斗 |
| `raw_supply_hourly` | 每個區域、每小時的需求與司機數 | 檢查供需及服務品質 |

### 3.2 為什麼資料要故意加入錯誤？

實際的叫車資料可能來自行動 App、司機端、付款系統、CRM 及合作夥伴。不同系統不一定會同時送達資料，也可能重複傳送或缺少欄位。

如果專題資料全部都很乾淨，就無法展示資料分析中重要的清理工作。因此我刻意加入以下問題：

- 同一筆訂單或事件被重複傳送。
- 時間格式無法讀取，或事件時間出現在未來。
- 完成時間早於上車時間。
- 上車或下車座標是空值、`0,0`，或不在台灣範圍。
- 訂單找不到對應乘客或司機。
- 車資為負數。
- 付款或退款金額高於車資。
- 優惠使用者和叫車使用者不同。
- Control 組卻出現優惠使用紀錄。
- 資料延遲一天以上才進入系統。

嚴重錯誤會被隔離，不放進主要指標；延遲到達但內容仍合理的資料會保留並加上警告。

---

## 4. 分析推演過程

### 步驟一：先保留原始資料

原始 CSV 先完整讀入 `raw_*` 資料表，不直接修改。這樣可以保留原始紀錄，也方便回頭檢查清理前後的差異。

### 步驟二：統一資料格式

我將文字前後的空白移除、英文狀態改為小寫，並把時間、座標及金額轉成正確格式。不能轉換的內容先變成空值，再交給後續規則判斷。

### 步驟三：處理重複資料

同一個 `trip_id` 如果出現多次，只保留最早收到的一筆；重複的行程事件也採用相同做法。其他資料不直接刪除，而是標示為 `duplicate_excluded`，留下檢查紀錄。

### 步驟四：檢查資料是否合理

我依序檢查事件時間、事件順序、座標、乘客與司機、車資、付款及優惠資格。嚴重錯誤標示為 `hard_invalid`，並放入 `trip_quality_issues`。

### 步驟五：重建每一趟行程

訂單的最後狀態不一定可信，因此我用事件資料重新判斷行程是否完成或取消。例如，一趟完成行程應依序出現：

`requested → accepted → picked_up → completed`

只有通過檢查的行程，才會在 `fct_trip_lifecycle` 中標示為 `valid_for_trip_kpi = true`。

### 步驟六：找出活動分析對象

旅客必須同時符合以下條件：

- 有合作夥伴提供的已確認抵台訂位。
- 同意接收 CRM 訊息。
- 不在風險排除名單。
- 活動分組發生在抵達以前。
- 確實收到活動訊息。
- 分組前 180 天內沒有台灣完成行程。

最後得到 6,824 位符合條件的旅客。

### 步驟七：比較活動結果

我比較每組的：

- 分組人數。
- 收到、開啟及點擊訊息的人數。
- 完成機場行程的人數。
- 七天內再次完成一般行程的人數。
- 有效優惠成本。
- 與 Control 組相比所增加的行程及收益。

### 步驟八：同時檢查營運狀況

活動增加需求後，還要查看司機是否足夠。因此我用每小時、每區域的資料計算接單率、取消率、P90 接車時間及需求與司機數量的差距。

最後再把每日優惠支出累加，和 NT$150,000 預算比較。

---

## 5. 資料清理結果

### 5.1 資料筆數變化

| 階段 | 筆數 | 說明 |
|---|---:|---|
| 原始訂單 | 52,222 | 尚未清理的叫車訂單 |
| 去除重複後 | 51,603 | 每個訂單只保留一筆 |
| 可用行程 | 48,347 | 通過事件、座標、付款及關聯檢查 |
| 活動分析對象 | 6,824 | 同時符合合作夥伴及 CRM 資格的旅客 |

### 5.2 主要無效資料

| 問題 | 受影響行程 | 處理方式 |
|---|---:|---|
| 未來時間或無法解析的時間 | 1,968 | 隔離 |
| 事件步驟時間前後顛倒 | 1,819 | 隔離 |
| 不合理的事件順序 | 1,424 | 隔離 |
| 無效座標 | 513 | 隔離 |
| 付款高於車資 | 304 | 隔離 |
| 負車資 | 178 | 隔離 |
| 找不到乘客 | 104 | 隔離 |
| 找不到司機 | 104 | 隔離 |
| 不合理速度 | 25 | 隔離 |
| 延遲到達的事件 | 4,522 | 保留，但加上警告 |

原始資料算出的完成行程車資為 NT$21,979,956，清理後為 NT$20,505,068。兩者相差約 NT$1,474,888，表示如果直接使用原始資料，會高估實際車資。

---

## 6. 活動分析結果

| 組別 | 分組人數 | 機場完成率 | 七天內再次叫車率 | 有效優惠成本 | 相較 Control 的額外貢獻 |
|---|---:|---:|---:|---:|---:|
| Control | 683 | 16.4% | 2.8% | NT$0 | 比較基準 |
| Airport 150 | 3,053 | 25.1% | 5.0% | NT$112,500 | -NT$42,480 |
| Bundle 100+100 | 3,088 | 23.5% | 8.3% | NT$96,400 | -NT$25,592 |

### 6.1 我如何解讀結果？

`Airport 150` 的機場完成率比 Control 高 8.7 個百分點，估計增加約 265 趟機場完成行程。這代表 NT$150 優惠對旅客第一次機場叫車有明顯幫助。

`Bundle 100+100` 的機場完成率比 Control 高 7.1 個百分點，七天內再次叫車率則達 8.3%，是三組中最高。這表示兩段式優惠比較有機會讓旅客再次使用服務。

但是兩組的額外貢獻都是負數。換句話說，活動確實增加行程，但增加的收益還不足以支付優惠成本。

---

## 7. 服務品質與預算結果

### 7.1 服務品質

桃園機場活動期間的平均每小時 P90 接車時間，相較活動前增加約 15.0%，高於原本設定的 10% 上限。這表示活動帶來需求時，機場的司機供給沒有完全跟上。

西門町的取消率比活動前增加約 1.7 個百分點，也高於 1 個百分點的上限。台北 101 與台北車站則沒有超過限制。

### 7.2 預算

活動預算為 NT$150,000，最後有效優惠支出為 NT$208,900，使用率為 139.3%，超支 NT$58,900。

專題中的每日預算表會比較「目前累積支出」與「照活動天數平均分配後，今天原本應該花多少」。如果支出超前 15%，就顯示警告，讓營運人員可以提早縮小發送人數或調整優惠。

---

## 8. 結論與建議

### 8.1 最後結論

本次活動證明優惠可以增加旅客叫車，但目前不適合直接全面推出。

原因有三個：

1. 兩種方案的額外貢獻都是負數。
2. 活動支出達預算的 139.3%。
3. 桃園機場的接車時間超過設定上限。

### 8.2 改善建議

1. 保留 Control 組，持續確認沒有優惠時的自然叫車率。
2. 優先修改 `Bundle 100+100`，降低第二次叫車的優惠金額，或設定最低車資。
3. 和旅遊合作夥伴討論共同負擔優惠成本。
4. 不一次發送給所有旅客，依照機場每小時的司機數量分批發送。
5. 當接車時間、取消率或預算超標時，自動暫停新的 CRM 發送。

### 8.3 專題限制

- 所有資料都是合成資料，不能代表任何真實叫車平台的營運結果。
- 沒有納入天氣、航班延誤、其他交通工具或競爭平台價格。
- 沒有真實合作夥伴成本及客服案件資料。
- 分析期間只有八週，無法判斷更長期的旅客留存。

---

## 9. SQL 分析章節

本專題使用 DuckDB SQL。以下依實際分析順序，說明每個資料表使用什麼指令、目的為何，以及產出什麼結果。完整 SQL 檔位於專案的 `sql/` 資料夾。

### 9.1 讀取原始 CSV

**使用資料表：** 所有 `raw_*` 資料表  
**主要指令：** `CREATE TABLE`、`SELECT`、`read_csv_auto`

```sql
CREATE OR REPLACE TABLE raw_trip_orders AS
SELECT *
FROM read_csv_auto(
  'data/raw_sample/raw_trip_orders.csv',
  header = true,
  all_varchar = true
);
```

這一步把 CSV 讀成資料表。`all_varchar = true` 代表先全部當文字讀入，避免錯誤日期或金額讓整個匯入失敗。

其他原始表也採用相同方式讀入，例如 `raw_trip_events`、`raw_users`、`raw_payments`。

完整檔案：[`sql/00_load_raw.sql`](../sql/00_load_raw.sql)

### 9.2 統一欄位格式

**輸入表：** `raw_trip_orders`  
**輸出表：** `stg_trip_orders`  
**主要指令：** `trim`、`lower`、`nullif`、`try_cast`

```sql
CREATE OR REPLACE TABLE stg_trip_orders AS
SELECT
  trim(trip_id) AS trip_id,
  trim(user_id) AS user_id,
  nullif(trim(driver_id), '') AS driver_id,
  try_cast(requested_at AS TIMESTAMPTZ) AS requested_at,
  try_cast(pickup_lat AS DOUBLE) AS pickup_lat,
  try_cast(pickup_lng AS DOUBLE) AS pickup_lng,
  try_cast(gross_fare_twd AS DOUBLE) AS gross_fare_twd,
  lower(trim(terminal_status)) AS terminal_status
FROM raw_trip_orders;
```

- `trim`：移除前後空白。
- `lower`：把 Completed、COMPLETED 等文字統一成 `completed`。
- `nullif`：把空字串改成真正的空值。
- `try_cast`：轉換日期或數字；無法轉換時回傳空值，不讓程式中斷。

完整檔案：[`sql/01_standardize_raw_data.sql`](../sql/01_standardize_raw_data.sql)

### 9.3 找出重複訂單

**輸入表：** `stg_trip_orders`  
**輸出表：** `stg_trip_orders_dedup`  
**主要指令：** `row_number`、`partition by`、`case when`

```sql
CREATE OR REPLACE TABLE stg_trip_orders_dedup AS
SELECT
  * EXCLUDE (row_num),
  CASE
    WHEN row_num = 1 THEN 'kept'
    ELSE 'duplicate_excluded'
  END AS record_disposition
FROM (
  SELECT
    *,
    row_number() OVER (
      PARTITION BY trip_id
      ORDER BY ingested_at
    ) AS row_num
  FROM stg_trip_orders
);
```

`PARTITION BY trip_id` 會把相同訂單放在一起，`row_number` 再依收到時間編號。第一筆保留，後續相同訂單標示為重複資料。

完整檔案：[`sql/02_deduplicate.sql`](../sql/02_deduplicate.sql)

### 9.4 檢查座標是否有效

**輸入表：** `stg_trip_orders_dedup`  
**輸出表：** `trip_quality_issues`  
**主要指令：** `WHERE`、`BETWEEN`、`OR`

```sql
SELECT
  trip_id,
  'invalid_coordinates' AS issue_code,
  'hard_invalid' AS severity,
  'quarantined' AS disposition
FROM stg_trip_orders_dedup
WHERE record_disposition = 'kept'
  AND (
    pickup_lat IS NULL
    OR pickup_lng IS NULL
    OR pickup_lat NOT BETWEEN 21.5 AND 25.5
    OR pickup_lng NOT BETWEEN 119.0 AND 122.5
  );
```

這段 SQL 找出空座標或不在台灣合理範圍內的行程，並將它們標示為需要隔離。

### 9.5 檢查車資與付款

**輸入表：** `stg_trip_orders_dedup`、`stg_payments`  
**主要指令：** `JOIN`、`GROUP BY`、`SUM`、`HAVING`

```sql
SELECT
  o.trip_id,
  o.gross_fare_twd,
  sum(p.amount_twd) AS total_payment_twd
FROM stg_trip_orders_dedup o
JOIN stg_payments p
  ON o.trip_id = p.trip_id
WHERE o.record_disposition = 'kept'
GROUP BY o.trip_id, o.gross_fare_twd
HAVING o.gross_fare_twd < 0
   OR sum(p.amount_twd) > o.gross_fare_twd;
```

`JOIN` 用 `trip_id` 把訂單和付款連起來。`GROUP BY` 將同一趟行程的付款合計，`HAVING` 再找出負車資或付款高於車資的異常行程。

完整檔案：[`sql/03_quality_checks.sql`](../sql/03_quality_checks.sql)

### 9.6 重建行程事件順序

**輸入表：** `stg_trip_events_dedup`  
**輸出表：** `int_trip_event_pivot`  
**主要指令：** `min`、`filter`、`group by`

```sql
CREATE OR REPLACE TABLE int_trip_event_pivot AS
SELECT
  trip_id,
  min(event_at) FILTER (WHERE event_type = 'requested') AS requested_at,
  min(event_at) FILTER (WHERE event_type = 'accepted') AS accepted_at,
  min(event_at) FILTER (WHERE event_type = 'picked_up') AS picked_up_at,
  min(event_at) FILTER (WHERE event_type = 'completed') AS completed_at,
  min(event_at) FILTER (WHERE event_type = 'cancelled') AS cancelled_at
FROM stg_trip_events_dedup
WHERE record_disposition = 'kept'
GROUP BY trip_id;
```

原本一趟行程會有多筆事件。這段 SQL 把同一個 `trip_id` 整理成一列，方便檢查時間順序。

例如完成行程需符合：

```sql
requested_at <= accepted_at
AND accepted_at <= picked_up_at
AND picked_up_at <= completed_at
```

完整檔案：[`sql/04_trip_lifecycle.sql`](../sql/04_trip_lifecycle.sql)

### 9.7 只保留可用行程

**輸入表：** `stg_trip_orders_dedup`、`trip_quality_issues`  
**輸出表：** `fct_trip_lifecycle`  
**主要指令：** `WITH`、`LEFT JOIN`、`CASE WHEN`

```sql
WITH hard_invalid AS (
  SELECT DISTINCT trip_id
  FROM trip_quality_issues
  WHERE severity = 'hard_invalid'
)
SELECT
  o.trip_id,
  o.user_id,
  CASE WHEN h.trip_id IS NULL THEN true ELSE false END AS valid_for_trip_kpi,
  CASE WHEN h.trip_id IS NULL THEN 'kept' ELSE 'quarantined' END AS record_disposition
FROM stg_trip_orders_dedup o
LEFT JOIN hard_invalid h
  ON o.trip_id = h.trip_id
WHERE o.record_disposition = 'kept';
```

`LEFT JOIN` 後沒有找到嚴重錯誤的行程，才會標示為可用。這樣後續所有指標都能使用相同的可信行程定義。

### 9.8 找出符合活動資格的旅客

**輸入表：** `stg_campaign_assignments_dedup`、`stg_partner_bookings`、`stg_users`、`stg_crm_events`、`fct_trip_lifecycle`  
**輸出表：** `mart_campaign_cohort`  
**主要指令：** `JOIN`、`EXISTS`、`NOT EXISTS`

```sql
SELECT
  a.user_id,
  a.experiment_arm,
  a.assigned_at,
  b.arrival_at
FROM stg_campaign_assignments_dedup a
JOIN stg_partner_bookings b
  ON a.user_id = b.user_id
JOIN stg_users u
  ON a.user_id = u.user_id
WHERE b.booking_status = 'confirmed'
  AND a.assignment_status = 'eligible'
  AND a.assigned_at <= b.arrival_at
  AND u.crm_opt_in
  AND NOT u.fraud_exclusion
  AND EXISTS (
    SELECT 1
    FROM stg_crm_events crm
    WHERE crm.user_id = a.user_id
      AND crm.crm_event_type = 'sent'
      AND crm.event_at BETWEEN a.assigned_at AND b.arrival_at
  )
  AND NOT EXISTS (
    SELECT 1
    FROM fct_trip_lifecycle f
    WHERE f.user_id = a.user_id
      AND f.valid_for_trip_kpi
      AND f.lifecycle_status = 'completed'
      AND f.requested_at >= a.assigned_at - INTERVAL '180 days'
      AND f.requested_at < a.assigned_at
  );
```

- `EXISTS`：確認旅客真的收到 CRM 訊息。
- `NOT EXISTS`：排除活動前 180 天內已完成台灣行程的旅客。
- 多個 `JOIN`：把活動分組、抵台訂位及乘客資料連在一起。

完整檔案：[`sql/05_campaign_cohort.sql`](../sql/05_campaign_cohort.sql)

### 9.9 計算活動漏斗

**輸入表：** `mart_campaign_cohort`、`stg_crm_events`、`fct_trip_lifecycle`  
**輸出表：** `mart_campaign_funnel`  
**主要指令：** `COUNT`、`FILTER`、`GROUP BY`

```sql
SELECT
  c.experiment_arm,
  count(*) AS assigned_users,
  count(*) FILTER (WHERE crm.crm_sent) AS crm_sent_users,
  count(*) FILTER (WHERE crm.crm_opened) AS crm_opened_users,
  count(*) FILTER (WHERE trips.airport_requested) AS airport_request_users,
  count(*) FILTER (WHERE trips.airport_completed) AS airport_completed_users
FROM mart_campaign_cohort c
LEFT JOIN crm
  ON c.user_id = crm.user_id
LEFT JOIN trips
  ON c.user_id = trips.user_id
GROUP BY c.experiment_arm;
```

這會把每組旅客從「分組」一路算到「收到訊息、開啟、叫車、完成行程」，用來查看哪一個步驟流失最多。

完整檔案：[`sql/06_campaign_funnel.sql`](../sql/06_campaign_funnel.sql)

### 9.10 計算完成率與增量

**輸入表：** `int_campaign_user`  
**輸出表：** `mart_experiment_results`  
**主要指令：** `COUNT`、`SUM`、`AVG`、`NULLIF`、`CROSS JOIN`

先計算每組結果：

```sql
SELECT
  experiment_arm,
  count(*) AS assigned_users,
  sum(completed_airport_trip::INTEGER) AS airport_completed_users,
  sum(completed_repeat_trip::INTEGER) AS repeat_trip_users,
  sum(reward_cost_twd) AS reward_cost_twd,
  avg(net_contribution_twd) AS contribution_per_user_twd
FROM int_campaign_user
GROUP BY experiment_arm;
```

再計算轉換率：

```sql
airport_completed_users::DOUBLE
  / nullif(assigned_users, 0) AS airport_conversion_rate
```

`NULLIF(assigned_users, 0)` 可以避免人數為零時發生除以零錯誤。

優惠組相較 Control 的增量計算方式為：

```sql
treatment_conversion_rate - control_conversion_rate
```

額外完成行程數為：

```sql
(treatment_conversion_rate - control_conversion_rate)
  * treatment_assigned_users
```

完整檔案：[`sql/07_experiment_results.sql`](../sql/07_experiment_results.sql)

### 9.11 計算每區每小時的服務品質

**輸入表：** `fct_trip_lifecycle`、`stg_supply_hourly`  
**輸出表：** `mart_marketplace_hourly`、`mart_marketplace_guardrails`  
**主要指令：** `date_trunc`、`quantile_cont`、`COUNT FILTER`

```sql
SELECT
  date_trunc('hour', requested_at) AS snapshot_hour,
  origin_zone AS service_zone,
  count(*) AS requests,
  count(*) FILTER (WHERE accepted_at IS NOT NULL) AS accepted_requests,
  count(*) FILTER (WHERE lifecycle_status = 'cancelled') AS cancelled_trips,
  quantile_cont(pickup_eta_min, 0.90)
    FILTER (WHERE lifecycle_status = 'completed') AS p90_pickup_eta_min
FROM fct_trip_lifecycle
WHERE valid_for_trip_kpi
GROUP BY 1, 2;
```

- `date_trunc('hour', ...)`：把時間整理成每小時。
- `quantile_cont(..., 0.90)`：計算 P90 接車時間。
- `COUNT FILTER`：在同一個查詢中分別計算接單及取消數。

活動期間與活動前的變化為：

```sql
campaign_avg_p90_pickup_eta_min
  / nullif(baseline_avg_p90_pickup_eta_min, 0) - 1
  AS p90_eta_pct_change_vs_baseline
```

完整檔案：[`sql/08_marketplace_health.sql`](../sql/08_marketplace_health.sql)

### 9.12 計算每日預算

**輸入表：** `fct_valid_redemptions`、`mart_campaign_cohort`  
**輸出表：** `mart_campaign_budget_daily`  
**主要指令：** `SUM OVER`、`ROW_NUMBER OVER`、`CASE WHEN`

```sql
SELECT
  campaign_date,
  daily_spend_twd,
  sum(daily_spend_twd) OVER (
    ORDER BY campaign_date
  ) AS cumulative_spend_twd,
  150000 AS budget_twd,
  CASE
    WHEN cumulative_spend_twd > 150000
      THEN 'alert_over_budget'
    WHEN cumulative_spend_twd > planned_cumulative_spend_twd * 1.15
      THEN 'alert_over_pace'
    ELSE 'on_track'
  END AS budget_status
FROM daily_spend;
```

`SUM OVER` 是累積加總，可以每天查看目前已花多少錢。`CASE WHEN` 再把結果分成正常、花太快及超過總預算。

完整檔案：[`sql/09_quality_and_reconciliation.sql`](../sql/09_quality_and_reconciliation.sql)

### 9.13 檢查清理前後差異

**輸入表：** `raw_trip_orders`、`fct_trip_lifecycle`  
**輸出表：** `mart_raw_vs_clean_kpi`

```sql
SELECT
  'trip_rows' AS metric,
  (SELECT count(*) FROM raw_trip_orders) AS raw_value,
  (
    SELECT count(*)
    FROM fct_trip_lifecycle
    WHERE valid_for_trip_kpi
  ) AS clean_value;
```

同樣的方法也用來比較完成率、取消率及完成行程車資。這一步可以證明資料清理確實改變了分析結果，而不是只做格式整理。

---

## 10. 如何重跑本專題

```powershell
python -m pip install -r requirements.txt
npm install
python src/generate_synthetic_data.py --mode sample
python src/run_pipeline.py
node src/build_dashboard.mjs
python src/build_report.py
```

執行順序為：產生合成資料 → 執行 SQL → 輸出分析資料表 → 建立 Dashboard → 建立報告。

---

## 11. 我從專題學到什麼？

這份專題讓我理解，資料分析不是把資料放進圖表就結束。分析以前要先確認資料是否可信；活動訂單增加後，還要同時檢查成本、預算及服務品質。

SQL 在這個專題中不只是計算工具，也負責記錄每一步規則。只要重新執行相同 SQL，就能得到相同的清理方式與指標，方便別人檢查分析是否合理。

最重要的學習是：活動有效不代表適合全面推出。完整的營運判斷需要同時回答「有沒有效」、「有沒有賺錢」、「現場接不接得住」以及「能不能持續執行」。
