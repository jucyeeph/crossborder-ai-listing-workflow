# 跨境电商 AI 产品自动上架工作流：项目方向指引

> 目标：用户只需要提供 `1688 产品链接` 或 `产品电商美工图压缩包 + 少量补充信息`，系统自动输出适合菲律宾市场的产品图片、产品标题、卖点、详情描述、定价建议，以及可直接导入 BigSeller ERP 的产品创建表格。

---

## 1. 项目愿景

这个项目不是单一脚本，而是一套由多个 AI 子工作流串联起来的“产品上架流水线”。

最终理想状态：

1. 用户输入供应商链接、图片包或基础资料；
2. AI 自动采集和理解产品；
3. AI 自动补充适合菲律宾市场的卖点、标题、规格、属性、关键词；
4. AI 自动生成或改造电商图片；
5. AI 自动上传图片到稳定图床；
6. AI 自动计算建议售价、活动价、利润空间；
7. AI 自动填充 BigSeller ERP 创建产品模板；
8. 用户只需要人工复核后导入 ERP。

项目核心不是“完全无人审核”，而是：

> AI 完成 80%～95% 的重复劳动，人负责最终判断、抽查和发布。

---

## 2. 适用业务场景

### 2.1 主要市场

- 菲律宾电商市场；
- 平台包括但不限于：
  - Shopee PH
  - TikTok Shop PH
  - Lazada PH
- 语言以英文为主，可根据品类加入少量本地化表达。

### 2.2 主要产品类型

优先从标准化程度较高的产品开始：

- 美甲产品；
- 甲油胶；
- 猫眼胶；
- 功能胶；
- 美甲工具；
- 套装类产品；
- 后续可扩展到其他跨境小商品。

### 2.3 输入来源

系统需要支持两种主要输入：

#### A. 1688 产品链接

用户提供一个或多个 1688 商品链接。

系统需要自动处理：

- 产品标题；
- 主图；
- 详情图；
- SKU 图片；
- 规格参数；
- 价格区间；
- 起批量；
- 属性信息；
- 供应商信息；
- 可选：评论、销量、店铺可信度等辅助信息。

#### B. 产品图片压缩包

用户上传一个压缩包，里面可能包含：

- 主图；
- 详情图；
- SKU 图；
- 白底图；
- 美工图；
- 工厂原图；
- 色卡图；
- 产品说明图。

系统需要自动识别图片类型并分类。

---

## 3. 项目边界

### 3.1 第一阶段不追求完全自动发布

第一阶段目标是：

> 自动生成 BigSeller ERP 可导入的创建产品表格，而不是直接登录 ERP 自动点击发布。

原因：

1. ERP 自动点击容易受页面变化、验证码、登录状态影响；
2. 模板导入更稳定；
3. 方便人工复核；
4. 更适合作为标准化 Skill；
5. 后续可以再开发 ERP 自动操作 Agent。

### 3.2 人工复核必须保留

AI 自动生成的信息可能存在以下问题：

- 产品功效夸大；
- 标题关键词不精准；
- 规格理解错误；
- 图片顺序不合理；
- SKU 映射错误；
- 定价不符合实际库存策略；
- 平台敏感词或违规词风险。

因此系统输出必须包含：

- 可编辑的中间 JSON；
- 可复核的 Markdown 报告；
- 可导入的 Excel / CSV 表格；
- 错误和疑点提示。

### 3.3 不直接依赖某一个 AI 模型

不要把项目设计成“只有某一个大模型才能跑”。

更好的设计是：

- 复杂理解任务交给强模型；
- 稳定转换任务交给便宜模型；
- 表格生成、校验、图片上传等确定性任务交给脚本；
- Agent 只负责调度和处理异常。

---

## 4. 总体架构

建议把项目拆成 4 层：

```text
用户输入层
  ↓
资料解析层
  ↓
AI 处理层
  ↓
确定性生成层
  ↓
人工复核 / ERP 导入层
```

### 4.1 用户输入层

负责接收用户提供的原始资料。

