#!/usr/bin/env python3

import argparse
import yaml
import numpy as np
from PIL import Image
import trimesh


def stl_to_occmap(
    stl_path,
    out_prefix,
    resolution,
    scale,
    z_min,
    z_max,
    padding,
    samples,
    inflate_radius
):
    mesh = trimesh.load_mesh(stl_path)

    if mesh.is_empty:
        raise RuntimeError("Loaded STL is empty.")

    # Apply unit scale, e.g. mm -> m use 0.001
    mesh.apply_scale(scale)

    bounds = mesh.bounds
    min_x, min_y, min_z = bounds[0]
    max_x, max_y, max_z = bounds[1]

    print("Mesh bounds after scale:")
    print(f"  x: {min_x:.3f} to {max_x:.3f}")
    print(f"  y: {min_y:.3f} to {max_y:.3f}")
    print(f"  z: {min_z:.3f} to {max_z:.3f}")

    min_x -= padding
    min_y -= padding
    max_x += padding
    max_y += padding

    width = int(np.ceil((max_x - min_x) / resolution))
    height = int(np.ceil((max_y - min_y) / resolution))

    print(f"Map size: {width} x {height} cells")
    print(f"Resolution: {resolution} m/cell")

    # Nav2 map convention:
    # 254 = free, 0 = occupied, 205 = unknown
    # Here we default to free because STL gives geometry but not exploration unknown.
    grid = np.full((height, width), 254, dtype=np.uint8)

    # Sample points from mesh surface
    print(f"Sampling {samples} points from STL surface...")
    points, _ = trimesh.sample.sample_surface(mesh, samples)

    # Elevation-based filtering:
    # Use the bottom of the mesh as floor height.
    floor_z = mesh.bounds[0][2]

    relative_z = points[:, 2] - floor_z

    print(f"Detected floor_z: {floor_z:.3f}")
    print(f"Relative elevation range: {relative_z.min():.3f} to {relative_z.max():.3f}")

    # Treat points above floor by a certain height as obstacles.
    # z_min and z_max are now relative to the floor.
    mask = (relative_z >= z_min) & (relative_z <= z_max)
    obstacle_points = points[mask]

    print(f"Obstacle points after z filter: {len(obstacle_points)}")

    if len(obstacle_points) == 0:
        print("WARNING: No obstacle points after height filtering.")
        print("Try lowering z_min or increasing z_max.")

    xs = obstacle_points[:, 0]
    ys = obstacle_points[:, 1]

    cols = ((xs - min_x) / resolution).astype(np.int32)
    rows = ((ys - min_y) / resolution).astype(np.int32)

    valid = (cols >= 0) & (cols < width) & (rows >= 0) & (rows < height)
    cols = cols[valid]
    rows = rows[valid]

    # Image row direction is top-to-bottom, map y is bottom-to-top.
    image_rows = height - 1 - rows

    grid[image_rows, cols] = 0

    # Optional obstacle inflation in pixels
    if inflate_radius > 0:
        inflate_cells = int(np.ceil(inflate_radius / resolution))
        print(f"Inflating obstacles by {inflate_cells} cells")

        occ = np.argwhere(grid == 0)
        inflated = grid.copy()

        for r, c in occ:
            r0 = max(0, r - inflate_cells)
            r1 = min(height, r + inflate_cells + 1)
            c0 = max(0, c - inflate_cells)
            c1 = min(width, c + inflate_cells + 1)

            for rr in range(r0, r1):
                for cc in range(c0, c1):
                    if (rr - r) ** 2 + (cc - c) ** 2 <= inflate_cells ** 2:
                        inflated[rr, cc] = 0

        grid = inflated

    pgm_path = out_prefix + ".pgm"
    yaml_path = out_prefix + ".yaml"

    Image.fromarray(grid).save(pgm_path)

    map_yaml = {
        "image": pgm_path.split("/")[-1],
        "mode": "trinary",
        "resolution": float(resolution),
        "origin": [float(min_x), float(min_y), 0.0],
        "negate": 0,
        "occupied_thresh": 0.65,
        "free_thresh": 0.25,
    }

    with open(yaml_path, "w") as f:
        yaml.dump(map_yaml, f, default_flow_style=False)

    print("Saved:")
    print(f"  {pgm_path}")
    print(f"  {yaml_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stl", required=True, help="Input STL file")
    parser.add_argument("--out", required=True, help="Output prefix, e.g. /path/map")
    parser.add_argument("--resolution", type=float, default=0.05, help="Map resolution in meters")
    parser.add_argument("--scale", type=float, default=1.0, help="Mesh scale. Use 0.001 if STL is in mm")
    parser.add_argument("--z-min", type=float, default=0.05, help="Minimum obstacle height")
    parser.add_argument("--z-max", type=float, default=2.0, help="Maximum obstacle height")
    parser.add_argument("--padding", type=float, default=1.0, help="Map padding in meters")
    parser.add_argument("--samples", type=int, default=1000000, help="Number of sampled surface points")
    parser.add_argument("--inflate", type=float, default=0.0, help="Obstacle inflation radius in meters")

    args = parser.parse_args()

    stl_to_occmap(
        stl_path=args.stl,
        out_prefix=args.out,
        resolution=args.resolution,
        scale=args.scale,
        z_min=args.z_min,
        z_max=args.z_max,
        padding=args.padding,
        samples=args.samples,
        inflate_radius=args.inflate,
    )


if __name__ == "__main__":
    main()