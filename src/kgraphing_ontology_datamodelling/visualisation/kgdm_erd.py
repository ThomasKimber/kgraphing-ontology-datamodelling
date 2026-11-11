from typing import Callable, Optional, Any, Self
import io
import tempfile
import asyncio

from functools import partial
from rdflib.namespace import RDF, RDFS, OWL
from rdflib import URIRef, BNode, Literal, Namespace, Graph
from pandas import DataFrame, Series
import tqdm

from svgtext import svgsystem, htmltext
from svgtext.render import BatchThreadProcessor, svg_to_png_data_uri_cached
from kgraphing_ontology_datamodelling.visualisation.core import Visualisation, ClassificationPass
from kgraphing import setfunctions, gerf
from kgraphing.visgerf import VisGerf
from kgraphing_ontology_datamodelling.queries import Q_entity_attribute_sheet, Q_relationship_sheet, Q_role_key_attribute_sheet
from kgraphing_ontology_datamodelling.queries import Q_get_object_by_type, Q_get_entity_roles, Q_get_key_attributes
from kgraphing_ontology_datamodelling.queries import Q_key_attribute_sheet, Q_get_entity_dependency_paths


from kgraphing.store import rdfquery

SVGFONTREGISTRY = svgsystem.SVGFontRegistry()
SVGFONTCOMFORTAA = SVGFONTREGISTRY.registry['Comfortaa Regular']
SVGFONTDEJAVUSANS = SVGFONTREGISTRY.registry['Comfortaa Regular']
SVGFONTDEJAVUSANS_MONO = SVGFONTREGISTRY.registry['DejaVu Sans Mono']

SVGFONTCSS = SVGFONTREGISTRY.css_style(include_fonts=['Comfortaa Regular', 'DejaVu Sans', 'DejaVu Sans Mono'])

def svg_optional_single_key_function():
    return svgsystem.SVGCircleWithSpokes(r=10,
                                         cx=0,
                                         cy=0,
                                         spokes=2,
                                         spoke_radius=6,
                                         rot_degrees=30,
                                         fill="none", 
                                         stroke="black", 
                                         stroke_width=1)

def svg_optional_multi_key_function():
    return svgsystem.SVGCircleWithSpokes(r=10,
                                         cx=0,
                                         cy=0,
                                         spokes=6,
                                         spoke_radius=6,
                                         fill="none", 
                                         stroke="black", 
                                         stroke_width=1)

def svg_mandatory_single_key_function():
    return svgsystem.SVGRectangleWithSpokes(x=0,
                                         y=0,
                                         width=20,
                                         height=20,
                                         spokes=2,
                                         spoke_radius=7,
                                         rot_degrees=30,
                                         fill="none", 
                                         stroke="black", 
                                         stroke_width=1)

def svg_mandatory_multi_key_function():
    return svgsystem.SVGRectangleWithSpokes(x=0,
                                         y=0,
                                         width=20,
                                         height=20,
                                         spokes=6,
                                         spoke_radius=7,
                                         rot_degrees=30,
                                         fill="none", 
                                         stroke="black", 
                                         stroke_width=1)

KGDM = Namespace(URIRef("https://kgraph.foo/onto/datamodelling#"))

class ModelThingClass:
    name : str
    label : str
    description : str
    uri : URIRef
    qualified_name : str

    def __init__(self,  name : str,
                        label : str,
                        description : str,
                        uri : URIRef,
                        qualified_name : str):
        self.name=name
        self.label=label
        self.description=description
        self.uri=uri
        self.qualified_name=qualified_name


