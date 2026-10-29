from functools import partial
from rdflib.namespace import RDF, RDFS, OWL
from rdflib import URIRef, BNode, Literal, Namespace


from kgraphing_ontology_datamodelling.visualisation.core import Visualisation, ClassificationPass
from kgraphing import setfunctions, gerf

from kgraphing.visgerf import VisGerf



KGDM = Namespace(URIRef("https://kgraph.foo/onto/datamodelling#"))

def include_node_function(gerf_object, identifier):
    empty_node=gerf.ObservedEntity(identifier=None, order=None, gerf_object=gerf_object)
    test_node = gerf_object.entities.get(identifier, empty_node)
    tests = [test_node.identifier in gerf_object.entities.keys(), 
             test_node.identifier not in (URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#nil'), ),
             test_node.order<=1, 
             test_node.term in (URIRef, BNode), 
             any({t in (URIRef("https://kgraph.foo/onto/datamodelling#Entity"),
                        URIRef("https://kgraph.foo/onto/datamodelling#Relationship"),
                        URIRef("https://kgraph.foo/onto/datamodelling#SubjectRole"),
                        URIRef("https://kgraph.foo/onto/datamodelling#ObjectRole")) for t in test_node.interactions.get(RDF.type,{False})})
            ]
    return all(tests)

def include_edge_function(gerf_object, identifier, predicate, element):
    tests = [identifier in gerf_object.entities.keys(), 
             element in gerf_object.entities.keys(), 
             predicate in gerf_object.relations.keys(),
             VisGerf._predicate_is_subclass_leaf(gerf_object, identifier, predicate, element),
             predicate not in (RDF.type, URIRef("https://kgraph.foo/onto/kgnam#isScopedWithin")),
             predicate in (
                           KGDM.subjectRoleIsPartOfRelationship, 
                           KGDM.objectRoleIsPartOfRelationship,
                           KGDM.subjectRoleIsAssociatedWithEntity,
                           KGDM.objectRoleIsAssociatedWithEntity
                          ),
            ]
    return all(tests)

styles_by_type = {
    frozenset({RDF.type, OWL.Class}) : { "color" : "red"},
    frozenset({URIRef('https://kgraph.foo/onto/datamodelling#Namespace')}) : { "color" : "yellow"},

    frozenset({URIRef('https://kgraph.foo/onto/datamodelling#Role'), 
               URIRef('https://kgraph.foo/onto/datamodelling#SubjectRole')}) : 
                                                                                { "color" : "#b14200", 
                                                                                "shape" : "hexagon", 
                                                                                "size" : 15},
    frozenset({URIRef('https://kgraph.foo/onto/datamodelling#Role'), 
               URIRef('https://kgraph.foo/onto/datamodelling#ObjectRole')}) : 
                                                                                { "color" : "#b16b00", 
                                                                                "shape" : "hexagon", 
                                                                                "size" : 15},
    frozenset({URIRef('https://kgraph.foo/onto/datamodelling#Relationship')}) : { "color" : "#ff931b", 
                                                                                "shape" : "circle", 
                                                                                "size" : 3,
                                                                                "label_size" : 30},
    frozenset({URIRef("test"), URIRef('https://kgraph.foo/onto/datamodelling#Namespace')}) : { "color" : "yellow"},
    frozenset({URIRef('https://kgraph.foo/onto/datamodelling#Attribute')}) : { "color" : "limegreen", 
                                                                                "shape" : "rectangle", 
                                                                                "size" : 10},
    frozenset({URIRef('https://kgraph.foo/onto/datamodelling#Entity')}) : { "color" : "#1b93ff", 
                                                                                "shape" : "rectangle", 
                                                                                "size" : 100, 
                                                                                "label_size" : 30},
    frozenset({URIRef('https://kgraph.foo/onto/datamodelling#Key'),
              URIRef('https://kgraph.foo/onto/datamodelling#PrimaryKey')}) : { "color" : "#5d69e3"}, 
    frozenset({URIRef('https://kgraph.foo/onto/datamodelling#Key'),
              URIRef('https://kgraph.foo/onto/datamodelling#ForeignKey')}) : { "color" : "#5dc4e3"}, 
    frozenset({URIRef('https://kgraph.foo/onto/datamodelling#Domain')}) : { "color" : "grey"},
    frozenset({URIRef('https://kgraph.foo/onto/datamodelling#SubjectArea')}) : { "color" : "blue"},
}

node_styles = {
    frozenset({"something"}) : {
        "color" : "",
        "opacity" : 1.0,
        "size": 1.0,
        "shape" : "rectangle",
        "border_color": "",
        "border_size": 1.0,
        "label_color": "",
        "label_size": 1.0,
        "hover": "",
        "click": "",
        "image" : "",
        "x" : 1.0, 
        "y": 1.0, 
        "z": 1.0
        
    }
}

edge_styles = {
    frozenset({"something"}) : {
        "color" : "black",
        "opacity" : 1.0,
        "size": 1.0,
        "arrow_color": "blue",
        "arrow_size": 1.0,
        "label_color": "black",
        "label_size": 1.0,
        "hover": "",
        "click": "",
    }
}


edge_styles = {
    frozenset({}) : {
        "color" : "black",
        "opacity" : 1.0,
        "size": 1.0,
        "arrow_color": "black",
        "arrow_size": 5.0,
        "label_color": "#808080",
        "label_size": 10.0    },
    frozenset({URIRef('https://kgraph.foo/onto/datamodelling#isDependentOn')}) : {
        "color" : "red",
        "opacity" : 1.0,
        "size": 3.0,
        "arrow_color": "red",
        "arrow_size": 10.0,
        "label_color": "black",
        "label_size": 10.0    },
        
}

vis_graph_settings = {
    "node_label_data_source" : "label", 
    "node_size_data_source" : "size", 
    "node_label_size_factor" : 1.5, 
    "node_size_factor" : 3.0, 
    "edge_size_data_source" : "size", 
    "edge_label_data_source" : "label", 
    "edge_size_factor" : 2.5, 
    "show_edge_label" : True,
    "edge_curvature" : 0.2,
    "graph_height" : 800,
    "details_height" : 300, 
    "layout_algorithm" : "forceAtlas2Based", 
    "central_gravity" : 2.5, 
    "gravitational_constant" : -20000,
    "spring_constant" : 0.51,
    "spring_length" : 40,
    "avoid_overlap" : 0.95
    
}


def classify_node_by_gerf_property(id, data, gerf_data, property_uri, key_set):
    """Function that assigns the best key available from a set of input keys"""
    empty_node = gerf.ObservedEntity(identifier=None, order=None, gerf_object=gerf_data)
    property_values = gerf_data.entities.get(id, empty_node).interactions.get(property_uri,set())
    candidate_keys = {e:k for e,k in enumerate(key_set)}
    matching_keys = {k:v for k,v in setfunctions.venn_partitions({**{"Q" : property_values}, **{e:set(k) for e,k in candidate_keys.items()}}, 
                                         notation_style="binindex").items() if 'Q' in k}
    
    matching_candidates = {k:v for k,v in candidate_keys.items() if k in { m for y in matching_keys for m in y}}
    best_keys = sorted([(k, setfunctions.lir_stats(property_values, val)) for k,val in matching_candidates.items()], key=lambda x : x[1][2], reverse=True)
    if len(best_keys)>0:
        return candidate_keys[best_keys[0][0]]
    else:
        return None

def classify_edge_on_data_predicate(id, data, gerf_data, property_uri, key_set):
    empty_node = gerf.ObservedEntity(identifier=None, order=None, gerf_object=gerf_data)
    property_values = set([data.get('predicate')])
    candidate_keys = {e:k for e,k in enumerate(key_set)}
    matching_keys = {k:v for k,v in setfunctions.venn_partitions({**{"Q" : property_values}, **{e:set(k) for e,k in candidate_keys.items()}}, 
                                         notation_style="binindex").items() if 'Q' in k}
    
    matching_candidates = {k:v for k,v in candidate_keys.items() if k in { m for y in matching_keys for m in y}}
    best_keys = sorted([(k, setfunctions.lir_stats(property_values, val)) for k,val in matching_candidates.items()], key=lambda x : x[1][2], reverse=True)
    
    if len(best_keys)>0:
        return candidate_keys[best_keys[0][0]]
    else:
        return None

def classify_edge_entity_by_gerf_property(id, data, gerf_data, property_uri, key_set):
    """Function that assigns the best key available from a set of input keys.
    This deals with the fact that entity interactions in gerf are captured as sets
    of features - and attempts to choose the best-fitting set of values against
    an input key_set of target assignments.
    The set-intersection stats are calculated between interactions identified by
    the property_uri and values provided in each of the key_set values.
    """
    empty_node = gerf.ObservedEntity(identifier=None, order=None, gerf_object=gerf_data)
    property_values = gerf_data.entities.get(data.get("predicate", None), empty_node).interactions.get(property_uri,set())
    candidate_keys = {e:k for e,k in enumerate(key_set)}
    matching_keys = {k:v for k,v in setfunctions.venn_partitions({**{"Q" : property_values}, **{e:set(k) for e,k in candidate_keys.items()}}, 
                                         notation_style="binindex").items() if 'Q' in k}
    
    matching_candidates = {k:v for k,v in candidate_keys.items() if k in { m for y in matching_keys for m in y}}
    best_keys = sorted([(k, setfunctions.lir_stats(property_values, val)) for k,val in matching_candidates.items()], key=lambda x : x[1][2], reverse=True)
    
    if len(best_keys)>0:
        return candidate_keys[best_keys[0][0]]
    else:
        return None



classify_nodes_on_type = ClassificationPass(
    classification_function=classify_node_by_gerf_property,
    class_annotations=styles_by_type,
    property_uri=RDF.type
)

classify_edges_on_type = ClassificationPass(
    classification_function=classify_edge_on_data_predicate,
    class_annotations=edge_styles,
    property_uri=RDF.type
)

ERDVisualisation = Visualisation(
    include_node_function=include_node_function,
    include_edge_function=include_edge_function,
    classify_node_passes=[classify_nodes_on_type],
    classify_edge_passes=[classify_edges_on_type],
    vis_graph_settings=vis_graph_settings
)
