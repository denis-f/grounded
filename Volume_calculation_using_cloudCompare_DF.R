# ______________________________________________________________________________________ 
# ______________________________________________________________________________________ 
# ______________________________________________________________________________________ 
# |                                                                                    |
# |          SCRIPTS REALIZED BY Fabrice VINATIER fabrice.vinatier@inrae.fr            | 
# |                          and Denis FEURER denis.feurer@ird.fr                      | 
# |                              ----------------                                      | 
# |                              LICENCE CC-BY-SA                                      | 
# |                              ----------------                                      |
# | This license lets others remix, adapt, and build upon your work even for           |
# | commercial purposes, as long as they credit you and license their new creations    |
# | under the identical terms.                                                         |
# |                                                                                    |
# | The proposed code has a purely academic purpose, is valid under the conditions     |
# | of use of the scientific project for which it was funded and at the date of        |
# | acceptance of the article presenting the code. As with any research work, the      |
# | code is not free of possible errors, approximations, sub-optimisations or          |
# | defects in monitoring dependencies between libraries of the programme.             |
# |                                                                                    |
# ______________________________________________________________________________________ 
# |                                                                                    |
# | Cette licence permet à d'autres personnes de remixer, d'adapter et de              |
# | développer ce travail, même à des fins commerciales, à condition qu'elles          |
# | créditent l'auteur et accordent une licence pour leurs nouvelles créations aux     |
# | mêmes conditions.                                                                  |
# |                                                                                    |
# | Le code proposé a une visée purement académique, est valable dans les conditions   |
# | d'utilisation du projet scientifique pour lequel il a été financé et à la date de  |
# | d'acceptation de l'article de présentation du code.                                |
# | Comme tout travail de recherche, le code n'est pas exempt d'éventuelles erreurs,   |
# | approximations, sous-optimisations ou défauts de suivi des dépendances entre       |
# | sous-éléments du programme.                                                        |
# ______________________________________________________________________________________ 
# ______________________________________________________________________________________ 
# ______________________________________________________________________________________ 
# |                                                                                    |
# |                    PREPARATION OF THE WORK ENVIRONMENT                             |
# ______________________________________________________________________________________ ---------------------------------------------------------------------

rm(list=ls(all=TRUE))
# Libraries                                                                            |----
library(terra)
library(plyr)
#library(rgeos)
library(scales)
library(prettymapr)

#It is necessary to install cloudCompare before launching the program:
# For linux distributions: sudo snap install cloudcompare

# ______________________________________________________________________________________ ---------------------------------------------------------------------
# |                                                                                    | ------------------------------------------------------------------------
# |                   MAIN FUNCTIONS                                                   | ------------------------------------------------------
# ______________________________________________________________________________________ ---------------------------------------------------------------------

# | Find zone of prospection    (CLOUDCOMPARE)   ProspectZone      Fabrice Vinatier  | ----------------------------------------------
ProspectZone=function(pathRef,pathCompared,pathCLOUDS){
  if(Sys.info()["sysname"]=="Windows") pathToProgram="C:/PROGRA~1/CloudCompare/CloudCompare"
  if(Sys.info()["sysname"]=="Linux")  pathToProgram="cloudcompare.CloudCompare"
  
  # Cloud to cloud difference using cloud compare, then rasterization of the cloud difference
  system(paste(pathToProgram,"-SILENT",
               "-O","-GLOBAL_SHIFT",paste(c(0,0,0),collapse=" "),pathRef, 
               "-O","-GLOBAL_SHIFT",paste(c(0,0,0),collapse=" "),pathCompared,
               "-c2c_dist -MAX_DIST 0.1",
               "-AUTO_SAVE OFF",
               "-RASTERIZE -GRID_STEP 0.001 -EMPTY_FILL INTERP -OUTPUT_RASTER_Z",collapse=" "),ignore.stderr = TRUE,ignore.stdout = TRUE)
  # Selection of the type of survey using the character string pathRef
  typeReleve=strsplit(tail(strsplit(pathRef,"/")[[1]],1),"_")[[1]][3]
  method=strsplit(pathRef,"/")[[1]][11]
  zoneStudy=strsplit(pathRef,"/")[[1]][1]
  
  # Estimation of the hole contour (in 2D)
  tmp=rast(paste(pathCLOUDS,dir(pathCLOUDS,pattern="_C2C_DIST_MAX_DIST_0.1_RASTER_Z_"),sep=""),lyrs=2) # downloading the raster of cloud difference
  tmp=focal(tmp,w=25,fun=mean,na.rm=T)
  tmp
}
  
