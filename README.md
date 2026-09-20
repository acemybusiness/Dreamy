# Dreamy DoubleStack SRL v1.2

Phone-first local image generator for dreamy double-stack fantasy scenes.

## Phone use
The phone interface is designed to be simple: description, proportional inch size, Create Image, preview, and downloads.

## Important
The current v1.2 image engine is local. The phone interface connects to a Flask backend running on a computer with ComfyUI/GPU. GitHub Pages can host the interface, but it cannot run ComfyUI or the Python image-generation backend.

## Local stack
- ComfyUI: local GPU generation
- Ollama: optional local prompt planning
- Flask/Pillow: app server, exports, SRL mark
- No paid API required

## Exports
PNG, JPG, WEBP, PDF, component PNG assets, manifest JSON, and a ZIP package.

## Originality
The app uses text-only high-level style descriptors and does not feed the supplied reference images into the generator. It avoids artist, franchise, logo, and character instructions. Generated output should still be reviewed for commercial use.
