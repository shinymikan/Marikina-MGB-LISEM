import rasterio
import numpy as np
from rasterio.mask import mask
import fiona
import geopandas as gpd

def interception():
    ######### Directory ##########
    shapefile_path = "raw-maps/Marikina Data Extracted/Marikina_Watershed_projected.shp"
    dataset_path = "raw-maps/Landsat_Bands/"

    with fiona.open(shapefile_path, "r") as shapefile:
        shapes = [feature['geometry'] for feature in shapefile]


    ######### Helper Functions ##########

    def preprocess_band(band_path):
        path = f'{dataset_path}/{band_path}'
        gdf = gpd.read_file(shapefile_path)

        with rasterio.open(path) as src:
            if gdf.crs != src.crs:
                print("Warning: CRS Mismatch")
                gdf = gdf.to_crs(src.crs)

            shapes = [geom.__geo_interface__ for geom in gdf.geometry]
            clipped, transform = mask(src, shapes, crop=True, nodata=0)

        band_clipped = clipped[0].astype("float32")

        return band_clipped, transform
    
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



    ######### SMAX ##########

    smax = np.full_like(lai, np.nan, dtype="float32")

    lulc_path = "output/LULC.tif"

    with rasterio.open(lulc_path) as src_lulc:
        lulc = src_lulc.read(1)

    forest = (lulc == 4)
    grass  = (lulc == 5)
    agri   = (lulc == 1)
    built  = (lulc == 3)

    smax[forest] = 0.2856 * lai[forest]
    smax[grass]  = 0.1713 * lai[grass]

    smax[agri] = (
        0.935
        + 0.498 * lai[agri]
        - 0.00575 * lai[agri]**2
    )

    smax[built] = (
        0.935
        + 0.498 * lai[built]
        - 0.00575 * lai[built]**2
    )

    nodata = np.nan
    smax[np.isnan(smax)] = nodata

    ######### Save Maps #########

    save_map(ndvi, "ndvi", transform)
    save_map(c_factor, "c_factor", transform)
    save_map(lai, "lai", transform)
    save_map(smax, "smax", transform)