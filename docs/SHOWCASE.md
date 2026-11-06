# ARC Showcase V2

The local Playground searches 22 fictional products in lighting, storage and textiles. The [catalog source](../src/arc/adapters/datasets/catalog.json) defines stable IDs, titles, two display attributes, searchable descriptions, and image tiles. ARC indexes the titles, attributes and descriptions with the same retrieval adapters used by the harness. The catalog is a separate corpus from SciFact and WANDS.

[Run it locally](QUICKSTART.md) · [V2 design review](https://github.com/re-tourist/adaptive-retrieval-core/pull/4)

## Try the catalog

- **Reading nook** queries “small brass reading lamp”.
- **Blanket storage** queries “woven basket for extra blankets”.
- **Soft textures** queries “soft green throw for a sofa”.

The page requests the first four results for each strategy. Keyword mode omits zero-score candidates in this catalog so an unmatched query can return an empty list. The browser binds photos and attributes to result IDs and uses the API's titles and ranks. In Compare, both strategies receive the same query and depth. “Only here” refers to the other list's returned depth, and a rank change is a difference in position, independent of score scale. [Live search](assets/showcase-v2/search.png) · [Live comparison](assets/showcase-v2/compare.png) · [Mobile search](assets/showcase-v2/search-mobile.png) · [Mobile comparison](assets/showcase-v2/compare-mobile.png)

## Images and provenance

The images are original, unbranded OpenAI imagegen outputs for fictional items. The lighting sheet comes from the [approved design source](https://github.com/re-tourist/adaptive-retrieval-core/blob/be1b2a0009a8f864fffaee923171b7084f0956c2/docs/design/showcase-v2/DESIGN.md#数据素材与能力边界). The two new sheets use the built-in tool and the prompts below. The three 1536 × 1024 sheets are stored as WebP for the packaged UI. Each tile is mapped by zero-based row-major position. WANDS results use text cards.

- [Lighting](../src/arc/entrypoints/playground/assets/lighting.webp), four products.
- [Storage](../src/arc/entrypoints/playground/assets/storage.webp), nine products.
- [Textiles](../src/arc/entrypoints/playground/assets/textiles.webp), nine products.

<details>
<summary>Image generation prompts</summary>

**Storage**

Use case product-mockup. One landscape 3:2 image, perfectly aligned edge-to-edge 3×3 contact sheet of nine independent premium Scandinavian homewares catalog photographs. Equal cells, exact seams at thirds, NO gutters, collage frames, text, labels, logos or watermarks. Each tile contains its one requested distinct item fully visible with breathing room, studio warm beige plaster wall and surface, quiet cream and earthy tones, soft daylight, editorial product photography, mild 3/4 perspective, consistent size, natural material textures. No objects across seams. Treat each cell separately, no extra props. Row order left to right. Row 1: large low oval natural seagrass open basket with handles; tall honey rattan laundry hamper with fitted lid; small rectangular dark walnut catchall tray. Row 2: two nested charcoal grey felt organizer bins; slim blonde oak freestanding three-tier ladder shelf; rectangular light canvas underbed storage box with pull tab and zipped lid. Row 3: stack of two lidded square ash wood boxes; compact dark sage metal wall-mounted three-hook rail isolated on the wall; low white ceramic scalloped catchall bowl.

**Textiles**

Use case product-mockup. One landscape 3:2 image, perfectly aligned edge-to-edge 3×3 contact sheet of nine independent premium Scandinavian homewares catalog photographs. Equal cells, exact seams at thirds, NO gutters, collage frames, text, labels, logos or watermarks. Each tile contains its one requested distinct item fully visible with breathing room, studio warm beige plaster wall and surface, quiet cream and earthy tones, soft daylight, editorial product photography, mild 3/4 perspective, consistent size, natural material textures. No objects across seams. Treat each cell separately, no extra props. Row order left to right. Row 1: folded dusty sage green cotton waffle throw with fringe; folded terracotta chunky knitted wool blanket; folded pale oatmeal linen coverlet with thin charcoal stripes. Row 2: square slate blue velvet decorative cushion upright; square ivory nubby boucle cushion upright; folded cream-and-black geometric woven runner rug. Row 3: two folded pale rust ribbed cotton bath towels; neatly folded warm white translucent linen curtain panel; deep moss green tufted rectangle bath mat flat angled view.

</details>

The screenshots came from live local ARC requests. The README image crops the browser capture to the query and product cards. The comparison captures use the pinned BGE and MiniLM models with the catalog's in-memory FAISS index. Diagnostics show measurements for the individual request. Published quality and latency results come from the separate [V0 acceptance report](ARC-V0-ACCEPTANCE.md).
