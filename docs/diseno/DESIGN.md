---
name: Autonomous Governance & Settlement Engine
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#43474d'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#73777e'
  outline-variant: '#c3c7ce'
  surface-tint: '#46617c'
  primary: '#000d1b'
  on-primary: '#ffffff'
  primary-container: '#04243c'
  on-primary-container: '#728ca9'
  inverse-primary: '#aec9e8'
  secondary: '#006876'
  on-secondary: '#ffffff'
  secondary-container: '#87ebff'
  on-secondary-container: '#006b79'
  tertiary: '#000c20'
  on-tertiary: '#ffffff'
  tertiary-container: '#062243'
  on-tertiary-container: '#748ab1'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#cfe5ff'
  primary-fixed-dim: '#aec9e8'
  on-primary-fixed: '#001d33'
  on-primary-fixed-variant: '#2e4963'
  secondary-fixed: '#9fefff'
  secondary-fixed-dim: '#6fd5e8'
  on-secondary-fixed: '#001f25'
  on-secondary-fixed-variant: '#004e59'
  tertiary-fixed: '#d5e3ff'
  tertiary-fixed-dim: '#b0c7f1'
  on-tertiary-fixed: '#001b3c'
  on-tertiary-fixed-variant: '#30476a'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  headline-xl:
    fontFamily: Plus Jakarta Sans
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.025em
  headline-xl-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 30px
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.005em
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
    letterSpacing: -0.011em
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: -0.006em
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: 0em
  label-md:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '600'
    lineHeight: 18px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.025em
  mono-data:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
    letterSpacing: -0.02em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-mobile: 0.75rem
  margin: 2rem
  margin-mobile: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

This design system embodies high-trust enterprise fintech precision tailored for autonomous AI agents handling real-time capital allocation and payment workflows. The visual identity reflects the rigorous engineering standards of top-tier infrastructure startups: clean, high-legibility typographic hierarchies, strictly structured data grids, razor-sharp geometric alignment, and restrained, intentional accents.

The design movement combines **Modern Technical Minimalism** with **Instrument-Grade UI**:
- **Aesthetic Tenets:** Dense visual hierarchy without clutter, razor-thin borders (1px) replacing bulky shadows, subtle monochromatic contrast, and decisive semantic color codes for autonomous system state shifts.
- **Target Audience:** CFOs, VP of Treasury, Chief Compliance Officers, and Engineering leads orchestrating agentic financial protocols.
- **Emotional Response:** Uncompromising reliability, operational predictability, total auditability, and immediate clarity during automated decision-making runs.

## Colors

The palette establishes an immediate institutional posture through foundational deep navies, balanced with high-velocity teal accents representing real-time machine actions.

### Core Architecture
- **Primary Brand (`#04243C`):** Used for primary commands, critical navigation anchors, authoritative headlines, and highest-priority interactive surfaces.
- **Primary Accent (`#2B9CAE`):** Represents AI activity, active telemetry, processing states, and high-frequency automated triggers.
- **Secondary Accent (`#1D3557`):** Utilized for structural framing, table headers, deep secondary buttons, and contextual data callouts.
- **Neutral Canvas (`#F8FAFC`):** The structural app canvas background, providing calm, low-glare visual grounding.
- **Surface Elevation (`#FFFFFF`):** High-contrast pure white reserved for cards, data grids, modal dialogs, and interactive workflow canvas elements.
- **Hairline Dividers (`#E2E8F0`):** Precise boundary delineation between columns, rows, and toolbars without heavy drop shadows.

### Semantic Machine State Tokens
Autonomous payment statuses require instantaneous visual recognition:
- **AUTO_APPROVED:** Foreground `#10B981` | Background `#ECFDF5` | Border `#A7F3D0`
- **SCALED_TO_HUMAN:** Foreground `#F59E0B` | Background `#FFFBEB` | Border `#FDE68A`
- **REJECTED / BLOCKED:** Foreground `#EF4444` | Background `#FEF2F2` | Border `#FECACA`
- **INSPECTION_PENDING:** Foreground `#6366F1` | Background `#EEF2FF` | Border `#C7D2FE`

## Typography

The typographic hierarchy couples **Plus Jakarta Sans** for structural headlines with **Inter** for dense transactional UI layouts. All monetary values, hash logs, transaction IDs, and agent API payloads utilize **JetBrains Mono** to guarantee tabular numerical alignment across high-throughput ledgers.

### Application Rules
- **Numerical Alignment:** Always pair numerical data tables with `font-feature-settings: "tnum" on, "zero" on`.
- **Vertical Rhythm:** Strict adherence to 4px baseline alignment ensures high visual density without eye fatigue.
- **Section Headers:** Use uppercase micro-labels (`label-sm`) with tracking for table headers, metadata descriptors, and workflow states.

## Layout & Spacing

The structural layout uses a responsive 12-column fluid grid system pinned to a maximum canvas constraint of 1440px for desktop workflows, accommodating persistent telemetry sidebars and multi-pane transaction inspection trays.