支持输入：

```text
/input
  /links
    1688_links.txt
  /assets
    product_images.zip
  /manual
    product_brief.md
```

用户可以只提供其中一种，也可以混合提供。

### 4.2 资料解析层

负责把非结构化资料变成结构化资料。

输出统一格式：

```json
{
  "source_type": "1688_link_or_image_zip",
  "raw_title": "",
  "raw_images": [],
  "raw_sku_images": [],
  "raw_attributes": {},
  "raw_price": {},
  "raw_description": "",
  "supplier_info": {}
}
```

### 4.3 AI 处理层

负责完成需要理解、判断、改写、优化的任务。

包括：

- 产品定位；
- 菲律宾市场本地化；
- 英文标题生成；
- 卖点提炼；
- 详情描述生成；
- SKU 命名优化；
- 平台关键词生成；
- 图片内容判断；
- 图片生成提示词编写；
- 风险提示。

### 4.4 确定性生成层

负责不应该交给 AI 随机发挥的任务。

包括：

- 图片重命名；
- 图片尺寸检查；
- 图片上传图床；
- 图片 URL 回填；
- 价格公式计算；
- BigSeller 模板字段映射；
- Excel / CSV 生成；
- 必填字段校验；
- SKU 唯一性检查。

### 4.5 人工复核 / ERP 导入层

输出给用户：

```text
/output
  /review
    product_review.md
    warnings.md
  /data
    product.normalized.json
    product.pricing.json
    product.erp_mapping.json
  /images
    generated_images/
    uploaded_image_urls.json
  /erp
    bigseller_product_upload.xlsx
```

---

## 5. 核心子工作流

---

# 子工作流 1：产品资料采集工作流

## 5.1 目标

把用户提供的 1688 链接或图片包，转换成统一的产品原始资料。

## 5.2 输入

```text
- 1688 产品链接
或
- 产品图片压缩包
或
- 用户手动补充的产品说明
```

## 5.3 输出

```text
product.raw.json
raw_images/
raw_sku_images/
raw_description.md
```

## 5.4 关键任务

### 如果输入是 1688 链接

需要完成：

1. 打开链接；
2. 获取商品标题；
3. 获取商品主图；
4. 获取详情图；
5. 获取 SKU 图；
6. 获取规格参数；
7. 获取价格区间；
8. 获取起批量；
9. 保存网页截图或 HTML 证据；
10. 生成 `product.raw.json`。

### 如果输入是图片压缩包

需要完成：

1. 解压；
2. 图片去重；
3. 判断图片类型；
4. 分类为主图、详情图、SKU 图、色卡图、说明图；
5. 使用视觉模型读取图片文字；
6. 生成产品初步理解；
7. 生成 `product.raw.json`。

## 5.5 注意事项

- 1688 页面结构可能变化，不要强依赖单一 DOM 选择器；
- 供应商图片可能有中文，需要翻译和本地化；
- 图片文件名通常不可信，要用图片内容重新判断；
- 如果采集失败，需要保留失败截图和日志。

---

# 子工作流 2：产品信息补充优化工作流

## 6.1 目标

把原始产品信息改造成适合菲律宾电商平台的英文产品资料。

## 6.2 输入

```text
product.raw.json
raw_images/
用户补充要求，可选
```

## 6.3 输出

```text
product.optimized.json
product_copywriting.md
warnings.md
```

## 6.4 需要生成的内容

### A. 英文产品标题

标题需要适合菲律宾市场。

要求：

- 英文；
- 不要生硬机翻；
- 包含核心关键词；
- 包含规格、颜色、功能等关键信息；
- 不夸大；
- 不堆砌无关关键词；
- 避免平台违规词。

示例结构：

```text
[Brand/Series] [Core Product Name] [Key Feature] [Color/Size/Qty] for [Use Case]
```

### B. 产品卖点

输出 5～8 条英文卖点。

每条卖点应该包含：

- 买家能理解的好处；
- 产品本身的特性；
- 使用场景；
- 避免夸大功效。

