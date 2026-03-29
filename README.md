# App Store Screenshot Generator

Generates App Store screenshots by compositing app screenshots onto a styled canvas with device frames, decorative wave background, and text overlays.

## Requirements

- Python 3.10+
- Pillow, PyYAML (see `requirements.txt`)

```
make install
```

## Usage

```
make generate APP=MyApp
make generate APP=MyApp DEVICE=iphone
make generate APP=MyApp DEVICE=ipad
```

Or directly:

```
.venv/bin/python generate.py --app MyApp [--device iphone|ipad|all]
```

Output is written to `output/<AppName>/iphone/` and `output/<AppName>/ipad/`.

## Adding a new app

1. Create the app directory and place source screenshots:

```
apps/
└── MyApp/
    ├── config.yaml
    └── screenshots/
        ├── 01_screen1.png
        └── 02_screen2.png
```

Screenshots are shared across devices by default. If a device needs different source images, place them in a subdirectory:

```
screenshots/
├── 01_screen1.png       ← shared (fallback)
└── ipad/
    └── 01_screen1.png   ← iPad-specific override
```

2. Write `config.yaml` (copy from the example app as a template):

```yaml
app:
  name: "MyApp"

devices:
  iphone:
    output_size: [1284, 2778]     # App Store accepted: 1284x2778 or 1242x2688
    device_width_ratio: 0.78
    font_headline_ratio: 0.075
    font_sub_ratio: 0.032
    wave_y_ratio: 0.78
    wave_amplitude_ratio: 0.13

  ipad:
    output_size: [2048, 2732]     # 12.9" iPad Pro
    device_width_ratio: 0.72
    font_headline_ratio: 0.065
    font_sub_ratio: 0.028
    wave_y_ratio: 0.78
    wave_amplitude_ratio: 0.13

style:
  background_color: [245, 245, 247]
  font: "SF-Pro-Display-Bold.otf"   # place in assets/fonts/
  bezel_ratio: 0.028
  bottom_margin_ratio: 0.010

screenshots:
  - id: screen1
    iphone: "01_screen1.png"
    ipad: "01_screen1.png"
    headline: "Your headline here."
    subheadline: "Optional subheadline."
    accent_color: [20, 20, 20]
    text_color: [100, 100, 100]
```

3. Run the generator.

## App Store dimensions

| Device | Size |
|--------|------|
| iPhone (6.7") | 1284 x 2778 |
| iPhone (6.5") | 1242 x 2688 |
| iPad Pro 12.9" | 2048 x 2732 |

## Project structure

```
appstore-screenshots/
├── generate.py
├── requirements.txt
├── Makefile
├── assets/
│   └── fonts/
└── apps/
    └── YourApp/
        ├── config.yaml
        └── screenshots/
```

## Fonts

The generator looks for fonts in `assets/fonts/`. If the specified font is not found, it falls back to system fonts (SF Pro, Helvetica, Arial).