### Form-Factor Breakpoints
- **Desktop (≥ 1280px):** 12 columns, 24px (`1.5rem`) gutters, 32px (`2rem`) outer margins. Supports 3-pane execution views (Agent List, Transaction Queue, Audit Inspector).
- **Tablet (768px – 1279px):** 8 columns, 16px (`1rem`) gutters, 24px (`1.5rem`) margins. Secondary agent inspectors collapse into off-canvas right drawers.
- **Mobile (< 768px):** 4 columns, 12px (`0.75rem`) gutters, 16px (`1rem`) margins. Single-stream stacked cards; secondary data sheets expand into bottom modal drawers.

## Elevation & Depth

To preserve the sharp, engineered aesthetic favored by YC-caliber enterprise platforms, visual depth relies on **1px crisp outlines, tonal surface shifts, and minimal micro-shadows**. Heavy diffuse blurs and multi-layered skeuomorphic shadows are deliberately omitted.

### Depth Hierarchy
- **Level 0 (Canvas Base):** Background `#F8FAFC`, non-elevated, full bleed.
- **Level 1 (Data Cards & Ledgers):** Pure White `#FFFFFF`, border `1px solid #E2E8F0`, shadow `0 1px 2px 0 rgba(4, 36, 60, 0.04)`.
- **Level 2 (Hovered Records & Floating Toolbars):** Pure White `#FFFFFF`, border `1px solid #CBD5E1`, shadow `0 4px 6px -1px rgba(4, 36, 60, 0.08), 0 2px 4px -2px rgba(4, 36, 60, 0.04)`.
- **Level 3 (Modal Overlays & Escalation Drawers):** Pure White `#FFFFFF`, border `1px solid #CBD5E1`, shadow `0 20px 25px -5px rgba(4, 36, 60, 0.12), 0 8px 10px -6px rgba(4, 36, 60, 0.06)`. Backdrop overlay uses `#04243C` at 35% opacity with `backdrop-filter: blur(4px)`.

## Shapes

The design system enforces a disciplined **Soft (`roundedness: 1`)** geometry. Radii are kept small and deliberate (4px default, 6px for interactive cards, 8px for modal frames), preventing soft or consumerized visuals in favor of a crisp, institutional fintech apparatus. Fully rounded pills are strictly limited to agent execution badges and status indicators.

## Components

### Buttons
- **Primary Action (Execute / Authorize):** Background `#04243C`, text `#FFFFFF`, border `1px solid transparent`, corner radius 4px. Hover: background `#1D3557`. Active: transform scale 0.99.
- **Agent Action (AI Trigger / Re-run Rule):** Background `#2B9CAE`, text `#FFFFFF`, border `1px solid transparent`. Hover: background `#238291`.
- **Secondary (Inspect / Export):** Background `#FFFFFF`, text `#04243C`, border `1px solid #E2E8F0`. Hover: background `#F8FAFC`, border `#CBD5E1`.
- **Critical Reject:** Background `#FEF2F2`, text `#EF4444`, border `1px solid #FECACA`. Hover: background `#FEE2E2`.

### Status Badges & Chips
- Embedded pill containers (`border-radius: 9999px`) with padding `2px 8px`. Typography: `label-sm` font weight 600.
- Must include a 6px solid circular indicator dot adjacent to the label.
  - **AUTO_APPROVED:** Green pulse dot `#10B981`, surface `#ECFDF5`, text `#065F46`, border `#A7F3D0`.
  - **SCALED_TO_HUMAN:** Amber static dot `#F59E0B`, surface `#FFFBEB`, text `#92400E`, border `#FDE68A`.
  - **REJECTED:** Red static dot `#EF4444`, surface `#FEF2F2`, text `#991B1B`, border `#FECACA`.

### Cards & Ledger Tables
- Cards use `#FFFFFF` background, `1px solid #E2E8F0`, 6px corner radius.
- Table headers use background `#F8FAFC`, border bottom `1px solid #E2E8F0`, typography `label-sm` in `#64748B`.
- Table rows use alternating hover states `#F8FAFC`, height `48px`, border bottom `1px solid #F1F5F9`.

### Input Fields & Controls
- Input boxes use `#FFFFFF`, height `36px`, border `1px solid #CBD5E1`, 4px radius, text `body-md` in `#04243C`.
- Focus state: border `1px solid #2B9CAE`, outline `2px solid rgba(43, 156, 174, 0.20)`.
- Checkboxes use 4px corner radius, `#FFFFFF` with `1px solid #CBD5E1`. Checked state: `#04243C` with crisp white checkmark.

### Domain-Specific Components
- **Agent Decision Inspector Drawer:** Right-pinned sheet (480px width) containing the step-by-step LLM reasoning trail, latency metrics, and API payload traces formatted in `JetBrains Mono`.
- **Confidence Metric Gauge:** Horizontal 4px progress rail showing automated confidence scoring (0-100%) color-coded using the teal-to-green gradient.