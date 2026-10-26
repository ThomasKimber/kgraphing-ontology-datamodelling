from kgraphing.store.rdfquery import QueryAPI
from rdflib import Graph, URIRef, BNode, Literal
from rdflib.plugins.sparql import prepareQuery

from importlib.resources import files

from kgraphing.store import rdfquery
from kgraphing.ingest import kgpipeline
from kgraphing_ontology_datamodelling import sparql
from functools import partial

DMPipeline=partial(kgpipeline.KGraphPipeline,
    mapping_config_location=str(files('kgraphing_ontology_datamodelling.mapping').joinpath("kgdm_mapping.json")),
    validation_shacl_list=[str(files('kgraphing_ontology_datamodelling.shacl').joinpath("kgnam_shacl.ttl")),
                          str(files('kgraphing_ontology_datamodelling.shacl').joinpath("kgdm_shacl.ttl"))])
