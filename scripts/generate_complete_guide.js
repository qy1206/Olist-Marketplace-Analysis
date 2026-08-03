const fs = require("fs");
const path = require("path");
const {
  Document,
  Packer,
  Paragraph,
  TextRun,
  Table,
  TableRow,
  TableCell,
  Header,
  Footer,
  AlignmentType,
  LevelFormat,
  TableOfContents,
  HeadingLevel,
  BorderStyle,
  WidthType,
  ShadingType,
  VerticalAlign,
  PageNumber,
  PageBreak,
  TabStopType,
  TabStopPosition,
  ExternalHyperlink,
} = require("docx");

const OUTPUT = path.resolve(__dirname, "../docs/Olist_Marketplace_Analytics_Complete_Guide_Bilingual.docx");
const PAGE_WIDTH = 11906;
const PAGE_HEIGHT = 16838;
const MARGIN = 1080;
const CONTENT_WIDTH = PAGE_WIDTH - MARGIN * 2;
const COLORS = {
  navy: "17365D",
  blue: "2F75B5",
  teal: "008C8C",
  green: "2E7D32",
  lightBlue: "DDEBF7",
  lightTeal: "DDEFEF",
  lightGreen: "E2F0D9",
  lightYellow: "FFF2CC",
  lightRed: "FCE4D6",
  gray: "F2F2F2",
  midGray: "D9E1F2",
  darkGray: "595959",
  white: "FFFFFF",
  black: "000000",
};

const thinBorder = { style: BorderStyle.SINGLE, size: 1, color: "B7C9DA" };
const borders = { top: thinBorder, bottom: thinBorder, left: thinBorder, right: thinBorder };
const children = [];

function run(text, options = {}) {
  return new TextRun({ text: String(text), font: options.font || "Microsoft YaHei", size: options.size || 21, ...options });
}

function paragraph(text = "", options = {}) {
  const runs = options.runs || [run(text, options.run || {})];
  return new Paragraph({
    children: runs,
    alignment: options.alignment,
    spacing: options.spacing || { after: 100, line: 300 },
    indent: options.indent,
    keepNext: options.keepNext,
    pageBreakBefore: options.pageBreakBefore,
    border: options.border,
    shading: options.shading,
    tabStops: options.tabStops,
  });
}

function addP(text, options = {}) { children.push(paragraph(text, options)); }
function addBlank() { children.push(new Paragraph({ spacing: { after: 80 } })); }
function addPageBreak() { children.push(new Paragraph({ children: [new PageBreak()] })); }

function addHeading(text, level = 1) {
  const heading = level === 1 ? HeadingLevel.HEADING_1 : level === 2 ? HeadingLevel.HEADING_2 : HeadingLevel.HEADING_3;
  children.push(new Paragraph({ heading, children: [run(text, { bold: true })], spacing: { before: level === 1 ? 260 : 180, after: 120 }, keepNext: true }));
}

let listId = 0;
function addBullet(text, level = 0) {
  children.push(new Paragraph({
    numbering: { reference: "bullets", level },
    children: [run(text)],
    spacing: { after: 70, line: 280 },
  }));
}

function addNumber(text) {
  children.push(new Paragraph({
    numbering: { reference: `numbers-${listId}`, level: 0 },
    children: [run(text)],
    spacing: { after: 80, line: 280 },
  }));
}

function restartNumbers() { listId += 1; }

function addCallout(title, body, color = COLORS.lightYellow) {
  const cell = new TableCell({
    borders,
    width: { size: CONTENT_WIDTH, type: WidthType.DXA },
    shading: { fill: color, type: ShadingType.CLEAR },
    margins: { top: 140, bottom: 140, left: 180, right: 180 },
    children: [
      new Paragraph({ children: [run(title, { bold: true, color: COLORS.navy, size: 22 })], spacing: { after: 70 } }),
      paragraph(body),
    ],
  });
  children.push(new Table({ width: { size: CONTENT_WIDTH, type: WidthType.DXA }, columnWidths: [CONTENT_WIDTH], rows: [new TableRow({ children: [cell] })] }));
  addBlank();
}

function cellContent(value, bold = false, color = COLORS.black) {
  const values = Array.isArray(value) ? value : [value];
  return values.map((item) => paragraph(item, { run: { bold, color, size: 19 }, spacing: { after: 30, line: 260 } }));
}

function addTable(headers, rows, widths, options = {}) {
  if (widths.reduce((a, b) => a + b, 0) !== CONTENT_WIDTH) throw new Error(`Table widths must sum to ${CONTENT_WIDTH}`);
  const tableRows = [];
  tableRows.push(new TableRow({
    tableHeader: true,
    children: headers.map((header, index) => new TableCell({
      borders,
      width: { size: widths[index], type: WidthType.DXA },
      shading: { fill: options.headerFill || COLORS.navy, type: ShadingType.CLEAR },
      verticalAlign: VerticalAlign.CENTER,
      margins: { top: 100, bottom: 100, left: 100, right: 100 },
      children: cellContent(header, true, COLORS.white),
    })),
  }));
  rows.forEach((row, rowIndex) => {
    tableRows.push(new TableRow({
      cantSplit: true,
      children: row.map((value, index) => new TableCell({
        borders,
        width: { size: widths[index], type: WidthType.DXA },
        shading: rowIndex % 2 === 1 ? { fill: options.altFill || "F8FBFD", type: ShadingType.CLEAR } : undefined,
        verticalAlign: VerticalAlign.TOP,
        margins: { top: 85, bottom: 85, left: 100, right: 100 },
        children: cellContent(value, false, COLORS.black),
      })),
    }));
  });
  children.push(new Table({ width: { size: CONTENT_WIDTH, type: WidthType.DXA }, columnWidths: widths, rows: tableRows }));
  addBlank();
}

function addCode(code) {
  const lines = String(code).trim().split("\n");
  const cell = new TableCell({
    borders,
    width: { size: CONTENT_WIDTH, type: WidthType.DXA },
    shading: { fill: "F4F6F8", type: ShadingType.CLEAR },
    margins: { top: 120, bottom: 120, left: 150, right: 150 },
    children: lines.map((line) => new Paragraph({ children: [run(line, { font: "Consolas", size: 18, color: "1F1F1F" })], spacing: { after: 15, line: 240 } })),
  });
  children.push(new Table({ width: { size: CONTENT_WIDTH, type: WidthType.DXA }, columnWidths: [CONTENT_WIDTH], rows: [new TableRow({ children: [cell] })] }));
  addBlank();
}

function addKeyValue(label, value) {
  addP("", { runs: [run(`${label}: `, { bold: true, color: COLORS.navy }), run(value)] });
}

