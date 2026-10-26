
from importlib.resources import files
from functools import partial
from rdflib.namespace import RDF, RDFS, OWL
from rdflib import URIRef, BNode, Literal, Namespace


from kgraphing.ingest import kgpipeline
from kgraphing.store import metadata, rdfquery 
from kgraphing_ontology_datamodelling.queries import dependencyQ, infer_key_types_q, infer_leaf_entities_q

DMPipeline = partial(kgpipeline.KGraphPipeline,
    mapping_config_location=str(files('kgraphing_ontology_datamodelling.mapping').joinpath("kgdm_mapping.json")),
    validation_shacl_list=[str(files('kgraphing_ontology_datamodelling.shacl').joinpath("kgnam_shacl.ttl")),
                          str(files('kgraphing_ontology_datamodelling.shacl').joinpath("kgdm_shacl.ttl"))])


def DMPostLoadInference(graph):
    """Perform inference tasks on graph"""
    dependency_links_g=dependencyQ.execute(graph, {}).graph
    key_inference_g=infer_key_types_q.execute(graph, {}).graph
    leaf_inference_g=infer_leaf_entities_q.execute(graph, {}).graph
    graph += dependency_links_g
    graph += key_inference_g
    graph += leaf_inference_g
    return graph
