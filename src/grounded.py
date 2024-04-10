import sys

try:
    dossier_avant = sys.argv[1]
    dossier_apres = arg2 = sys.argv[2]
except IndexError as error:
    pass
    raise Exception("nombre d'arguments insuffisant")

print(f"le dossier d'entrée est : {dossier_avant}")
print(f"le dossier de sortie est : {dossier_apres}")