const rawTables = [
  ["orders", "99,441", "一行一个订单 / one order", "状态、下单、批准、发货、实际与预计送达日期"],
  ["order_items", "112,650", "一行一个订单商品序号 / order-item", "商品、卖家、售价、运费；同一订单可有多行"],
  ["order_payments", "103,886", "一行一个付款序号 / payment sequence", "付款方式、分期数、付款金额；同一订单可多次付款"],
  ["order_reviews", "99,224", "评论记录 / review row", "评分、评论与时间；review_id 不是可靠唯一键"],
  ["customers", "99,441", "一行一个 customer_id", "customer_unique_id、城市、州"],
  ["products", "32,951", "一行一个 product_id", "葡萄牙文类别、尺寸、重量、照片数"],
  ["sellers", "3,095", "一行一个 seller_id", "卖家城市与州"],
  ["product_category_translation", "71", "一行一个葡语类别", "把葡语商品类别翻译成英文"],
  ["geolocation", "1,000,163", "地理坐标记录；ZIP prefix 非唯一", "经纬度、城市、州；V1 dashboard 未直接使用"],
  ["marketing_qualified_leads", "8,000", "一行一个 mql_id", "首次接触日期、landing page、来源 origin"],
  ["closed_deals", "842", "一行一个已成交 mql_id", "seller_id、won_date、销售人员、业务类型与细分"],
];

const sqlFiles = [
  ["1", "00_source_profiling/01_table_inventory.sql", "盘点 BigQuery raw dataset 的 11 张表、行数与大小", "raw metadata → inventory", "__TABLES__, ORDER BY"],
  ["2", "00_source_profiling/02_source_quality_and_keys.sql", "检查 orders 粒度、NULL、order-item 重复、review 重复风险", "raw tables → quality evidence", "COUNT, DISTINCT, GROUP BY, HAVING, subquery"],
  ["3", "01_staging/01_stg_orders.sql", "标准化订单状态，并产生 purchase_date / purchase_month", "raw.orders → stg_orders", "LOWER, TRIM, DATE, DATE_TRUNC, VIEW"],
  ["4", "01_staging/02_stg_order_items.sql", "把 price 和 freight 转为 NUMERIC，计算 item_total_value", "raw.order_items → stg_order_items", "CAST, AND, non-negative checks"],
  ["5", "01_staging/03_stg_order_payments.sql", "清理付款方式；把 2 行信用卡 0 分期纠正为 1，并保留 flag", "raw.order_payments → stg_order_payments", "CASE, COUNTIF, audit flag"],
  ["6", "01_staging/04_stg_marketing_funnel.sql", "LEFT JOIN 8,000 leads 与 842 deals，保留未成交 lead", "MQL + closed_deals → lead-level funnel", "LEFT JOIN, COALESCE, NULLIF, DATE_DIFF"],
  ["7", "02_marts/01_mart_orders.sql", "先把商品和付款聚合到 order_id，再构建一行一订单的主 mart", "staging + customers → mart_orders", "WITH/CTE, STRING_AGG, pre-aggregation"],
  ["8", "02_marts/02_mart_order_seller.sql", "构建一行一个 order_id × seller_id 的卖家分析 mart", "items + orders + sellers + products + reviews", "multi-table JOIN, review pre-aggregation"],
  ["9", "02_marts/03_mart_marketing_funnel.sql", "按 contact_month × origin 汇总 leads 与 wins", "lead staging → acquisition mart", "GROUP BY, COUNTIF, SAFE_DIVIDE"],
  ["10", "02_marts/04_mart_seller_lifecycle.sql", "把成交 lead 接到 won_date 后的卖家订单，判断是否 activated", "funnel + order-seller mart → lifecycle mart", "date condition JOIN, MIN, activation CASE"],
  ["11", "03_analysis/01_acquisition_channel_quality.sql", "比较各渠道从 lead 到成交、激活、GMV、评价、履约的质量", "funnel mart + lifecycle mart → channel analysis", "multiple CTEs, business ratios"],
  ["12", "03_analysis/02_seller_activation_performance.sql", "给已激活卖家做整体与渠道内排名", "lifecycle mart → seller ranking", "RANK() OVER, PARTITION BY"],
  ["13", "03_analysis/03_delivery_review_analysis.sql", "比较准时与不同延迟区间的评分；只说明关联，不宣称因果", "mart_orders + reviews → delivery/review buckets", "CASE buckets, conditional rates"],
  ["14", "04_quality_checks/01_join_fanout_reconciliation.sql", "核对订单行数、商品金额、运费、付款金额没有因 JOIN 被放大", "staging totals ↔ mart totals", "UNION ALL, reconciliation, PASS/FAIL"],
  ["15", "04_quality_checks/02_final_kpi_validation.sql", "核对 raw、marts、analysis 的六个最终 KPI", "source truth ↔ final model", "nested queries, final controls"],
];

