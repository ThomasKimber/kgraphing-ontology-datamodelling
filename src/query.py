from kgraphing.store.rdfquery import QueryAPI

SPARQL_POST_LOAD_CALCULATE_DEPENDENCY = """
PREFIX kgdm: <https://kgraph.foo/onto/datamodelling#>
SELECT
    ?objectEntity ?p ?subjectEntity
WHERE
    {
    ?relationship a kgdm:Relationship.
    ?subjectRole a kgdm:SubjectRole.
    ?objectRole a kgdm:ObjectRole.
    ?objectEntity a kgdm:Entity.
    ?subjectEntity a kgdm:Entity.
    ?subjectRole kgdm:isAssociatedWith ?subjectEntity.
    ?objectRole kgdm:isAssociatedWith ?objectEntity.
    ?subjectRole kgdm:isPartOf ?relationship.
    ?objectRole kgdm:isPartOf ?relationship.

    VALUES ?p {kgdm:isDependentOn}
    
    }
"""

class StoredQuery:
    def __init__(self, 
                 query : str, 
                 init_namespace : dict, 
                 parameters: dict):
        self.prepared_query = prepareQuery(query, initNs=init_namespace)
        self.parameters=parameters

    def run_query(graph: Graph, 
                  parameters: dict)
class QueryRegistry:
    def __init__(self):
        self.registry={}

    def register_query(self, 
                       prepared_query : prepareQuery):
        