class ModelRelationshipClass(ModelThingClass):
    def __init__(self,  name : str,
                        label : str,
                        description : str,
                        uri : URIRef,
                        qualified_name : str,
                        from_entity_uri : URIRef, 
                        to_entity_uri : URIRef, 
                        from_entity_label : str, 
                        to_entity_label : str, 
                        subject_role_uri : URIRef, 
                        object_role_uri : URIRef,
                        object_role_cardinality : int, 
                        object_role_optionality : str,
                        subject_role_cardinality : int, 
                        subject_role_optionality : str
                        ):
        self.name=name
        self.label=label
        self.description=description
        self.uri=uri
        self.qualified_name=qualified_name
        self.from_entity_uri = from_entity_uri
        self.to_entity_uri = to_entity_uri 
        self.from_entity_label = from_entity_label
        self.to_entity_label = to_entity_label
        self.subject_role_uri = subject_role_uri
        self.object_role_uri = object_role_uri
        self.object_role_cardinality = object_role_cardinality
        self.object_role_optionality = object_role_optionality
        self.subject_role_cardinality = subject_role_cardinality
        self.subject_role_optionality =subject_role_optionality

    @classmethod
    def from_relationship_sheet_row(cls, row : Series)-> Self:
        return cls(**{"name" : row.relationship_name, 
                      "label" : row.relationship_label, 
                      "description" : row.relationship_description, 
                      "uri" : URIRef(row.relationship), 
                      "qualified_name" : row.relationship_qualified_name,
                      "from_entity_uri" : URIRef(row.relationship_from_entity), 
                        "to_entity_uri" : URIRef(row.relationship_to_entity),
                        "from_entity_label" : row.relationship_from_entity_label, 
                        "to_entity_label" : row.relationship_to_entity_label, 
                        "subject_role_uri" : URIRef(row.subject_role), 
                        "object_role_uri" : URIRef(row.object_role),
                        "object_role_cardinality" : row.object_role_cardinality, 
                        "object_role_optionality" : row.object_role_optionality,
                        "subject_role_cardinality" : row.subject_role_cardinality, 
                        "subject_role_optionality" : row.subject_role_optionality
        })

class ModelDomainClass(ModelThingClass):
    def __init__(self,  name : str,
                        label : str,
                        description : str,
                        uri : URIRef,
                        qualified_name : str):
        self.name=name
        self.label=label
        self.description=description
        self.uri=uri
        self.qualified_name=qualified_name

    @classmethod
    def from_entity_attribute_row(cls, row : Series)-> Self:
        return cls(**{"name" : row.domain_name, 
                      "label" : row.domain_label, 
                      "description" : row.domain_description, 
                      "uri" : row.domain, 
                      "qualified_name" : row.domain_qualified_name            
        })
    
class ModelAttributeClass(ModelThingClass):
    domain : ModelDomainClass
    sequence : int
    optional : bool
    isPK : bool
    isFK : bool
    def __init__(self,  name : str,
                        label : str,
                        description : str,
                        uri : URIRef,
                        qualified_name : str,
                        domain : ModelDomainClass,
                        sequence : int, 
                        optional : bool, 
                        isPK : bool, 
                        isFK : bool
                        ):
        self.name=name
        self.label=label
        self.description=description
        self.uri=uri
        self.qualified_name=qualified_name
        self.domain=domain
        self.sequence=sequence
        self.optional=optional
        self.isPK=isPK
        self.isFK=isFK


    @classmethod
    def from_entity_attribute_row(cls, row : Series)-> Self:
        
        return cls(**{"name" : row.attribute_name,
                      "label" : row.attribute_label,
                      "description" : row.attribute_description,
                      "uri" : row.attribute,
                      "qualified_name" : row.attribute_qualified_name,
                      "domain" : ModelDomainClass.from_entity_attribute_row(row),
                      "sequence" : row.attribute_sequence,
                      "optional" : row.optional,
                      "isPK" : row.isPK,
                      "isFK" : row.isFK
        })

    @classmethod
    def from_role_key_attribute_row(cls, row : Series)-> Self:
        
        return cls(**{"name" : row.attribute_name,
                      "label" : row.attribute_label,
                      "description" : None,
                      "uri" : row.attribute,
                      "qualified_name" : None,
                      "domain" : ModelDomainClass.from_entity_attribute_row(row),
                      "sequence" : None,
                      "optional" : None,
                      "isPK" : None,
                      "isFK" : None
        })

    @classmethod
    def attribute_list_from_entity_attribute_sheet(cls, df : DataFrame)-> list[Self]:
        a_list=[]
        for i,row in df.iterrows():
            a_list.append(cls.from_entity_attribute_row(row))
        return a_list

    @classmethod
    def attribute_list_from_role_key_attribute_sheet(cls, df : DataFrame)-> list[Self]:
        a_list=[]
        for i,row in df.iterrows():
            a_list.append(cls.from_role_key_attribute_row(row))
        return a_list

