from codes import lulc, interception,convert2, pcraster

print("Getting the LULC...")
lulc.lulc()
print("Done!")
print("Getting the Interception...")
interception.interception()
print("Converting generated maps to pcraster maps...")
convert2.convert()
print("Generating the rest of the maps...")
pcraster.pcraster()
print("Done!")
