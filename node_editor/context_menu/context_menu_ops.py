import bpy
from bpy import types as btypes
from ...btypes import BOperator
from ...functions import get_active_node_tree

prop_names = {
    "FunctionNodeInputInt": "integer",
    "ShaderNodeValue": "default_value",
    "FunctionNodeInputVector": "vector",
    "GeometryNodeInputMaterial": "material",
    "FunctionNodeInputBool": "boolean",
    "FunctionNodeInputColor": "color",
    # "GeometryNodeObjectInfo": "",
    "FunctionNodeInputString": "string",
}


@BOperator("strike", label="Extract to node", undo=True)
class STRIKE_OT_extract_node_prop(btypes.Operator):
    """Extract this value from a node into a separate input node"""

    types = {
        "INT": "FunctionNodeInputInt",
        "VALUE": "ShaderNodeValue",
        "BOOLEAN": "FunctionNodeInputBool",
        "VECTOR": "FunctionNodeInputVector",
        "STRING": "FunctionNodeInputString",
        "MATERIAL": "GeometryNodeInputMaterial",
        "RGBA": "FunctionNodeInputColor",
        "RGB": "FunctionNodeInputColor",
    }

    prop_names = prop_names

    @classmethod
    def poll(cls, context):
        if not hasattr(context, "button_pointer") or context.area.type != "NODE_EDITOR":
            return False

        node_tree = get_active_node_tree(context)
        if not node_tree:
            return False

        socket = context.button_pointer
        if not socket or not hasattr(socket, "is_output") or socket.is_output or socket.type not in cls.types:
            return False
        return True

    def execute(self, context: btypes.Context):
        socket: btypes.NodeSocket = context.button_pointer
        orig_node = socket.node
        value = socket.default_value
        # TODO make the value match when it is connected

        try:
            node_type = self.types[socket.type]
        except KeyError:
            self.report(
                {"WARNING"},
                "This socket type does not have an associated input node for the property to be extracted to",
            )
            return {"FINISHED"}

        bpy.ops.node.add_node(
            "INVOKE_DEFAULT",
            type=node_type,
        )

        node = context.active_node
        node.label = socket.label if socket.label else socket.name
        node.location.x = orig_node.location.x - 20 - node.width
        node.location.y += 40

        bpy.ops.node.translate_attach("INVOKE_DEFAULT")

        output = node.outputs[0]
        if node.bl_idname == "ShaderNodeValue":
            output.default_value = value
        else:
            setattr(node, self.prop_names[node.bl_idname], value)
        node_tree = context.area.spaces.active.path[-1].node_tree
        node_tree.links.new(output, socket)

        return {"FINISHED"}


@BOperator("strike", label="Extract to named attribute", undo=True)
class STRIKE_OT_extract_node_prop_to_named_attr(btypes.Operator):
    """Extract this value to a named attribute"""

    types = {
        "INT": "INT",
        "VALUE": "FLOAT",
        "BOOLEAN": "BOOLEAN",
        "VECTOR": "FLOAT_VECTOR",
        "RGBA": "FLOAT_COLOR",
        "RGB": "FLOAT_COLOR",
    }

    prop_names = prop_names

    @classmethod
    def poll(cls, context):
        if not hasattr(context, "button_pointer") or context.area.type != "NODE_EDITOR":
            return False

        node_tree = get_active_node_tree(context)
        if not node_tree or node_tree.type != "GEOMETRY":
            return False

        socket = context.button_pointer
        if not socket or not hasattr(socket, "is_output") or socket.is_output or socket.type not in cls.types:
            return False
        return True

    def invoke(self, context: btypes.Context, event: btypes.Event):
        socket: btypes.NodeSocket = context.button_pointer
        orig_node = socket.node

        bpy.ops.node.add_node(
            "INVOKE_DEFAULT",
            type="GeometryNodeInputNamedAttribute",
        )

        node = context.active_node
        self.node = node
        node.label = socket.label if socket.label else socket.name
        node.location.x = orig_node.location.x - 20 - node.width
        node.location.y += 40
        node.data_type = self.types[socket.type]

        bpy.ops.node.translate_attach("INVOKE_DEFAULT")

        for output in node.outputs:
            if output.enabled:
                break
        # output = node.outputs[0]
        node_tree = context.area.spaces.active.path[-1].node_tree
        node_tree.links.new(output, socket)
        return {"FINISHED"}
        # return context.window_manager.invoke_props_popup(self, event)

    def draw(self, context: btypes.Context):
        layout = self.layout
        layout.activate_init = True
        row = layout.row()
        row.activate_init = True
        row.active_default = True
        context.active_node.inputs[0].draw(context, row, context.active_node, "hoho")
        # layout.prop(self.node.inputs[0], "default_value")
        # layout.template_node_view(context.space_data.node_tree, context.active_node, context.active_node.inputs[0])

    def execute(self, context: btypes.Context):
        return {"FINISHED"}


