from Grounded.DataObject import ScaleBar, Mire

import csv


class ScaleBarLoader:

    @staticmethod
    def load(scale_bar_file_path: str) -> list[ScaleBar]:
        array_scale_bar = list()
        with open(scale_bar_file_path, newline='') as csvfile:
            lecteur_csv = csv.reader(csvfile, delimiter=',')
            next(lecteur_csv)
            for line in lecteur_csv:
                if len(line) == 3:
                    try:
                        array_scale_bar.append(ScaleBar(Mire(int(line[0])), Mire(int(line[1])), float(line[2])))
                    except ValueError:
                        raise SyntaxError("invalid scale bar format")

        return array_scale_bar