const measures = [
  ["Total Orders", "DISTINCTCOUNT(FactOrders[order_id])", "唯一订单数；重复 order_id 只算一次", "99,441"],
  ["GMV", "SUM(FactOrders[product_value])", "商品销售金额，不含运费", "R$13.59M"],
  ["AOV", "DIVIDE([GMV], [Total Orders])", "平均每单商品销售金额", "R$136.68"],
  ["Active Sellers", "DISTINCTCOUNT(FactOrderSeller[seller_id])", "至少出现在订单商品中的唯一卖家", "3,095"],
  ["Seller Orders", "DISTINCTCOUNT(FactOrderSeller[order_id])", "有商品卖家记录的唯一订单", "98,666"],
  ["Orders per Seller", "DIVIDE([Seller Orders], [Active Sellers])", "平均每个活跃卖家的订单数", "31.88"],
  ["Seller GMV", "SUM(FactOrderSeller[product_value])", "当前卖家筛选环境下的商品金额", "随筛选变化"],
  ["Total Freight", "SUM(FactOrders[freight_value])", "订单层总运费", "随筛选变化"],
  ["Freight-to-GMV Ratio", "DIVIDE([Total Freight], [GMV])", "运费相对于商品金额的比例", "16.57%"],
  ["Total Leads", "SUM(FactAcquisition[total_leads])", "营销合格 leads 总数", "8,000"],
  ["Won Leads", "SUM(FactAcquisition[won_leads])", "成功 closed/won 的 leads", "842"],
  ["Lead-to-Close Rate", "DIVIDE([Won Leads], [Total Leads])", "从 lead 到成交的转化率", "10.53%"],
  ["Activated Sellers", "CALCULATE(DISTINCTCOUNT(FactSellerLifecycle[seller_id]), FactSellerLifecycle[is_activated] = TRUE())", "成交后至少有一笔 post-win order 的卖家", "380"],
  ["Activation Rate", "DIVIDE([Activated Sellers], [Won Leads])", "成交卖家中真正开始出单的比例", "45.13%"],
  ["Median Lead-to-Close Days", "MEDIAN(FactSellerLifecycle[days_to_close])", "从首次接触到成交的中位天数", "14 days"],
  ["Median Days to First Sale", "MEDIANX(FILTER(FactSellerLifecycle, FactSellerLifecycle[is_activated] = TRUE()), FactSellerLifecycle[days_to_first_sale])", "已激活卖家从成交到首单的中位天数", "44 days"],
  ["Delivered Orders", "CALCULATE([Total Orders], FactOrders[delivery_status] IN {\"on_time\", \"late\"})", "已实际送达、可以判断准时性的订单", "96,476"],
  ["On-Time Orders", "CALCULATE([Total Orders], FactOrders[delivery_status] = \"on_time\")", "实际送达日期不晚于预计日期", "88,649"],
  ["Late Orders", "CALCULATE([Total Orders], FactOrders[delivery_status] = \"late\")", "实际送达日期晚于预计日期", "7,827"],
  ["On-Time Delivery Rate", "DIVIDE([On-Time Orders], [Delivered Orders])", "已送达订单中的准时比例", "91.89%"],
  ["Late Delivery Rate", "DIVIDE([Late Orders], [Delivered Orders])", "已送达订单中的延迟比例", "8.11%"],
  ["Average Delivery Days", "AVERAGE(FactOrders[delivery_days])", "下单到实际送达的平均天数", "12.50 days"],
  ["Average Review Score", "AVERAGEX(VALUES(FactOrderSeller[order_id]), CALCULATE(MAX(FactOrderSeller[average_review_score])))", "先按唯一订单取一次评分，再平均，避免多卖家订单重复加权", "4.11 / 5"],
  ["Seller Delivered Orders", "CALCULATE([Seller Orders], FactOrderSeller[delivery_status] IN {\"on_time\", \"late\"})", "当前卖家环境中已送达的唯一订单", "随筛选变化"],
  ["Seller Late Orders", "CALCULATE([Seller Orders], FactOrderSeller[delivery_status] = \"late\")", "当前卖家环境中延迟的唯一订单", "随筛选变化"],
  ["Seller Late Delivery Rate", "DIVIDE([Seller Late Orders], [Seller Delivered Orders])", "卖家的延迟履约比例", "随筛选变化"],
];

const pagePlan = [
  ["01 Executive Overview", "10", "高层总览：订单、GMV、AOV、活跃卖家、准时率、评分；月度 GMV、月度订单、订单状态、年份 slicer", "先回答平台规模、价值和总体健康度"],
  ["02 Acquisition Funnel", "12", "7 张 KPI cards；渠道 leads/wins、渠道转化率、月度趋势；年份和 origin slicers", "回答哪些来源不仅带来 leads，而且能成交和激活"],
  ["03 Seller Performance", "12", "卖家数量、订单、GMV、每卖家订单、评分、延迟率；州别与月度图；年份和州 slicers", "回答哪些卖家地区贡献高、哪些地区有履约风险"],
  ["04 Fulfilment and CX", "11", "已送达、准时/延迟率、配送天数、评分、运费比；配送状态与州别风险", "回答物流表现如何，以及延迟与客户体验怎样相关"],
  ["05 Seller Detail", "9", "卖家订单、GMV、评分、延迟率；月度趋势、配送结果；seller_id 与年份 slicers", "聚焦一个 seller_id。当前是筛选式详情页，不是原生 drill-through"],
];

// Cover
children.push(new Paragraph({ spacing: { before: 1050, after: 260 }, alignment: AlignmentType.CENTER, children: [run("OLIST MARKETPLACE ANALYTICS", { bold: true, size: 44, color: COLORS.navy })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 220 }, children: [run("完整项目理解与面试讲义", { bold: true, size: 36, color: COLORS.blue })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 80 }, children: [run("Complete Project Learning & Interview Guide", { italics: true, size: 24, color: COLORS.darkGray })] }));
addBlank();
addCallout("这份讲义怎样使用 / How to use this guide", "先自己阅读并用自己的话解释每一章。看到 SQL 或 DAX 时，不要背整段；先回答：输入是什么、每一行代表什么、为什么这样计算、输出给谁使用。哪里不明白，再带着具体章节回来问。", COLORS.lightBlue);
addTable(["项目 / Project", "当前技术资产 / Current assets"], [
  ["Olist Marketplace Growth, Seller Onboarding & Fulfilment Analytics", "11 raw CSVs；15 SQL files；4 BigQuery marts；26 DAX measures；5 Power BI pages；54 visuals"],
  ["核心商业问题 / Core question", "Which acquisition origins produce sellers who close, activate, generate strong GMV, and fulfil orders reliably?"],
  ["工具 / Stack", "BigQuery + GoogleSQL；Power BI + DAX；Git/GitHub；Python 仅作轻量本地验证"],
], [3100, CONTENT_WIDTH - 3100]);
addP("Prepared for learning, portfolio explanation and Data Analyst interviews", { alignment: AlignmentType.CENTER, run: { italics: true, color: COLORS.darkGray } });
addPageBreak();

addHeading("目录 / Table of Contents", 1);
children.push(new TableOfContents("", { hyperlink: true, headingStyleRange: "1-3" }));
addCallout("Word 提示", "如果目录没有立刻显示页码：在 Microsoft Word 中按 Ctrl+A，然后按 F9 更新字段。", COLORS.gray);
addPageBreak();

addHeading("1. 先用一句话看懂项目 / Project in one sentence", 1);
addP("这是一个把 Olist 的营销 lead 数据连接到电商订单数据的端到端分析项目：先判断哪个 acquisition origin 能带来成交卖家，再判断这些卖家是否真正开始出单、创造商品销售金额，并且准时履约。", { run: { size: 23 } });
addP("English interview version: I built an end-to-end marketplace analytics solution that links marketing-qualified leads to seller activation, post-win commercial performance, fulfilment quality and customer reviews.", { run: { italics: true, color: COLORS.navy } });
addCallout("你的差异化不是 dataset 本身", "Olist 很多人做，但多数人只做普通 sales dashboard。你的版本把 marketing funnel 接到 seller lifecycle，并用 grain、pre-aggregation、fanout reconciliation 和 KPI validation 证明数字没有被 JOIN 放大。", COLORS.lightGreen);
addHeading("1.1 业务对象 / Business entities", 2);
addTable(["对象", "在项目中的意思", "关键 ID"], [
  ["Lead", "对 Olist 有兴趣并进入 marketing funnel 的潜在卖家", "mql_id"],
  ["Closed deal", "已经成功谈成合作的 lead", "mql_id + seller_id"],
  ["Activated seller", "成交后至少出现一笔 won_date 之后订单的卖家", "seller_id"],
  ["Order", "消费者的一次订单", "order_id"],
  ["Order item", "订单中的一个商品序号，属于某个 seller", "order_id + order_item_id"],
  ["Review", "消费者对订单的评分/评论记录", "order_id；review_id 不可靠唯一"],
], [1900, 4700, CONTENT_WIDTH - 6600]);

