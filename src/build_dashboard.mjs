import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const summary = JSON.parse(await fs.readFile(path.join(root, "outputs", "summary.json"), "utf8"));
const config = JSON.parse(await fs.readFile(path.join(root, "config.json"), "utf8"));
const campaign = config.campaign;
const dashboardDir = path.join(root, "dashboard");
const previewDir = path.join(dashboardDir, "screenshots");
await fs.mkdir(previewDir, { recursive: true });
await fs.mkdir(path.join(root, "tmp"), { recursive: true });

const C = {
  navy: "#102A43",
  blue: "#0B7285",
  teal: "#12B886",
  amber: "#F08C00",
  red: "#C92A2A",
  paleBlue: "#E7F5FF",
  paleTeal: "#E6FCF5",
  paleAmber: "#FFF3BF",
  paleRed: "#FFF5F5",
  gray: "#F1F3F5",
  border: "#CED4DA",
  ink: "#212529",
};

function asNumber(value) {
  if (value === null || value === undefined || value === "") return null;
  const converted = Number(value);
  return Number.isFinite(converted) ? converted : value;
}

function setTitle(sheet, title, subtitle) {
  sheet.getRange("A1:P1").merge();
  sheet.getRange("A1").values = [[title]];
  sheet.getRange("A1:P1").format = {
    fill: C.navy,
    font: { bold: true, color: "#FFFFFF", size: 18 },
    horizontalAlignment: "left",
    verticalAlignment: "center",
  };
  sheet.getRange("A1:P1").format.rowHeight = 30;
  sheet.getRange("A2:P2").merge();
  sheet.getRange("A2").values = [[subtitle]];
  sheet.getRange("A2:P2").format = {
    fill: C.navy,
    font: { color: "#D9E2EC", italic: true, size: 10 },
    horizontalAlignment: "left",
    verticalAlignment: "center",
  };
  sheet.getRange("A2:P2").format.rowHeight = 22;
}

function tableHeader(sheet, range) {
  sheet.getRange(range).format = {
    fill: C.blue,
    font: { bold: true, color: "#FFFFFF" },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    wrapText: true,
    borders: { preset: "outside", style: "thin", color: C.border },
  };
}

function tableBody(sheet, range) {
  sheet.getRange(range).format = {
    borders: { preset: "inside", style: "thin", color: "#E9ECEF" },
    verticalAlignment: "center",
  };
}

function card(sheet, titleCell, valueCell, title, formula, format, fill) {
  sheet.getRange(titleCell).merge();
  sheet.getRange(valueCell).merge();
  sheet.getRange(titleCell).values = [[title]];
  sheet.getRange(titleCell).format = {
    fill,
    font: { bold: true, color: C.ink, size: 10 },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    wrapText: true,
    borders: { preset: "outside", style: "thin", color: C.border },
  };
  sheet.getRange(valueCell).formulas = [[formula]];
  sheet.getRange(valueCell).format = {
    fill,
    font: { bold: true, color: C.navy, size: 18 },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    numberFormat: format,
    borders: { preset: "outside", style: "thin", color: C.border },
  };
}

const wb = Workbook.create();
const dashboard = wb.worksheets.add("Dashboard");
const experiment = wb.worksheets.add("Experiment");
const funnel = wb.worksheets.add("Funnel");
const marketplace = wb.worksheets.add("Marketplace");
const budget = wb.worksheets.add("Budget");
const quality = wb.worksheets.add("Data Quality");
const notes = wb.worksheets.add("Notes");
for (const sheet of [dashboard, experiment, funnel, marketplace, budget, quality, notes]) sheet.showGridLines = false;