@BOperator("strike", label="Extract to new group input", undo=True)
class STRIKE_OT_extract_node_prop_to_group_input(btypes.Operator):
    """Extract this property as an input paramater for this node group"""

    @classmethod
    def poll(cls, context):
        if not hasattr(context, "button_pointer") or context.area.type != "NODE_EDITOR":
            return False

        node_tree = get_active_node_tree(context)
        if not node_tree or node_tree.type != "GEOMETRY":
            return False

        socket = context.button_pointer
        if not socket or not hasattr(socket, "is_output") or socket.is_output:
            return False
        return True

    def execute(self, context):
        socket: btypes.NodeSocket = context.button_pointer
        node_tree = get_active_node_tree(context)
        orig_node = socket.node
        if not (context.active_node and context.active_node.type == "GROUP_INPUT"):
            bpy.ops.node.add_node(
                "INVOKE_DEFAULT",
                type="NodeGroupInput",
            )
            bpy.ops.node.translate_attach("INVOKE_DEFAULT")
            node = context.active_node
            node.location.x = orig_node.location.x - 20 - node.width
            node.location.y += 40

        node = context.active_node
        node.label = socket.label if socket.label else socket.name

        node_tree.links.new(node.outputs[-1], socket)

        return {"FINISHED"}


@BOperator("strike", label="Extract to group input", undo=True)
class STRIKE_OT_extract_node_to_group_input(btypes.Operator):
    """Extract this node as an input paramater for this node group"""

    types = {
        "FunctionNodeInputInt": "NodeSocketInt",
        "ShaderNodeValue": "NodeSocketFloat",
        "FunctionNodeInputVector": "NodeSocketVector",
        "GeometryNodeInputMaterial": "NodeSocketMaterial",
        "FunctionNodeInputBool": "NodeSocketBool",
        "FunctionNodeInputColor": "NodeSocketColor",
        "FunctionNodeInputString": "NodeSocketString",
    }

    prop_names = prop_names

    with_subtype: bpy.props.BoolProperty(default=True)

    @classmethod
    def poll(cls, context):
        if context.area.type != "NODE_EDITOR":
            return False

        node_tree = get_active_node_tree(context)
        if not node_tree:
            return False

        # Check to see whether this is a material or compositor, rather than a node group
        for ng in bpy.data.node_groups:
            if ng == node_tree:
                break
        else:

            return False

        if not node_tree.nodes.active or node_tree.nodes.active.bl_idname not in cls.types:
            return False
        return True

    def execute(self, context: btypes.Context):
        node_tree = get_active_node_tree(context)
        # node_tree: btypes.NodeTree = context.space_data.node_tree
        node: btypes.Node = context.active_node
        socket_name = node.label if node.label else node.name
        to_socket = []
        socket_type = self.types[node.bl_idname]
        matching = False

        # Get information from the socket the node is connected to rather than the node
        if node.outputs[0].links:
            link = node.outputs[0].links[0]
            to_sockets = [l.to_socket for l in node.outputs[0].links]
            to_socket = link.to_socket
            if not node.label:
                socket_name = to_socket.label if to_socket.label else to_socket.name
            if to_socket.type == link.from_socket.type:
                matching = True
                if self.with_subtype:
                    socket_type = to_socket.bl_idname

        # Create a dictionary containing the keys of all inputs in geo nodes modifiers for the current node tree
        # I really wish the devs would implement a sane system for interacting with geo nodes modifiers from the api
        # It would probably add a few more years on to the end of my life that have been stolen by the current system.
        modifiers = [
            m for obj in bpy.data.objects for m in obj.modifiers if m.type == "NODES" and m.node_group == node_tree
        ]

        def get_modifier_input_names(m):
            keys = set()
            for k in m.keys():
                if not k.endswith("_attribute_name") and not k.endswith("_use_attribute") and k.startswith("Input_"):
                    keys.add(k)
            return keys

        inputs = {}
        for m in modifiers:
            inputs[m.name] = get_modifier_input_names(m)

        # Add the new group input
        socket = node_tree.inputs.new(socket_type, socket_name)
        if node.bl_idname == "ShaderNodeValue":
            value = node.outputs[0].default_value
        else:
            value = getattr(node, self.prop_names[node.bl_idname])
        socket.default_value = value
        node_tree.active_input = len(node_tree.inputs) - 1

        # Set all occurences of that property to the default value
        for ng in bpy.data.node_groups:
            for n in ng.nodes:
                if hasattr(n, "node_tree") and n.node_tree == node_tree:
                    n.inputs[-1].default_value = value
                    pass

        # Do the same for modifiers if it is geometry nodes
        if node_tree.type == "GEOMETRY":
            for obj in bpy.data.objects:
                for modifier in obj.modifiers:
                    if modifier.type == "NODES" and modifier.node_group == node_tree:
                        # find the new key and change that property
                        keys = get_modifier_input_names(modifier)
                        keys.difference_update(inputs[modifier.name])
                        new_key = list(keys)[0]
                        modifier[new_key] = value

        # Set the min and max values if applicable
        if to_socket and matching:
            rna = to_socket.bl_rna.properties["default_value"]
            if hasattr(socket, "min_value") and not socket.default_value < rna.soft_min:
                socket.min_value = rna.soft_min
            if hasattr(socket, "max_value") and not socket.default_value > rna.soft_min:
                socket.max_value = rna.soft_max

        # Create a new group input node and replace the old node with it
        input_node = node_tree.nodes.new("NodeGroupInput")
        input_node.label = socket_name
        input_node.location = node.location
        for output in input_node.outputs[:-2]:
            output.hide = True

        # Hide the newly created socket from other input nodes
        for n in node_tree.nodes:
            if n.type == "GROUP_INPUT" and n != input_node:
                # shown = [o for o in n.outputs if not o.hide and not o.links]
                for o in n.outputs[:-1]:
                    if not o.links:
                        o.hide = True
                # if len(shown) <= 1:

        # Relink the new group input node
        if to_socket:
            for socket in to_sockets:
                node_tree.links.new(input_node.outputs[-2], socket)
        node_tree.nodes.active = input_node
        node_tree.nodes.remove(node)
        return {"FINISHED"}


