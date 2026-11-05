
from importlib.resources import files
from rdflib.namespace import RDF, RDFS, OWL
from rdflib import URIRef, BNode, Literal, Namespace
from kgraphing.store import rdfquery 

dependencyQ=rdfquery.QueryAPI("Entity Dependencies",
                             query=files('kgraphing_ontology_datamodelling.sparql').joinpath('infer_entity_dependencies.sparql').read_text(encoding="utf-8"),
                             description="Infer kgdm:isDependentOn triples from graph contents.",
                             parameters={},
                             init_namespace={"kgdm":"https://kgraph.foo/onto/datamodelling#", 
                                             "kgnam":"https://kgraph.foo/onto/kgnam#"})
layout_breadcrumbs_q=rdfquery.QueryAPI("Layout Breadcrumbs",
                             query=files('kgraphing_ontology_datamodelling.sparql').joinpath('infer_layout_breadcrumbs.sparql').read_text(encoding="utf-8"),
                             description="Infer kgdm:layoutBreadcrumb triples from graph contents.",
                             parameters={},
                             init_namespace={"kgdm":"https://kgraph.foo/onto/datamodelling#", 
                                             "kgnam":"https://kgraph.foo/onto/kgnam#"})

infer_key_types_q=rdfquery.QueryAPI("Infer Key Types",
                             query=files('kgraphing_ontology_datamodelling.sparql').joinpath('infer_key_type_from_association.sparql').read_text(encoding="utf-8"),
                             description="Infer kgdm:PrimaryKey or ForeignKey triples from association.",
                             parameters={},
                             init_namespace={"kgdm":"https://kgraph.foo/onto/datamodelling#", 
                                             "kgnam":"https://kgraph.foo/onto/kgnam#"})

infer_leaf_entities_q = rdfquery.QueryAPI("Infer Leaf Entities",
                             query=files('kgraphing_ontology_datamodelling.sparql').joinpath('infer_leaf_entities.sparql').read_text(encoding="utf-8"),
                             description="Classify all Entities with isLeafEntity depending on their isDependentOn links.",
                             parameters={},
                             init_namespace={"kgdm":"https://kgraph.foo/onto/datamodelling#", 
                                             "kgnam":"https://kgraph.foo/onto/kgnam#"})

Q_get_entity_dependencies = rdfquery.QueryAPI("Get Dependencies",
                             query=files('kgraphing_ontology_datamodelling.sparql').joinpath('get_dependency_for_node.sparql').read_text(encoding="utf-8"),
                             description="Return all nodes that are dependent on a given node.",
                             parameters={"node" : URIRef},
                             init_namespace={"kgdm":"https://kgraph.foo/onto/datamodelling#", 
                                             "kgnam":"https://kgraph.foo/onto/kgnam#"})

Q_get_entity_dependants = rdfquery.QueryAPI("Get Dependants",
                             query=files('kgraphing_ontology_datamodelling.sparql').joinpath('get_dependants_for_node.sparql').read_text(encoding="utf-8"),
                             description="Return all nodes on which a given node depends.",
                             parameters={"node" : URIRef},
                             init_namespace={"kgdm":"https://kgraph.foo/onto/datamodelling#", 
                                             "kgnam":"https://kgraph.foo/onto/kgnam#"})

Q_get_object_by_label = rdfquery.QueryAPI("Get Object By Label",
                             query=files('kgraphing_ontology_datamodelling.sparql').joinpath('object_search_on_label.sparql').read_text(encoding="utf-8"),
                             description="Return all nodes whose labels match search parameter - with optional type filter.",
                             parameters={"search" : Literal, 
                                         "type" : URIRef},
                             init_namespace={"kgdm":"https://kgraph.foo/onto/datamodelling#", 
                                             "kgnam":"https://kgraph.foo/onto/kgnam#"})

Q_get_object_by_type = rdfquery.QueryAPI("Get Object By Type",
                             query=files('kgraphing_ontology_datamodelling.sparql').joinpath('object_search_by_type.sparql').read_text(encoding="utf-8"),
                             description="Return all nodes whose labels match type parameter.",
                             parameters={"type" : URIRef},
                             init_namespace={"kgdm":"https://kgraph.foo/onto/datamodelling#", 
                                             "kgnam":"https://kgraph.foo/onto/kgnam#"})


Q_entity_attribute_sheet = rdfquery.QueryAPI("Entity and Attribute Sheet",
                             query=files('kgraphing_ontology_datamodelling.sparql').joinpath('entity_attribute_sheet.sparql').read_text(encoding="utf-8"),
                             description="Report showing entities and their attributes with PK/FK flags.",
                             parameters={"entity" : URIRef},
                             init_namespace={"kgdm":"https://kgraph.foo/onto/datamodelling#", 
                                             "kgnam":"https://kgraph.foo/onto/kgnam#"})

Q_relationship_sheet = rdfquery.QueryAPI("Relationship Sheet",
                             query=files('kgraphing_ontology_datamodelling.sparql').joinpath('relationship_sheet.sparql').read_text(encoding="utf-8"),
                             description="Report showing relationships with associated flags and properties.",
                             parameters={"relationship" : URIRef},
                             init_namespace={"kgdm":"https://kgraph.foo/onto/datamodelling#", 
                                             "kgnam":"https://kgraph.foo/onto/kgnam#"})
Q_role_sheet = rdfquery.QueryAPI("Role Sheet",
                             query=files('kgraphing_ontology_datamodelling.sparql').joinpath('role_sheet.sparql').read_text(encoding="utf-8"),
                             description="Report showing roles with associated flags and properties.",
                             parameters={"role" : URIRef},
                             init_namespace={"kgdm":"https://kgraph.foo/onto/datamodelling#", 
                                             "kgnam":"https://kgraph.foo/onto/kgnam#"})

Q_get_entity_roles = rdfquery.QueryAPI("Entity Associated Roles",
                             query=files('kgraphing_ontology_datamodelling.sparql').joinpath('get_entity_roles.sparql').read_text(encoding="utf-8"),
                             description="Returns all roles associated to an entity.",
                             parameters={"entity" : URIRef},
                             init_namespace={"kgdm":"https://kgraph.foo/onto/datamodelling#", 
                                             "kgnam":"https://kgraph.foo/onto/kgnam#"})

Q_get_role_relationships = rdfquery.QueryAPI("Role Associated Relationships",
                             query=files('kgraphing_ontology_datamodelling.sparql').joinpath('get_role_relationships.sparql').read_text(encoding="utf-8"),
                             description="Returns all relationships associated to a role.",
                             parameters={"role" : URIRef},
                             init_namespace={"kgdm":"https://kgraph.foo/onto/datamodelling#", 
                                             "kgnam":"https://kgraph.foo/onto/kgnam#"})
Q_get_entity_dependency_paths = rdfquery.QueryAPI("Role Associated Relationships",
                             query=files('kgraphing_ontology_datamodelling.sparql').joinpath('get_entity_dependency_paths.sparql').read_text(encoding="utf-8"),
                             description="Returns all outbound relationship paths associated with a given entity.",
                             parameters={"entity" : URIRef},
                             init_namespace={"kgdm":"https://kgraph.foo/onto/datamodelling#", 
                                             "kgnam":"https://kgraph.foo/onto/kgnam#"})



