#!/usr/bin/env python3
"""Render the NullFrame GitHub profile assets from profile-manifest.json.

The committed SVGs contain outlined display text and therefore do not depend on
remote fonts or GitHub's image proxy loading a custom font. Inkscape is the only
external build-time requirement.
"""

from __future__ import annotations

import html
import json
import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "profile-manifest.json"
BUILD = ROOT / "build"
ASSETS = ROOT / "assets"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def text(
    x: int,
    y: int,
    value: str,
    size: int,
    fill: str,
    *,
    weight: int = 400,
    spacing: float = 0,
    opacity: float = 1,
    anchor: str = "start",
) -> str:
    return (
        f'<text x="{x}" y="{y}" fill="{fill}" fill-opacity="{opacity}" '
        f'font-family="DejaVu Sans Mono" font-size="{size}" '
        f'font-weight="{weight}" letter-spacing="{spacing}" '
        f'text-anchor="{anchor}">{esc(value)}</text>'
    )


def svg_document(width: int, height: int, body: list[str], label: str) -> str:
    return "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
            (
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
                f'height="{height}" viewBox="0 0 {width} {height}" '
                f'role="img" aria-label="{esc(label)}">'
            ),
            f"<title>{esc(label)}</title>",
            *body,
            "</svg>",
            "",
        ]
    )


def corner_ticks(x: int, y: int, w: int, h: int, color: str, length: int, stroke: int) -> list[str]:
    x2, y2 = x + w, y + h
    return [
        f'<path d="M{x},{y + length} V{y} H{x + length}" fill="none" stroke="{color}" stroke-width="{stroke}"/>',
        f'<path d="M{x2 - length},{y} H{x2} V{y + length}" fill="none" stroke="{color}" stroke-width="{stroke}"/>',
        f'<path d="M{x},{y2 - length} V{y2} H{x + length}" fill="none" stroke="{color}" stroke-width="{stroke}"/>',
        f'<path d="M{x2 - length},{y2} H{x2} V{y2 - length}" fill="none" stroke="{color}" stroke-width="{stroke}"/>',
    ]


def render_mark(palette: dict[str, str]) -> str:
    body = [f'<rect width="400" height="400" fill="{palette["base"]}"/>']
    body.append(
        f'<rect x="116" y="116" width="168" height="168" fill="none" '
        f'stroke="{palette["line"]}" stroke-width="6"/>'
    )
    body.extend(corner_ticks(72, 72, 256, 256, palette["accent"], 64, 14))
    return svg_document(400, 400, body, "NullFrame crop-mark symbol")


def render_hero(brand: dict[str, str], palette: dict[str, str]) -> str:
    body = [f'<rect width="1280" height="320" fill="{palette["base"]}"/>']
    body.append(
        f'<rect x="48" y="40" width="1184" height="240" fill="none" '
        f'stroke="{palette["line"]}" stroke-width="1"/>'
    )
    body.extend(corner_ticks(32, 24, 1216, 272, palette["accent"], 30, 4))
    body.append(text(1008, 260, "00", 236, palette["text"], weight=700, opacity=0.025))
    body.append(text(80, 78, "00 / PROFILE", 11, palette["accent"], weight=700, spacing=2.2))
    body.append(text(80, 184, brand["name"], 76, palette["text"], weight=700, spacing=11.5))
    body.append(text(84, 224, brand["discipline"], 14, palette["muted"], weight=400, spacing=2.4))
    body.append(text(953, 238, f'HANDLE / {brand["handle"]}', 10, palette["muted"], spacing=1.1))
    body.append(text(953, 258, f'REV / {brand["revision"]}', 10, palette["muted"], spacing=1.1))
    return svg_document(1280, 320, body, "NullFrame — Software, Tooling, Infrastructure")


def render_card(project: dict[str, str], palette: dict[str, str]) -> str:
    rail = palette[project["rail"]]
    body = [f'<rect width="400" height="152" fill="{palette["base"]}"/>']
    body.append(
        f'<rect x="12" y="12" width="376" height="128" fill="{palette["surface"]}" '
        f'stroke="{palette["line"]}" stroke-width="1"/>'
    )
    body.append(f'<rect x="12" y="12" width="4" height="128" fill="{rail}"/>')
    body.append(
        f'<path d="M12,30 V12 H30" fill="none" stroke="{palette["accent"]}" stroke-width="3"/>'
    )
    body.append(
        text(34, 40, f'{project["index"]} / SELECTED SYSTEM', 9, palette["muted"], spacing=1.1)
    )
    title_size = 20 if len(project["name"]) > 15 else 23
    body.append(text(34, 78, project["name"], title_size, palette["text"], weight=700, spacing=1.2))
    body.append(text(34, 108, project["status"], 10, rail, weight=700, spacing=0.8))
    body.append(
        text(
            34,
            130,
            f'{project["visibility"]} · {project["year"]}',
            9,
            palette["muted"],
            spacing=0.7,
        )
    )
    return svg_document(400, 152, body, f'{project["name"]} — {project["status"]}')


def outline_svg(source: str, output: Path) -> None:
    BUILD.mkdir(parents=True, exist_ok=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    source_path = BUILD / f"{output.stem}.source.svg"
    source_path.write_text(source, encoding="utf-8")
    env = os.environ.copy()
    env["XDG_CONFIG_HOME"] = str(BUILD / ".config")
    env["XDG_CACHE_HOME"] = str(BUILD / ".cache")
    env["XDG_DATA_HOME"] = str(BUILD / ".data")
    subprocess.run(
        [
            "inkscape",
            str(source_path),
            "--export-text-to-path",
            "--export-plain-svg",
            f"--export-filename={output}",
        ],
        check=True,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    rendered = output.read_text(encoding="utf-8")
    if "<text" in rendered or "http://" in rendered.replace("http://www.w3.org/2000/svg", ""):
        raise RuntimeError(f"Asset validation failed: {output}")


def main() -> None:
    if shutil.which("inkscape") is None:
        raise SystemExit("Inkscape is required to outline SVG display text.")
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    brand = data["brand"]
    palettes = data["palettes"]

    outline_svg(render_mark(palettes["dark"]), ASSETS / "mark.svg")
    for mode in ("dark", "light"):
        palette = palettes[mode]
        outline_svg(render_hero(brand, palette), ASSETS / f"hero-{mode}.svg")
        for project in data["projects"]:
            outline_svg(
                render_card(project, palette),
                ASSETS / f'project-{project["slug"]}-{mode}.svg',
            )

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    required_copy = [brand["positioning"], *(project["name"] for project in data["projects"])]
    missing = [value for value in required_copy if value.lower() not in readme.lower()]
    if missing:
        raise RuntimeError(f"README is out of sync with the manifest: {missing}")

    print("Rendered 9 outlined SVG assets.")


if __name__ == "__main__":
    main()
