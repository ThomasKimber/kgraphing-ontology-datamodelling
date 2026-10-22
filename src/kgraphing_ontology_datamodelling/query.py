from kgraphing.store.rdfquery import QueryAPI
from rdflib import Graph, URIRef, BNode, Literal
from rdflib.plugins.sparql import prepareQuery

from importlib.resources import files

from kgraphing.store import rdfquery
from kgraphing_ontology_datamodelling import sparql

        
class QueryRegistry:
    def __init__(self):
        self.registry={}

    def register_query(self, 
                       prepared_query : rdfquery.QueryAPI):
        self.registry[prepared_query.name]=prepared_query
        