addHeading("2. End-to-end 架构 / Architecture", 1);
addCode(`Official Olist CSV files (11)\n  -> BigQuery: olist_raw\n  -> olist_staging (4 cleaned views)\n  -> olist_marts (4 Power BI-ready views)\n  -> olist_analysis (3 business analysis views)\n  -> olist_quality (2 reconciliation views)\n  -> Power BI Import mode\n  -> Semantic model: Facts + Dimensions + Measures\n  -> 5 report pages / 54 visuals`);
addTable(["层 / Layer", "为什么存在 / Why it exists", "不能混淆的重点"], [
  ["Raw", "原始证据；保留官方 CSV 原貌", "不要直接改 CSV；错误修正放 staging"],
  ["Staging", "清理类型、文字、NULL 与衍生日期；保留清理 flag", "staging 不负责最终 dashboard 汇总"],
  ["Marts", "把数据整理成稳定 grain，供 Power BI 使用", "Power BI 读取 marts，不直接 JOIN 11 张 raw 表"],
  ["Analysis", "回答特定商业问题，例如渠道质量、卖家排名、延迟与评分", "关联不等于因果"],
  ["Quality", "比较 source 与 model，证明 JOIN 没有重复金额", "PASS/FAIL 是控制证据，不是装饰"],
  ["Power BI", "语义模型、DAX、筛选互动和管理层可视化", "DAX 会响应 filter context"],
], [1500, 4200, CONTENT_WIDTH - 5700]);

addHeading("3. Original dataset：11 张表怎样看", 1);
addP("看任何表时先问 grain：一行代表什么。只要 grain 不清楚，就不要急着 SUM 或 JOIN。", { run: { bold: true, color: COLORS.navy } });
addTable(["Raw table", "Rows", "Grain（一行代表什么）", "主要用途"], rawTables, [2350, 900, 2350, CONTENT_WIDTH - 5600]);
addHeading("3.1 最重要的连接键 / Join keys", 2);
addCode(`orders.customer_id = customers.customer_id\norder_items.order_id = orders.order_id\norder_payments.order_id = orders.order_id\norder_reviews.order_id = orders.order_id\norder_items.product_id = products.product_id\norder_items.seller_id = sellers.seller_id\nclosed_deals.mql_id = marketing_qualified_leads.mql_id\nclosed_deals.seller_id = sellers.seller_id`);
addCallout("为什么 842 个成交卖家只有 380 个 activated?", "842 是 closed deals；其中 380 个 seller_id 后来在 order_items 出现，并且有 won_date 当天或之后的订单。没有订单匹配的 462 个不能自动当作错误删除，它们只是没有在当前电商订单期间显示激活证据。", COLORS.lightYellow);

addHeading("4. Grain：这个项目最重要的思维", 1);
addP("Grain = 每一行代表的业务单位。面试官问模型时，先讲 grain，比先讲函数更专业。", { run: { size: 23, bold: true } });
addTable(["数据对象", "正确 grain", "为什么重要"], [
  ["stg_orders / mart_orders", "one row per order_id", "可以安全计算唯一订单、订单级收入与配送"],
  ["stg_order_items", "one row per order_id × order_item_id", "同一订单可能多个商品和卖家"],
  ["stg_order_payments", "one row per order_id × payment_sequential", "一个订单可能多种付款/多笔记录"],
  ["stg_marketing_funnel", "one row per mql_id", "保留所有 8,000 leads，包括未成交"],
  ["mart_order_seller", "one row per order_id × seller_id", "卖家业绩需要把同一订单按 seller 分开"],
  ["mart_marketing_funnel", "one row per contact_month × origin", "已经汇总，Power BI 用 SUM，不用 DISTINCTCOUNT mql_id"],
  ["mart_seller_lifecycle", "one row per won mql_id", "追踪成交后是否激活与首单表现"],
], [2500, 3000, CONTENT_WIDTH - 5500]);

addHeading("4.1 JOIN fanout 小例子", 2);
addP("假设 order O1 有 2 个 items，也有 2 个 payment rows。直接把两张表都 JOIN 到 orders，会变成 2 × 2 = 4 行。", { run: { bold: true } });
addTable(["order_id", "item", "item_price"], [["O1", "A", "100"], ["O1", "B", "50"]], [2600, 2600, CONTENT_WIDTH - 5200], { headerFill: COLORS.teal });
addTable(["order_id", "payment", "payment_value"], [["O1", "credit_card", "120"], ["O1", "voucher", "30"]], [2600, 3000, CONTENT_WIDTH - 5600], { headerFill: COLORS.teal });
addP("错误的 JOIN 结果会让 item A 和 item B 各自重复两次，SUM(item_price) 从正确的 150 变成 300。", { run: { bold: true, color: "C00000" } });
addP("正确做法：先在各自 CTE 里 GROUP BY order_id，再把 item_summary（1 行）和 payment_summary（1 行）JOIN 到 orders。", { run: { bold: true, color: COLORS.green } });
addCode(`WITH item_summary AS (\n  SELECT order_id, SUM(item_price) AS product_value\n  FROM stg_order_items\n  GROUP BY order_id\n),\npayment_summary AS (\n  SELECT order_id, SUM(payment_value) AS payment_value\n  FROM stg_order_payments\n  GROUP BY order_id\n)\nSELECT ...\nFROM stg_orders AS o\nLEFT JOIN item_summary AS i ON o.order_id = i.order_id\nLEFT JOIN payment_summary AS p ON o.order_id = p.order_id;`);

addHeading("5. 15 个 SQL 文件：完整路线", 1);
addTable(["#", "File", "目的 / Purpose", "Input → Output", "核心语法"], sqlFiles, [450, 2450, 3000, 1950, CONTENT_WIDTH - 7850]);