### C. 产品详情描述

应包含：

- 产品介绍；
- 适用人群；
- 使用方式；
- 注意事项；
- 包装清单；
- 售后提醒；
- 储存方式。

### D. SKU 规格命名

需要把供应商 SKU 转成消费者能理解的名称。

例如：

```text
供应商 SKU: HMT-07
优化后 SKU: HMT-07 Rose Gold Cat Eye
```

### E. 平台关键词

输出：

```text
primary_keywords
secondary_keywords
long_tail_keywords
forbidden_or_risky_keywords
```

### F. 风险提示

包括：

- 信息缺失；
- 规格不明确；
- SKU 图不匹配；
- 图片文字无法识别；
- 可能违规词；
- 功效表达风险；
- 定价需要人工确认。

---

# 子工作流 3：电商图片生成与图床上传工作流

## 7.1 目标

根据供应商图片和产品信息，生成更适合菲律宾市场的电商图片，并上传到稳定图床，返回可用于 ERP 的图片 URL。

## 7.2 输入

```text
raw_images/
product.optimized.json
image_style_guide.md
```

## 7.3 输出

```text
generated_images/
uploaded_image_urls.json
image_report.md
```

## 7.4 图片类型

建议先支持以下类型：

1. 主图；
2. SKU 图；
3. 详情图；
4. 规格说明图；
5. 使用步骤图；
6. 套装内容图；
7. 对比图；
8. 色卡图。

## 7.5 图片处理原则

### 第一阶段：不强行生成全新图片

优先策略：

1. 原图清洗；
2. 中文转英文；
3. 重新排版；
4. 尺寸裁剪；
5. 添加英文卖点；
6. 背景优化；
7. 品牌风格统一。

不建议一开始就让 AI 完全重画产品图，因为容易出现：

- 产品形状变形；
- 颜色不准确；
- 包装文字错误；
- SKU 对不上；
- 买家收到货后产生落差。

### 第二阶段：AI 辅助生成

可用于：

- 背景图；
- 氛围图；
- 使用场景图；
- 图标；
- 装饰元素；
- 详情页结构图。

但产品主体必须尽量保真。

## 7.6 图床要求

稳定图床应该满足：

- URL 长期可访问；
- 支持批量上传；
- 支持 API；
- 支持目录管理；
- 支持删除或覆盖；
- 支持 CDN；
- 最好能绑定自己的域名；
- 上传后返回直链；
- 图片不能被压缩到影响展示。

## 7.7 推荐图床方案

优先建议：

```text
Cloudflare R2 + 自定义域名 + Worker/脚本上传
```

原因：

- 成本低；
- 可控性强；
- 适合批量图片；
- 可配合脚本自动上传；
- 后续可以和内部系统打通；
- 不依赖第三方免费图床稳定性。

## 7.8 图片 URL 命名规范

建议：

```text
/products/{platform}/{date}/{product_code}/{image_type}_{index}.jpg
```

示例：

```text
/products/shopee-ph/2026-06-15/HMT-CAT-EYE/main_01.jpg
/products/shopee-ph/2026-06-15/HMT-CAT-EYE/detail_01.jpg
/products/shopee-ph/2026-06-15/HMT-CAT-EYE/sku_HMT07.jpg
```

---

# 子工作流 4：产品定价工作流

## 8.1 目标

根据供应商成本、汇率、平台成本、物流成本、利润要求，生成适合菲律宾市场的定价建议。

## 8.2 输入

```text
product.raw.json
product.optimized.json
pricing_config.json
```

## 8.3 输出

```text
product.pricing.json
pricing_report.md
```

## 8.4 定价配置

建议把定价公式写成配置文件，不要写死在 AI 提示词里。

示例：

```json
{
  "currency": {
    "rmb_to_php": 8.2
  },
  "platform": {
    "net_receive_rate": 0.70,
    "fixed_cost_php": 5
  },
  "pricing": {
    "base_multiplier": 2.5,
    "min_margin_php": 20,
    "rounding_rule": "end_with_9"
  },
  "campaign": {
    "discount_price_ratio": 0.85,
    "bundle_price_ratio": 0.90
  }
}
```