// Experiment sheet
setTitle(experiment, "Campaign Experiment", "Intent-to-treat results. Currency in TWD; conversion and repeat metrics use assigned users as denominator.");
const expHeaders = ["Experiment arm", "Assigned users", "Airport completed", "D7 repeat", "Airport conversion", "D7 repeat rate", "Reward cost", "Incremental conversion", "95% CI low", "95% CI high", "Incremental trips", "Incremental contribution", "Cost / incremental trip", "Decision"];
const expRows = summary.mart_experiment_results.map((row) => [
  row.experiment_arm, asNumber(row.assigned_users), asNumber(row.airport_completed_users), asNumber(row.repeat_trip_users),
  asNumber(row.airport_conversion_rate), asNumber(row.d7_repeat_rate), asNumber(row.reward_cost_twd),
  asNumber(row.incremental_conversion_rate), asNumber(row.incremental_conversion_ci_low), asNumber(row.incremental_conversion_ci_high),
  asNumber(row.incremental_completed_trips), asNumber(row.incremental_contribution_twd), asNumber(row.cost_per_incremental_trip_twd), row.experiment_decision,
]);
experiment.getRange("A4:N4").values = [expHeaders];
experiment.getRange(`A5:N${4 + expRows.length}`).values = expRows;
tableHeader(experiment, "A4:N4");
tableBody(experiment, `A5:N${4 + expRows.length}`);
experiment.getRange(`B5:D${4 + expRows.length}`).format.numberFormat = "#,##0";
experiment.getRange(`E5:F${4 + expRows.length}`).format.numberFormat = "0.0%";
experiment.getRange(`G5:G${4 + expRows.length}`).format.numberFormat = '"NT$"#,##0';
experiment.getRange(`H5:J${4 + expRows.length}`).format.numberFormat = "0.0%";
experiment.getRange(`K5:K${4 + expRows.length}`).format.numberFormat = "#,##0.0";
experiment.getRange(`L5:M${4 + expRows.length}`).format.numberFormat = '"NT$"#,##0';
experiment.getRange(`N5:N${4 + expRows.length}`).conditionalFormats.add("containsText", { text: "candidate", format: { fill: C.paleTeal, font: { color: C.teal, bold: true } } });
experiment.getRange(`N5:N${4 + expRows.length}`).conditionalFormats.add("containsText", { text: "hold", format: { fill: C.paleAmber, font: { color: C.amber, bold: true } } });
experiment.getRange("A4:N7").format.autofitColumns();
experiment.getRange("A4:N7").format.autofitRows();
experiment.getRange("N4:N7").format.columnWidth = 24;
experiment.freezePanes.freezeRows(4);

// Funnel sheet
setTitle(funnel, "Campaign Funnel", "Only users in the cleaned, CRM-consented campaign cohort are included.");
const funnelHeaders = ["Experiment arm", "Assigned", "CRM sent", "CRM opened", "CRM clicked", "Airport requested", "Airport completed", "D7 repeat", "Reward cost (TWD)"];
const funnelRows = summary.mart_campaign_funnel.map((row) => [
  row.experiment_arm, asNumber(row.assigned_users), asNumber(row.crm_sent_users), asNumber(row.crm_opened_users), asNumber(row.crm_clicked_users), asNumber(row.airport_request_users), asNumber(row.airport_completed_users), asNumber(row.repeat_trip_users), asNumber(row.reward_cost_twd),
]);
funnel.getRange("A4:I4").values = [funnelHeaders];
funnel.getRange(`A5:I${4 + funnelRows.length}`).values = funnelRows;
tableHeader(funnel, "A4:I4");
tableBody(funnel, `A5:I${4 + funnelRows.length}`);
funnel.getRange(`B5:H${4 + funnelRows.length}`).format.numberFormat = "#,##0";
funnel.getRange(`I5:I${4 + funnelRows.length}`).format.numberFormat = '"NT$"#,##0';
funnel.getRange("A4:I7").format.autofitColumns();

// Marketplace sheet
setTitle(marketplace, "Marketplace Health", "Zone-level guardrails. P90 of P90 ETA is the 90th percentile of hourly P90 pickup time.");
const marketHeaders = ["Service zone", "Zone-hours", "Acceptance rate", "Cancellation rate", "P90 pickup ETA (min)", "Avg demand-supply gap", "Intervention hours", "Observed metric hours", "Source-only hours"];
const marketRows = summary.mart_marketplace_summary.map((row) => [
  row.service_zone, asNumber(row.zone_hours), asNumber(row.acceptance_rate), asNumber(row.cancellation_rate), asNumber(row.p90_of_p90_pickup_eta_min), asNumber(row.avg_demand_supply_gap), asNumber(row.intervention_hours), asNumber(row.observed_metric_hours), asNumber(row.source_only_hours),
]);
marketplace.getRange("A4:I4").values = [marketHeaders];
marketplace.getRange(`A5:I${4 + marketRows.length}`).values = marketRows;
tableHeader(marketplace, "A4:I4");
tableBody(marketplace, `A5:I${4 + marketRows.length}`);
marketplace.getRange(`B5:B${4 + marketRows.length}`).format.numberFormat = "#,##0";
marketplace.getRange(`C5:D${4 + marketRows.length}`).format.numberFormat = "0.0%";
marketplace.getRange(`E5:I${4 + marketRows.length}`).format.numberFormat = "#,##0.0";
marketplace.getRange(`D5:D${4 + marketRows.length}`).conditionalFormats.add("cellIs", { operator: "greaterThan", formula: 0.1, format: { fill: C.paleRed, font: { color: C.red, bold: true } } });
marketplace.getRange("A4:I8").format.autofitColumns();

