import json
from . import json_models as jm
from . import structures as struct

class CWBlockScriptGenerator:
    def __init__(self):
        pass

    def generate(self, program: struct.Program) -> str:
        script = self.generate_program(program)
        dict_rep = jm.to_dict([script])
        return json.dumps(dict_rep)

    def generate_program(self, program: struct.Program) -> jm.Script:
        content = [self.generate_item(item) for item in program.main_block]
        return jm.Script(
            alias="",
            class_="script",
            content=content
        )

    def generate_item(self, item: struct.Item) -> jm.FunctionDeclaration:
        if isinstance(item, struct.FunctionDeclaration):
            text = [
                "",  # PlainText("")
                jm.Parameter(value=item.name, t="string")
            ]
            variable_overrides = [jm.FunctionParameter(value=param.name) for param in item.parameters]
            
            actions = []
            for stmt in item.body:
                for call in stmt.dependencies:
                    actions.append(self.generate_script_block(call))
                for call in stmt.content:
                    actions.append(self.generate_script_block(call))
            
            return jm.FunctionDeclaration(
                globalid="",
                id="6",
                text=text,
                variable_overrides=variable_overrides,
                actions=actions
            )
        elif isinstance(item, struct.Event):
            raise NotImplementedError("Event item generation is unimplemented")
        else:
            raise ValueError(f"Unknown item type: {item}")

    def generate_script_block(self, call: struct.Call) -> jm.Action:
        if isinstance(call, struct.CWScriptBlockCall):
            text = []
            for arg in call.arguments:
                if isinstance(arg, struct.LiteralArg):
                    text.append(jm.Parameter(value=arg.literal.value, t="string"))
                elif isinstance(arg, struct.IdentifierArg):
                    text.append(jm.Parameter(value=f"{{l!{arg.variable.name}}}", t="string"))
                elif isinstance(arg, struct.RawString):
                    text.append(arg.value)  # PlainText(value)
                else:
                    raise ValueError(f"Unknown argument type: {arg}")
            
            if call.return_var is not None:
                text.append(jm.Parameter(value=call.return_var.name, t="string"))
                
            return jm.Action(
                globalid="",
                id=call.block_id.id,
                text=text
            )
        elif isinstance(call, struct.FunctionCall):
            text = [
                "",  # PlainText("")
                jm.Tuple(value=[], t="tuple"),
                "",  # PlainText("")
                jm.Parameter(value=call.return_var.name if call.return_var is not None else "", t="string")
            ]
            return jm.Action(
                globalid="",
                id="87",
                text=text
            )
        else:
            raise ValueError(f"Unknown call type: {call}")