class ModelEntityClass(ModelThingClass):
    attribute_list : list[ModelAttributeClass]

    def __init__(self,  name : str,
                        label : str,
                        description : str,
                        uri : URIRef,
                        qualified_name : str,
                        attribute_list : list[ModelAttributeClass],
                        is_leaf : bool
                        ):
        self.name=name
        self.label=label
        self.description=description
        self.uri=uri
        self.qualified_name=qualified_name
        self.attribute_list=attribute_list
        self.is_leaf=is_leaf

    @classmethod
    def from_entity_attribute_sheet(cls, df : DataFrame)-> Self:
        row = df.iloc[0]
        return cls(**{  "name" : row.entity_name,
                        "label" : row.entity_label,
                        "description" : row.entity_description,
                        "uri" : row.entity,
                        "qualified_name" : row.entity_qualified_name,
                        "attribute_list" : ModelAttributeClass.attribute_list_from_entity_attribute_sheet(df),
                        "is_leaf" : row.entity_is_leaf
        })

    def attribute_list_to_dataframe(self) -> DataFrame:
        frame_contents=[]
        key_glyph_map = {
            True : "Yes",
            False : ""
        }
        for a in sorted(self.attribute_list, key=lambda x : x.sequence):
            frame_contents.append({"Attribute" : a.name, "Type" : a.domain.name, "Optional" : a.optional, "PK" : key_glyph_map.get(a.isPK,a.isPK), "FK" : key_glyph_map.get(a.isFK,"")})
        return DataFrame(frame_contents)
    
    def to_mermaid(self):
        pass

    def to_svg_component(self):

        attribute_data_grid=self.attribute_list_to_dataframe()
        
        svg_font_registry = svgsystem.SVGFontRegistry()

        css_style_content = SVGFONTCSS + "\n".join([ 
            """.layout_rect{\n stroke-width:1;\n stroke:red;\n fill:none;}\n""",
            """.layout_line{\n stroke-width:0.5;\n stroke:lightblue;\n fill:none;}\n"""     
                      ])
        svg_attribute_data_grid = svgsystem.SVGDataGridLayout(attribute_data_grid,
                                         {},
                                         True,
                                         SVGFONTCOMFORTAA, 
                                         12,
                                         SVGFONTDEJAVUSANS_MONO,
                                         10,
                                         (1,10))
        
        entity_description_markup = htmltext.html_to_markup(self.description, 65)

        entity_description_text = svgsystem.SVGMultiSpanText(entity_description_markup, 
                                                1.0, 
                                                SVGFONTDEJAVUSANS,
                                                12) 
        
        panel_content = svgsystem.SVGVerticalComposite(contents=[entity_description_text,svg_attribute_data_grid],
                    padding=5)
        
        
        svg_panel_style = svgsystem.SVGPanelStyle(
            title_bar_fill="lightblue",
            panel_canvas_fill="white",
            opacity=1.0,
            stroke_width="2px"
            )
        if self.is_leaf:
            corner_radii=(0,0,0,0)
        else:
            corner_radii=(20,20,20,20)
        
        panel = svgsystem.SVGTitledPanelFromContent(
            identifier=self.qualified_name,
            title_text=f"<b>{self.name}</b>",
            title_font=SVGFONTCOMFORTAA, 
            title_font_size=12,
            title_margins=(10,5,5,5),
            content_element=panel_content, 
            corner_radii=corner_radii,
            content_margins=(10,5,5,2),
            panel_style=svg_panel_style,
        )

        
        v_bounds = panel.bounds[0]-3,panel.bounds[1]-2,panel.bounds[2]+5, panel.bounds[3]+3
        vb_bounds = v_bounds[2]-v_bounds[0], v_bounds[3]-v_bounds[1], 

        viewbox=str(svgsystem.SVGViewBox(*v_bounds,*[b*2 for b in vb_bounds]))

        defs_block = f"""<defs><style type="text/css">{css_style_content}</style></defs>"""

        svg_image = viewbox.replace("%%placeholder%%", 
                            defs_block +\
                            str(panel))
        return svg_image, vb_bounds

