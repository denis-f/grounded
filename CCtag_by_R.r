my_path="~/Documents/0_PROJETS/2023-202x_VALO_densito_operationelle/2023-2024_Stage_chaine_traitement/DATA/"
data_dir="~/Documents/0_PROJETS/2023-202x_VALO_densito_operationelle/2023-2024_Stage_chaine_traitement/DATA/AF1H1_copy/"
Out_dir="~/Documents/0_PROJETS/2023-202x_VALO_densito_operationelle/2023-2024_Stage_chaine_traitement/DATA/AF1H1_copy_out/"
detection_args=paste("-n 3 -i ",data_dir,sep="")
detection_results_filename="stdoutANDstderr.txt"
suffix_CCTAG_coords_file="_CCTAG_coords_andID.txt"
reglets=data.frame(A=c(0,1),B=c(2,3),C=c(4,5),D=c(6,7))
reglets_size=data.frame(A=0.22,B=0.22,C=0.22,D=0.22)
rel_path_out_clouds_and_scale="AF1H1_copy_clouds_and_scale"

#reglets[,1]
#setwd(my_path)

commande="/home/feurer/Documents/0_PROJETS/2023-202x_VALO_densito_operationelle/SCRIPTS/CCTag-develop/build/Linux-x86_64/detection"
#execution de la commande sur le répertoire sélectionné
a=system2(command = commande, args = detection_args, stdout = TRUE, stderr = TRUE)
write(a,file=paste(my_path,detection_results_filename,sep=""))
#a=readLines(paste(my_path,detection_results_filename,sep=""))

#on fait un data frame en dupliquant les indices de ligne pour débugage
res=data.frame(line=1:length(a),content=a)
#on ne récupère que les lignes avec numéro de frame, les lignes se terminant par 1 ainsi que la ligne Done qui contient le numéro d'image et la ligne detected qui contient le nombre de points détectés
res_short=res[grep("frame| 1$|Done|detected",res[,2]),]
#l'indice de fin de bloc est celui où il y a "Done"
idx2=grep("Done",res_short[,2])
#C'est aussi la ligne où il y a le nom des images
image_list=basename(res_short[idx2,2])
#l'indice de début de bloc est calculé à partir de l'indice de fin de bloc
idx1=c(1,1+idx2[-length(idx2)])


#boucle sur les blocs => à la fin on a un fichier par image avec les coordonnées des mires des réglets complets
for (i in 1:length(idx2)) {
  #this_image=basename(res_short[idx2[i],2])
  #on récupère le nom de l'image sans extension dans la ligne idx2[i] qui contient "Done" (on aurait aussi pu prendre dans image_list)
  this_image=sub(pattern = "(.*)\\..*$", replacement = "\\1", basename(res_short[idx2[i],2]))
  #le nombre de points détectés est dans la ligne précédente
  n_detected=as.numeric(strsplit(res_short[idx2[i]-1,2]," ")[[1]][1])
  #on ne traite que les images où il y a plus de 0 mires détectées ; on vérifie qu'on a le bon nombre de lignes
  if ((n_detected==idx2[i]-idx1[i]-2) & (n_detected!=0)) {
    #il suffit de couper les lignes aux espaces et de transformer ça en data.frame et remettre dans le bon sens pour avoir les targets détéctées
    detected_targets=t(data.frame(strsplit(res_short[(idx1[i]+1):(idx2[i]-2),2]," ")))
    #On se focalise à présent sur les targets détectées dans les réglets complets
    detected_targets_in_complete_rulers=NULL
    for (reglet in reglets) {
      #on récupère les indices de match entre les target detectées et le réglet courant
      idx_ruler=match(reglet,detected_targets[,3])
      #si aucun des index n'est un NA, c'est qu'on a bien un réglet complet => on l'ajoute ; on garde les coordonnées image (colonnes 1 et 2) et l'ID (colonne 3)
      if (!(any(is.na(idx_ruler)))) {
        detected_targets_in_complete_rulers=rbind(detected_targets_in_complete_rulers,detected_targets[idx_ruler,c(1,2,3)])
      }
    }
    #si on a détecté des réglets complets, on écrit un fichier avec les coordonnées des targets
    if (!is.null(detected_targets_in_complete_rulers)) {
      #write.table(t(data.frame(strsplit(res_short[(idx1[i]+1):(idx2[i]-2),2]," "))),file = paste(Out_dir,this_image,"_CCTAG_alldata.txt",sep=""),quote=FALSE,row.names = FALSE,col.names = FALSE)
      #write.table(t(data.frame(strsplit(res_short[(idx1[i]+1):(idx2[i]-2),2]," ")))[,c(1,2)],file = paste(Out_dir,this_image,"_CCTAG_coords.txt",sep=""),quote=FALSE,row.names = FALSE,col.names = FALSE)
      write.table(detected_targets_in_complete_rulers,file = paste(Out_dir,this_image,suffix_CCTAG_coords_file,sep=""),quote=FALSE,row.names = FALSE,col.names = FALSE)
    } else {
      print(paste("No completer ruler detected within",this_image))
    }
  } else {
    if (n_detected==0) {
      print(paste("0 target detected within",this_image)) 
    } else { #cas où on a au moins une target détectée mais psa le nombre de lignes attendu
      print(paste("error with",this_image))  
    }
  }
}

