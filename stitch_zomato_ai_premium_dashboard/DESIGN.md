---
name: Lumina Gastronomy
colors:
  surface: '#131313'
  surface-dim: '#131313'
  surface-bright: '#3a3939'
  surface-container-lowest: '#0e0e0e'
  surface-container-low: '#1c1b1b'
  surface-container: '#201f1f'
  surface-container-high: '#2a2a2a'
  surface-container-highest: '#353534'
  on-surface: '#e5e2e1'
  on-surface-variant: '#e4beba'
  inverse-surface: '#e5e2e1'
  inverse-on-surface: '#313030'
  outline: '#ab8986'
  outline-variant: '#5b403e'
  surface-tint: '#ffb3ae'
  primary: '#ffb3ae'
  on-primary: '#68000b'
  primary-container: '#ff5352'
  on-primary-container: '#5c0008'
  inverse-primary: '#ba1724'
  secondary: '#ffb77a'
  on-secondary: '#4c2700'
  secondary-container: '#d37b20'
  on-secondary-container: '#432100'
  tertiary: '#c8c6c5'
  on-tertiary: '#313030'
  tertiary-container: '#929090'
  on-tertiary-container: '#2a2a2a'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffdad7'
  primary-fixed-dim: '#ffb3ae'
  on-primary-fixed: '#410004'
  on-primary-fixed-variant: '#930014'
  secondary-fixed: '#ffdcc2'
  secondary-fixed-dim: '#ffb77a'
  on-secondary-fixed: '#2e1500'
  on-secondary-fixed-variant: '#6d3a00'
  tertiary-fixed: '#e5e2e1'
  tertiary-fixed-dim: '#c8c6c5'
  on-tertiary-fixed: '#1c1b1b'
  on-tertiary-fixed-variant: '#474746'
  background: '#131313'
  on-background: '#e5e2e1'
  surface-variant: '#353534'
typography:
  display-lg:
    fontFamily: Geist
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Geist
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Geist
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  title-md:
    fontFamily: Geist
    fontSize: 20px
    fontWeight: '500'
    lineHeight: 28px
  body-lg:
    fontFamily: Geist
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-caps:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  gutter: 20px
  margin-mobile: 16px
  margin-desktop: 40px
---

## Brand & Style

The design system is a premium, high-end interface tailored for an AI-driven culinary experience. It targets a sophisticated audience that values speed, precision, and a "luxury concierge" feel. 

The visual style is **Glassmorphism** set against a **Deep Dark** backdrop. The aesthetic relies on the interplay of light and transparency, using frosted glass surfaces to create a sense of depth without traditional heavy shadows. The emotional response should be one of "effortless intelligence"—where the UI feels like it’s breathing through subtle background blurs and vibrant, energetic accents.

**Key Principles:**
- **Luminosity:** Elements should feel like they emit or refract light.
- **Precision:** Clean lines and high-contrast typography to ensure the AI's data is easily digestible.
- **Fluidity:** Use of gradients to suggest movement and the "alive" nature of the AI.

## Colors

The palette is anchored by an absolute dark background to allow the glass effects to pop. 

- **Primary Accent:** A high-energy gradient spanning from a punchy red to a warm orange. This is reserved for primary CTAs, active states, and AI-driven insights.
- **Surface Strategy:** Surfaces are not solid. They use a low-opacity white tint combined with a heavy backdrop blur (10px - 20px) to simulate frosted glass.
- **Functional Grays:** Used sparingly for borders and Dividers to maintain structure without breaking the glass illusion.

## Typography

This design system utilizes **Geist** for its technical precision and modern, minimalist footprint. The typeface’s monospaced influence in its DNA provides a subtle nod to the "AI" backend while maintaining high readability for consumer use.

**Usage Rules:**
- **High Contrast:** Always use #FFFFFF for primary content and #A0A0A0 for supporting metadata.
- **Display Weights:** Use Bold and SemiBold for headings to create a clear visual hierarchy against the dark background.
- **Tight Kerning:** Negative letter-spacing on larger headlines creates a "designed" editorial look.

## Layout & Spacing

The layout follows a **Fluid Grid** model with generous internal padding to support the "Glass" aesthetic. Glass containers require breathing room (margins) to allow the background content/colors to be visible through their blur.

- **Desktop:** 12-column grid with 40px margins.
- **Mobile:** 4-column grid with 16px margins.
- **Rhythm:** Use a 4px/8px incremental system. Components like the Sidebar should have a fixed width of 280px on desktop, while the main content area remains fluid.

## Elevation & Depth

Depth is achieved through **Backdrop Blurs** rather than traditional Y-offset shadows. 

- **Level 1 (Base):** The #0F0F0F background.
- **Level 2 (Cards/Sidebar):** Surface tint `rgba(255,255,255, 0.05)` with a 10px-16px backdrop-blur. 
- **Level 3 (Modals/Popovers):** Surface tint `rgba(255,255,255, 0.08)` with a 32px backdrop-blur and a subtle `1px` inner-stroke of `rgba(255,255,255, 0.1)`.

**Borders:** Use thin, low-opacity strokes to define edges. This prevents the glass from bleeding into the background while keeping the look light.

## Shapes

The shape language is modern and approachable. 
- **Standard UI Elements:** Use `0.5rem` (8px) for buttons and input fields.
- **Main Containers:** Large cards and the sidebar use `1.5rem` (24px) for a softer, premium feel.
- **AI Badges:** Use fully pill-shaped (rounded-full) corners to distinguish "smart" or "automated" tags from static content.

## Components

### Buttons
- **Primary:** Background is the `accent_gradient`. Text is white with a subtle drop shadow for legibility.
- **Secondary (Glass):** `rgba(255,255,255, 0.05)` background with a `1px` border of `rgba(255,255,255, 0.1)`.

### Cards
- Interactive cards should feature a subtle hover state where the `backdrop-blur` increases and the border-opacity doubles. 

### AI Explanation Blocks
- These blocks use a distinct `1px` border using the primary gradient. 
- Background has a slightly higher opacity (`0.08`) to signal "special" content. 
- Include a small sparkle icon or "AI" badge in the top right corner.

### Sidebar
- Full-height, fixed glass panel. 
- Active states for navigation items should use a vertical gradient bar (2px wide) on the left edge and a subtle `rgba(255,77,77, 0.1)` background tint.

### Star Ratings
- Use the vibrant orange (#FF9F43) for filled stars and `rgba(255,255,255, 0.2)` for empty ones. Include a subtle glow effect on the icons.

### Input Fields
- Dark, inset backgrounds (`rgba(0,0,0,0.3)`) with a white focus ring at `0.4` opacity. 
- Placeholder text in `text_secondary`.