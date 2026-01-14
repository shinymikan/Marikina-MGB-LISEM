from pcraster import *
from pcraster.framework import *
from osgeo import gdal, gdalconst

def pcraster():
    setclone('mask.map')
    setglobaloption('lddin')


    ####################
    ## Input base maps##
    ####################
    print("Unpacking base maps...")

    mask = readmap('raw-maps/mask.map')
    dem = readmap('raw-maps/dem.map')
    dem_mask = dem*mask
    soil = readmap('raw-maps/soil.map')
    soil_mask = soil*mask
    landcover = readmap('raw-maps/landcover.map')
    landcover_mask = landcover*mask
    lai = readmap('raw-maps/lai.map')
    lai_mask = lai*mask
    cover = readmap('raw-maps/cover.map')
    cover_mask = cover*mask



    #####################
    ##Input data tables##
    #####################

    print("Reading input data tables...")
    
    soil_theta = lookupscalar("raw-maps/soil_theta.tbl", soil_mask) #soil porosity (cm3/cm3)
    soil_wp = lookupscalar("raw-maps/soil_wp.tbl", soil_mask) #soil moisture content during dry season (cm3/cm3)
    soil_fc = lookupscalar("raw-maps/soil_fc.tbl", soil_mask) #soil moisture content during wet season (cm3/cm3)
    soil_depth = lookupscalar("raw-maps/soil_depth.tbl", soil_mask) #soil depth in mm
    soil_psi = lookupscalar("raw-maps/soil_psi.tbl", soil_mask) #soil suction wetting front (cm)
    mannings = lookupscalar("raw-maps/soil_mannings.tbl", soil_mask) #manning's coefficient (-)

    ksat = lookupscalar("raw-maps/landcov_ksat.tbl", landcover_mask) #saturated hydraulic conductivity (mm/hr)
    plant_height = lookupscalar("raw-maps/landcov_plantheight.tbl", landcover_mask) #plant height in m
    rr = lookupscalar("raw-maps/landcov_rr.tbl", landcover_mask) #random roughness

    #####################################
    ##Report maps from the input tables##
    #####################################

    print("Generating maps from input tables...")

    report(soil_theta, 'output/soil_porosity.map')
    report(soil_wp, 'output/soil_wp.map')
    report(soil_fc, 'output/soil_fc.map')
    report(soil_depth, 'output/soil_depth.map')
    report(soil_psi, 'output/soil_psi.map')
    report(mannings, 'output/mannings.map')

    report(ksat, 'output/ksat.map')
    report(plant_height, 'output/plant_height.map')
    report(rr, 'output/rr.map')


    ##################################
    ##Derive catchment-related maps##
    ##################################
    print("Deriving catchment-related maps...")

    ldd_dem = lddcreatedem(dem*mask, 1e30, 1e30, 1e30, 1e30)
    ldd = lddcreate(ldd_dem*mask, 1e30, 1e30, 1e30, 1e30)
    outpoint = pit(ldd)
    gradient2 = max(0.01, sin(atan(slope(dem))))

    report(gradient2, 'output/gradient2.map')
    report(ldd, 'output/ldd.map')
    report(outpoint, 'output/outpoint.map')


    ############################
    ##Create rainfall zone map##
    ############################

    print("Creating rainfall zone...")

    rainfall_zone = nominal(mask)
    report(rainfall_zone, 'output/id.map')

    #######################
    ##Create landuse maps##
    #######################

    print("Creating land use maps...")

    con1 = landcover == 4 #create boolean condition wherein the statement is true if the landcover is forest 
    con2 = landcover == 5 #create boolean condition wherein the statement is true if the landcover is shrub
    con5 = con1|con2 #creates a boolean condition that incorporates the previous 2 conditions
    litter = ifthenelse(con5 == 1, scalar(0.7), scalar(0)) #creates a map wherein if the condition is satisfied, a value of 0.7 is assigned to the pixel. if the condition is unsatisfied, a value of 0 is assigned to the pixel

    con6 = landcover == 1 #create boolean condition wherein the statement is true if the landcover is agri
    con7 = landcover == 4 #create boolean condition wherein the statement is true if the landcover is grass
    con8 = landcover == 1 #create boolean condition wherein the statement is true if the landcover is agri

    smax_forest = lai*scalar(0.2856)*scalar(con1)
    smax_shrub = lai*scalar(0.1713)*scalar(con2)
    smax_pc = lai*scalar(0.1713)*scalar(con8)
    smax_grass = ((ln(lai) * scalar(0.912)) + scalar(0.703))*scalar(con7)

    smax_ac1 = scalar(0.935)+scalar(0.498)
    smax_ac2 = lai-scalar(0.00575) 
    smax_ac3 = lai*lai
    smax_ac4 = smax_ac1*smax_ac2*smax_ac3*scalar(con6)        

    smax_total = smax_forest + smax_shrub + smax_pc + smax_grass + smax_ac4  
            
    grass = mask*scalar(0)


    report(litter, 'output/litter.map')
    report(grass, 'output/grass.map')
    report(smax_total, 'output/smax.map')


    #######################
    ##create surface maps##
    #######################

    print("Creating surface maps...")

    stone = mask*scalar(0)
    crust = mask*scalar(0)
    compact = mask*scalar(0)
    hardsurf = mask*scalar(0)

    report(stone, 'output/stone.map')
    report(crust, 'output/crust.map')
    report(compact, 'output/compact.map')
    report(hardsurf, 'output/hardsurf.map')

    #######################
    ##Create channel maps##
    #######################

    print("Creating channel maps...")

    accuflux = accuflux(ldd, 1)
    streamorder = streamorder(ldd)

    channelmask = ifthenelse((accuflux >= scalar(100000)) | (streamorder >= scalar(6)), scalar(1), scalar(0))
    channelldd = ifthen(channelmask == scalar(1), ldd)

    chancoh = channelmask * scalar(8)
    chanman = channelmask * scalar(0.04)
    chanside = channelmask * scalar(0)
    chanksat = channelmask * scalar(1)
    changrad = channelmask * scalar(0.002)
    chanwidth = channelmask * scalar(6)

    report(channelmask, 'output/channelmask.map') #previously accuflux100_or_streamorder6.map
    report(channelldd, 'output/channelldd.map')
    report(chancoh, 'output/chancoh.map')
    report(chanman, 'output/chanman.map')
    report(chanside, 'output/chanside.map')
    report(chanksat, 'output/chanksat.map')
    report(changrad, 'output/changrad.map')
    report(chanwidth, 'output/chanwidth.map')