addHeading("6. 15 个 SQL 文件逐个解释", 1);
sqlFiles.forEach((row) => {
  const [num, file, purpose, io, concepts] = row;
  addHeading(`${num}. ${file}`, 2);
  addKeyValue("要解决的问题", purpose);
  addKeyValue("数据流", io);
  addKeyValue("你要会解释的语法", concepts);
  if (num === "1") addP("`__TABLES__` 是 BigQuery dataset 的 metadata 表，不是 11 个 CSV 的内容；它列出已上传的 table_id、row_count 和 size_bytes。", { run: { color: COLORS.navy } });
  if (num === "2") addP("结果为空不一定是失败。例如重复 order-item 查询没有 rows，代表组合键没有重复。对 review 的检查则发现 547 个订单有多行 review，因此后面必须先按 order_id 聚合。", { run: { color: COLORS.navy } });
  if (num === "3") addP("这个 view 不改变原始 orders；它清理文字并新增日期字段。raw 和 staging 都是 99,441 行，证明没有意外删单。", { run: { color: COLORS.navy } });
  if (num === "4") addP("`CAST(price AS NUMERIC)` 是把金额统一为适合精确计算的类型；`item_total_value = item_price + freight_value`，但 dashboard 的 GMV 只用 product_value，不含 freight。", { run: { color: COLORS.navy } });
  if (num === "5") addP("两行 credit_card 的 payment_installments 为 0。业务上信用卡付款至少 1 期，因此用 CASE 改为 1，同时保留 original value 和 corrected flag，确保可审计。", { run: { color: COLORS.navy } });
  if (num === "6") addP("MQL 放左边是因为要保留全部 8,000 leads。没成交的 deal 字段为 NULL，CASE 把它标为 not_won；最终 842 won，转化率 10.53%。", { run: { color: COLORS.navy } });
  if (num === "7") addP("这是整个项目防止 fanout 的关键文件。items 与 payments 各自先变成 one row per order，再 JOIN；最终 mart_rows 必须等于 unique_orders。", { run: { color: COLORS.navy } });
  if (num === "8") addP("评论是 order-level，不是 seller-level。多卖家订单的订单评分会出现在多个 seller rows，因此总体 Average Review Score 的 DAX 必须先按唯一 order_id 取一次，不能直接 AVG 所有 seller rows。", { run: { color: COLORS.navy } });
  if (num === "9") addP("这个 mart 已经是月份 × 来源汇总表，所以 Total Leads 的 DAX 用 SUM(total_leads)，不是 DISTINCTCOUNT(mql_id)，因为 mart 已经没有 mql_id。", { run: { color: COLORS.navy } });
  if (num === "10") addP("JOIN 条件不仅是 seller_id，还要求 performance.purchase_date >= won_date，避免把成交前订单误当作销售团队带来的 activation。", { run: { color: COLORS.navy } });
  if (num === "11") addP("渠道不能只看 lead volume；还要同时看 close rate、activation、首单速度、post-win product value、评分与准时率。", { run: { color: COLORS.navy } });
  if (num === "12") addP("RANK() OVER 不会把卖家合并；它保留每个 seller row，并新增名次。PARTITION BY origin 会让每个 origin 重新从第 1 名开始。", { run: { color: COLORS.navy } });
  if (num === "13") addP("这里把订单分成 on_time_or_early、late_1_3_days、late_4_7_days、late_8_plus_days、not_delivered。只能说 delivery delay 与 review score 有 association，不能证明 delay caused the score。", { run: { color: COLORS.navy } });
  if (num === "14") addP("六个 source/model 比较都应 difference = 0。它直接针对最常见的数据仓库错误：JOIN 后行数和金额被重复。", { run: { color: COLORS.navy } });
  if (num === "15") addP("最终再核对 total orders、leads、closed leads、activated sellers、marketplace sellers、reviewed orders。六项 PASS、零项 FAIL 才能把 KPI 交给 Power BI。", { run: { color: COLORS.navy } });
});

addHeading("7. 项目 SQL 语法：一定要会解释", 1);
addHeading("7.1 WHERE、GROUP BY、HAVING", 2);
addTable(["语法", "作用", "项目例子"], [
  ["WHERE", "先筛选原始 rows", "WHERE price >= 0"],
  ["GROUP BY", "把 rows 分组后聚合", "GROUP BY order_id"],
  ["HAVING", "筛选聚合后的 groups", "HAVING COUNT(*) > 1"],
], [1600, 3100, CONTENT_WIDTH - 4700]);
addHeading("7.2 COUNT 系列", 2);
addTable(["函数", "意思", "何时用"], [
  ["COUNT(*)", "数当前结果有几行", "当每一行就是你要数的单位"],
  ["COUNT(DISTINCT order_id)", "数不重复订单", "表里一个订单可能多行"],
  ["COUNTIF(condition)", "只数 condition 为 TRUE 的行", "won leads、late orders、NULL checks"],
], [2500, 3000, CONTENT_WIDTH - 5500]);
addHeading("7.3 CASE", 2);
addCode(`CASE\n  WHEN delivered_date IS NULL THEN 'not_delivered'\n  WHEN delivered_date <= estimated_date THEN 'on_time'\n  ELSE 'late'\nEND AS delivery_status`);
addP("CASE 从上到下检查，返回第一个成立的结果。它既可清理错误，也可建立业务分类。", { run: { color: COLORS.navy } });
addHeading("7.4 CAST", 2);
addCode(`CAST(price AS NUMERIC) AS item_price`);
addP("CAST 改变数据类型。金额转 NUMERIC 是为了稳定、精确的加总；不是为了让数字看起来不同。", { run: { color: COLORS.navy } });
addHeading("7.5 COALESCE + NULLIF", 2);
addCode(`COALESCE(NULLIF(LOWER(TRIM(origin)), ''), 'unknown') AS origin`);
restartNumbers();
addNumber("TRIM 去前后空格；LOWER 转小写。");
addNumber("NULLIF(cleaned_origin, '')：如果清理后是空字串，就变 NULL。");
addNumber("COALESCE(value, 'unknown')：如果 value 是 NULL，就用 unknown。");
addHeading("7.6 WITH / CTE", 2);
addP("WITH name AS (...) 是给一个临时查询结果取名。把复杂 SQL 拆成可理解的积木；它只在这次 statement 内存在。", { run: { color: COLORS.navy } });
addHeading("7.7 LEFT JOIN", 2);
addP("LEFT JOIN 保留左表全部 rows。MQL 放左边，所以没成交的 lead 仍保留，deal 字段显示 NULL；这是计算真实转化率的前提。", { run: { color: COLORS.navy } });
addHeading("7.8 SAFE_DIVIDE", 2);
addCode(`SAFE_DIVIDE(won_leads, total_leads)`);
addP("分母为 0 时返回 NULL，而不是让 query 报错。Power BI 对应常用 DAX DIVIDE。", { run: { color: COLORS.navy } });
addHeading("7.9 STRING_AGG", 2);
addP("把同一订单的多种付款方式从多行合成文字，例如 credit_card, voucher，让 mart 仍保持一行一个订单。", { run: { color: COLORS.navy } });
addHeading("7.10 RANK() OVER", 2);
addCode(`RANK() OVER (\n  PARTITION BY origin\n  ORDER BY post_win_product_value DESC\n) AS origin_product_value_rank`);
addP("窗口函数保留原 rows，并新增计算列；GROUP BY 则会把多行压成更少行。这是两者最重要的区别。", { run: { color: COLORS.navy } });
addHeading("7.11 UNION ALL", 2);
addP("把多个同结构结果上下堆叠。quality check 用它把六个不同 metric 的 source/model 比较放进同一张控制表。", { run: { color: COLORS.navy } });

