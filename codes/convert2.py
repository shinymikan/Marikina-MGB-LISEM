from osgeo import gdal, gdalconst

def convert():

    def ConvertToPCRaster(inputFile, outputFile, ot, VS):
        src_ds = gdal.Open(inputFile)
        if src_ds is None:
            raise FileNotFoundError(f"Cannot open {inputFile}")
        
        dst_ds = gdal.Translate(
            outputFile,
            src_ds,
            format='PCRaster',         # PCRaster driver
            outputType=ot,             # e.g., gdalconst.GDT_Float32
            metadataOptions=[VS]       # e.g., 'VS_Scalar', 'VS_Ldd'
        )
        
        src_ds = None
        dst_ds = None
        print(f"Saved {outputFile} as PCRaster map.")

    # Example usage
    ConvertToPCRaster('output/cover.tif', 'raw-maps/cover.map', gdalconst.GDT_Float32, 'VS_Scalar')
    ConvertToPCRaster('output/lai.tif', 'raw-maps/lai.map', gdalconst.GDT_Float32, 'VS_Scalar')
    ConvertToPCRaster('output/landcover.tif', 'raw-maps/landcover.map', gdalconst.GDT_Float32, 'VS_Scalar')


