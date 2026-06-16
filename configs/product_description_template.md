# 产品描述模板

该模板用于在生成产品描述时，自动附加品牌标准的前缀和后缀。

---

## AI 文本生成约束规则（必须遵守）

在生成产品标题、描述、卖点等所有文本内容时，AI 必须遵守以下规则：

**规则 1 — 禁止年份硬编码**
不得在产品描述中写入具体年份（如 "2025 new"、"2026 latest"）。年份信息会随时间失效，导致产品描述过时。若需强调新品，使用 "Latest"、"New Arrival"、"Upgraded Version" 等不含年份的表述。

**规则 2 — 描述必须与 SKU 变种一致**
产品描述的核心特性必须与当前 SKU 的 `variant_value` 严格对应。
- 若 SKU 为 "Dual Head w/Ball"，描述中必须突出"双头"和"圆球头"特性
- 若 SKU 为 "Flat Head"，描述中必须突出"平头"特性
- 禁止将其他变种的特性写入当前 SKU 的描述中

**规则 3 — 分类 ID 必须基于产品实质类型判断**
不得根据产品名称中的修饰词（如"猫眼"）来决定分类，必须根据产品的实质类型：
- 工具/设备类（磁铁棒、灯、打磨机等）→ `102034` (Manicure Tools & Devices)
- 胶/液体类（甲油胶、底胶、封层等）→ `102029` / `101615`
- 详见 `nail_category_ids.yaml` 中的分类识别规则

**规则 4 — 禁止凭空捏造规格**
描述中的规格参数（尺寸、重量、容量等）必须来自 1688 原始数据或用户确认信息，不得自行估算或填写占位数据。

**规则 5 — 品牌名称规范**
标题必须以 `JUCYEE` 开头，描述正文中品牌相关内容使用 `bomd` 或 `JUCYEE`，不得混用或缩写。

---

## 前缀 (Prefix)

```text
<<All the products in our store are !! ONHAND !! >>
【Fast ship out from Pasay City.】
Normally confirm order today will be ship out tomorrow.

IF you are Nail video creator or nail salon
welcome to contact us, we can provide free samples,
We offer local quality warranty and wholesale prices,
and also social media traffic and skill support.
We can help you with photo retouching and video editing.

If you are a novice manicurist, 
our products are affordable and  high-quality, perfect for starting from novice to professional.

bomd products are suitable for
Home Manicure - Create Your Personal Nail Aesthetics Hobby
Skills training - turn a hobby into your professional skill
Professional Nail Salon - Start Your Nail Beauty Business
```

## 动态内容 (Dynamic Content)

*产品特征、规格和使用方法等由AI提取生成的具体产品信息将放置在此处。*

*生成时须遵守上方"AI 文本生成约束规则"，特别是：禁止年份硬编码、描述须与SKU变种一致。*

## 后缀 (Suffix)

```text
#uv gel
#color gel
#nail gel polish
#soak off uv gel
#uv nail polish
#uvgel
#colorgel
#nailgelpolish
#soakoffuvgel
#uvnailpolish
#bomd
#jucyee
#bomdgelpolish
```