addHeading("8. Power BI semantic model", 1);
addTable(["Power BI table", "来自 BigQuery", "Grain / Role"], [
  ["FactOrders", "mart_orders", "one row per order；平台订单、金额、客户、配送"],
  ["FactOrderSeller", "mart_order_seller", "one row per order × seller；卖家业绩与履约"],
  ["FactAcquisition", "mart_marketing_funnel", "contact_month × origin；渠道汇总"],
  ["FactSellerLifecycle", "mart_seller_lifecycle", "one row per won mql；成交后激活"],
  ["DimDate", "Power BI date table", "连续日期；统一 Year / Quarter / Month 筛选"],
  ["DimOrigin", "从 acquisition origin 去重", "one row per origin；渠道维度"],
  ["DimSeller", "从 seller_id 去重", "one row per seller；州与城市维度"],
  ["_Measures", "手工建立", "只存 DAX measures，不存业务 rows"],
], [2100, 2500, CONTENT_WIDTH - 4600]);
addHeading("8.1 Relationships", 2);
addP("关系采用 dimension 端 1、fact 端 *，single-direction filtering。不要直接把 fact tables 互相 many-to-many 连接。", { run: { bold: true, color: COLORS.navy } });
addTable(["Dimension", "Fact", "Key"], [
  ["DimDate", "FactOrders", "Date → purchase_date"],
  ["DimDate", "FactOrderSeller", "Date → purchase_date"],
  ["DimDate", "FactAcquisition", "Date → contact_month"],
  ["DimDate", "FactSellerLifecycle", "Date → contact_month"],
  ["DimOrigin", "FactAcquisition", "origin → origin"],
  ["DimOrigin", "FactSellerLifecycle", "origin → origin"],
  ["DimSeller", "FactOrderSeller", "seller_id → seller_id"],
], [2400, 3000, CONTENT_WIDTH - 5400]);
addCallout("为什么 DimDate 要 Mark as date table?", "它告诉 Power BI 哪一列是连续、唯一的正式日期轴。Year Month 必须按 Year Month Sort 排序；不要拿 Year 去按 Year Month Sort 排序，因为同一个 Year 对应 12 个 sort values。", COLORS.lightBlue);
addHeading("8.2 Filter context", 2);
addP("同一个 measure 会随着 Year、origin、seller_state、seller_id slicer 改变。DAX 不是把一个固定数字贴在 card；它是在当前 filter context 下重新计算。", { run: { color: COLORS.navy } });
addCode(`Seller GMV = SUM(FactOrderSeller[product_value])\n\nNo seller filter  -> all seller product value\nSeller ID selected -> only that seller's product value\nYear selected      -> only rows related to that year`);

addHeading("9. 26 个 DAX measures：公式、意义和结果", 1);
addTable(["Measure", "DAX", "业务意义", "当前全局结果"], measures, [1850, 3550, 3000, CONTENT_WIDTH - 8400], { headerFill: COLORS.teal });

addHeading("9.1 三个最容易算错的 measure", 2);
addHeading("A. Total Orders", 3);
addCode(`Total Orders = DISTINCTCOUNT(FactOrders[order_id])`);
addP("`DISTINCTCOUNT` 的意思就是不重复计数。虽然 FactOrders 设计为一行一个订单，仍用 DISTINCTCOUNT 让业务定义明确，并能防止模型变化后误计重复。", { run: { color: COLORS.navy } });
addHeading("B. GMV", 3);
addCode(`GMV = SUM(FactOrders[product_value])`);
addP("GMV 在这个项目定义为商品销售金额，不含 freight。必须把 KPI definition 讲清楚，否则不同公司会用不同口径。", { run: { color: COLORS.navy } });
addHeading("C. Average Review Score", 3);
addCode(`Average Review Score =\nAVERAGEX(\n  VALUES(FactOrderSeller[order_id]),\n  CALCULATE(MAX(FactOrderSeller[average_review_score]))\n)`);
addP("FactOrderSeller 是 order × seller。一个多卖家订单会出现多行，但 review 是 order-level。如果直接 AVERAGE，会让多卖家订单权重更高。这里先用 VALUES(order_id) 建立唯一订单清单，再每单取一次 score，最后平均。", { run: { color: COLORS.navy } });

addHeading("10. 5 页 dashboard：每一页要回答什么", 1);
addTable(["Page", "Visuals", "内容", "业务问题"], pagePlan, [1850, 700, 4500, CONTENT_WIDTH - 7050]);
addHeading("10.1 Executive Overview 的阅读顺序", 2);
restartNumbers();
addNumber("先读规模：Total Orders、GMV、AOV、Active Sellers。");
addNumber("再读健康度：On-Time Delivery Rate、Average Review Score。");
addNumber("看趋势：Monthly GMV Trend 与 Monthly Order Trend 是否同方向。");
addNumber("看结构：Order Status Distribution 是否有较多 canceled/unavailable。");
addNumber("用 Year slicer 检查指标是否随时间筛选正确变化。");
addHeading("10.2 Acquisition Funnel 的阅读顺序", 2);
addP("Total Leads → Won Leads → Activated Sellers 是两段 funnel。Lead-to-Close 衡量销售成交；Activation Rate 衡量成交后是否真正开始卖。不要把两种转化率混为一个。", { run: { color: COLORS.navy } });
addHeading("10.3 Seller Performance 的阅读顺序", 2);
addP("先看卖家规模与贡献，再比较州别 GMV 和订单，最后用 Late Delivery Risk 找出高贡献但高风险的州。Seller Detail 页用于继续筛到单个 seller_id。", { run: { color: COLORS.navy } });
addHeading("10.4 Fulfilment & CX 的阅读顺序", 2);
addP("Delivered Orders 是准时率的分母；not_delivered 不应混入 on-time/late rate。然后比较州别 late rate 与 delivery outcome 下的 review score，但只能说 association。", { run: { color: COLORS.navy } });