# | Delimitate border of excavated holes         delimitateHoles   Fabrice Vinatier  | ----------------------------------------------
delimitateHoles=function(pathCLOUDS=pathDIR,rasterZone=rast_sel,tol_simplify=0.01,width_buffer=0.02,area_hole=0.008,thres_hole=0.00021,K.Cox.threshold=0.35,minimal_hole_area=0.004){
  roundness=function(pol){4*pi*expanse(pol)/(perim(pol)^2)} #fonction which calculates roundness according to cox formula Cox, E. P. (1927). A Method of Assigning Numerical and Percentage Values to the Degree of Roundness of Sand Grains. Journal of Paleontology, 1(3), 179–183. http://www.jstor.org/stable/1298056
  
  mask_zone=(rasterZone>thres_hole)      # Thresholding the smoothed raster to identify the hole
  rCLUMP=patches(mask_zone,zeroAsNA=T)         # detecting patches of connected cells with a unique ID
  dCLUMP=na.omit(data.frame(freq(rCLUMP))) # Estimation of areas of patches (in number of cells)
  maxV=dCLUMP[dCLUMP$count*mean(res(rCLUMP))^2>area_hole,"value"] # Identification of hole contour that reached a minimal area (multiple holes)
  rCLUMP[is.na(rCLUMP)]=0      # Selection of hole contour (1/3)
  rCLUMP[!rCLUMP[]%in%maxV]=NA # Selection of hole contour (2/3)
  rCLUMP[rCLUMP[]%in%maxV]=1   # Selection of hole contour (3/3)
  vCLUMP=as.polygons(rCLUMP,aggregate=T) # Polygonization of the hole contour
  vCLUMP=simplifyGeom(vCLUMP,tolerance=tol_simplify)  # Reduction of stairs in the polygon
  vCLUMP=disagg(vCLUMP)                # Splitting multiple polygons
#print(roundness(vCLUMP))
  vCLUMP=vCLUMP[roundness(vCLUMP)>K.Cox.threshold] # Discarding "non-round" polygons
  vCLUMP=vCLUMP[expanse(vCLUMP)>minimal_hole_area]
#print(roundness(vCLUMP))
  vCLUMP=buffer(vCLUMP,width=width_buffer) # Enlargement of polygon area
  vCLUMP=vCLUMP[order(crds(vCLUMP)[,1]),]   # Reordering the multiple polygons from left to right #DF /!\ça a pas l'air de marcher
  
  vCLUMP
}  

# | Rasterize clouds    (CLOUDCOMPARE)         rasterizeClouds           Denis Feurer  | ----------------------------------------------
rasterizeClouds=function(pathRef,pathCompared,pathCLOUDS){
  if(Sys.info()["sysname"]=="Windows")pathToProgram="C:/PROGRA~1/CloudCompare/CloudCompare"
  if(Sys.info()["sysname"]=="Linux")  pathToProgram="cloudcompare.CloudCompare"
  
  
  # Rasterization of each cloud
  system(paste(pathToProgram,"-SILENT",
               "-O",
               "-GLOBAL_SHIFT",paste(c(0,0,0),collapse=" "),pathRef,
               "-SOR 6 1",
               "-RASTERIZE -GRID_STEP 0.001 -EMPTY_FILL INTERP -OUTPUT_RASTER_Z",collapse=" "),ignore.stderr = TRUE,ignore.stdout = TRUE)
  
  system(paste(pathToProgram,"-SILENT",
               "-O",
               "-GLOBAL_SHIFT",paste(c(0,0,0),collapse=" "),pathCompared,
               "-SOR 6 1",
               "-RASTERIZE -GRID_STEP 0.001 -EMPTY_FILL INTERP -OUTPUT_RASTER_Z",collapse=" "),ignore.stderr = TRUE,ignore.stdout = TRUE)
}  