@BOperator("strike", label="Connect to group input", undo=True)
class STRIKE_OT_connect_prop_to_group_input(btypes.Operator):
    """Connect this input to an existing group input"""

    input_index: bpy.props.IntProperty()

    @classmethod
    def poll(cls, context):
        if not hasattr(context, "button_pointer") or context.area.type != "NODE_EDITOR":
            return False

        node_tree = get_active_node_tree(context)
        if not node_tree:
            return False

        socket = context.button_pointer
        if not socket or not hasattr(socket, "is_output") or socket.is_output:
            return False
        return True

    def execute(self, context: btypes.Context):
        ng = get_active_node_tree(context)
        socket = context.button_pointer
        orig_node = socket.node
        nodes = ng.nodes
        links = ng.links

        # Use the active node if it is a group input, otherwise create a new one and use that
        if nodes.active and nodes.active.select and nodes.active.type == "GROUP_INPUT":
            node = nodes.active
        else:
            bpy.ops.node.add_node("INVOKE_DEFAULT", type="NodeGroupInput")
            node = context.active_node
            node.location.x = orig_node.location.x - 20 - node.width
            for i, output in enumerate(node.outputs):
                if i != self.input_index and i != len(node.outputs) - 1:
                    output.hide = True
            bpy.ops.node.translate_attach_remove_on_cancel("INVOKE_DEFAULT")

        output = node.outputs[self.input_index]
        output.hide = False
        links.new(output, socket)
        return {"FINISHED"}