const guardrailHeaders = ["Service zone", "Baseline P90 ETA", "Campaign P90 ETA", "ETA vs baseline", "Cancellation change", "Guardrail status"];
const guardrailRows = summary.mart_marketplace_guardrails.map((row) => [
  row.service_zone, asNumber(row.baseline_avg_p90_pickup_eta_min), asNumber(row.campaign_avg_p90_pickup_eta_min), asNumber(row.p90_eta_pct_change_vs_baseline), asNumber(row.cancellation_rate_pp_change_vs_baseline), row.guardrail_status,
]);
marketplace.getRange("A12:F12").values = [guardrailHeaders];
marketplace.getRange(`A13:F${12 + guardrailRows.length}`).values = guardrailRows;
tableHeader(marketplace, "A12:F12");
tableBody(marketplace, `A13:F${12 + guardrailRows.length}`);
marketplace.getRange(`B13:C${12 + guardrailRows.length}`).format.numberFormat = "0.0";
marketplace.getRange(`D13:E${12 + guardrailRows.length}`).format.numberFormat = "0.0%";
marketplace.getRange(`F13:F${12 + guardrailRows.length}`).conditionalFormats.add("containsText", { text: "breach", format: { fill: C.paleRed, font: { color: C.red, bold: true } } });
marketplace.getRange(`F13:F${12 + guardrailRows.length}`).conditionalFormats.add("containsText", { text: "pass", format: { fill: C.paleTeal, font: { color: C.teal, bold: true } } });
marketplace.getRange("A12:F18").format.autofitColumns();

// Budget sheet
setTitle(budget, "Campaign Budget", "Valid reward spend is compared with the pro-rata budget plan. Alert threshold: 15% over plan.");
const budgetHeaders = ["Date", "Daily spend (TWD)", "Cumulative spend", "Planned cumulative", "Budget", "Spend rate", "Status"];
const budgetRows = summary.mart_campaign_budget_daily.map((row) => [
  row.campaign_date, asNumber(row.daily_spend_twd), asNumber(row.cumulative_spend_twd), asNumber(row.planned_cumulative_spend_twd), asNumber(row.budget_twd), asNumber(row.budget_spend_rate), row.budget_status,
]);
const finalBudgetStatus = budgetRows.at(-1)[6];
budget.getRange("A4:G4").values = [budgetHeaders];
budget.getRange(`A5:G${4 + budgetRows.length}`).values = budgetRows;
tableHeader(budget, "A4:G4");
tableBody(budget, `A5:G${4 + budgetRows.length}`);
budget.getRange(`B5:E${4 + budgetRows.length}`).format.numberFormat = '"NT$"#,##0';
budget.getRange(`F5:F${4 + budgetRows.length}`).format.numberFormat = "0.0%";
budget.getRange(`G5:G${4 + budgetRows.length}`).conditionalFormats.add("containsText", { text: "alert", format: { fill: C.paleRed, font: { color: C.red, bold: true } } });
budget.getRange("A4:G8").format.autofitColumns();
budget.getRange("G4:G60").format.columnWidth = 20;
budget.freezePanes.freezeRows(4);

// Data-quality sheet
setTitle(quality, "Data Quality and Reconciliation", "Hard-invalid trips are quarantined; late events are retained with warning after sequence validation.");
const qualityHeaders = ["Issue", "Severity", "Disposition", "Affected records", "Affected trips"];
const qualityRows = summary.mart_data_quality_report.map((row) => [row.issue_code, row.severity, row.disposition, asNumber(row.affected_trip_records), asNumber(row.affected_trips)]);
quality.getRange("A4:E4").values = [qualityHeaders];
quality.getRange(`A5:E${4 + qualityRows.length}`).values = qualityRows;
tableHeader(quality, "A4:E4");
tableBody(quality, `A5:E${4 + qualityRows.length}`);
quality.getRange(`D5:E${4 + qualityRows.length}`).format.numberFormat = "#,##0";
quality.getRange(`B5:B${4 + qualityRows.length}`).conditionalFormats.add("containsText", { text: "hard", format: { fill: C.paleRed, font: { color: C.red, bold: true } } });
quality.getRange("A16:D16").values = [["KPI", "Raw value", "Clean value", "Difference"]];
const reconcileRows = summary.mart_raw_vs_clean_kpi.map((row) => [row.metric, asNumber(row.raw_value), asNumber(row.clean_value), null]);
quality.getRange(`A17:D${16 + reconcileRows.length}`).values = reconcileRows;
for (let row = 17; row < 17 + reconcileRows.length; row += 1) quality.getRange(`D${row}`).formulas = [[`=C${row}-B${row}`]];
tableHeader(quality, "A16:D16");
tableBody(quality, `A17:D${16 + reconcileRows.length}`);
quality.getRange("B17:D17").format.numberFormat = "#,##0";
quality.getRange("B18:D19").format.numberFormat = "0.0%";
quality.getRange("B20:D20").format.numberFormat = '"NT$"#,##0';
quality.getRange("A4:E13").format.autofitColumns();

