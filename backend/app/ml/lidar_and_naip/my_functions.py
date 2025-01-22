import os
from glob import glob
from math import ceil

import numpy as np
import rasterio
from rasterio.merge import merge
from rasterio.windows import Window


# ============================
# NDHM generation function
# ============================
def generate_ndhm(dsm_file: str, dtm_file: str, output_ndhm_file: str) -> None:
    """
    DSM DTM used for NDHM (Normalized Digital Height Model)generation
    over 99.99th percentile becomes 0

    Args:
        dsm_file (str): DSM file directory
        dtm_file (str): DTM DSM file directory
        output_ndhm_file (str): output NDHM DSM file directory
    """
    with rasterio.open(dsm_file) as dsm, rasterio.open(dtm_file) as dtm:
        # DSM DTM read
        dsm_data = dsm.read(1)
        dtm_data = dtm.read(1)

        # NDHM generation
        ndhm_data = dsm_data - dtm_data
        ndhm_data[ndhm_data < 0] = 0  # negative value eliminated

        # 99.9th percentile calculation
        valid_ndhm_values = ndhm_data[ndhm_data > 0]  # only valid NDHM values used
        if valid_ndhm_values.size > 0:
            percentile_99_9 = np.percentile(valid_ndhm_values, 99.999)
            print(f"99.99th Percentile Height: {percentile_99_9}")

            # over 99.9th percentile becomes 0
            ndhm_data[ndhm_data > percentile_99_9] = 0
        else:
            print("No valid NDHM values found. Skipping percentile adjustment.")

        # output file saved
        profile = dsm.profile
        profile.update(dtype=rasterio.float32)

        with rasterio.open(output_ndhm_file, "w", **profile) as dst:
            dst.write(ndhm_data.astype(rasterio.float32), 1)

    print(f"NDHM generated with 99.99th percentile adjustment: {output_ndhm_file}")


# ============================
# patch split function (CHM & NAIP)
# ============================
def save_patches(
    image_path: str, output_dir: str, patch_size: int = 256, overlay: int = 0
) -> None:
    """
    patch split and saved
    Args:
        image_path (str): og image file directory
        output_dir (str): patch file directory
        patch_size (int): size of patch (default: 256)
        overlay (int): patch overlap (default: 0)
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with rasterio.open(image_path) as src:
        height, width = src.height, src.width
        step = patch_size - overlay

        n_patches_height = ceil((height - overlay) / step)
        n_patches_width = ceil((width - overlay) / step)

        patch_id = 0
        for i in range(n_patches_height):
            for j in range(n_patches_width):
                row_start = i * step
                col_start = j * step
                if row_start + patch_size > height:
                    row_start = height - patch_size
                if col_start + patch_size > width:
                    col_start = width - patch_size

                window = Window(col_start, row_start, patch_size, patch_size)
                patch = src.read(1, window=window)

                patch_filename = f"patch_{patch_id}.tif"
                patch_filepath = os.path.join(output_dir, patch_filename)
                patch_transform = src.window_transform(window)  # ✅ patch transform

                profile = src.profile
                profile.update(
                    {
                        "height": patch_size,
                        "width": patch_size,
                        "count": 1,
                        "transform": patch_transform,  # ✅ individual patch transform applied
                    }
                )

                with rasterio.open(patch_filepath, "w", **profile) as dst:
                    dst.write(patch, 1)

                patch_id += 1
    print(f"Patches saved to: {output_dir}")


def save_combined_patches(
    chm_path: str,
    naip_path: str,
    output_dir: str,
    patch_size: int = 256,
    overlay: int = 0,
) -> None:
    """
    CHM(1band)과 NAIP(4band)image patch split and saved together
    saved into training data size (H, W, 5)
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with rasterio.open(chm_path) as src_chm, rasterio.open(naip_path) as src_naip:
        height, width = src_chm.height, src_chm.width
        step = patch_size - overlay

        n_patches_height = ceil((height - overlay) / step)
        n_patches_width = ceil((width - overlay) / step)

        patch_id = 0
        for i in range(n_patches_height):
            for j in range(n_patches_width):
                row_start = i * step
                col_start = j * step
                if row_start + patch_size > height:
                    row_start = height - patch_size
                if col_start + patch_size > width:
                    col_start = width - patch_size

                window = Window(col_start, row_start, patch_size, patch_size)
                patch_transform = src_chm.window_transform(
                    window
                )  # ✅ patch transformaion

                # CHM (1band) patch
                chm_patch = src_chm.read(1, window=window)
                chm_patch = np.expand_dims(chm_patch, axis=-1)  # (H, W, 1)

                # NAIP (4band) patch
                naip_patch = np.moveaxis(
                    src_naip.read(list(range(1, 5)), window=window), 0, -1
                )  # (H, W, 4)

                # CHM + NAIP concatenated
                combined_patch = np.concatenate(
                    [chm_patch, naip_patch], axis=-1
                )  # (H, W, 5)

                patch_filename = f"patch_{patch_id}.tif"
                patch_filepath = os.path.join(output_dir, patch_filename)

                profile = src_chm.profile
                profile.update(
                    {
                        "count": 5,  # 5channel input (1band CHM + 4band NAIP)
                        "height": patch_size,
                        "width": patch_size,
                        "dtype": rasterio.float32,
                        "transform": patch_transform,
                        "nodata": None,  # Nodata value eliminated
                    }
                )

                with rasterio.open(patch_filepath, "w", **profile) as dst:
                    dst.write(
                        np.moveaxis(combined_patch, -1, 0)
                    )  # ✅ (H, W, 5) → (5, H, W) saved

                patch_id += 1

    print(f"✅ Combined patches saved to: {output_dir} (Stored in (H, W, 5) format)")


# ============================
# patch merge function
# ============================
def merge_patches(patch_dir: str, merged_image_path: str) -> None:
    """
    patch file merge and save
    Args:
        patch_dir (str): patch file directory
        merged_image_path (str): merged image file path
    """
    patch_files = glob(os.path.join(patch_dir, "*.tif"))
    if len(patch_files) == 0:
        raise FileNotFoundError("No patch files found in the specified directory.")

    datasets = [rasterio.open(patch) for patch in patch_files]
    merged_array, merged_transform = merge(datasets)

    out_meta = datasets[0].meta.copy()
    out_meta.update(
        {
            "height": merged_array.shape[1],
            "width": merged_array.shape[2],
            "transform": merged_transform,
        }
    )

    with rasterio.open(merged_image_path, "w", **out_meta) as dst:
        dst.write(merged_array)

    for dataset in datasets:
        dataset.close()

    print(f"Merged image saved to: {merged_image_path}")