class ModelKeyClass(ModelThingClass):
    def __init__(self,  name : str,
                        label : str,
                        description : str,
                        uri : URIRef,
                        qualified_name : str,
                        attribute_list : list[ModelAttributeClass],
                        subtype : str, 
                        ):
        self.name=name
        self.label=label
        self.description=description
        self.uri=uri
        self.qualified_name=qualified_name
        self.attribute_list=attribute_list
        self.subtype=subtype

    def attribute_list_to_dataframe(self) -> DataFrame:
        frame_contents=[]
        key_glyph_map = {
            True : "Yes",
            False : ""
        }
        for a in sorted(self.attribute_list, key=lambda x : x.sequence):
            frame_contents.append({"Attribute" : a.name, "Type" : a.domain.name, "Optional" : a.optional, "PK" : key_glyph_map.get(a.isPK,a.isPK), "FK" : key_glyph_map.get(a.isFK,"")})
        return DataFrame(frame_contents)
    
    @classmethod
    def from_role_key_sheet(cls, df : DataFrame)-> Self:
        row = df.iloc[0]
        return cls(**{  "name" : row.role_key_name,
                        "label" : row.role_key_label,
                        "description" : row.role_key_description,
                        "uri" : row.role_key,
                        "qualified_name" : row.role_key_qualified_name,
                        "attribute_list" : ModelAttributeClass.attribute_list_from_role_key_attribute_sheet(df),
                        "subtype" : row.role_key_type
        })

    def to_svg_component(self):
        
        markup=htmltext.html_to_markup(f"<h1><b>{self.name}</b></h1>" + "".join([f"<p>{a.name} : {a.domain.name}</p>" for a in self.attribute_list]), 65)
        att_textspans=svgsystem.SVGMultiSpanText(span_markup=markup, linespace=1, font=SVGFONTDEJAVUSANS, fontsize=12)

        v_bounds = att_textspans.bounds[0]-3,att_textspans.bounds[1]-2,att_textspans.bounds[2]+5, att_textspans.bounds[3]+3
        vb_bounds = v_bounds[2]-v_bounds[0], v_bounds[3]-v_bounds[1], 

        viewbox=str(svgsystem.SVGViewBox(*v_bounds,*[b*2 for b in vb_bounds]))

        style_content = SVGFONTCSS + "\n".join([ """.layout_rect{\n stroke-width:1;\n stroke:red;\n fill:none;}\n""",
                            """.layout_line{\n stroke-width:0.5;\n stroke:lightblue;\n fill:none;}\n"""     
                            ])
        defs_block = f"""<defs>{"".join([])}<style type="text/css">{style_content}</style></defs>"""
        svg_image = viewbox.replace("%%placeholder%%", 
                            defs_block +\
                            str(att_textspans) 
                            )
        return svg_image,vb_bounds
    
