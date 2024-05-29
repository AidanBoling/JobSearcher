from dataclasses import dataclass, field
# from db_control import DbControl

TYPES = {
    'list': {
        'operators': ['any', 'not_in'],
        'form_input_type': 'multi-select',
        },
    'text': {
        'operators': ['ilike', 'not_ilike'],
        'form_input_type': 'text'
        },
    'number': {
        'operators': ['==', '!=', '<=', '>=', '<', '>'],
        'form_input_type': 'number'
        },
    'date': {
        'operators': ['==', '!=', '<=', '>=', '<', '>'],
        'form_input_type': 'date'
        }
    }

LABELS = {
    'any': 'is any of',
    'not_in': 'is none of',
    'ilike': 'contains',
    'not_ilike': 'does not contain',
    '==': 'is',
    '!=': 'is not',
    '<=': 'less than or equal',
    '>=': 'greater than or equal',
    '<': 'less than',
    '>': 'greater than'
    }





@dataclass
class FrontendFilter:
    """
    Dataclass to hold filter data for purposes of form selection via frontend.
    "name" is the column name, "type" is the input selection type, to lookup in TYPES dict,
    and "values" is any value, or list of values, that should be populated into form field
    """
    # def __init__(self, column_name: str, filter_type: str, values=None):
    name: str
    type: str
    values: 'typing.Any' = ''
    input_type: str = field(default_factory=str)
    op_list: list[tuple] = field(default_factory=list)
    

    def __post_init__(self):
        self.operators = TYPES[self.type]['operators']
        self.input_type = TYPES[self.type]['form_input_type']

        for op in self.operators:
            op_label = LABELS[op]
            self.op_list.append((op, op_label))


    def __repr__(self):
        return f'<FFilter: column="{self.name}", type="{self.type}">'
    




