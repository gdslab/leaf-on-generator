import os
import numpy as np
from math import ceil
import rasterio
from rasterio.windows import Window
from rasterio.merge import merge
from glob import glob

# ============================
# NDHM 생성 함수
# ============================
def generate_ndhm(dsm_file, dtm_file, output_ndhm_file):
    """
    DSM과 DTM을 사용하여 NDHM (Normalized Digital Height Model)을 생성합니다.
    99.99th 백분위수를 초과하는 값은 0으로 설정합니다.
    
    Args:
        dsm_file (str): DSM 파일 경로
        dtm_file (str): DTM 파일 경로
        output_ndhm_file (str): 출력 NDHM 파일 경로
    """
    with rasterio.open(dsm_file) as dsm, rasterio.open(dtm_file) as dtm:
        # DSM과 DTM 데이터를 읽어옴
        dsm_data = dsm.read(1)
        dtm_data = dtm.read(1)
        
        # NDHM 생성
        ndhm_data = dsm_data - dtm_data
        ndhm_data[ndhm_data < 0] = 0  # 음수 값 제거
        
        # 99.9th 백분위수 계산
        valid_ndhm_values = ndhm_data[ndhm_data > 0]  # 유효한 NDHM 값만 사용
        if valid_ndhm_values.size > 0:
            percentile_99_9 = np.percentile(valid_ndhm_values, 99.999)
            print(f"99.99th Percentile Height: {percentile_99_9}")
            
            # 99.9th 백분위수 초과 값 0으로 설정
            ndhm_data[ndhm_data > percentile_99_9] = 0
        else:
            print("No valid NDHM values found. Skipping percentile adjustment.")
        
        # 출력 파일 저장
        profile = dsm.profile
        profile.update(dtype=rasterio.float32)
        
        with rasterio.open(output_ndhm_file, "w", **profile) as dst:
            dst.write(ndhm_data.astype(rasterio.float32), 1)
    
    print(f"NDHM generated with 99.99th percentile adjustment: {output_ndhm_file}")

# ============================
# 패치 분할 함수
# ============================
def save_patches(image_path, output_dir, patch_size=256, overlay=0):
    """
    이미지를 작은 패치로 분할하고 저장합니다.
    Args:
        image_path (str): 원본 이미지 파일 경로
        output_dir (str): 패치를 저장할 폴더 경로
        patch_size (int): 각 패치의 크기
        overlay (int): 패치 간 오버랩 크기
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
                patch_transform = src.window_transform(window)
                
                profile = src.profile
                profile.update({
                    'height': patch_size,
                    'width': patch_size,
                    'count': 1,
                    'transform': patch_transform
                })
                
                with rasterio.open(patch_filepath, 'w', **profile) as dst:
                    dst.write(patch, 1)
                
                patch_id += 1
    print(f"Patches saved to: {output_dir}")

# ============================
# 패치 병합 함수
# ============================
def merge_patches(patch_dir, merged_image_path):
    """
    패치 파일들을 병합하여 하나의 이미지로 저장합니다.
    Args:
        patch_dir (str): 패치가 저장된 폴더 경로
        merged_image_path (str): 병합된 이미지를 저장할 경로
    """
    patch_files = glob(os.path.join(patch_dir, '*.tif'))
    if len(patch_files) == 0:
        raise FileNotFoundError("No patch files found in the specified directory.")
    
    datasets = [rasterio.open(patch) for patch in patch_files]
    merged_array, merged_transform = merge(datasets)
    
    out_meta = datasets[0].meta.copy()
    out_meta.update({
        'height': merged_array.shape[1],
        'width': merged_array.shape[2],
        'transform': merged_transform
    })
    
    with rasterio.open(merged_image_path, 'w', **out_meta) as dst:
        dst.write(merged_array)
    
    for dataset in datasets:
        dataset.close()
    print(f"Merged image saved to: {merged_image_path}")

# ============================
# 좌표 시스템 업데이트 함수
# ============================
def update_coordinate_system(src_dir, gen_dir, updated_gen_dir):
    """
    Source 패치의 좌표 시스템을 Generated 패치에 적용합니다.
    Args:
        src_dir (str): Source 패치 폴더 경로
        gen_dir (str): Generated 패치 폴더 경로
        updated_gen_dir (str): 좌표가 업데이트된 패치를 저장할 폴더 경로
    """
    if not os.path.exists(updated_gen_dir):
        os.makedirs(updated_gen_dir)
    
    src_patches = sorted(glob(os.path.join(src_dir, '*.tif')))
    gen_patches = sorted(glob(os.path.join(gen_dir, '*.tif')))
    
    if len(src_patches) != len(gen_patches):
        raise ValueError("The number of src and gen patches must be equal.")
    
    for src_patch, gen_patch in zip(src_patches, gen_patches):
        with rasterio.open(src_patch) as src_ds:
            src_transform = src_ds.transform
            src_crs = src_ds.crs
            profile = src_ds.profile
        
        with rasterio.open(gen_patch) as gen_ds:
            gen_data = gen_ds.read(1)
        
        profile.update({
            'transform': src_transform,
            'crs': src_crs
        })
        
        updated_gen_patch_path = os.path.join(updated_gen_dir, os.path.basename(gen_patch))
        with rasterio.open(updated_gen_patch_path, 'w', **profile) as dst:
            dst.write(gen_data, 1)
    print(f"Coordinate system updated patches saved to: {updated_gen_dir}")