// Notes sheet
setTitle(notes, "Method and Decision Notes", "A transparent record of assumptions, calculation rules, and practical operating actions.");
const noteRows = [
  ["Project status", "Independent educational portfolio; all rider, driver, and trip data is synthetic."],
  ["Experiment method", "Intent-to-treat: each eligible allocated user remains in their assigned group."],
  ["Campaign decision", "Do not fully scale either current reward. Redesign Bundle with partner funding or lower second-trip subsidy; retain a Control holdout."],
  ["Marketplace action", "Prioritize airport peak periods: add supply and pause additional CRM sends when ETA or cancellation guardrails breach."],
  ["Quality handling", "Repair duplicates/time formatting; quarantine impossible sequences, invalid coordinates, or financial integrity failures; retain late arrivals as warnings."],
  ["Market context source", "https://stat.taiwan.net.tw/statistics?action=month"],
  ["Airport context source", "https://www.taoyuan-airport.com/api/imagecrop/fileid/F4EC574E-463D-F111-BC24-0050569094FE"],
  ["Full definitions", "See docs/metric_definitions.md and docs/cleaning_rules.md in the repository."],
];
notes.getRange("A4:B4").values = [["Topic", "Detail"]];
notes.getRange(`A5:B${4 + noteRows.length}`).values = noteRows;
tableHeader(notes, "A4:B4");
tableBody(notes, `A5:B${4 + noteRows.length}`);
notes.getRange(`B5:B${4 + noteRows.length}`).format.wrapText = true;
notes.getRange("A4:B12").format.autofitColumns();
notes.getRange("B5:B12").format.columnWidth = 82;
notes.getRange("A5:B12").format.autofitRows();

// Dashboard formulas and presentation.
setTitle(dashboard, "TPE Arrival to Local | Operations Dashboard", `Synthetic portfolio case | ${campaign.start_date} to ${campaign.end_date} | Decision: redesign rewards before scaling`);
card(dashboard, "A4:C4", "A5:C6", "Airport 150 incremental conversion", "='Experiment'!H6", "0.0%", C.paleBlue);
card(dashboard, "D4:F4", "D5:F6", "Bundle D7 repeat rate", "='Experiment'!F7", "0.0%", C.paleTeal);
card(dashboard, "G4:I4", "G5:I6", "Airport 150 incremental contribution", "='Experiment'!L6", '"NT$"#,##0;[Red]-"NT$"#,##0', C.paleAmber);
card(dashboard, "J4:L4", "J5:L6", "Valid trips after cleaning", "='Data Quality'!C17", "#,##0", C.gray);
card(dashboard, "M4:O4", "M5:O6", `Campaign budget: ${finalBudgetStatus}`, `='Budget'!F${4 + budgetRows.length}`, "0.0%", finalBudgetStatus === "on_track" ? C.paleTeal : C.paleRed);
dashboard.getRange("A8:P8").merge();
dashboard.getRange("A8").values = [["Recommendation: keep a Control holdout; redesign the Bundle with partner co-funding or a lower second-trip reward. Do not scale during airport peak hours until pickup ETA and cancellation guardrails improve."]];
dashboard.getRange("A8:P8").format = { fill: C.paleAmber, font: { bold: true, color: C.ink }, wrapText: true, verticalAlignment: "center", borders: { preset: "outside", style: "thin", color: C.border } };
dashboard.getRange("A8:P8").format.rowHeight = 32;