## 8.5 定价输出

每个 SKU 输出：

```json
{
  "sku": "HMT-07",
  "rmb_cost": 5.2,
  "estimated_php_cost": 42.64,
  "suggested_original_price": 109,
  "suggested_sale_price": 89,
  "campaign_price": 79,
  "estimated_net_receive": 57.3,
  "estimated_margin": 14.66,
  "margin_warning": true
}
```

## 8.6 定价策略

需要支持：

- 普通单品定价；
- 多 SKU 定价；
- 套装定价；
- 引流款定价；
- 利润款定价；
- 活动价；
- Shopee / TikTok / Lazada 分平台定价；
- 高客单产品低倍率策略；
- 低客单产品最低利润保护；
- 尾数定价，如 49 / 59 / 69 / 99。

## 8.7 AI 在定价中的角色

AI 不应该直接“拍脑袋定价”。

AI 适合做：

- 判断产品定位；
- 判断是否适合引流；
- 判断是否适合套装；
- 提醒风险；
- 解释定价结果。

公式计算必须由脚本完成。

---

# 子工作流 5：BigSeller ERP 模板化上传工作流

## 9.1 目标

根据 BigSeller 创建产品模板，把前面生成的产品信息、图片 URL、价格、SKU 等内容填入模板，生成可直接导入 ERP 的表格。

## 9.2 输入

```text
product.optimized.json
uploaded_image_urls.json
product.pricing.json
bigseller_template.xlsx
bigseller_mapping.yaml
```

## 9.3 输出

```text
bigseller_product_upload.xlsx
erp_upload_report.md
```

## 9.4 字段映射

需要建立一个明确的字段映射文件。

示例：

```yaml
product_title:
  source: product.optimized.title
  target_column: Product Name
  required: true

main_image:
  source: uploaded_image_urls.main[0]
  target_column: Main Image
  required: true

description:
  source: product.optimized.description
  target_column: Description
  required: true

sku_name:
  source: product.optimized.skus[].sku_name
  target_column: SKU Name
  required: true

sale_price:
  source: product.pricing.skus[].suggested_sale_price
  target_column: Price
  required: true
```

## 9.5 ERP 表格生成原则

1. 模板字段不能随意改名；
2. 不确定字段必须留空并提示；
3. 必填字段缺失时不能生成最终表格；
4. SKU 行数必须和图片、价格一一对应；
5. 生成后必须跑校验；
6. 输出一份 `erp_upload_report.md` 告诉用户哪些字段已填、哪些字段需要人工检查。

---

## 10. 推荐 GitHub 项目结构

```text
crossborder-ai-listing-workflow/
  README.md
  PROJECT_GUIDE.md

  /docs
    project_direction.md
    workflow_overview.md
    data_schema.md
    image_style_guide.md
    pricing_rules.md
    erp_mapping_guide.md
    skill_design_guide.md

  /configs
    pricing_config.example.json
    bigseller_mapping.example.yaml
    image_upload_config.example.yaml
    platform_rules.shopee_ph.yaml
    platform_rules.tiktok_ph.yaml
    platform_rules.lazada_ph.yaml

  /inputs
    /sample_1688_link
    /sample_image_zip

  /outputs
    /.gitkeep

  /schemas
    product.raw.schema.json
    product.optimized.schema.json
    product.pricing.schema.json
    uploaded_image_urls.schema.json
    erp_mapping.schema.json

  /workflows
    /01_product_collect
      README.md
      prompt.md
      runbook.md
      test_cases.md

    /02_product_optimize
      README.md
      prompt.md
      runbook.md
      test_cases.md

    /03_image_generate_upload
      README.md
      prompt.md
      runbook.md
      test_cases.md

    /04_pricing
      README.md
      prompt.md
      runbook.md
      test_cases.md

    /05_bigseller_template_export
      README.md
      prompt.md
      runbook.md
      test_cases.md

  /skills
    /product_collect_skill
      SKILL.md

    /product_optimize_skill
      SKILL.md

    /image_upload_skill
      SKILL.md

    /pricing_skill
      SKILL.md

    /bigseller_export_skill
      SKILL.md

  /scripts
    collect_1688.py
    classify_images.py
    upload_to_r2.py
    calculate_pricing.py
    generate_bigseller_excel.py
    validate_output.py

  /tests
    /fixtures
    test_pricing.py
    test_erp_mapping.py
    test_image_urls.py
    test_sku_mapping.py

  /templates
    bigseller_template.xlsx
    product_review_template.md
    erp_upload_report_template.md
```

