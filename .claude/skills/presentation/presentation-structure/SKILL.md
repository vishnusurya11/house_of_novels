---
name: presentation-structure
description: Knowledge about the presentation slide format, weight system, navigation, and section structure
---

# Presentation Structure Skill

Knowledge about how the presentation at `presentation/index.html` is structured.

## File Location

`presentation/index.html` — a single-file HTML presentation with inline CSS and JS.

## Slide Format

Each slide is a div with `data-slide` (sequential number) and optional `data-weight` (journey percentage):

```html
<!-- Regular slide -->
<div class="slide" data-slide="12" data-weight="5">
    <h1>Slide Title</h1>
    <!-- content -->
</div>

<!-- Section divider slide -->
<div class="slide section-slide" data-slide="10">
    <h1>Section Name</h1>
    <p class="section-desc">Description of this section</p>
</div>

<!-- Title slide (centered) -->
<div class="slide title-slide" data-slide="1">
    <h1>Presentation Title</h1>
    <p class="subtitle">Subtitle text</p>
</div>
```

## Journey Bar Weight System

- Slides with `data-weight="N"` contribute N% to the journey progress bar
- All weights across the entire presentation MUST sum to exactly 100
- The journey bar reads weights at page load and pre-computes cumulative sums
- Slides without `data-weight` contribute 0% (informational slides, appendix)
- The bar is hidden on slide 1 (title slide)

### Weight Distribution by Section

| Section | Range | Total Weight |
|---------|-------|-------------|
| Part 0: Introduction | Slides 1-4 | 0% |
| Part 1: Prerequisites | Slides 5-9 | 0% |
| Part 2: Better Prompting | Slides 10-17 | 20% |
| Part 3: Project Memory | Slides 18-24 | 20% |
| Part 4: Structured Workflows | Slides 25-28 | 10% |
| Part 5: Domain Knowledge | Slides 29-33 | 15% |
| Part 6: Agentic Engineering | Slides 34-46 | 35% |
| Appendix | Slides 47+ | 0% |

## Navigation System

- `goToSlide(n)` — used in TOC links, must match actual `data-slide` numbers
- `totalSlides` is auto-computed from DOM (`document.querySelectorAll('[data-slide]').length`)
- Arrow keys, Space, and touch swipe for navigation
- Slide counter shows `current / total` at bottom-left

## Renumbering Rules

After adding, removing, or reordering slides:
1. Renumber ALL `data-slide` attributes sequentially starting from 1
2. Update all `goToSlide()` calls in the TOC/Journey Map slide
3. The JS `totalSlides` auto-computes — no manual update needed
4. Verify no gaps or duplicates exist

## Section Divider Format

Section dividers use the `section-slide` class and show the current journey percentage:

```html
<div class="slide section-slide" data-slide="10">
    <p class="section-number">Part 2</p>
    <h1>Better Prompting</h1>
    <p class="section-desc">Journey: 0% — effective prompting for real results.</p>
</div>
```
