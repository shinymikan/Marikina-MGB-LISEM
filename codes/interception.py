import rasterio
import numpy as np
from rasterio.mask import mask
import fiona
import geopandas as gpd
from rasterio.warp import reproject, Resampling

def interception():
    ######### Directory ##########
    mask_path = "raw-maps/mask.tif"
    dataset_path = "raw-maps/Landsat_Bands/"


    ######### Helper Functions ##########

    def preprocess_band(band_name):
        band_path = f"{dataset_path}/{band_name}"

        # --- Open mask first (REFERENCE GRID) ---
        with rasterio.open(mask_path) as mask_src:
            mask = mask_src.read(1)
            mask_transform = mask_src.transform
            mask_crs = mask_src.crs
            mask_shape = mask.shape

            # Output array: SAME SIZE AS MASK
            band_aligned = np.empty(mask_shape, dtype="float32")

            # --- Open Landsat band ---
            with rasterio.open(band_path) as band_src:
                reproject(
                    source=band_src.read(1),
                    destination=band_aligned,
                    src_transform=band_src.transform,
                    src_crs=band_src.crs,
                    dst_transform=mask_transform,
                    dst_crs=mask_crs,
                    resampling=Resampling.bilinear  # continuous data
                )

        # --- Apply mask ---
        band_aligned[mask == 0] = np.nan

        return band_aligned, mask_transform
    
    def save_map(map, map_name, transform):
        with rasterio.open(
        "raw-maps/Landsat_Bands/LC08_L2SP_116050_20201224_20210310_02_T1_SR_B1.TIF"
        ) as src:
            map_meta = src.meta.copy()

        map_meta.update({
            "driver": "GTiff",
            "height": int(map.shape[0]),
            "width": int(map.shape[1]),
            "transform": transform,          
            "count": 1,
            "dtype": "float32",
            "nodata": 0,
            "crs": src.crs                 
        })

        output_path = f'output/{map_name}.tif'

        map_out = map.astype("float32")[np.newaxis, :, :]

        with rasterio.open(output_path, "w", **map_meta) as dest:
            dest.write(map_out)

    ######### Map Generation ##########

    red, transform = preprocess_band('LC08_L2SP_116050_20201224_20210310_02_T1_SR_B4.TIF')
    nir, _ = preprocess_band('LC08_L2SP_116050_20201224_20210310_02_T1_SR_B5.TIF')

    red = np.where(red <= 0, np.nan, red)
    nir = np.where(nir <= 0, np.nan, nir)

    ndvi = np.where((nir + red) == 0, np.nan, (nir-red)/(nir+red))
    c_factor = 1 - np.exp(-2*ndvi/(1.5-ndvi))
    lai = np.where(c_factor < 1, np.log(1-c_factor)/(-0.4), np.nan)
    c_factor = np.where(c_factor < 0, 0, c_factor)
    lai = np.where(lai < 0, 0, lai)

    ######### Save Maps #########

    save_map(ndvi, "ndvi", transform)
    save_map(c_factor, "cover", transform)
    save_map(lai, "lai", transform)