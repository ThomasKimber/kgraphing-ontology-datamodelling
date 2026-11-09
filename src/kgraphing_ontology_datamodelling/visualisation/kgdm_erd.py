from typing import Callable, Optional, Any, Self
import io
import tempfile
import asyncio

from functools import partial
from rdflib.namespace import RDF, RDFS, OWL
from rdflib import URIRef, BNode, Literal, Namespace
from pandas import DataFrame, Series
import tqdm

from svgtext import svgsystem, htmltext, render
from svgtext.render import svg_to_png, batch_svg_to_png
from kgraphing_ontology_datamodelling.visualisation.core import Visualisation, ClassificationPass
from kgraphing import setfunctions, gerf
from kgraphing.visgerf import VisGerf
from kgraphing_ontology_datamodelling.queries import Q_entity_attribute_sheet, Q_relationship_sheet, Q_role_key_attribute_sheet
from kgraphing_ontology_datamodelling.queries import Q_get_object_by_type, Q_get_entity_roles, Q_get_key_attributes
from kgraphing_ontology_datamodelling.queries import Q_key_attribute_sheet


from kgraphing.store import rdfquery

def svg_to_urldata(svg : str)->str:
    #with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as tmp:
    #    tmp.write(svg)
    #    virtual_filename = tmp.name  # This is the string path you pass to the API
    #    image_data = convert.image_to_data_url(virtual_filename, 'svg', return_data_format=False)
    #    return image_data
    base64text=render.base64_text_to_data_url(svg,data_format="svg")
    return render.base64_text_to_data_url(base64text, "png")

def png_bytes_to_urldata(img : bytes)->str:
    #with tempfile.NamedTemporaryFile(mode='wb', suffix='.png', delete=False) as tmp:
    #    tmp.write(img)
    #    virtual_filename = tmp.name  # This is the string path you pass to the API
    #    image_data = convert.image_to_data_url(virtual_filename, 'png', return_data_format=False)
    #    tmp.flush()
    #    return image_data
    base64text=render.binary_data_to_base64_text(img)
    return render.base64_text_to_data_url(base64text, "png")


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

        css_style_content = svg_font_registry.css_style(include_fonts=['Comfortaa Regular', 'DejaVu Sans', 'DejaVu Sans Mono']) + "\n".join([ 
            """.layout_rect{\n stroke-width:1;\n stroke:red;\n fill:none;}\n""",
            """.layout_line{\n stroke-width:0.5;\n stroke:lightblue;\n fill:none;}\n"""     
                      ])
        svg_attribute_data_grid = svgsystem.SVGDataGridLayout(attribute_data_grid,
                                         {},
                                         True,
                                         svg_font_registry.registry['Comfortaa Regular'], 
                                         12,
                                         svg_font_registry.registry['DejaVu Sans Mono'],
                                         10,
                                         (1,10))
        
        entity_description_markup = htmltext.html_to_markup(self.description, 65)

        entity_description_text = svgsystem.SVGMultiSpanText(entity_description_markup, 
                                                1.0, 
                                                svg_font_registry.registry['DejaVu Sans'],
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
            title_font=svg_font_registry.registry['Comfortaa Regular'], 
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
        svg_font_registry = svgsystem.SVGFontRegistry()
        markup=htmltext.html_to_markup(f"<h1><b>{self.name}</b></h1>" + "".join([f"<p>{a.name} : {a.domain.name}</p>" for a in self.attribute_list]), 65)
        att_textspans=svgsystem.SVGMultiSpanText(span_markup=markup, linespace=1, font=svg_font_registry.registry['DejaVu Sans'], fontsize=12)
        shape=svgsystem.SVGCircleWithSpokes(10,0,0,6,7,fill="none", stroke="black", stroke_width=2)

        composite = svgsystem.SVGHorizontalComposite(contents=[shape, att_textspans], padding=5.0)

        v_bounds = composite.bounds[0]-3,composite.bounds[1]-2,composite.bounds[2]+5, composite.bounds[3]+3
        vb_bounds = v_bounds[2]-v_bounds[0], v_bounds[3]-v_bounds[1], 

        viewbox=str(svgsystem.SVGViewBox(*v_bounds,*[b*2 for b in vb_bounds]))

        style_content = svg_font_registry.css_style() + "\n".join([ """.layout_rect{\n stroke-width:1;\n stroke:red;\n fill:none;}\n""",
                            """.layout_line{\n stroke-width:0.5;\n stroke:lightblue;\n fill:none;}\n"""     
                            ])
        defs_block = f"""<defs>{"".join([])}<style type="text/css">{style_content}</style></defs>"""
        svg_image = viewbox.replace("%%placeholder%%", 
                            defs_block +\
                            str(composite) 
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
        "color" : "grey",
        "opacity" : 1.0,
        "size": 3.0,
        "arrow_color": "black",
        "arrow_size": 10.0,
        "label_color": "black",
        "label_size": 10.0    },
}