# | Volume calculation    (CLOUDCOMPARE)         calcVol           Fabrice Vinatier  | ----------------------------------------------
calcVol=function(pathRef,pathCompared,pathCLOUDS,holes){
  if(Sys.info()["sysname"]=="Windows")pathToProgram="C:/PROGRA~1/CloudCompare/CloudCompare"
  if(Sys.info()["sysname"]=="Linux")  pathToProgram="cloudcompare.CloudCompare"

  
  # Get new filenames
  listFilesRef=dir(pathCLOUDS,pattern=gsub(".ply","_SOR_",tail(strsplit(pathRef,"/")[[1]],1)))
  listFilesRef=listFilesRef[grep(".bin",listFilesRef)]
  pathRefNew=paste(pathCLOUDS,listFilesRef,sep="")
  listFilesCompared=dir(pathCLOUDS,pattern=gsub(".ply","_SOR_",tail(strsplit(pathCompared,"/")[[1]],1)))
  listFilesCompared=listFilesCompared[grep(".bin",listFilesCompared)]
  pathComparedNew=paste(pathCLOUDS,listFilesCompared,sep="")
  
  # Estimation of volume behind hole contours
  rCROPref=list() ; rCROPcomp=list()
  vols=sapply(1:length(holes),function(winSel){ # calculation on every polygons
    dWIN=crds(holes[winSel,]) # Recuperation of the numeric coordinates of the hole vertexes
    # Cropping the cloud around hole borders, meshing, then resampling at high density of points (Reference)
    system(paste(pathToProgram,"-SILENT",
                 "-C_EXPORT_FMT ASC",
                 "-O","-GLOBAL_SHIFT",paste(c(0,0,0),collapse=" "),pathRefNew,
                 "-CROP2D Z",
                 dim(dWIN)[1],
                 paste(c(t(dWIN),recursive=T),collapse=" "),
                 "-DELAUNAY -BEST_FIT",
                 "-SAMPLE_MESH DENSITY 10000000",
                 "-RASTERIZE -GRID_STEP 0.001 -EMPTY_FILL INTERP -OUTPUT_RASTER_Z",
                 collapse=" "),ignore.stderr = TRUE,ignore.stdout = TRUE)
    
    # Cropping the cloud around hole borders, meshing, then resampling at high density of points (Comparison)
    system(paste(pathToProgram,"-SILENT",
                 "-C_EXPORT_FMT ASC",
                 "-O","-GLOBAL_SHIFT",paste(c(0,0,0),collapse=" "),pathComparedNew,
                 "-CROP2D Z",
                 dim(dWIN)[1],
                 paste(c(t(dWIN),recursive=T),collapse=" "),
                 "-DELAUNAY -BEST_FIT",
                 "-SAMPLE_MESH DENSITY 10000000",
                 "-RASTERIZE -GRID_STEP 0.001 -EMPTY_FILL INTERP -OUTPUT_RASTER_Z",
                 collapse=" "),ignore.stderr = TRUE,ignore.stdout = TRUE)
    # Get the rasterized files
    rasterCROPED=dir(pathCLOUDS,pattern="_CROPPED_SAMPLED_POINTS_RASTER_Z_")
    rCROPref[[winSel]] <<-rast(paste0(pathCLOUDS,rasterCROPED[grep("_0_",rasterCROPED)]),lyrs=1) # downloading the raster of cloud difference
    rCROPcomp[[winSel]]<<-rast(paste0(pathCLOUDS,rasterCROPED[grep("_1_",rasterCROPED)]),lyrs=1)# downloading the raster of cloud difference
    file.remove(paste(pathCLOUDS,dir(pathCLOUDS,pattern="_RASTER_"),sep=""))
 
    # Recuperation of the transformed clouds
    cloudCROPED=dir(pathCLOUDS,pattern="_CROPPED_SAMPLED_POINTS_")
    
    cropRef=paste(pathCLOUDS,cloudCROPED[grep("_0_",cloudCROPED)],sep="")
    cropCompared=paste(pathCLOUDS,cloudCROPED[grep("_1_",cloudCROPED)],sep="")
    # Volume calculation between the comparison and the reference clouds
    system(paste("cloudcompare.CloudCompare","-SILENT",
                 "-O","-GLOBAL_SHIFT",paste(c(0,0,0),collapse=" "),cropCompared, 
                 "-O","-GLOBAL_SHIFT",paste(c(0,0,0),collapse=" "),cropRef,
                 "-VOLUME -GRID_STEP 0.001",
                 collapse=" "),ignore.stderr = TRUE,ignore.stdout = TRUE)
    # Recuperation of the result
    vol=readLines(paste(pathCLOUDS,dir(pathCLOUDS,pattern="VolumeCalculationReport_"),sep=""),4)[1]
    vol=strsplit(vol," ")[[1]][2]
    vol=as.numeric(vol)
    # Removing temporary CloudCompare files
    file.remove(paste(pathCLOUDS,dir(pathCLOUDS,pattern="_CROPPED_"),sep=""))
    file.remove(paste(pathCLOUDS,dir(pathCLOUDS,pattern="VolumeCalculationReport_"),sep=""))
    vol})
  # Attribution of a ID for every volume calculated from multiple or single holes
  file.remove(paste(pathCLOUDS,dir(pathCLOUDS,pattern="_SOR_"),sep=""))
  repD=paste("D",1:length(vols),sep="")
  holes$ID=repD
  # Results
  data.frame(Replicate=repD,Volume=vols)
}

