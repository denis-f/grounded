from abc import ABC, abstractmethod
from Grounded.DataObject import PointCloud, Raster


class PointCloudProcessor(ABC):

    @abstractmethod
    def mise_a_echelle(self, point_cloud: PointCloud, facteur: float) -> PointCloud:
        pass

    @abstractmethod
    def cloud_to_cloud_difference(self, point_cloud_before_excavation: PointCloud,
                                  point_cloud_after_excavation: PointCloud) -> Raster:
        pass
