####################################################################
#                                                                  #
# THIS FILE IS PART OF THE pycollada LIBRARY SOURCE CODE.          #
# USE, DISTRIBUTION AND REPRODUCTION OF THIS LIBRARY SOURCE IS     #
# GOVERNED BY A BSD-STYLE SOURCE LICENSE INCLUDED WITH THIS SOURCE #
# IN 'COPYING'. PLEASE READ THESE TERMS BEFORE DISTRIBUTING.       #
#                                                                  #
# THE pycollada SOURCE CODE IS (C) COPYRIGHT 2011                  #
# by Jeff Terrace and contributors                                 #
#                                                                  #
####################################################################

"""Contains objects representing animations."""

from collada import source
from collada.common import DaeObject
from collada.common import DaeError

class INTERPOLATION:
    """An enum of the interpolation methods supported by COLLADA"""
    LINEAR = 'LINEAR'
    BEZIER = 'BEZIER'
    CARDINAL = 'CARDINAL'
    HERMITE = 'HERMITE'
    BSPLINE = 'BSPLINE'
    STEP = 'STEP'

class SEMANTIC:
    """An enum of the semantic methods supported by COLLADA"""
    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'
    INTERPOLATION = 'INTERPOLATION'

class Input(DaeObject):
    """Class for holding animation sampler input coming from <input> tags."""
    def __init__(self, semantic, source):
        self.semantic = semantic
        self.source = source

    @staticmethod
    def load(collada, localscope, node):
        semantic = node.get('semantic')
        source = node.get('source')
        if not semantic or not source:
            raise DaeError("Input node of animation sampler missing semantic or source")
        if source[1:] not in localscope:
            raise DaeError("Input of animation sampler refering to source '%s' not found" % source)
        return Input(semantic, localscope[source[1:]])

class Sampler(DaeObject):
    """Class for holding animation sampling coming from <sampler> tags."""
    
    def __init__(self, id, inputs):
        self.id = id
        self.inputs = inputs

    @property
    def input(self):
        return next(x for x in self.inputs if x.semantic == SEMANTIC.INPUT)

    @property
    def output(self):
        return next(x for x in self.inputs if x.semantic == SEMANTIC.OUTPUT)

    @property
    def interpolation(self):
        return next(x for x in self.inputs if x.semantic == SEMANTIC.INTERPOLATION)

    @staticmethod
    def load( collada, localscope, node ):
        id = node.get('id') or ''
        
        inputs = []
        for input_node in node.findall(collada.tag('input')):
            inputs.append(Input.load(collada, localscope, input_node))
        
        return Sampler(id, inputs)
    
    def __str__(self): return '<Sampler id=%s>' % (self.id,)
    def __repr__(self): return str(self)

class Channel(DaeObject):
    """Class for holding animation channel coming from <channel> tags."""
    
    def __init__(self, source, target):
        self.source = source
        self.target = target
    
    @staticmethod
    def load( collada, localscope, node ):
        source = node.get('source')
        target = node.get('target')
        
        if not source or not target:
            raise DaeError("Animation channel node missing source or target")
        if source[1:] not in localscope:
            raise DaeError("Input of animation channel '%s' not found" % (source))
        
        source = localscope[source[1:]]
        return Channel(source, target)
    
    def __str__(self): return '<Channel source=%s target=%s>' % (self.source, self.target)
    def __repr__(self): return str(self)

class Animation(DaeObject):
    """Class for holding animation data coming from <animation> tags."""

    def __init__(self, id, name, sourceById, samplers, channels, children, xmlnode=None):
        self.id = id
        self.name = name
        self.samplers = samplers
        self.channels = channels
        self.children = children
        self.sourceById = sourceById
        self.xmlnode = xmlnode
        if self.xmlnode is None:
            self.xmlnode = None

    @staticmethod
    def load(collada, localscope, node):
        id = node.get('id') or ''
        name = node.get('name') or ''

        sourcebyid = localscope
        sources = []
        sourcenodes = node.findall(collada.tag('source'))
        for sourcenode in sourcenodes:
            ch = source.Source.load(collada, {}, sourcenode)
            sources.append(ch)
            sourcebyid[ch.id] = ch

        samplers = {}
        for sampler_node in node.findall(collada.tag('sampler')):
            try:
                sampler = Sampler.load(collada, sourcebyid, sampler_node)
                samplers[sampler.id] = sampler
            except DaeError as ex:
                collada.handleError(ex)

        channels = []
        for channel_node in node.findall(collada.tag('channel')):
            try:
                channels.append(Channel.load(collada, samplers, channel_node))
            except DaeError as ex:
                collada.handleError(ex)

        child_nodes = node.findall(collada.tag('animation'))
        children = []
        for child in child_nodes:
            try:
                child = Animation.load(collada, sourcebyid, child)
                children.append(child)
            except DaeError as ex:
                collada.handleError(ex)

        anim = Animation(id, name, sourcebyid, list(samplers.values()), channels, children, node)
        return anim

    def __str__(self):
        return '<Animation id=%s, children=%d>' % (self.id, len(self.children))

    def __repr__(self):
        return str(self)