#À cette étape on a donc un fichier par image avec les coordonnées des targets détectées dans les réglets complets (on a viré les targets détectées quand une seule target du réglet est détectée)
#Il s'agit donc de faire :
#1. calcul des coordonnées 3D de chaque mire estimée à partir de chaque image
#   (problème => micmac ne garde pas l'ID dans le le fichier out avec les coordonnées 3D ; heureusement les points sont dans le même ordre)
# il faut :
#   faire le calcul pour chaque fichier image

#on reboucle sur les images
list_coordinates_by_image <- vector(mode = "list", length = length(image_list))
names(list_coordinates_by_image)=image_list
for (i in 24:length(idx2)) {
  #this_image=basename(res_short[idx2[i],2])
  #on récupère le nom de l'image dans la ligne idx2[i] qui contient "Done"
  this_image_file=basename(res_short[idx2[i],2])
  this_image=sub(pattern = "(.*)\\..*$", replacement = "\\1", basename(res_short[idx2[i],2]))
  b=system2(command = "/home/feurer/micmac/bin/mm3d", args = paste("Im2XYZ ",my_path,"micmac/PIMs-QuickMac/Nuage-Depth-",this_image_file,".xml ",Out_dir,this_image,suffix_CCTAG_coords_file," ",Out_dir,this_image,"_CCTAG_3D_coords.txt",sep=""), stdout = TRUE, stderr = TRUE)
  #Il se peut que micmac ne trouve pas le point dans le nuage de points 3D pour certaines (voire toutes) target
  #micmac crée alors un fichier "Filtered_xxxx"
  micmac_filtered_filename=paste(Out_dir,"Filtered_",this_image,suffix_CCTAG_coords_file,sep="")
  if ((file.exists(micmac_filtered_filename) && file.size(micmac_filtered_filename)!=0) | !(file.exists(micmac_filtered_filename)))  {
    #si micmac a créé un fichier non vide (il a donc au moins trouvé une target dans le nuage de point 3D même si pas toutes) ou micmac a pas créé de fichier
    if (!(file.exists(micmac_filtered_filename))) {
      # pas de souci, pas de filtre, on fait direct le merge
      CCTAGs_withID=read.table(paste(Out_dir,this_image,suffix_CCTAG_coords_file,sep=""))
    } else {
      #cas ou on a le fichier "Filtered_xxx non vide
      #du coup on lit les deux fichiers de coordonnées images de CCTAGs (originaux et filtered), pour récupérer les IDs depuis le fichier de départ
      this_image_detected_CCTAGs=read.table(paste(Out_dir,this_image,suffix_CCTAG_coords_file,sep=""))
      this_image_filtered_CCTAGs=read.table(paste(Out_dir,"Filtered_",this_image,suffix_CCTAG_coords_file,sep="")) #ici il faudrait vérifier que le fichier existe
      #on récupère les ID de CCTAGs tout en faisant bien gaffe à garder l'ordre du fichier Filtered_CCTAGS, qui est le même ordre que le fichier avec les coordonnées 3D
      CCTAGs_withID=merge(this_image_filtered_CCTAGs,this_image_detected_CCTAGs,by.x=1,by.y=1,all.x=TRUE,sort=FALSE)[,c(1,2,4)]
    }
    CCTAGs_withID_and_3D_coords=cbind(CCTAGs_withID,read.table(paste(Out_dir,this_image,"_CCTAG_3D_coords.txt",sep="")))
    list_coordinates_by_image[[this_image_file]] <- CCTAGs_withID_and_3D_coords
  } #si on est là c'est qu'il y a bien un fichier filtered mais il est vide, on ne fait donc rien
  
}
list_coords_ok=list_coordinates_by_image[!sapply(list_coordinates_by_image,is.null)]
coords_and_ims=lapply(names(list_coords_ok), function(x){data.frame(im=x,list_coords_ok[[x]][,c(3,4,5,6)])})
big=do.call(rbind,coords_and_ims)
coords3D=t(data.frame(x_moy=sapply(split(big[,3],big[,2]),mean), y_moy=sapply(split(big[,4],big[,2]),mean), z_moy=sapply(split(big[,5],big[,2]),mean)))
coords3Dsd=t(data.frame(x_moy=sapply(split(big[,3],big[,2]),sd), y_moy=sapply(split(big[,4],big[,2]),sd), z_moy=sapply(split(big[,5],big[,2]),sd)))
mean_size=lapply(reglets,function(reglet){sqrt(sum((coords3D[,colnames(coords3D)==reglet[1]] - coords3D[,colnames(coords3D)==reglet[2]])^2))})
mean_scale_factor=mean(as.numeric(reglets_size/mean_size))
dir.create(paste(my_path,rel_path_out_clouds_and_scale,sep=""))
mat_trans=diag(4)
mat_trans[-4,-4]=mat_trans[-4,-4]*mean_scale_factor
write(x=mat_trans,file=paste(my_path,rel_path_out_clouds_and_scale,"/scale_factor_matrix.txt",sep=""),ncolumns = 4)

#commandes à exécuter dans un terminal pour mettre les nuages à l'échelle et avoir des résultats en PLY
#cloudcompare.CloudCompare -C_EXPORT_FMT PLY -O apres_1.ply -APPLY_TRANS scale_factor_matrix.txt
#cloudcompare.CloudCompare -C_EXPORT_FMT PLY -O avant_0.ply -APPLY_TRANS scale_factor_matrix.txt



