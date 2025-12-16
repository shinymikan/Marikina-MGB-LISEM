import rasterio
import numpy as np
from rasterio.mask import mask
from rasterio.features import geometry_mask
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import fiona
import geopandas as gpd
from scipy.ndimage import generic_filter


def lulc():
    ######### Directory ##########
    shapefile_path = "raw-maps/Marikina Data Extracted/Marikina_Watershed_projected.shp"
    dataset_path = "raw-maps/Landsat_Bands/"
    samples_path = "raw-maps/Marikina Training Samples (20201224) - Sted/training_samples_20251109_combined_dissolved.shp"

    with fiona.open(shapefile_path, "r") as shapefile:
        shapes = [feature['geometry'] for feature in shapefile]


    ######### Helper Functions ##########

    #For Preprocessing Bands
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


    #For 8-Neighbor Filtering
    def max_voting_filter(array):
        def max_vote(values):
            values = values[~np.isnan(values)]
            if len(values) == 0:
                return np.nan
            return np.bincount(values.astype(int)).argmax()
        return generic_filter(array,max_vote,size = 3, mode = 'constant', cval = np.nan)

    ######### Preprocess Each Bands ##########

    b1, transform = preprocess_band('LC08_L2SP_116050_20201224_20210310_02_T1_SR_B1.TIF')
    b2, _ = preprocess_band('LC08_L2SP_116050_20201224_20210310_02_T1_SR_B2.TIF')
    b3, _ = preprocess_band('LC08_L2SP_116050_20201224_20210310_02_T1_SR_B3.TIF')
    b4, _ = preprocess_band('LC08_L2SP_116050_20201224_20210310_02_T1_SR_B4.TIF')
    b5, _ = preprocess_band('LC08_L2SP_116050_20201224_20210310_02_T1_SR_B5.TIF')
    b6, _ = preprocess_band('LC08_L2SP_116050_20201224_20210310_02_T1_SR_B6.TIF')
    b7, _ = preprocess_band('LC08_L2SP_116050_20201224_20210310_02_T1_SR_B7.TIF')

    np.seterr(divide='ignore', invalid ='ignore')

    ndvi = (b5 - b4)/(b5 + b4) 
    ndvi[(b5 + b4) == 0] = np.nan


    ######### Feature Preprocessing ##########

    features = np.dstack((b1,b2,b3,b4,b5,b6,b7,ndvi))
    X = features.reshape(-1, features.shape[-1])
    gdf = gpd.read_file(samples_path)
    training_shapes = gdf.geometry
    training_labels = gdf["Class"]

    labels = np.full(ndvi.shape, np.nan)
    out_shape = ndvi.shape

    mapping = {
        "Agriculture": 1,
        "Bareland": 2,
        "Builtup" : 3,
        "Forest" : 4,
        "Grassland / Shurbs": 5,
        "Waterbody" : 6
    }

    for geom, label in zip(training_shapes, training_labels):
        mask_geom = geometry_mask(
            [geom.__geo_interface__],
            transform=transform,
            invert=True,
            out_shape=labels.shape
        )
        labels[mask_geom] = mapping[label]

    ######### Training ##########

    y = labels.flatten()
    mask_valid = ~np.isnan(y)
    X_train = X[mask_valid]
    y_train = y[mask_valid]

    X_train, X_test, y_train, y_test = train_test_split(X_train, y_train, test_size = 0.3, random_state=42, stratify=y_train)
    clf = RandomForestClassifier(n_estimators=500, random_state=42)
    clf.fit(X_train,y_train)

    y_pred = clf.predict(X)
    lulc = y_pred.reshape(ndvi.shape)

    mask_geom = geometry_mask(
        shapes,
        transform=transform,
        invert=True,
        out_shape=lulc.shape
    )

    lulc_clipped = np.where(mask_geom, lulc, np.nan)


    ######### Post-Processing ##########

    lulc_cleaned = max_voting_filter(lulc_clipped)

    cm = confusion_matrix(y_test, clf.predict(X_test))
    reverse_map = {v: k for k, v in mapping.items()}

    print("========== Confusion Matrix ==========")
    print(cm)

    print("========== Classification Report ==========")
    print(classification_report(y_test,clf.predict(X_test)))


    with rasterio.open(
        "raw-maps/Landsat_Bands/LC08_L2SP_116050_20201224_20210310_02_T1_SR_B1.TIF"
    ) as src:
        lulc_meta = src.meta.copy()

    lulc_meta.update({
        "driver": "GTiff",
        "height": int(lulc_cleaned.shape[0]),
        "width": int(lulc_cleaned.shape[1]),
        "transform": transform,          # must match lulc_clipped
        "count": 1,
        "dtype": "int16",
        "nodata": 0,
        "crs": src.crs                   # NOT b1.crs
    })

    output_path = "output/LULC.tif"

    # Ensure correct shape: (bands, rows, cols)
    lulc_out = lulc_cleaned.astype("int16")[np.newaxis, :, :]

    with rasterio.open(output_path, "w", **lulc_meta) as dest:
        dest.write(lulc_out)
