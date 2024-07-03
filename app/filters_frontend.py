from dataclasses import dataclass, field

TYPES = {
    'list': {
        'operators': ['any', 'not_in'],
        'form_input_type': 'multi-select',
        },
    'text': {
        'operators': ['icontains', 'not_icontains', '==', '!='],
        'form_input_type': 'text'
        },
    'number': {
        'operators': ['<', '<=', '>', '>=', '==', '!='],
        'form_input_type': 'number'
        },
    'date': {
        'operators': ['==', '!=', ('<', 'before'), ('<=', 'on or before'), ('>', 'after'), ('>=', 'on or after')],
        'form_input_type': 'date',
        'value_options': ['Exact date', 'Today', 'Yesterday', 'One week ago', 'One month ago', 'Other relative date']
        },
    'boolean': {
        'operators': ['==', '!='],
        'form_input_type': 'boolean'
        },
    }

DEFAULT_LABELS = {
    'any': 'any of',
    'not_in': 'none of',
    'ilike': 'contains',
    'not_ilike': 'does not contain',
    'icontains': 'contains',
    'not_icontains': 'does not contain',
    '==': 'is',
    '!=': 'is not',
    '<=': 'less or equal',
    '>=': 'greater or equal',
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
    name: str
    type: str
    values: 'typing.Any' = ''
    input_type: str = field(default_factory=str)
    op_list: list[tuple] = field(default_factory=list)
    

    def __post_init__(self):
        self.operators = TYPES[self.type]['operators']
        self.input_type = TYPES[self.type]['form_input_type']

        # self.op_list = [(op, LABELS[op]) for op in self.operators]
        self.op_list = [op if type(op) is tuple else (op, DEFAULT_LABELS[op]) for op in self.operators]

        value_options = TYPES[self.type].get('value_options')
        if value_options:
            self.values = [option if type(option) is tuple else (option, option) for option in value_options]

            # for option in value_options:
            #     if type(option) is tuple:
            #         self.value_options.append(option)
            #     else:
            #         self.value_options.append((option, option))


    def __repr__(self):
        return f'<FFilter: column="{self.name}", type="{self.type}">'
    




