// 先机 · Tailwind 主题 —— 对齐 invest-cue 参考站设计语言
// 调色板用参考站 CSS 变量原值；字体改 Noto Serif SC / Noto Sans SC / JetBrains Mono。
// 须在 tailwind Play CDN 之后引入；CDN 的 MutationObserver 会给 JS 动态插入的卡片补样式。
tailwind.config = {
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // —— 主色：朱砂红(高置信 / 激活态) ——
        "primary": "#c8372d",            // --vermilion
        "primary-container": "#a51d18",
        "on-primary": "#ffffff",
        "on-primary-container": "#fbedeb",
        "primary-soft": "#fbedeb",       // --vermilion-soft 状态胶囊底
        "cinnabar": "#c8372d",
        // —— 黄铜金(待验证) ——
        "brass": "#b07d2b",              // --brass
        "brass-soft": "#f7efdf",         // --brass-soft
        // —— 玉绿(印证 / 已认证) ——
        "jade": "#1e6b5c",               // --jade
        "jade-soft": "#e2efec",          // --jade-soft
        "secondary": "#1e6b5c",
        "secondary-container": "#e2efec",
        "on-secondary-container": "#1e6b5c",
        // —— 中性 ——
        "ink": "#11161c",                // --ink 深色文字 / 暗色 splash
        "rock": "#5b6573",               // --stone 次要文字
        "stone": "#5b6573",
        "paper": "#f2f4f7",              // --paper 页面底
        "background": "#f2f4f7",
        "on-background": "#11161c",
        "surface": "#ffffff",            // 白卡(浮在 paper 上)
        "surface-bright": "#ffffff",
        "surface-container-lowest": "#ffffff",
        "surface-container-low": "#f7f8fa",
        "surface-container": "#eef0f3",
        "surface-container-high": "#e8ebf0",
        "surface-container-highest": "#e2e6eb",
        "surface-dim": "#e2e6eb",
        "surface-variant": "#eef0f3",    // 进度条/竖条轨道底
        "on-surface": "#11161c",
        "on-surface-variant": "#5b6573",
        "outline": "#c2c8d0",
        "outline-variant": "#e2e6eb",    // --hairline
        "error": "#ba1a1a",
        "porcelain": "#f2f4f7",
      },
      borderRadius: { DEFAULT: "0.25rem", lg: "0.5rem", xl: "0.875rem", "2xl": "1rem", full: "9999px" },
      spacing: {
        gutter: "16px", xl: "32px", "margin-desktop": "40px", base: "4px",
        xs: "8px", lg: "24px", md: "16px", "margin-mobile": "20px", sm: "12px",
      },
      fontFamily: {
        "headline-sm": ["Noto Serif SC", "serif"],
        "display-lg": ["Noto Serif SC", "serif"],
        "headline-md": ["Noto Serif SC", "serif"],
        "data-mono": ["JetBrains Mono", "monospace"],
        "body-lg": ["Noto Sans SC", "sans-serif"],
        "body-md": ["Noto Sans SC", "sans-serif"],
        "label-caps": ["JetBrains Mono", "monospace"],
      },
      fontSize: {
        "display-lg": ["30px", { lineHeight: "38px", fontWeight: "700" }],
        "headline-md": ["27px", { lineHeight: "34px", fontWeight: "700" }],
        "headline-sm": ["18px", { lineHeight: "26px", fontWeight: "600" }],
        "data-mono": ["13px", { lineHeight: "16px", letterSpacing: "-0.02em", fontWeight: "500" }],
        "body-lg": ["16px", { lineHeight: "24px", fontWeight: "400" }],
        "body-md": ["14px", { lineHeight: "21px", fontWeight: "400" }],
        "label-caps": ["11px", { lineHeight: "14px", letterSpacing: "0.14em", fontWeight: "500" }],
      },
    },
  },
};
