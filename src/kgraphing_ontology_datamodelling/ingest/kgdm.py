
from importlib.resources import files
from functools import partial
from rdflib.namespace import RDF, RDFS, OWL
from rdflib import URIRef, BNode, Literal, Namespace


from kgraphing.ingest import kgpipeline
from kgraphing.store import metadata, rdfquery 

DMPipeline = partial(kgpipeline.KGraphPipeline,
    mapping_config_location=str(files('kgraphing_ontology_datamodelling.mapping').joinpath("kgdm_mapping.json")),
    validation_shacl_list=[str(files('kgraphing_ontology_datamodelling.shacl').joinpath("kgnam_shacl.ttl")),
                          str(files('kgraphing_ontology_datamodelling.shacl').joinpath("kgdm_shacl.ttl"))])

dependencyQ=rdfquery.QueryAPI("Entity Dependencies",
                             query=files('kgraphing_ontology_datamodelling.sparql').joinpath('infer_entity_dependencies.sparql').read_text(encoding="utf-8"),
                             description="Infer kgdm:isDependentOn triples from graph contents.",
                             parameters={},
                             init_namespace={"kgdm":"https://kgraph.foo/onto/datamodelling#"})

infer_key_types_q=rdfquery.QueryAPI("Infer Key Types",
                             query=files('kgraphing_ontology_datamodelling.sparql').joinpath('infer_key_type_from_association.sparql').read_text(encoding="utf-8"),
                             description="Infer kgdm:PrimaryKey or ForeignKey triples from association.",
                             parameters={},
                             init_namespace={"kgdm":"https://kgraph.foo/onto/datamodelling#"})

infer_leaf_entities_q = rdfquery.QueryAPI("Infer Leaf Entities",
                             query=files('kgraphing_ontology_datamodelling.sparql').joinpath('infer_leaf_entities.sparql').read_text(encoding="utf-8"),
                             description="Classify all Entities with isLeafEntity depending on their isDependentOn links.",
                             parameters={},
                             init_namespace={"kgdm":"https://kgraph.foo/onto/datamodelling#"})

def DMPostLoadInference(graph):
    """Perform inference tasks on graph"""
    dependency_links_g=dependencyQ.execute(graph, {}).graph
    key_inference_g=infer_key_types_q.execute(graph, {}).graph
    leaf_inference_g=infer_leaf_entities_q.execute(graph, {}).graph
    graph += dependency_links_g
    graph += key_inference_g
    graph += leaf_inference_g
    return graph

Q_get_entity_dependencies = rdfquery.QueryAPI("Get Dependencies",
                             query=files('kgraphing_ontology_datamodelling.sparql').joinpath('get_dependency_for_node.sparql').read_text(encoding="utf-8"),
                             description="Return all nodes that are dependent on a given node.",
                             parameters={"node" : URIRef},
                             init_namespace={"kgdm":"https://kgraph.foo/onto/datamodelling#"})

Q_get_entity_dependants = rdfquery.QueryAPI("Get Dependants",
                             query=files('kgraphing_ontology_datamodelling.sparql').joinpath('get_dependants_for_node.sparql').read_text(encoding="utf-8"),
                             description="Return all nodes on which a given node depends.",
                             parameters={"node" : URIRef},
                             init_namespace={"kgdm":"https://kgraph.foo/onto/datamodelling#"})

Q_get_object_by_label = rdfquery.QueryAPI("Get Object By Label",
                             query=files('kgraphing_ontology_datamodelling.sparql').joinpath('object_search.sparql').read_text(encoding="utf-8"),
                             description="Return all nodes whose labels match search parameter - with optional type filter.",
                             parameters={"search" : Literal, 
                                         "type" : URIRef},
                             init_namespace={"kgdm":"https://kgraph.foo/onto/datamodelling#"})

