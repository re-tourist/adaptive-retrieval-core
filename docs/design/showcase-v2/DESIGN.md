# ARC Showcase V2 视觉审查

基线为 [PR #3](https://github.com/re-tourist/adaptive-retrieval-core/pull/3) 的 `ca3b21a`。本目录是独立设计原型，供选定视觉和交互方向。

| 设计稿 | 尺寸 | 审查重点 |
| --- | --- | --- |
| [Search Home](search-home.png) | 1440 × 900 | 首屏能否从一句自然语言查询扫到商品图、名称和两个属性 |
| [Compare Strategies](compare.png) | 1440 × 900 | 能否读出同一商品在不同策略中的名次变化 |
| [GitHub README Hero](readme-hero.png) | 1280 × 980 | 能否快速理解 ARC 的用途并找到 Demo 预览和 Quickstart |
| [移动端搜索](search-home-mobile.png) · [移动端对比](compare-mobile.png) | 390 × 980 · 390 × 1150 | 双列商品图、完整查询、成对名次与诊断入口 |

## 为什么这样排

PR #3 把策略、Top K、时延和 Trace 放在与结果同等醒目的位置。这对排障有价值，但第一次访问时，读者需要先解释控制项，再判断搜索找到了什么。当前 README 的主图展示的是技术笔记上的策略比较，首屏缺少直观的搜索结果。

考虑了两种布局。**搜索结果优先**采用居中查询区、四张商品卡和独立对比视图。**策略对比优先**以固定双列打开首页，读者能立刻看到两种策略，但两列重复内容会挤占图片区，也容易让人误以为基础安装包含模型。选择第一种。搜索和对比共享查询、照片、字号与色板，切换保留查询。对比按名次对齐，每个 Hybrid 商品旁显示相对 Keyword 的位移。新出现指商品未进入当前 Keyword 展示深度，位移仅描述顺序。移动端仍保留两列，缩略图与位移并列，名称另起一行。

README 使用 GitHub 风格预览壳。标题下用一句话交代 ARC 的用途与四种策略，紧接三个入口和 Search Home 画面。正式采用时，这部分可用普通 Markdown 图片和链接表达。

## 参考研究

- **Meilisearch Ecommerce**。浏览器中检查了顶部搜索、左侧筛选、商品图片网格，并查看搜索组件。ARC 采用图像先于商品属性的顺序，小样例只保留必要控件。[案例索引](https://github.com/meilisearch/demos) · [运行演示](https://ecommerce.meilisearch.com/) · [搜索组件](https://github.com/meilisearch/ecommerce-demo/blob/main/components/organisms/MeiliSearchBar.vue)
- **Typesense Ecommerce**。浏览器中检查了带商品图、名称、长描述和 Find Similar 入口的结果网格，对照了搜索和商品模板。ARC 让每张卡只保留两项识别属性，将技术信息放到结果以外。[运行演示](https://ecommerce-store.typesense.org/) · [搜索与结果模板](https://github.com/typesense/showcase-ecommerce-store/blob/master/src/app.js)
- **Qdrant Startup Search**。浏览器中从 Hybrid 切换到 Keyword，观察同一输入区如何复用查询和示例词。ARC 沿用查询上下文，并为审查排序增加同名次并排视图。[运行演示](https://demo.qdrant.tech/) · [仓库与模式说明](https://github.com/qdrant/qdrant_demo)

## 数据、素材与能力边界

- 四件商品、属性、三条示例查询和两套排序由本原型编写。页面显式标为 illustrative catalog 和 design prototype。自定义查询若超出样例范围，会显示无 fixture 状态。排名用于说明 UI，来源为 [prototype.js](prototype.js)。
- [商品图](assets/lamp-sheet.png)由内置 OpenAI imagegen 生成，是一张本地 2×2 接触表。四格分别对应左上 Luma、右上 Studio、左下 Cove、右下 Vale。原型使用本地素材，无第三方图片、品牌或热链接。WANDS 的在线适配器读取商品文本字段，原型的合成图与 WANDS 无关。
- 当前零配置 CPU Demo 用 BM25 检索 ARC 技术笔记。设计稿的商品目录是未来可选示例。Hybrid 需要已配置的 embedding 模型和匹配索引，对比画面标为 model-enabled preview。折叠诊断使用解释性文案，无模拟时延或分数。

生成素材的提示词（内置 imagegen）：

> Use case: product-mockup. Create one landscape 3:2 contact sheet for a fictional premium homewares search prototype. Four distinct catalog photographs arranged in a perfectly edge-to-edge 2×2 grid, the vertical and horizontal seams exactly at the midlines, with NO margins, gutters, frames, labels, text, watermarks or logos. Each tile shows a single entire small lamp, including base, centered with generous breathing room on all sides. Nothing crosses seams. Same editorial studio camera at a gentle three-quarter angle, clean soft shadows, muted warm neutrals, quiet modern Scandinavian retail catalog. Top left: compact aged-brass adjustable desk lamp with a curved brass arm and small conical all-metal brass shade on pale cream plaster. Top right: short matte charcoal adjustable task lamp with a flared black metal shade and round base on desaturated warm gray plaster. Bottom left: compact reading table lamp with a small gently tapered ivory linen shade and a brushed brass stem, on light warm stone plaster. Bottom right: low mushroom bedside lamp, rounded amber glass dome over a dark walnut cylinder, on warm taupe plaster. Distinct silhouettes and believable materials, no wires clutter, no plants, no props, no lifestyle objects. Product center of mass in the center of each cell. Harmonized photography appropriate for a quiet digital showroom.

## 复现与检查

本地打开 [index.html](index.html) 可交互查看两种状态，另有 [README Hero 源稿](readme-hero.html)。复现截图时，用独立用户目录启动 Edge 或 Chrome，再用 Node.js 20 运行捕获脚本。Node.js 22 及以上可省略 WebSocket 实验标记。

```sh
msedge.exe --headless=new --remote-debugging-port=9226 --user-data-dir="<temporary-directory>" about:blank
node --experimental-websocket docs/design/showcase-v2/render.mjs
```

Edge 实际渲染五张 PNG，检查了图片解码、截图尺寸、横向溢出和裁切。交互检查覆盖示例查询、同查询切换、排名变化、无 fixture 提示和折叠诊断。人工查看桌面与 390 px 终稿。首轮将长示例词收为短标签，缩小 README 内的截图框，确保商品卡片进入预览首屏。

## 验收后再实施

优先复用 `/playground/config` 和 `/search`。用真实快照判断策略可用性，仅有 BM25 时将对比入口置为不可用并说明配置要求。若批准商品方向，将原创商品与素材作为独立可选目录，按稳定商品 ID 补齐卡片展示信息。两个策略共享查询和快照约束，从实际返回的名次按 ID 算位移，按需展开真实 Trace。README 使用实施后重拍的图，完整技术设计、部署与实验报告由文档入口承载。
