from dataclasses import dataclass, field
from db_control import DbControl

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
        # self.values = values
        # self.optionsHTML = self.options_text()
        # self.valuesHTML = 

        # Put together HTML for options and values from here??? 
        # In filter_control, prep relevant bits for each filter via dict??


    def __repr__(self):
        return f'<FFilter: column="{self.name}", type="{self.type}">'
    

    # def options_text(self):
    #     selected = ''
    #     options = ''
    #     for i, item in enumerate(self.op_list):
    #         if i == 0:
    #             selected = 'selected '
    #         options += f'<option {selected}value="{item[0]}">{item[1]}</option>'
        
    #     return options
    

    # def get_col_unique_values(self):
    #     if not self.values and self.type != 'text' and self.get_values:
    #         unique_vals = self.db_control.get_from_col(self.name, unique=True)

    #         self.values = sorted(unique_vals, key=str.lower)
    #         if '' in self.values:
    #             self.values.remove('')
    #             self.values.append('')
    #         print(f'Unique values for {self.name}: ', self.values)



# @dataclass
# class FrontendFilter:

#     def __init__(self, db_control: DbControl, column_name: str, filter_type: str, values=None, get_values:bool=True):
#         self.db_control = db_control
#         self.name = column_name
#         self.type = filter_type
#         self.operators = TYPES[self.type]['operators']
#         self.op_labels = LABELS
#         self.input_type = TYPES[self.type]['form_input_type']
#         self.get_values = get_values
#         self.values = values

#         self.get_col_unique_values()
#         # Put together HTML for options and values from here??? 
#         # In filter_control, prep relevant bits for each filter via dict??


#     def __repr__(self):
#         return f'<FFilter: column="{self.name}", type="{self.type}">'
    

#     def get_col_unique_values(self):
#         if not self.values and self.type != 'text' and self.get_values:
#             unique_vals = self.db_control.get_from_col(self.name, unique=True)

#             self.values = sorted(unique_vals, key=str.lower)
#             if '' in self.values:
#                 self.values.remove('')
#                 self.values.append('')
#             print(f'Unique values for {self.name}: ', self.values)