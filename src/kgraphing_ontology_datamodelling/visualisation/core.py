"""Template for a visgerf style visualisation - classes import from this
template for specific use-cases"""
from typing import Callable, Optional, Any
from kgraphing.visgerf import VisGerf
from kgraphing.gerf import Gerf
from kgraphing import nxproperties
from networkx import MultiDiGraph
from functools import partial
import gravis
import inspect

class ClassificationPass:
    def __init__(self, 
                 classification_function : Callable, 
                 class_annotations : dict[frozenset, dict[str,Any]],
                 **kwargs):
        self.classification_function = classification_function
        self.class_annotations = class_annotations
        self.kwargs=kwargs

    @property
    def function(self):
        return partial(self.classification_function,
                       key_set=self.class_annotations,
                       **self.kwargs)


class Visualisation:
    def __init__(self,
                 include_node_function: Callable | None = None, 
                 include_edge_function: Callable| None = None, 
                 node_properties_function: Callable| None = None, 
                 edge_properties_function: Callable| None = None, 
                 classify_node_passes: list[ClassificationPass] | None = None, 
                 classify_edge_passes: list[ClassificationPass] | None = None, 
                 vis_graph_settings : dict[str,Any] | None = None):
        
        self.include_node_function=include_node_function
        self.include_edge_function=include_edge_function 
        self.node_properties_function=node_properties_function
        self.edge_properties_function=edge_properties_function
        self.classify_node_passes=classify_node_passes
        self.classify_edge_passes=classify_edge_passes
        
        self.vis_graph_settings=vis_graph_settings

    def prepare_vis(self, 
                    gerf_object : Gerf):
        VG = VisGerf(gerf_object)

        self.nx_graph = VG.gerf_to_base_nx(gerf_object=gerf_object,
                                           include_node_function=self.include_node_function,
                                           include_edge_function=self.include_edge_function,
                                           node_properties_function=self.node_properties_function,
                                           edge_properties_function=self.edge_properties_function)
        
        for class_pass in self.classify_node_passes:

            self.nx_graph = nxproperties.decorate_networkx_nodes_with_function(self.nx_graph, 
                                                    partial(class_pass.function,gerf_data=gerf_object), 
                                                    class_pass.class_annotations)

        for class_pass in self.classify_edge_passes:

            self.nx_graph = nxproperties.decorate_networkx_edges_with_function(self.nx_graph, 
                                                    partial(class_pass.function,gerf_data=gerf_object), 
                                                    class_pass.class_annotations)

        return self.nx_graph
    

    def to_gravis_vis(self):
        
        return gravis.vis(self.nx_graph, **self.vis_graph_settings)

    def to_gravis_d3(self):
        
        return gravis.vis(self.nx_graph, **self.vis_graph_settings)

    def to_gravis_three(self):
        return gravis.three(self.nx_graph, **{k:v for k,v in self.vis_graph_settings.items() if k not in ("layout_algorithm", 
                                                                                                     "central_gravity", 
                                                                                                     "gravitational_constant", 
                                                                                                     "spring_constant", 
                                                                                                     "spring_length", 
                                                                                                     "avoid_overlap")})