vis_graph_settings = {
    "node_label_data_source" : "label", 
    "node_size_data_source" : "size", 
    "node_label_size_factor" : 2.5, 
    "node_size_factor" : 3.0, 
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

def erd_gen_svg_image_for_node(graph, node_id, gerf_data)->dict[URIRef,dict[str,Any]]:
    empty_node = gerf.ObservedEntity(identifier=None, order=None, gerf_object=gerf_data)
    node_type = gerf_data.entities.get(node_id, empty_node).interactions.get(RDF.type,set())
    key_set = {frozenset({KGDM.Entity}) : KGDM.Entity, 
               frozenset({KGDM.SubjectRole}) : KGDM.SubjectRole, 
               frozenset({KGDM.ObjectRole}) : KGDM.ObjectRole, 
               frozenset({KGDM.Relationship}) : KGDM.Relationship,
               frozenset({KGDM.PrimaryKey}) : KGDM.PrimaryKey,
               frozenset({KGDM.ForeignKey}) : KGDM.ForeignKey
               }
    candidate_keys = {e:k for e,k in enumerate(key_set)}
    matching_keys = {k:v for k,v in setfunctions.venn_partitions({**{"Q" : node_type}, **{e:set(k) for e,k in candidate_keys.items()}}, 
                                         notation_style="binindex").items() if 'Q' in k}
    
    matching_candidates = {k:v for k,v in candidate_keys.items() if k in { m for y in matching_keys for m in y}}
    best_keys = sorted([(k, setfunctions.lir_stats(node_type, val)) for k,val in matching_candidates.items()], key=lambda x : x[1][2], reverse=True)
    svg_image={}
    if len(best_keys)>0:
        match key_set[candidate_keys[best_keys[0][0]]]:
            case KGDM.Entity:
                entity_sheet_df=DataFrame(rdfquery.results_to_resultlist(Q_entity_attribute_sheet.execute(
                    graph, 
                    {"entity" : node_id}
                    ))).fillna("")
                mec = ModelEntityClass.from_entity_attribute_sheet(entity_sheet_df)
                svg, bounds = mec.to_svg_component()

                svg_image = {"image": svg,"size" : 100}
            case KGDM.Relationship:
                pass
            case KGDM.SubjectRole | KGDM.ObjectRole:
                role_sheet_df=DataFrame(rdfquery.results_to_resultlist(Q_role_key_attribute_sheet.execute(
                    graph,
                    {"role" : node_id}))).fillna("")

                mrc = ModelRoleClass.from_role_key_sheet(role_sheet_df)

                svg, bounds = mrc.to_svg_component()
                svg_image = {"image": svg, "size" : max(bounds)*2}
            case KGDM.PrimaryKey | KGDM.ForeignKey:
                key_sheet_df=DataFrame(rdfquery.results_to_resultlist(Q_key_attribute_sheet.execute(
                graph,
                {"role_key" : node_id}))).fillna("")

                mkc = ModelKeyClass.from_role_key_sheet(key_sheet_df)

                svg, bounds = mkc.to_svg_component()
                svg_image = {"image": svg, "size" : max(bounds)*2}
                

    else:
        print(f"It was a {key_set[candidate_keys[best_keys[0][0]]]}")
    
    return svg_image

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

async def calculate_images_and_return_classification_pass_for_erd(gerf, 
                                                                  node_selection : list[URIRef]|None=None):
    if node_selection is None:
        entity_list = rdfquery.results_to_resultlist(Q_get_object_by_type.execute(gerf.source_graph, 
                                                                              parameter_bindings={"type":KGDM.Entity}))
    else:
        entity_list = [{'subject':n} for n in node_selection]
    entity_list = set([URIRef(r['subject']) for r in entity_list])
    role_list=set()
    key_list=set()
    role_keys={}

    for e in entity_list:
        e_roles = rdfquery.results_to_resultlist(Q_get_entity_roles.execute(gerf.source_graph, parameter_bindings={"entity" : e}))
        role_list=role_list.union(set([URIRef(r['role']) for r in e_roles]))
        
        key_list=key_list.union(set([URIRef(r['role_key']) for r in e_roles if r['role_key'] is not None]))
        role_keys={**role_keys, **{URIRef(r['role']) : URIRef(r['role_key']) for r in e_roles if r['role_key'] is not None}}

    e_svg_d = {}
    for e in tqdm.tqdm(entity_list.union(role_list).union(key_list)):
        e_svg_d[e]=erd_gen_svg_image_for_node(gerf.source_graph, e, gerf)
    e_png_d=await batch_svg_to_png(({k:v['image'] for k,v in e_svg_d.items()}))

    combined_style_d={}
    for e in entity_list.union(role_list).union(key_list):
        if e in role_list:

            combined_style_d[e]={
                "image":png_bytes_to_urldata(e_png_d[e]),
                "size":e_svg_d[e]['size'],
                "hover":f"<img src=\"{png_bytes_to_urldata(e_png_d.get(role_keys.get(e,e)))}\"></img>"
            }
        else:
            combined_style_d[e]={
                "image":png_bytes_to_urldata(e_png_d[e]),
                "size":e_svg_d[e]['size'],
                "hover":f"<img src=\"{png_bytes_to_urldata(e_png_d[e])}\"></img>"
            }
    return combined_style_d


ERDVisualisation = Visualisation(
    include_node_function=include_node_function,
    include_edge_function=include_edge_function,
    classify_node_passes=[classify_nodes_on_type],
    classify_edge_passes=[classify_edges_on_type],
    vis_graph_settings=vis_graph_settings
)