dashboard.getRange("A11:C11").values = [["Experiment arm", "Airport conversion", "D7 repeat rate"]];
dashboard.getRange("A12:C14").formulas = [
  ["='Experiment'!A5", "='Experiment'!E5", "='Experiment'!F5"],
  ["='Experiment'!A6", "='Experiment'!E6", "='Experiment'!F6"],
  ["='Experiment'!A7", "='Experiment'!E7", "='Experiment'!F7"],
];
tableHeader(dashboard, "A11:C11");
dashboard.getRange("B12:C14").format.numberFormat = "0.0%";
const conversionChart = dashboard.charts.add("bar", dashboard.getRange("A11:C14"));
conversionChart.title = "Airport conversion vs. D7 repeat rate";
conversionChart.hasLegend = true;
conversionChart.yAxis = { numberFormatCode: "0%", min: 0, max: 0.30 };
conversionChart.setPosition("E10", "L23");

dashboard.getRange("A25:B25").values = [["Service zone", "P90 pickup ETA (min)"]];
dashboard.getRange("A26:B29").formulas = [
  ["='Marketplace'!A5", "='Marketplace'!E5"],
  ["='Marketplace'!A6", "='Marketplace'!E6"],
  ["='Marketplace'!A7", "='Marketplace'!E7"],
  ["='Marketplace'!A8", "='Marketplace'!E8"],
];
tableHeader(dashboard, "A25:B25");
dashboard.getRange("B26:B29").format.numberFormat = "0.0";
const etaChart = dashboard.charts.add("bar", dashboard.getRange("A25:B29"));
etaChart.title = "Pickup reliability by zone";
etaChart.hasLegend = false;
etaChart.yAxis = { numberFormatCode: "0.0", min: 0, max: 25 };
etaChart.setPosition("E25", "L38");

dashboard.getRange("M11:N11").values = [["Data-quality issue", "Affected trips"]];
for (let i = 0; i < Math.min(7, qualityRows.length); i += 1) {
  const sourceRow = 5 + i;
  const destinationRow = 12 + i;
  dashboard.getRange(`M${destinationRow}:N${destinationRow}`).formulas = [[`='Data Quality'!A${sourceRow}`, `='Data Quality'!E${sourceRow}`]];
}
tableHeader(dashboard, "M11:N11");
dashboard.getRange("N12:N18").format.numberFormat = "#,##0";
const qualityChart = dashboard.charts.add("bar", dashboard.getRange("M11:N18"));
qualityChart.title = "Largest quality issues";
qualityChart.hasLegend = false;
qualityChart.setPosition("M20", "P38");

dashboard.getRange("A40:P41").merge();
dashboard.getRange("A40").values = [["Sources: Synthetic operations data generated by this repository; Taiwan Tourism Administration and Taoyuan Airport public context links are recorded in the Notes tab and docs/sources.md. Currency: TWD."]];
dashboard.getRange("A40:P41").format = { fill: C.gray, font: { color: "#495057", size: 9 }, wrapText: true, verticalAlignment: "center" };

dashboard.getRange("A1:P41").format.font = { name: "Aptos", color: C.ink };
dashboard.getRange("A1:P1").format.font = { name: "Aptos Display", bold: true, color: "#FFFFFF", size: 18 };
dashboard.getRange("A2:P2").format.font = { name: "Aptos", color: "#D9E2EC", italic: true, size: 10 };
dashboard.getRange("A1:P41").format.columnWidth = 13;
dashboard.getRange("A1:A41").format.columnWidth = 20;
dashboard.getRange("M1:M41").format.columnWidth = 28;
dashboard.getRange("N1:N41").format.columnWidth = 16;

const inspection = await wb.inspect({ kind: "table", range: "Dashboard!A1:P18", include: "values,formulas", tableMaxRows: 18, tableMaxCols: 16 });
const formulaErrors = await wb.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 100 }, summary: "formula errors" });
console.log(inspection.ndjson);
console.log(formulaErrors.ndjson);
const preview = await wb.render({ sheetName: "Dashboard", range: "A1:P41", scale: 1.3, format: "png" });
await fs.writeFile(path.join(previewDir, "dashboard_preview.png"), new Uint8Array(await preview.arrayBuffer()));
for (const sheetName of ["Experiment", "Funnel", "Marketplace", "Budget", "Data Quality", "Notes"]) {
  const sheetPreview = await wb.render({ sheetName, autoCrop: "all", scale: 1, format: "png" });
  await fs.writeFile(path.join(root, "tmp", `dashboard_${sheetName.toLowerCase().replaceAll(" ", "_")}.png`), new Uint8Array(await sheetPreview.arrayBuffer()));
}
const xlsx = await SpreadsheetFile.exportXlsx(wb);
await xlsx.save(path.join(dashboardDir, "airport_campaign_dashboard.xlsx"));
