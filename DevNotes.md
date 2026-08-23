# Development Notes

## 🎨 Visual Makeover & Custom CSS SVGs (Completed - 2026-05-23)
We did a complete branding overhaul to transform the application into a super cute **Pastel Piggy Pink & Gold Coin** theme:
- **Design Tokens (`index.css`)**: Reconfigured primary variables to feature Piggy Pink (`#ff8da1`) and Shiny Gold (`#ffd166`) with soft cream overlays. Programmed a slow, drifting ambient radial gradient animation on the HTML body.
- **Micro-Animations**: Styled bouncy text focus highlights, elastic scaling transitions on buttons on-click, and lift shadows for dashboard piggy bank cards (`.hover-bounce`).
- **Interactive Split-Screen (`Login.tsx`, `Register.tsx`)**: Created a responsive split screen layout for widescreen monitors (collapsing nicely on mobile devices). 
  - **CSS Piggy Animation**: Hand-crafted a pure vector SVG pink piglet illustration that floats gently (`animate-float-piggy`).
  - **Gold Coin Dropper**: Programmed three distinct golden coin SVGs falling into the piggy slot (`animate-coin-1/2/3`) with rotating keyframes and staggered delays.
- **Analytics Theme Alignment (`StatisticsCharts.tsx`)**: Redesigned Recharts tooltip panels to be rounded cards, and set chart colors to match the theme (deposits: gold, expenses: pink, segment categories: soft pastel).

## 🎨 Premium Layout Spacing & Multi-Pane Analytics (Completed - 2026-05-23)
- **Spacious Screen-Centered Layout (`PiggyBankView.tsx`, `Settings.tsx`, `index.css`)**: Solved top-cramping and spacing issues. Replaced top-aligned containers with `.page-layout-container` using generous vertical paddings to balance the pages in the viewport. Formatted "Back to Dashboard" with `.back-to-dashboard-link`, adding roomier `2.25rem` spacing and a micro-interaction hover offset (`translateX(-6px)`).
- **Interactive Pointer-Hover Bridge**: Corrected the gold coin FAB menu disappearing bug. Added a dynamic transparent pseudo-element (`::before` bridge on `.inline-fab-container`) that automatically captures pointer events when hovered, creating a solid bridge between the piglet trigger and the gold coin.
- **Dynamic Single PiggyBank Analytics**: Mounted a three-pane analytics card featuring:
  - An interactive chronological SVG Line Chart showing Running Balance, Income, or Expenses over time, with a togglable Y-axis metric dropdown.
  - A Monthly Summary cash flow Bar Chart.
  - An Expense Category breakdown Pie Chart displaying customized category segments.

## 📈 The Magic Under the Hood: Scalable Vector Graphics (SVG) & Recharts D3 Mechanics

These charts and animations are powered by pure, hardware-accelerated **SVG (Scalable Vector Graphics)** (not to be confused with SVD/Singular Value Decomposition in mathematics!). Here is why they are so powerful and smooth:

### 1. SVG-based Interactive Charting (Recharts + D3)
- **Direct DOM Mapping**: Recharts doesn't draw pixels on a flat canvas; instead, it uses React combined with **D3.js**'s mathematical scaling engine to dynamically calculate layout bounds and inject structured SVG tags (`<rect>`, `<path>`, `<circle>`, `<g>`) directly into the web page's DOM.
- **Buttery-Smooth Mouse Tracking**: Because every bar, pie segment, and tooltip is a standalone SVG node, they support native CSS transition transforms and direct React event listeners (`onMouseEnter`, `onClick`), yielding incredibly fast visual responses.
- **Perfect Scaling (`<ResponsiveContainer>`)**: Vector graphics use geometric math rather than raster arrays. No matter if the charts are viewed on a high-DPI Retina screen or scaled down on mobile viewports, the curves, grids, and typography remain perfectly sharp without a single pixel of blurriness.

### 2. Pure CSS-Animated Hand-Crafted SVGs (`PiggyCartoon.tsx`)
- **Zero Asset Clutter**: The floating piggy bank and coin slot are composed of pure raw `<svg>` elements structured inline. No heavy PNGs or GIF images are downloaded.
- **60fps Native Keyframes**: We leverage native GPU hardware acceleration using CSS animations (`floatPiggy`, `coinDrop`, `sparkleStar`) to float the body, drop coins into the slot with randomized delay timings, and sparkle the stars with absolute fluid responsiveness.

### 3. Interactive Inline Gold Coin FAB (`Dashboard.tsx`, `index.css`)
- **Horizontal Spit-out Action**: Placed right next to the "New PiggyBank" button, hovering the `🐷` trigger fires a smooth `cubic-bezier` transform that ejects the Toggle Analytics coin horizontally to the left with an elegant, visually separated gap.

---

# TODO

- [ ] Compare the config.yaml vs config.py and possibly move the configuration to Config.yaml
- [ ] Use REST API to move the logic to API endpoint to allow for calling
- [ ] Use FAST API to host the asynchronous non blocking server
- [ ] Use Streamlit to provide a simple web and API test
- [ ] Add currency category in the data
- [ ] Add a user login form for login feature
- [ ] Change multiple accounts into "piggy bank" which allows for name editing and integrate them into a single user to allow for more useful operation
- [ ] Update the transfer feature so that it has the option to directly transfer to the known account and transfer to unknown account. When it is used to transfer between piggy banks, it shouldn't be accounted in the expenditure.
- [ ] Update the total cost feature so that it can automatically aggregate the cost across all piggy banks.
- [ ] Combine the entire dataset into a altogether data that only stores each month's total cost and cost percentage, to reduce the memory and dataset stored.
- [ ] Seek for other option except csv, which is not practical in real-world scenario. 