addHeading("11. 当前关键结果 / Validated headline metrics", 1);
addTable(["KPI", "Result", "一句话解释"], [
  ["Total Orders", "99,441", "分析期间平台订单规模"],
  ["GMV", "R$13.59M", "商品销售金额，不含运费"],
  ["AOV", "R$136.68", "平均每单商品金额"],
  ["Active Sellers", "3,095", "有订单商品记录的卖家"],
  ["Total Leads → Won Leads", "8,000 → 842", "Lead-to-Close Rate 10.53%"],
  ["Won Leads → Activated Sellers", "842 → 380", "Activation Rate 45.13%"],
  ["Median Lead-to-Close", "14 days", "首次接触到成交的中位速度"],
  ["Median Days to First Sale", "44 days", "成交到首单的中位速度"],
  ["Delivered Orders", "96,476", "有 actual delivery，可判断准时性"],
  ["On-Time / Late", "88,649 / 7,827", "On-Time Rate 91.89%，Late Rate 8.11%"],
  ["Average Delivery Days", "12.50", "下单到实际送达平均天数"],
  ["Average Review Score", "4.11 / 5", "按唯一订单去重后的平均评分"],
  ["Freight-to-GMV Ratio", "16.57%", "运费相对商品销售金额的比例"],
], [2500, 1900, CONTENT_WIDTH - 4400]);
addCallout("数据口径提醒", "这些是当前全局 filter context 的结果。Power BI 加上 Year、origin、seller state 或 seller ID 筛选后，measure 会动态变化。", COLORS.lightYellow);

addHeading("12. 质量控制与可相信程度", 1);
addTable(["风险", "项目怎样控制", "证据"], [
  ["订单重复", "orders 的 rows 与 distinct order_id 相等", "99,441 = 99,441"],
  ["Order-item 重复", "检查 order_id + order_item_id", "duplicate query returns no rows"],
  ["Review duplicate candidate key", "不把 review_id 当唯一真相；先按 order_id 聚合", "814 duplicate review_id rows；547 orders 多 review rows"],
  ["JOIN fanout", "items/payments/reviews 先按目标 grain 聚合", "6 reconciliation checks PASS，0 FAIL"],
  ["最终 KPI 漂移", "raw ↔ marts ↔ analysis 再核对", "6 final checks PASS，0 FAIL"],
  ["人工修正无法追踪", "保留 original_payment_installments 与 corrected flag", "2 corrected payment rows"],
], [2200, 4600, CONTENT_WIDTH - 6800]);

addHeading("13. 局限 / Limitations", 1);
addBullet("数据是巴西 Olist 的历史公开数据（2016–2018），不是新加坡或实时业务数据。");
addBullet("没有 website behavioural events，所以不能分析 view_item → add_to_cart → checkout 漏斗。");
addBullet("Review 是订单层级；多卖家订单无法把一个评分精确归因到某个 seller。Seller-level review 只能谨慎解释。");
addBullet("Delivery delay 与 low review 的关系是 association，不是 causal proof。");
addBullet("`product_value` 与 `payment_value` 是不同业务口径；GMV 在 dashboard 明确定义为商品金额，不含 freight。");
addBullet("Seller Detail 当前依靠 seller_id slicer，不是 Power BI 原生 drill-through metadata。");
addBullet("Closed seller 未在订单期间出现，不代表一定失败；只能说当前数据没有 activation evidence。");

addHeading("14. 面试怎样讲 / Interview explanation", 1);
addHeading("14.1 60 秒英文版本", 2);
addP("I built an end-to-end Olist marketplace analytics project in BigQuery and Power BI. The core question was which acquisition channels produced sellers who not only closed, but also activated, generated post-win product value and fulfilled orders reliably. I profiled eleven raw CSV tables, created staging views, four analytical marts and reconciliation checks. The key modelling challenge was preventing join fanout across orders, items, payments and reviews, so I pre-aggregated one-to-many tables to the target grain before joining. In Power BI, I built a star-style semantic model with twenty-six DAX measures and five pages covering executive KPIs, acquisition, seller performance, fulfilment and seller detail.", { run: { italics: true, color: COLORS.navy } });
addHeading("14.2 两分钟中文逻辑", 2);
restartNumbers();
addNumber("业务问题：哪些渠道带来的卖家不只成交，还能激活、创造金额并稳定履约。");
addNumber("数据：11 张 Olist raw 表，电商订单与 marketing funnel 用 seller_id 接起来。");
addNumber("难点：orders、items、payments、reviews 的 grain 不同，直接 JOIN 会重复金额。");
addNumber("解决：staging 清理；CTE 先聚合到 order 或 order-seller grain；建立 4 marts。");
addNumber("验证：fanout 与 final KPI 各 6 项检查，均 6 PASS、0 FAIL。");
addNumber("Power BI：3 个 dimensions、4 个 facts、26 measures、5 pages，所有 KPI 与 SQL 口径一致。");
addNumber("结果：8,000 leads 中 842 成交，380 激活；准时送达率约 91.89%；GMV R$13.59M。");
addHeading("14.3 常见追问与回答", 2);
addTable(["Interview question", "回答重点"], [
  ["Why not load all raw tables directly into Power BI?", "SQL marts enforce grain, centralise business logic, reduce model complexity and make KPI reconciliation possible."],
  ["What was the hardest technical problem?", "Preventing fanout from one-to-many joins. I pre-aggregated items, payments and reviews before joining."],
  ["Why DISTINCTCOUNT for orders?", "The business definition is unique order_id, and DISTINCTCOUNT remains safe under seller-level or future duplicated rows."],
  ["Why is GMV not payment_value?", "I defined project GMV as product value excluding freight. Payment value is retained separately and reconciled."],
  ["Why use median for time-to-close?", "Cycle-time distributions can be skewed by outliers; median describes the typical seller more robustly."],
  ["Can you claim late delivery caused poor reviews?", "No. The analysis shows association only; other factors may influence reviews."],
  ["Why is the dataset common but your project still useful?", "The differentiation is the lead-to-seller lifecycle, explicit grains, fanout controls, SQL-to-DAX reconciliation and business storytelling."],
], [3200, CONTENT_WIDTH - 3200]);

addHeading("15. 自测：不要看答案先讲", 1);
restartNumbers();
[
  "mart_orders 为什么必须 one row per order_id?",
  "如果直接 JOIN order_items 和 order_payments，金额为什么会重复?",
  "为什么 MQL 到 closed_deals 用 LEFT JOIN，不用 INNER JOIN?",
  "COALESCE(NULLIF(LOWER(TRIM(origin)), ''), 'unknown') 每一步做什么?",
  "COUNT(*)、COUNT(DISTINCT order_id)、COUNTIF(...) 有什么不同?",
  "GMV 为什么不含 freight? AOV 的分母是什么?",
  "为什么 Average Review Score 不能直接 AVG(FactOrderSeller[average_review_score])?",
  "Lead-to-Close Rate 与 Activation Rate 的分母分别是什么?",
  "DimDate 为什么是 dimension 端 1，fact 端 *?",
  "RANK() OVER 与 GROUP BY 的主要区别是什么?",
  "六个 join fanout checks 在证明什么?",
  "你能从 delivery/review analysis 做因果结论吗? 为什么?",
].forEach(addNumber);

