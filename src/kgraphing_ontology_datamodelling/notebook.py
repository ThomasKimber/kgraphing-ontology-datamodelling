import sys, os
rootpath  = os.path.abspath("..")
from importlib import reload
from functools import partial

from rdflib import Graph, URIRef, Literal, BNode, Namespace
from rdflib.collection import Collection
from rdflib.util import from_n3
from rdflib.namespace import RDF, RDFS, OWL
from rdflib.plugins.sparql import prepareQuery

from importlib.resources import files
import pandas as pd

import gravis


from IPython.display import HTML

import kgraphing
kgraphing=reload(kgraphing)
from kgraphing import gerf
from kgraphing import setfunctions
from kgraphing.visgerf import VisGerf
from kgraphing.ingest import kgpipeline

from kgraphing import nxproperties, ocache
from kgraphing.store import kgstore
from kgraphing.store import metadata, rdfquery 

from kgraphing.declarations import RDFSubjectAtom, RDFPredicateAtom, RDFObjectAtom, RDFTriple

from kgraphing_ontology_datamodelling.visualisation.kgdm import BasicVisualisation
from kgraphing_ontology_datamodelling.visualisation.kgdm_erd import ERDVisualisation
from kgraphing_ontology_datamodelling.visualisation.kgdm_erd import erd_gen_svg_image_for_node, png_bytes_to_urldata, svg_to_urldata

from kgraphing_ontology_datamodelling.ingest import DMPipeline, DMPostLoadInference

from kgraphing_ontology_datamodelling.queries import Q_get_entity_dependencies, Q_get_entity_dependants, \
                                                         Q_get_object_by_label, Q_get_object_by_type, \
                                                         Q_entity_attribute_sheet, Q_relationship_sheet, \
                                                        Q_role_sheet, dependencyQ

library_model_df = pd.read_excel("kgraphing-ontology-datamodelling/samples/library_template_v1.xlsx", sheet_name="Example(Library Model)")

name_master_location="namemaster.db"
kgp=DMPipeline(name_master_location=name_master_location)

final_g = kgp.process(library_model_df, ignore_validate=True)
DMPostLoadInference(final_g)

print(kgp.shacl_validation_results[1][2])

OC = ocache.OntologyCache("ocache")
OC.purge()
OC.initialise()
OC.register("https://kgraph.foo/onto/kgnam#", 
            False, 
            files('kgraphing.ontologies').joinpath('kgnam.owl'))

OC.register("https://kgraph.foo/onto/datamodelling#", 
            False, 
            files('kgraphing_ontology_datamodelling').joinpath('kgdm.owl'))

G = gerf.Gerf(final_g, OC)
KGDM = Namespace(URIRef("https://kgraph.foo/onto/datamodelling#"))

G.enrich_metadata() # Update/enrich the ontology cache
G.perform_inference_closure() # Do the RDFS inference
G.update_total_graph() # Write inference contents back to the total graph

nx_g=ERDVisualisation.prepare_vis(G)

from kgraphing_ontology_datamodelling.visualisation.kgdm_erd import calculate_images_and_return_classification_pass_for_erd
from kgraphing_ontology_datamodelling.visualisation.kgdm_erd import classify_node_by_identity

# This await currently only runs in a notebook
s_d = await calculate_images_and_return_classification_pass_for_erd(G)

ERDVisualisation.nx_graph=nxproperties.decorate_networkx_nodes_with_function(nx_g, 
                                                    partial(classify_node_by_identity,gerf_data=G, property_uri=None, key_set=s_d.keys()), 
                                                    s_d)

vis_html=ERDVisualisation.to_gravis_vis().to_html()
HTML(vis_html)