---

## 11. 数据流设计

建议所有子工作流都围绕统一的中间数据文件运行。

```text
1688 link / image zip
  ↓
product.raw.json
  ↓
product.optimized.json
  ↓
generated_images + uploaded_image_urls.json
  ↓
product.pricing.json
  ↓
bigseller_product_upload.xlsx
```

不要让每个 Agent 自己随意决定输出格式。

必须规定：

- 输入文件名；
- 输出文件名；
- JSON Schema；
- 校验规则；
- 错误报告格式。

---

## 12. 每个子工作流的标准格式

每个 workflow 文件夹都应该包含：

```text
README.md
prompt.md
runbook.md
test_cases.md
```

### 12.1 README.md

说明这个子工作流的作用。

### 12.2 prompt.md

给 AI / Agent 使用的提示词。

### 12.3 runbook.md

给 Codex / Hermes / OpenClaw 使用的执行步骤。

### 12.4 test_cases.md

用于验证这个工作流是否跑通。

---

## 13. Skill 设计建议

这个项目最终可以落地成 Skills，但不要一开始就只做 Skills。

更好的顺序是：

```text
规则文档
  ↓
脚本
  ↓
测试用例
  ↓
单个 Skill
  ↓
多个 Skill 串联
  ↓
Agent 自动调度
```

原因：

- Skill 适合封装稳定能力；
- 但早期需求还在变化，直接写 Skill 容易返工；
- 脚本和数据结构稳定后，再封装成 Skill 更可靠。

---

## 14. Codex / Hermes / Agent 的推荐分工

### 14.1 Codex 适合做什么

Codex 适合：

- 写脚本；
- 改代码；
- 生成 Excel；
- 写 JSON Schema；
- 写测试；
- 修复报错；
- 整理项目结构；
- 把稳定流程封装成 Skill。

Codex 不适合一开始就自由发挥业务规则。

应该给 Codex 明确：

- 输入是什么；
- 输出是什么；
- 文件放哪里；
- 成功标准是什么；
- 不允许改什么；
- 怎么测试。

### 14.2 Hermes 适合做什么

Hermes 更适合：

- 规划工作流；
- 拆解 PRD；
- 审核流程漏洞；
- 审核提示词；
- 设计验收标准；
- 判断工作流是否适合 Skill 化；
- 给 Codex 派发任务。

### 14.3 便宜模型适合做什么

便宜模型适合：

- 标题初稿；
- 卖点初稿；
- 图片分类初稿；
- 翻译初稿；
- 批量 SKU 命名；
- 格式转换。

但必须有：

- Schema 校验；
- 规则校验；
- 抽样人工复核；
- 强模型复核机制。

### 14.4 脚本适合做什么

脚本负责所有确定性任务：

- 解压文件；
- 图片重命名；
- 图片上传；
- 价格计算；
- Excel 生成；
- 字段映射；
- JSON 校验；
- 错误报告。

### 14.5 Agent 适合做什么

Agent 负责调度，而不是替代所有程序。

Agent 应该做：

- 判断用户输入是哪种类型；
- 选择要跑哪个子工作流；
- 调用脚本；
- 调用 AI；
- 检查输出；
- 报告异常；
- 询问人工补充信息。

---

## 15. 是否应该做成 Skills？

结论：

