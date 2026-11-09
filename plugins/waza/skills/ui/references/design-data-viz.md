# Design Reference: Data Visualization

Load this only when the surface is a dashboard, analytics view, chart-heavy interface, or any number-dense data display. Marketing pages, landing pages, and generic component work do not need it.

## Dashboard defaults

Dashboards are utility surfaces: orient the user, show status, enable action. No hero sections, no marketing copy. Every element must earn its place by answering a question the user has.

- Primary layout: status summary at top, detail below; or sidebar filters + main chart area. The main question must be answerable without expansion; disclose supplementary records, not the answer itself. Check sparse and typical data without padding gaps with filler.
- Whitespace: tighter than marketing pages; users scan, not read. Use generous column spacing, not generous row height.
- Number density: many numbers on screen at once is not a problem. Crowding without alignment is. Use `font-variant-numeric: tabular-nums` for all numeric columns. Right-align numbers. Left-align labels.

## Chart selection

| Use case | Chart type |
|---|---|
| Comparing values across categories | Bar chart (horizontal if labels are long) |
| Trend over time | Line chart; avoid bars for time series with many points |
| Part-whole relationships | Treemap (6+ segments) or stacked bar; pie only for 2-4 segments |
| Distribution | Histogram or box plot; never pie chart |
| Correlation | Scatter plot; do not use line chart |

## Number-dense interfaces

- Subtle row separators: `1px` line at `rgba(0,0,0,0.06)` (light) or `rgba(255,255,255,0.05)` (dark). Alternating row backgrounds only if the table is very wide (12+ columns).
- Column spacing: at least `16px` between adjacent columns; more between logically distinct groups.

## Using a product as a benchmark

When the user references a product for visual benchmark ("make it feel like Grafana" / "similar to Linear analytics"): run the three-property decomposition from direction question 2 in `SKILL.md` with data-visualization-specific properties, not general aesthetic ones. Useful properties: chart color palette (exact values), grid line weight and opacity, axis label size and color, tooltip border-radius and shadow, empty-state treatment. Do not extract "minimal" or "clean" as properties; those are not actionable.