# | Filtering multiple ply                       filterRRF         Fabrice Vinatier  | ----------------------------------------------
# useful for flash lidar data
filterRRF=function(pathIN=pathRef,pathOUT="IN/2018-10_Mauguio/Flash_Lidar/Fosse1_H3_V_Avant.ply"){
  # Selection of all ply files
  filesPLY=sapply(dir(pathIN,pattern=".ply$"),function(file_sel){vcgPlyRead(paste(pathIN,"/",file_sel,sep=""))$vb},simplify="array")
  # Application of a median filter on depth
  medPLY=apply(filesPLY,1:2,median)
  tmp=t(medPLY)
  tmp=as.data.frame(tmp)
  tmp=tmp[tmp$V1!=0 & tmp$V2!=0 & tmp$V3!=0,]
  medPLY=t(tmp)
  # Formatting the resulting data.frame in a ply file for export
  medPLY=list(vb=medPLY,material=list())
  attr(medPLY,"class")="mesh3d"
  vcgPlyWrite(medPLY,filename = pathOUT)
}


# ______________________________________________________________________________________ ---------------------------------------------------------------------
# |                                                                                    | ------------------------------------------------------------------------
# |                     VOLUME CALCULATION                                             | ------------------------------------------------------
# ______________________________________________________________________________________ ---------------------------------------------------------------------

# Selection of the directory where clouds are located
# <attributes>_0.ply: before excavation (Reference cloud in cloucompare)
# <attributes>_1.ply: after excavation (Compared cloud in cloudcompare)
path0=file.choose()
path1=file.choose()
#file_scale_factor="/home/feurer/Documents/0_PROJETS/2023-202x_VALO_densito_operationelle/2023-2024_Stage_chaine_traitement/DATA/AF1H1_copy_clouds_and_scale/scale_factor_matrix.txt"

# Suppression of the residual cloudCompare files
endFile=strsplit(path0,"/")
pathDIR=sub(endFile[[1]][length(endFile[[1]])],"",path0)
file.remove(paste(pathDIR,dir(pathDIR,pattern="_C2C_"),sep=""),showWarnings=F)
file.remove(paste(pathDIR,dir(pathDIR,pattern="_SOR"),sep=""),showWarnings=F)
file.remove(paste(pathDIR,dir(pathDIR,pattern="VolumeCalculationReport_"),sep=""),showWarnings=F)
file.remove(paste(pathDIR,dir(pathDIR,pattern="_RASTER_"),sep=""),showWarnings=F)

# Volume calculation
print("Prospect zone calculation")
start_time <- Sys.time()
zone_tot=ProspectZone(pathRef=path0,pathCompared=path1,pathCLOUDS=pathDIR);# Calculation of the prospecting zone
end_time <- Sys.time()
print(end_time - start_time)
plot(zone_tot,main=basename(path0)) # Plotting the prospecting zone
#zone_sel=draw(x="extent")  # selection of the prospecting zone
#rast_sel=crop(zone_tot,zone_sel) # cropping of the prospecting zone
#plot(rast_sel) 
rast_sel=zone_tot
#giving an arbitrary metric coordinate system to be able to ysae the expanse function
crs(rast_sel)<-"epsg:32632"

#calculating/automatically detecting the individual holes
print("Detecting Holes")
start_time <- Sys.time()
holes_sel=delimitateHoles(pathCLOUDS=pathDIR,rasterZone=rast_sel,tol_simplify=0.01,
                          width_buffer=0.02,area_hole=0.008,thres_hole=0.005,K.Cox.threshold=0.6) # thres_hole_FL=0.0004,thres_hole_PH=0.00021
end_time <- Sys.time()
print(end_time - start_time)
plot(holes_sel,add=T) #plotting the detected holes

#deleting temporary files
print("Deleting temporary clouds and computing SOR rasters of the clouds")
start_time <- Sys.time()
file.remove(paste(pathDIR,dir(pathDIR,pattern="_C2C_"),sep=""))
#compute rasters of the clouds
rasterizeClouds(pathRef=path0,pathCompared=path1,pathCLOUDS=pathDIR)
end_time <- Sys.time()
print(end_time - start_time)

print("Volumes calculation")
start_time <- Sys.time()
res=calcVol(pathRef=path0,pathCompared=path1,pathCLOUDS=pathDIR,holes=holes_sel) #calculating the volumes of each holes
end_time <- Sys.time()
print(end_time - start_time)
print(res)
text(holes_sel,paste(res$Replicate," \n ",res$Volume*1000000))

#export des résultats
write.table(res,paste(pathDIR,"results.txt",sep=""),quote=F,row.names=F)

pdf(paste(pathDIR,"results.pdf",sep=""), width = 8, height = 8)
plot(zone_tot,main=basename(path0))
plot(holes_sel,add=T)
text(holes_sel,paste(res$Replicate," \n ",res$Volume*1000000))
dev.off()
            