> 最终应该做成 Skills，但不要把所有东西做成一个大 Skill。

建议拆成多个小 Skill：

```text
1688 产品资料采集 Skill
产品信息菲律宾市场优化 Skill
电商图片处理与图床上传 Skill
跨境电商定价 Skill
BigSeller ERP 表格生成 Skill
产品上架全流程调度 Skill
```

其中前 5 个是基础 Skill，第 6 个是调度 Skill。

---

## 16. 为什么不要做成一个大 Skill？

如果做成一个大 Skill，会出现：

1. 难调试；
2. 难复用；
3. 某一步失败导致全流程失败；
4. 很难判断错在哪里；
5. 不方便替换模型；
6. 不方便单独优化图片或定价；
7. 不方便分配给不同 Agent。

更好的方式是：

```text
小 Skill + 标准数据文件 + 调度器
```

---

## 17. 最小可行版本 MVP

第一阶段不要做太大。

建议 MVP 只跑通一个品类、一个平台、一个模板。

### MVP 目标

```text
输入：一个 1688 产品链接或一组产品图片
输出：
1. product.raw.json
2. product.optimized.json
3. uploaded_image_urls.json
4. product.pricing.json
5. bigseller_product_upload.xlsx
6. product_review.md
```

### MVP 范围

- 品类：美甲单品；
- 平台：Shopee PH；
- ERP：BigSeller 创建产品模板；
- 图片：先上传原图或简单处理图，不追求全自动美工；
- 定价：使用固定公式；
- SKU：先支持普通多规格 SKU；
- 语言：英文；
- 人工复核：必须保留。

---

## 18. MVP 不做的事情

第一阶段暂时不做：

- 自动登录 BigSeller；
- 自动点击 ERP 页面发布；
- 全平台同步；
- 完全自动 AI 重绘产品图；
- 多店铺差异化发布；
- 广告标题自动生成；
- 视频生成；
- 评论分析；
- 竞品实时抓取；
- 库存自动同步；
- 自动采购判断。

这些可以作为第二阶段、第三阶段扩展。

---

## 19. 推荐开发路线

### 第 1 步：整理 BigSeller 模板

目标：

- 上传 BigSeller 创建产品模板；
- 分析所有字段；
- 标记必填字段；
- 标记可选字段；
- 标记 SKU 相关字段；
- 建立 `bigseller_mapping.yaml`。

交付物：

```text
docs/erp_mapping_guide.md
configs/bigseller_mapping.example.yaml
schemas/erp_mapping.schema.json
```

### 第 2 步：设计统一产品数据结构

目标：

- 定义 `product.raw.json`；
- 定义 `product.optimized.json`；
- 定义 `product.pricing.json`；
- 定义 `uploaded_image_urls.json`。

交付物：

```text
docs/data_schema.md
schemas/*.schema.json
```

### 第 3 步：先做模板生成脚本

目标：

先不管 AI，先用一份手写 JSON 生成 BigSeller 表格。

原因：

这是整个系统最终落地的关键出口。

交付物：

```text
scripts/generate_bigseller_excel.py
tests/test_erp_mapping.py
```

### 第 4 步：做定价脚本

目标：

用固定公式生成价格结果。

交付物：

```text
scripts/calculate_pricing.py
configs/pricing_config.example.json
tests/test_pricing.py
```

### 第 5 步：做产品信息优化 Prompt

目标：

输入原始产品资料，输出标准 JSON。

交付物：

```text
workflows/02_product_optimize/prompt.md
schemas/product.optimized.schema.json
tests/fixtures/product_raw_sample.json
```

### 第 6 步：做图片上传脚本

目标：

把本地图片上传到稳定图床，返回 URL JSON。

交付物：

```text
scripts/upload_to_r2.py
configs/image_upload_config.example.yaml
tests/test_image_urls.py
```

### 第 7 步：做图片处理工作流

目标：

先实现图片分类、重命名、尺寸检查。

交付物：

```text
scripts/classify_images.py
workflows/03_image_generate_upload/runbook.md
```

