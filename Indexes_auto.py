# This program will calculate spectral index images from hyperspectral data
import os
import cv2
import numpy as np

# Small epsilon to avoid division by zero
EPS = 1e-6

# List of all wavelengths needed for the indices
REQUIRED_WAVELENGTHS = sorted(list(set([
    420, 430, 440, 450,
    500, 510, 530, 550, 570,
    670, 680, 700, 710, 720, 730, 740, 750,
    800, 840,
    900, 970
])))


def choose_folder(folder_name: str) -> str:
    """If Corrected_<folder> exists, use it; else use the original folder."""
    corrected = "Corrected_" + folder_name
    return corrected if os.path.isdir(corrected) else folder_name


# Reading the folder list from file
with open('folder_list.txt', 'r') as f1:
    folder_list = [line.strip() for line in f1 if line.strip()]

folder_number = 0

for folder in folder_list:
    folder_number += 1

    # Keep the original behavior of skipping the first 3 folders
    if folder_number < 4:
        continue

    folder = choose_folder(folder)
    print(f"Processing folder: {folder}")

    from collections import Counter

    # Detect most frequent file extension (jpg or png) in Spectral_Cube
    spectral_dir = os.path.join(folder, 'Spectral_Cube')

    extensions = []
    for fname in os.listdir(spectral_dir):
        if fname.lower().startswith('image') and fname.lower().endswith(('.jpg', '.png')):
            extensions.append(os.path.splitext(fname)[1].lower())

    if not extensions:
        raise RuntimeError(f"No image jpg/png files found in {spectral_dir}")

    file_extension = Counter(extensions).most_common(1)[0][0].lstrip('.')

    spectral_cube_path = os.path.join(folder, 'Spectral_Cube')

    # Load all required bands into memory as grayscale float32
    bands = {}
    for wl in REQUIRED_WAVELENGTHS:
        img_path = os.path.join(spectral_cube_path, f"image{wl}.{file_extension}")
        if not os.path.exists(img_path):
            raise FileNotFoundError(
                f"Expected band image not found: {img_path}. "
                f"Index calculation requires wavelength {wl} nm."
            )
        # Load as grayscale
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise IOError(f"Could not read image: {img_path}")
        bands[wl] = img.astype(np.float32)

    # Create output folder for indices
    index_out_folder = os.path.join(folder, 'Indexes_out')
    if not os.path.exists(index_out_folder):
        os.makedirs(index_out_folder)

    # Helper to normalize an index image to [0,255], apply heatmap, and attach legend
    def save_index_heatmap(index_array: np.ndarray, name: str, fixed_range=None):
        """
        fixed_range: tuple (vmin, vmax) if you want a fixed scale.
                     If None, vmin/vmax are computed from 1st and 99th percentiles.
        """
        arr = index_array.copy()

        # If fixed range requested, clip to that range first
        if fixed_range is not None:
            vmin, vmax = fixed_range
            arr = np.clip(arr, vmin, vmax)
        else:
            vmin = vmax = None  # will be determined from data

        # Mask finite values
        finite_mask = np.isfinite(arr)
        if not np.any(finite_mask):
            # If everything is invalid, just make a black image and dummy range
            norm_img = np.zeros_like(arr, dtype=np.uint8)
            if fixed_range is None:
                vmin, vmax = 0.0, 1.0
        else:
            valid = arr[finite_mask]

            # Determine vmin, vmax
            if fixed_range is None:
                # Use 1st and 99th percentiles instead of simple min/max
                p1, p99 = np.percentile(valid, [5, 95])
                if abs(p99 - p1) < 1e-12:
                    # Fallback to min/max if percentiles collapse
                    vmin = float(valid.min())
                    vmax = float(valid.max())
                else:
                    vmin = float(p1)
                    vmax = float(p99)
            # If fixed_range is not None, vmin/vmax already set

            # Avoid division by zero if range is tiny
            if abs(vmax - vmin) < 1e-12:
                norm_img = np.zeros_like(arr, dtype=np.uint8)
            else:
                # Clip to [vmin, vmax] for visualization
                arr_clipped = np.clip(arr, vmin, vmax)
                norm = (arr_clipped - vmin) / (vmax - vmin)
                norm = np.clip(norm, 0.0, 1.0)
                norm_img = (norm * 255).astype(np.uint8)

        # Apply heatmap (JET)
        heatmap = cv2.applyColorMap(norm_img, cv2.COLORMAP_JET)

        # -------- Create color legend to the right --------
        h, w, _ = heatmap.shape
        legend_width = 260  # more than twice the previous width to fit large numbers

        # Vertical gradient for colorbar: top = max, bottom = min
        gradient = np.linspace(255, 0, h, dtype=np.uint8).reshape(h, 1)
        colorbar = cv2.applyColorMap(gradient, cv2.COLORMAP_JET)

        # Create legend image with padding for text
        legend = np.zeros((h, legend_width, 3), dtype=np.uint8)
        # Place colorbar inside legend (e.g., from x=20 to x=60)
        bar_x0, bar_x1 = 20, 60
        legend[:, bar_x0:bar_x1, :] = colorbar

        # Put 9 tick labels (more detailed scale)
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 2.0      # 5x bigger than original 0.4
        thickness = 2

        # 9 values from vmin to vmax
        ticks = np.linspace(vmin, vmax, 9)

        # Larger margins so first and last labels fully fit
        top_margin = 60
        bottom_margin = 60
        usable_h = h - top_margin - bottom_margin
        if usable_h <= 0:
            usable_h = h  # fallback

        for i, val in enumerate(ticks):
            # fraction from 0 (bottom) to 1 (top)
            frac = (val - vmin) / (vmax - vmin) if vmax != vmin else 0.0
            # y coordinate: bottom_margin near bottom, top_margin near top
            y = int(h - bottom_margin - frac * usable_h)
            # x offset to the right of the bar
            x = bar_x1 + 10
            label = f"{val:.2f}"
            cv2.putText(
                legend,
                label,
                (x, y),
                font,
                font_scale,
                (255, 255, 255),
                thickness,
                cv2.LINE_AA
            )

        # Concatenate heatmap and legend side by side
        out_img = cv2.hconcat([heatmap, legend])

        out_path = os.path.join(index_out_folder, f"Image_{name}.jpg")
        cv2.imwrite(out_path, out_img)
        print(f"Saved {out_path} (vmin={vmin:.5g}, vmax={vmax:.5g})")

    # Shortcuts for bands (for readability)
    R420 = bands[420]
    R430 = bands[430]
    R440 = bands[440]
    R450 = bands[450]
    R500 = bands[500]
    R510 = bands[510]
    R530 = bands[530]
    R550 = bands[550]
    R570 = bands[570]
    R670 = bands[670]
    R680 = bands[680]
    R700 = bands[700]
    R710 = bands[710]
    R720 = bands[720]
    R730 = bands[730]
    R740 = bands[740]
    R750 = bands[750]
    R800 = bands[800]
    R840 = bands[840]
    R900 = bands[900]
    R970 = bands[970]

    # Now compute all indices

    # ARI1 = 1 / R550 - 1 / R700
    ARI1 = 1.0 / (R550 + EPS) - 1.0 / (R700 + EPS)
    save_index_heatmap(ARI1, 'ARI1')

    # ARI2 = R800 * (1/R550 - 1/R700)
    ARI2 = R800 * (1.0 / (R550 + EPS) - 1.0 / (R700 + EPS))
    save_index_heatmap(ARI2, 'ARI2')

    # CARI = R720 / R510 - 1
    CARI = (R720 / (R510 + EPS)) - 1.0
    save_index_heatmap(CARI, 'CARI')

    # CRI1 = 1/R510 - 1/R550
    CRI1 = 1.0 / (R510 + EPS) - 1.0 / (R550 + EPS)
    save_index_heatmap(CRI1, 'CRI1')

    # CRI2 = 1/R510 - 1/R700
    CRI2 = 1.0 / (R510 + EPS) - 1.0 / (R700 + EPS)
    save_index_heatmap(CRI2, 'CRI2')

    # CI_rededge = R840 / R720 - 1
    CI_rededge = (R840 / (R720 + EPS)) - 1.0
    save_index_heatmap(CI_rededge, 'CI_rededge')

    # GM1 = R750 / R550
    GM1 = R750 / (R550 + EPS)
    save_index_heatmap(GM1, 'GM1')

    # GM2 = R750 / R700
    GM2 = R750 / (R700 + EPS)
    save_index_heatmap(GM2, 'GM2')

    # NPCI = (R680 - R430) / (R680 + R430)  --> normalized difference, fix scale [-1, 1]
    NPCI = (R680 - R430) / (R680 + R430 + EPS)
    save_index_heatmap(NPCI, 'NPCI', fixed_range=(-1.0, 1.0))

    # NPQI = (R420 - R440) / (R420 + R440)  --> normalized difference, fix scale [-1, 1]
    NPQI = (R420 - R440) / (R420 + R440 + EPS)
    save_index_heatmap(NPQI, 'NPQI', fixed_range=(-1.0, 1.0))

    # NDVI = (R800 - R670) / (R800 + R670)  --> normalized difference, fix scale [-1, 1]
    NDVI = (R800 - R670) / (R800 + R670 + EPS)
    save_index_heatmap(NDVI, 'NDVI', fixed_range=(-1.0, 1.0))

    # PRI = (R530 - R570) / (R530 + R570)  --> normalized difference, fix scale [-1, 1]
    PRI = (R530 - R570) / (R530 + R570 + EPS)
    save_index_heatmap(PRI, 'PRI', fixed_range=(-1.0, 1.0))

    # PSRI = (R680 - R500) / R750
    PSRI = (R680 - R500) / (R750 + EPS)
    save_index_heatmap(PSRI, 'PSRI')

    # RENDVI = (R750 - R710) / (R750 + R710)  --> normalized difference, fix scale [-1, 1]
    RENDVI = (R750 - R710) / (R750 + R710 + EPS)
    save_index_heatmap(RENDVI, 'RENDVI', fixed_range=(-1.0, 1.0))

    # SRPI = R430 / R680
    SRPI = R430 / (R680 + EPS)
    save_index_heatmap(SRPI, 'SRPI')

    # SIPI = (R800 - R450) / (R800 - R680)
    SIPI = (R800 - R450) / (R800 - R680 + EPS)
    save_index_heatmap(SIPI, 'SIPI')

    # VREI1 = R740 / R720
    VREI1 = R740 / (R720 + EPS)
    save_index_heatmap(VREI1, 'VREI1')

    # VREI2 = (R730 - R750) / (R720 + R730)
    VREI2 = (R730 - R750) / (R720 + R730 + EPS)
    save_index_heatmap(VREI2, 'VREI2')

    # WBI = R970 / R900
    WBI = R970 / (R900 + EPS)
    save_index_heatmap(WBI, 'WBI')

    print(f"Finished folder: {folder}")