class ModelRoleClass(ModelThingClass):
    def __init__(self,  name : str,
                        label : str,
                        description : str,
                        uri : URIRef,
                        qualified_name : str,
                        key : ModelKeyClass,
                        subtype : str, 
                        is_optional : bool, 
                        has_many : bool
                        ):
        self.name=name
        self.label=label
        self.description=description
        self.uri=uri
        self.qualified_name=qualified_name
        self.key=key
        self.subtype=subtype
        self.is_optional=is_optional
        self.has_many=has_many

        # Handle spurious data options:
        if not isinstance(self.is_optional, bool):
            if str(self.is_optional).lower().strip() in ("yes", "y", "true", "optional", "1"):
                self.is_optional=True
            else:
                self.is_optional=False

        if not isinstance(self.has_many, bool):
            if str(self.has_many).lower().strip() in ("many", "m", "true", "*"):
                self.has_many=True
            else:
                self.has_many=False

    @classmethod
    def from_role_key_sheet(cls, df : DataFrame)-> Self:
        key = ModelKeyClass.from_role_key_sheet(df)
        row = df.iloc[0]
        return cls(**{  "name" : row.role_name,
                        "label" : row.role_label,
                        "description" : row.role_description,
                        "uri" : row.role,
                        "qualified_name" : row.role_qualified_name,
                        "key" : key,
                        "subtype" : row.role_type, 
                        "is_optional" : row.role_optionality, 
                        "has_many" : row.role_cardinality 
        })

    def to_svg_component(self):
        css_style_content = "\n".join([ 
            """.layout_rect{\n stroke-width:1;\n stroke:red;\n fill:none;}\n""",
            """.layout_line{\n stroke-width:0.5;\n stroke:lightblue;\n fill:none;}\n"""])

        match self.is_optional:
            case True:
                if self.has_many:
                    shape=svgsystem.SVGCircleWithSpokes(10,0,0,6,7,fill="none", stroke="black", stroke_width=2)
                else:
                    shape=svgsystem.SVGCircleWithSpokes(10,0,0,2,7,30,fill="none", stroke="black", stroke_width=2)

            case False:
                if self.has_many:
                    shape=svgsystem.SVGRectangleWithSpokes(0,0,20,20,6,7,fill="none", stroke="black", stroke_width=2)
                else:
                    shape=svgsystem.SVGRectangleWithSpokes(0,0,20,20,2,7,30,fill="none", stroke="black", stroke_width=2)

        v_bounds = shape.bounds[0]-2,shape.bounds[1]-2,shape.bounds[2]+4, shape.bounds[3]+4
        vb_bounds = v_bounds[2]-v_bounds[0], v_bounds[3]-v_bounds[1], 

        viewbox=str(svgsystem.SVGViewBox(*v_bounds,*[b*2 for b in vb_bounds]))

        defs_block = f"""<defs><style type="text/css">{css_style_content}</style></defs>"""

        svg_image = viewbox.replace("%%placeholder%%", 
                            defs_block +\
                            str(shape))
        return svg_image, vb_bounds

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
                           KGDM.objectRoleIsAssociatedWithEntity,
                           #KGDM.isDependentOn,
                           KGDM.layoutBreadcrumb
                          ),
            ]
    return all(tests)

styles_by_type = {
    frozenset({RDF.type, OWL.Class}) : { "color" : "red"},
    frozenset({URIRef('https://kgraph.foo/onto/datamodelling#Namespace')}) : { "color" : "yellow"},

    frozenset({URIRef('https://kgraph.foo/onto/datamodelling#Role'), 
               URIRef('https://kgraph.foo/onto/datamodelling#SubjectRole')}) : 
                                                                                { "color" : "#fff", 
                                                                                "shape" : "circle", 
                                                                                "size" : 15,
                                                                                "label_size" : 5},
    frozenset({URIRef('https://kgraph.foo/onto/datamodelling#Role'), 
               URIRef('https://kgraph.foo/onto/datamodelling#ObjectRole')}) : 
                                                                                { "color" : "#fff", 
                                                                                "shape" : "circle", 
                                                                                "size" : 15,
                                                                                "label_size" : 5},
    frozenset({URIRef('https://kgraph.foo/onto/datamodelling#Relationship')}) : { "color" : "#ff931b", 
                                                                                "shape" : "circle", 
                                                                                "size" : 3,
                                                                                "label_size" : 30},
    frozenset({URIRef("test"), URIRef('https://kgraph.foo/onto/datamodelling#Namespace')}) : { "color" : "yellow"},
    frozenset({URIRef('https://kgraph.foo/onto/datamodelling#Attribute')}) : { "color" : "limegreen", 
                                                                                "shape" : "rectangle", 
                                                                                "size" : 10},
    frozenset({URIRef('https://kgraph.foo/onto/datamodelling#Entity')}) : { "color" : "#fff", 
                                                                                "shape" : "rectangle", 
                                                                                "size" : 100, 
                                                                                "label_size" : 50},
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
        "label_size": 2.4,
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
        "arrow_size": 0.0,
        "label_color": "#808080",
        "label_size": 10.0    },
    frozenset({URIRef('https://kgraph.foo/onto/datamodelling#isDependentOn')}) : {
        "color" : "white",
        "opacity" : 1.0,
        "size": 3.0,
        "arrow_color": "white",
        "arrow_size": 10.0,
        "label_color": "black",
        "label_size": 10.0    },
    frozenset({URIRef('https://kgraph.foo/onto/datamodelling#layoutBreadcrumb')}) : {
        "color" : "white",
        "opacity" : 1.0,
        "size": 3.0,
        "arrow_color": "white",
        "arrow_size": 10.0,
        "label_color": "black",
        "label_size": 10.0    },
}