### 第 8 步：做 1688 采集工作流

目标：

抓取或半自动提取 1688 商品资料。

交付物：

```text
scripts/collect_1688.py
workflows/01_product_collect/runbook.md
```

### 第 9 步：串联成完整流水线

目标：

一个命令跑完整流程。

示例：

```bash
python scripts/run_pipeline.py --input inputs/sample_1688_link
```

输出：

```text
outputs/{product_code}/bigseller_product_upload.xlsx
```

### 第 10 步：封装成 Skills

等前面稳定后，再封装：

```text
skills/product_collect_skill/SKILL.md
skills/product_optimize_skill/SKILL.md
skills/image_upload_skill/SKILL.md
skills/pricing_skill/SKILL.md
skills/bigseller_export_skill/SKILL.md
```

---

## 20. 验收标准

一个子工作流是否合格，不看它“看起来很智能”，而看它是否满足以下标准。

### 20.1 产品采集合格标准

- 能读取输入；
- 能保存原始图片；
- 能生成 `product.raw.json`；
- 失败时有日志；
- 不会覆盖原始资料；
- 能说明哪些字段没采集到。

### 20.2 产品优化合格标准

- 输出符合 JSON Schema；
- 英文标题自然；
- SKU 命名清晰；
- 卖点不夸大；
- 描述能直接用于菲律宾市场；
- 风险提示明确。

### 20.3 图片工作流合格标准

- 图片分类正确；
- 图片命名规范；
- 上传后 URL 可访问；
- URL 能回填到 JSON；
- 图片和 SKU 对应关系不乱；
- 失败图片能被记录。

### 20.4 定价工作流合格标准

- 公式可配置；
- 每个 SKU 都有价格；
- 低利润 SKU 有警告；
- 活动价不能低于最低利润线；
- 输出报告能解释价格来源。

### 20.5 ERP 表格合格标准

- 能打开；
- 字段没有错位；
- 必填字段完整；
- SKU 行数正确；
- 图片 URL 正确；
- 可被 BigSeller 识别；
- 生成前后有校验报告。

---

## 21. 风险清单

### 21.1 业务风险

- AI 误判产品用途；
- 平台标题违规；
- 功效词夸大；
- SKU 名称和图片不一致；
- 价格过低导致亏损；
- 图片和实物差距过大；
- 供应商页面信息不准确。

### 21.2 技术风险

- 1688 反爬；
- 图片下载失败；
- 图床上传失败；
- ERP 模板字段变化；
- Excel 格式不兼容；
- Agent 中途失败；
- AI 输出不符合 JSON；
- 多 SKU 映射混乱。

### 21.3 管理风险

- 工作流太大导致难维护；
- 没有测试用例；
- 没有版本管理；
- 没有人工复核；
- 没有日志；
- 没有失败回滚；
- Agent 自己乱改规则。

---

## 22. 防错机制

必须加入以下机制：

1. 所有输出都保存中间文件；
2. 所有 AI 输出必须过 JSON Schema；
3. 所有图片 URL 必须做访问测试；
4. 所有价格必须由脚本计算；
5. 所有 ERP 字段必须做必填校验；
6. 所有 SKU 必须做唯一性检查；
7. 所有异常必须写入 `warnings.md`；
8. 最终表格生成前必须生成 `product_review.md`；
9. 不允许 Agent 静默失败；
10. 不允许 Agent 私自修改配置规则。

---

## 23. 给 Codex 的第一条项目指令建议

可以这样开始：

