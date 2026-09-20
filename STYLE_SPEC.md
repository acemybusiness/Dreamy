# Dreamy SRL — Fusion + Description-Driven Stretch Specification v1.5

## Core concept
Dreamy creates a cohesive finished image from either:

1. **Fusion Mode** — two distinct ideas blended into one believable scene.
2. **Description-Driven Stretch Mode** — one image description expanded intelligently across the full requested height.

The app should never rely on a fixed list of decorative additions. The description itself drives what supporting components are added.

## Description-Driven Stretch
When the user enters one description, Dreamy should:

1. Identify the primary subject(s).
2. Identify mood, color palette, lighting, environment, motion and material cues.
3. Determine how much vertical structure the requested aspect ratio needs.
4. Create compatible supporting components derived from those cues.
5. Arrange them across the height so the composition feels complete.
6. Use transitions such as mist, reflection, cloud, light, shadow, terrain, roots, water, particles, foliage or atmospheric haze only when they fit the description.
7. Preserve one coherent lighting direction and one harmonized palette.
8. Avoid repeating the same object just to fill space.
9. Avoid inserting fixed motifs such as waterfalls, moons, floating islands, flowers or auroras unless the description or visual logic supports them.

### Example
Input:
"An anatomical heart with a glowing moon inside it above a floating pool."

Possible derived supporting components:
- lunar haze around the heart
- reflected moonlight in the pool
- hanging roots or organic tendrils
- drifting mist
- subtle celestial particles
- dark atmospheric clouds
- lower reflection/grounding area

These additions come from the heart / moon / pool / night / glow relationships, not from a template.

## Vertical planning
Dreamy should automatically scale composition complexity to aspect ratio.

Shorter vertical image:
- primary focal area
- transition
- lower anchor

Taller image:
- primary focal area
- secondary supporting feature
- transition zone
- tertiary visual element
- lower anchor / reflection / foreground

Very tall image:
- use more zones, but maintain one scene and avoid a stacked-collage appearance

## Fusion Mode
Two user ideas remain recognizable, but share:
- one lighting environment
- one color language
- one atmosphere
- coherent perspective/depth
- transitional material or light

## Visual DNA
- near-black negative space when appropriate
- luminous gold, violet, indigo, cyan and selective pink when supported by the description
- soft volumetric light
- realistic clouds, mist, water, organic rock, foliage and reflective surfaces where relevant
- strong foreground-to-background depth
- one dominant focal glow
- secondary glow accents
- high detail without clutter
- dreamlike photoreal / painterly finish
- cohesive vertical storytelling

## Composition modes
- Auto
- Fusion
- Description Stretch
- Double Stack
- Portal Merge
- Reflection Merge
- Horizon Blend
- Celestial Overlay
- Landscape Within Landscape

## Output
- master image
- component assets derived from the scene plan
- SRL signature
- prompt / scene plan / seed / engine manifest
- PNG / JPG / WEBP / PDF

## Non-copy rule
Reference images define only high-level visual qualities and quality targets. Dreamy should generate new geometry, new layouts, new object relationships, and new focal arrangements rather than reproducing a supplied reference composition.