vis_graph_settings = {
    "node_label_data_source" : "label", 
    "node_size_data_source" : "size", 
    "node_label_size_factor" : 2.5, 
    "node_size_factor" : 1.0, 
    "edge_size_data_source" : "size", 
    "edge_label_data_source" : "label", 
    "edge_size_factor" : 2.5, 
    "show_edge_label" : False,
    "edge_curvature" : 0.2,
    "graph_height" : 800,
    "details_height" : 300, 
    "layout_algorithm" : "forceAtlas2Based", 
    "central_gravity" : 1.5, 
    "gravitational_constant" : -10000,
    "spring_constant" : 0.51,
    "spring_length" : 40,
    "avoid_overlap" : 0.4
    
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
    candidate_keys = {e:frozenset(k) for e,k in enumerate(key_set)}
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

def classify_node_by_identity(id, data, gerf_data, property_uri, key_set):
    return id

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

def populate_style_dict(index_object_tuple):
    index, input_object = index_object_tuple
    object_type = type(input_object)
    output_style_dict=dict()

    match input_object:
        
        case ModelEntityClass():
            svg_component, svg_component_size = input_object.to_svg_component()
            png_component = svg_to_png_data_uri_cached(svg_component)

            output_style_dict[index]={
                "image":png_component,
                "size": float(max(svg_component_size)),
                "hover" : f"<img src=\"{png_component}\" width=\"100%\"></img>"
            }
            
        case ModelRoleClass():
            svg_component, svg_component_size = input_object.to_svg_component()
            png_component = svg_to_png_data_uri_cached(svg_component)
            hover_component, hover_component_size = input_object.key.to_svg_component()
            output_style_dict[index]={
                "image":png_component,
                "size": float(max(svg_component_size)*5),
                "hover" : f"<img src=\"{svg_to_png_data_uri_cached(hover_component)}\" width=\"100%\"></img>"
            }

        case ModelRelationshipClass():
            output_style_dict[index]={
            }
        
    return output_style_dict
    
model_processor = BatchThreadProcessor(
    function=populate_style_dict,
    batch_size=50,
    pool_size=8,
)

def process_entity_sheet(entity_sheet):
    
    entity_index = dict()
    attribute_index = dict()
    domain_index = dict()
    # 1st pass, collate indices for content processing
    for i,e in enumerate(entity_sheet):
        entity = e.get('entity')
        attribute = e.get('attribute')
        domain = e.get('domain')
        if entity :
            if entity in entity_index:
                entity_index[entity].add(i)
            else:
                entity_index[entity]=set([i])
        if attribute:
            if attribute in attribute_index:
                attribute_index[attribute].add(i)
            else:
                attribute_index[attribute]=set([i])
        if domain:
            if domain in domain_index:
                domain_index[domain].add(i)
            else:
                domain_index[domain]=set([i])
    entities = dict()

    for e,ix in entity_index.items():
        entities[URIRef(e)] = ModelEntityClass.from_entity_attribute_sheet(DataFrame(list(map(entity_sheet.__getitem__, ix))))
    return entities

def process_relationship_sheet(relationship_sheet):
    relationships=dict()
    for r in relationship_sheet:
        relationships[URIRef(Series(r).relationship)] = ModelRelationshipClass.from_relationship_sheet_row(Series(r))
    return relationships

def process_role_key_sheet(role_key_sheet):
    roles=dict()
    role_index=dict()
    for i,e in enumerate(role_key_sheet):
        role = e.get('role')
        key = e.get('key')
        attribute=e.get('attribute')
        if role :
            if role in role_index:
                role_index[role].add(i)
            else:
                role_index[role]=set([i])
    for r, ix, in role_index.items():
        roles[URIRef(r)]=ModelRoleClass.from_role_key_sheet(DataFrame(list(map(role_key_sheet.__getitem__, ix))))
    return roles

def process_key_sheet(key_sheet):
    keys=dict()
    key_index=dict()
    for i,e in enumerate(key_sheet):
        key = e.get('role_key')
        attribute=e.get('attribute')
        if key :
            if key in key_index:
                key_index[key].add(i)
            else:
                key_index[key]=set([i])
    for k, ix, in key_index.items():
        keys[URIRef(k)]=ModelKeyClass.from_role_key_sheet(DataFrame(list(map(key_sheet.__getitem__, ix))))
    return keys

def entity_list_to_components(entity_list : list[URIRef],
                              graph : Graph)->dict[URIRef,dict]:
    path_nodes = dict()
    for path in rdfquery.results_to_resultlist(
        Q_get_entity_dependency_paths.execute_batched(graph, 
                                                      parameter_bindings={"subjectEntity":[URIRef(n) for n in entity_list]}
                                                     )
        ):
        for c,e in path.items():
            if c in ("subjectEntity", "subjectRole", "relationship", "objectRole", "objectEntity", "objectRoleKey", "subjectRoleKey"):
                match c:
                    case "subjectEntity" | "objectEntity":
                        if "entity" not in path_nodes:
                            path_nodes['entity']=set([URIRef(e)])
                        else:
                            path_nodes['entity'].add(URIRef(e))
                    case "subjectRole" | "objectRole":
                        if "role" not in path_nodes:
                            path_nodes['role']=set([URIRef(e)])
                        else:
                            path_nodes['role'].add(URIRef(e))
                    case "relationship":
                        if "relationship" not in path_nodes:
                            path_nodes['relationship']=set([URIRef(e)])
                        else:
                            path_nodes['relationship'].add(URIRef(e))
                    case "objectRoleKey" | "subjectRoleKey":
                        if "key" not in path_nodes:
                            path_nodes['key']=set([URIRef(e)])
                        else:
                            path_nodes['key'].add(URIRef(e))
    
    entity_sheet = rdfquery.results_to_resultlist(Q_entity_attribute_sheet.execute_batched(graph,
                                            parameter_bindings = {"entity" : path_nodes['entity']}))
    relationship_sheet = rdfquery.results_to_resultlist(Q_relationship_sheet.execute_batched(graph,
                                            parameter_bindings = {"relationship" : path_nodes['relationship']}))
    role_sheet = rdfquery.results_to_resultlist(Q_role_key_attribute_sheet.execute_batched(graph,
                                            parameter_bindings = {"role" : path_nodes['role']}))
    key_sheet = rdfquery.results_to_resultlist(Q_key_attribute_sheet.execute_batched(graph,
                                            parameter_bindings = {"role_key" : path_nodes['key']}))
    
    entity_objects = process_entity_sheet(entity_sheet)
    relationship_objects = process_relationship_sheet(relationship_sheet)
    role_objects = process_role_key_sheet(role_sheet)
    key_objects=process_key_sheet(key_sheet)
    
    process_dict = {**entity_objects, **relationship_objects, **role_objects, **key_objects}
    return process_dict

ERDVisualisation = Visualisation(
    include_node_function=include_node_function,
    include_edge_function=include_edge_function,
    classify_node_passes=[classify_nodes_on_type],
    classify_edge_passes=[classify_edges_on_type],
    vis_graph_settings=vis_graph_settings
)