```text
你现在要创建一个 GitHub 项目：crossborder-ai-listing-workflow。

项目目标：
开发一套跨境电商 AI 产品自动上架工作流。用户提供 1688 产品链接或产品图片压缩包后，系统最终输出适合菲律宾市场的产品信息、图片 URL、定价结果，以及可导入 BigSeller ERP 的创建产品表格。

重要原则：
1. 不要一开始做 ERP 自动登录和自动点击发布；
2. 第一阶段只做模板化表格输出；
3. 所有子工作流必须有明确输入、输出、中间文件和校验规则；
4. AI 负责理解和生成，脚本负责确定性处理；
5. 不要把所有功能写成一个大脚本；
6. 先创建项目结构和文档，不要急着实现所有功能；
7. 所有输出格式必须可测试、可复核、可扩展。

请先完成：
1. 创建推荐目录结构；
2. 创建 README.md；
3. 创建 docs/project_direction.md；
4. 创建 docs/data_schema.md 初稿；
5. 创建 configs/pricing_config.example.json；
6. 创建 configs/bigseller_mapping.example.yaml；
7. 创建 workflows/01_product_collect 到 workflows/05_bigseller_template_export 的 README.md；
8. 不要写复杂爬虫，不要做真实上传，不要调用真实 API；
9. 提交一次 commit，commit message 为：init project structure for ai listing workflow。
```

---

## 24. 给 Hermes 的第一条规划指令建议

```text
你是这个项目的产品架构和流程审阅 Agent。

项目目标：
我要开发一套跨境电商 AI 产品自动上架工作流。用户提供 1688 产品链接或产品图片压缩包后，最终输出适合菲律宾市场的产品资料、图片 URL、定价结果，以及 BigSeller ERP 可导入表格。

请你审阅当前项目方向，重点检查：
1. 子工作流拆分是否合理；
2. 每个子工作流的输入输出是否清晰；
3. 是否适合未来封装成 Skills；
4. 是否存在过度自动化风险；
5. 哪些步骤应该由脚本完成，哪些步骤应该由 AI 完成；
6. MVP 应该先做哪一段；
7. BigSeller 模板化上传是否应该作为第一优先级；
8. 有哪些必须提前定义的数据结构和测试用例。

请输出：
1. 项目流程审阅报告；
2. MVP 开发顺序建议；
3. 风险清单；
4. 每个子工作流的验收标准；
5. 给 Codex 的可执行任务拆分。
```

---

## 25. 最推荐的落地方式

最终建议采用：

```text
GitHub 项目
  +
标准数据 Schema
  +
Python/Node 脚本
  +
小型 Skills
  +
Hermes 规划审阅
  +
Codex 代码实现
  +
人工复核
```

不要采用：

```text
一个超大 Prompt 直接让 Agent 全自动跑完
```

原因：

- 不稳定；
- 不可复查；
- 不可测试；
- 不可维护；
- 出错后很难定位。

---

## 26. 推荐最终形态

未来成熟后，用户操作可以简化成：

```bash
ai-listing create --from-1688 "https://detail.1688.com/xxx"
```

或者：

```bash
ai-listing create --from-zip "./new_product_images.zip"
```

系统自动输出：

```text
outputs/2026-06-15-HMT-CAT-EYE/
  product_review.md
  product.raw.json
  product.optimized.json
  product.pricing.json
  uploaded_image_urls.json
  bigseller_product_upload.xlsx
  warnings.md
```

用户只需要打开：

```text
product_review.md
bigseller_product_upload.xlsx
```

确认后导入 BigSeller。

---

## 27. 当前最优先行动

建议下一步不要直接开发全流程，而是先做这 3 件事：

### 第一优先级：解析 BigSeller 模板

因为 ERP 模板是最终出口，出口不清楚，前面所有 AI 生成都可能白做。

### 第二优先级：定义标准 JSON Schema

因为所有子工作流都要围绕这些数据结构衔接。

### 第三优先级：用假数据生成一份 BigSeller 表格

先证明“从结构化数据 → ERP 表格”这条路能跑通。

只要这三步跑通，后面的 AI 优化、图片上传、1688 采集都可以逐步接上。

---

## 28. 一句话总结

这个项目应该被设计成：

> 以 BigSeller ERP 模板为最终出口，以标准 JSON 数据为中间层，以脚本保证稳定性，以 AI 完成产品理解和本地化优化，以 Skills 封装成熟能力，以 Agent 负责调度和异常处理的跨境电商产品自动上架流水线。
