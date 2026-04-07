"""
Utility to extract a named screen region from a screenshot and save it as a .npy capture file.

Usage:
    python3.12 dev/save_region_from_screenshot.py \
        --image path/to/screenshot.png \
        --game bomberman_quest \
        --region zone_background \
        --target in_forest_zone

The script resizes the screenshot to the Game Boy resolution (160x144),
crops the region, and saves it to the correct captures directory.
"""

import click
import numpy as np
from PIL import Image
import os

# Game Boy screen resolution
GB_WIDTH = 160
GB_HEIGHT = 144

# All known region definitions per game
REGION_DEFINITIONS = {
    "bomberman_quest": {
        "screen_top":      (0,   0,  160, 16),
        "dialogue_strip":  (0,  12,  160, 10),
        "dialogue_icon":   (112, 18,  48, 50),
        "hud_bottom":      (0, 136,  160,  8),
        "zone_background": (0,   0,  160, 32),
    },
    "bomberman_pocket": {
        "area_intro_strip": (0,   0, 160, 20),
        "pause_indicator":  (96, 128,  64, 16),
        "zone_background":  (0,   0, 160, 32),
    },
    "bomberman_max": {
        "screen_top":           (0,  0, 160, 16),
        "stage_briefing_strip": (0, 84, 160,  8),
        "zone_background":      (0,  0, 160, 32),
    },
}


@click.command()
@click.option("--image", required=True, type=click.Path(exists=True), help="Path to screenshot image file.")
@click.option("--game", required=True, type=str, help="Game variant (e.g. bomberman_quest).")
@click.option("--region", required=True, type=str, help="Region name (e.g. zone_background).")
@click.option("--target", default=None, type=str,
              help="Target name for multi-target regions (e.g. in_forest_zone). Omit for single-target regions.")
def save_region(image, game, region, target):
    """Extract a region from a screenshot and save as a .npy capture file."""
    from gameboy_worlds.utils import load_parameters
    parameters = load_parameters()

    key = f"{game}_rom_data_path"
    if key not in parameters:
        raise click.ClickException(f"'{key}' not found in config. Add it to rom_data_path_vars.yaml.")

    rom_data_path = parameters[key]
    captures_dir = os.path.join(rom_data_path, "captures")

    if target:
        save_dir = os.path.join(captures_dir, region)
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, target) + ".npy"
    else:
        os.makedirs(captures_dir, exist_ok=True)
        save_path = os.path.join(captures_dir, region) + ".npy"

    # Get region coords
    game_regions = REGION_DEFINITIONS.get(game, {})
    if region not in game_regions:
        raise click.ClickException(
            f"Region '{region}' not defined for game '{game}'. "
            f"Available: {list(game_regions.keys())}"
        )
    x, y, w, h = game_regions[region]

    # Load and resize screenshot to GB resolution, convert to grayscale to match dev_play captures
    img = Image.open(image).convert("L")  # grayscale
    img_resized = img.resize((GB_WIDTH, GB_HEIGHT), Image.NEAREST)
    frame = np.array(img_resized, dtype=np.uint8)  # shape (144, 160)

    # Crop region and add channel dim: (h, w, 1)
    cropped = frame[y:y + h, x:x + w, np.newaxis]

    if os.path.exists(save_path):
        overwrite = input(f"File already exists: {save_path}\nOverwrite? (y/n): ")
        if overwrite.strip().lower() != "y":
            print("Aborted.")
            return

    np.save(save_path, cropped)
    print(f"Saved {cropped.shape} array to: {save_path}")


if __name__ == "__main__":
    save_region()