addHeading("16. 完成状态与下一步 / Status and next steps", 1);
addTable(["项目部分", "当前状态", "你接下来要做"], [
  ["Raw data + BigQuery", "已建立并核对", "会说 11 张表、连接键与 grain"],
  ["15 SQL files", "已完成", "分阶段重写关键 queries：6、7、8、10、12、14"],
  ["Quality validation", "6 PASS/0 FAIL × 2 组", "能解释为什么不是只看 query completed"],
  ["Power BI model", "已建立", "会画出 facts、dimensions、1:*、single direction"],
  ["26 DAX measures", "已建立", "先独立写 8 个核心 measures，再学 filter context"],
  ["5 dashboard pages", "已完成并保存", "逐页练习 30–60 秒业务讲解"],
  ["Portfolio readiness", "技术主体完成，表达能力仍需训练", "README、截图、GitHub、英文讲解和 mock interview"],
], [2500, 2600, CONTENT_WIDTH - 5100]);
addCallout("最有效的复习顺序", "第一轮只讲业务和 grain；第二轮讲 SQL 为什么这样变形；第三轮独立写核心 SQL/DAX；第四轮用 dashboard 讲 insights；最后做英文 mock interview。不要同时硬背全部代码。", COLORS.lightGreen);

addHeading("17. 中英术语表 / Glossary", 1);
addTable(["English", "中文解释", "项目中的例子"], [
  ["grain", "每一行代表的业务单位", "order、order-item、order-seller、lead"],
  ["fact table", "存业务事件与可聚合数值的表", "FactOrders, FactOrderSeller"],
  ["dimension table", "用于分类与筛选的描述性表", "DimDate, DimOrigin, DimSeller"],
  ["fanout", "一对多 JOIN 导致行数相乘", "items × payments"],
  ["pre-aggregation", "JOIN 前先聚合到目标 grain", "item_summary by order_id"],
  ["reconciliation", "对账；比较 source 与 model", "difference = 0, PASS"],
  ["filter context", "当前 slicer/visual 施加的筛选环境", "Year、origin、seller_id"],
  ["activation", "成交卖家开始产生 post-win order", "first_post_win_order_date not null"],
  ["fulfilment", "订单履约与配送表现", "on-time, late, delivery days"],
  ["association", "两个现象同时变化的关系", "delay bucket vs review score"],
  ["causation", "一个因素直接导致另一个结果", "本项目不能证明 delay caused review"],
  ["audit flag", "记录某行是否被规则修正", "installment_corrected_flag"],
], [2100, 3100, CONTENT_WIDTH - 5200]);

addHeading("Appendix A. 关键本地文件 / Key local files", 1);
addTable(["Asset", "Path / Meaning"], [
  ["Power BI report", "D:\\olist-marketplace-analytics\\powerbi\\Olist_Marketplace_Analytics.pbix"],
  ["15 SQL files", "D:\\olist-marketplace-analytics\\sql\\"],
  ["DAX configuration source", "D:\\olist-marketplace-analytics\\powerbi\\configure_measures.ps1"],
  ["Dashboard layout source", "D:\\olist-marketplace-analytics\\powerbi\\build_dashboard_layout.py"],
  ["Raw inventory", "D:\\olist-marketplace-analytics\\docs\\data_inventory.md"],
  ["This guide", "D:\\olist-marketplace-analytics\\docs\\Olist_Marketplace_Analytics_Complete_Guide_Bilingual.docx"],
], [3100, CONTENT_WIDTH - 3100]);

addHeading("Appendix B. 口径速记 / KPI definition cheat sheet", 1);
addTable(["KPI", "Numerator", "Denominator", "Exclusion / Note"], [
  ["AOV", "GMV", "Total Orders", "GMV excludes freight"],
  ["Lead-to-Close", "Won Leads", "Total Leads", "保留 not-won leads"],
  ["Activation Rate", "Activated Sellers", "Won Leads", "activation requires post-win order"],
  ["On-Time Delivery Rate", "On-Time Orders", "Delivered Orders", "not_delivered 不进分母"],
  ["Late Delivery Rate", "Late Orders", "Delivered Orders", "on-time + late = delivered"],
  ["Freight-to-GMV", "Total Freight", "GMV", "不是 freight / item_total_value"],
], [2300, 2500, 2500, CONTENT_WIDTH - 7300]);

const doc = new Document({
  creator: "Codex",
  title: "Olist Marketplace Analytics Complete Guide Bilingual",
  subject: "BigQuery, SQL, Power BI, DAX and interview preparation",
  description: "A complete bilingual learning and interview guide for the Olist marketplace analytics portfolio project.",
  styles: {
    default: { document: { run: { font: "Microsoft YaHei", size: 21, color: COLORS.black }, paragraph: { spacing: { after: 100, line: 300 } } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Microsoft YaHei", color: COLORS.navy },
        paragraph: { spacing: { before: 300, after: 140 }, outlineLevel: 0, border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: COLORS.blue, space: 3 } } } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 27, bold: true, font: "Microsoft YaHei", color: COLORS.blue },
        paragraph: { spacing: { before: 220, after: 110 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 23, bold: true, font: "Microsoft YaHei", color: COLORS.teal },
        paragraph: { spacing: { before: 160, after: 90 }, outlineLevel: 2 } },
    ],
  },
  numbering: {
    config: [
      { reference: "bullets", levels: [
        { level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } },
        { level: 1, format: LevelFormat.BULLET, text: "–", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 980, hanging: 260 } } } },
      ] },
      ...Array.from({ length: 20 }, (_, i) => ({ reference: `numbers-${i}`, levels: [
        { level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } },
      ] })),
    ],
  },
  sections: [{
    properties: { page: { size: { width: PAGE_WIDTH, height: PAGE_HEIGHT }, margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN, header: 500, footer: 500 } } },
    headers: { default: new Header({ children: [new Paragraph({ border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: COLORS.blue, space: 2 } }, children: [run("Olist Marketplace Analytics | Complete Learning Guide", { size: 17, color: COLORS.darkGray })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({
      tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
      children: [run("BigQuery • SQL • Power BI • DAX", { size: 17, color: COLORS.darkGray }), run("\tPage ", { size: 17, color: COLORS.darkGray }), new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 17, color: COLORS.darkGray })],
    })] }) },
    children,
  }],
});

Packer.toBuffer(doc).then((buffer) => {
  fs.mkdirSync(path.dirname(OUTPUT), { recursive: true });
  fs.writeFileSync(OUTPUT, buffer);
  console.log(OUTPUT);
  console.log(`Bytes: ${buffer.length}`);
});
