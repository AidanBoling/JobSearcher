from sqlalchemy.sql.expression import and_, or_
from sqlalchemy import true, false
from models.job_posts import JobPost
from models.base import Base


class DbFilter:
    """
    Transforms a filter from strings, ints, into a statement that can be used in filtered db queries.
    """
    def __init__(self, model: Base, key: str, value, operator: str):
        self.model = model
        self.col = model.get_column(model, key)
        self.key = key
        self.value = value
        self.operator = operator
        
        self.op_map = {
            '==': self.col.__eq__,
            '!=': self.col.__ne__,
            '<=': self.col.__le__,
            '<': self.col.__lt__,
            '>=': self.col.__ge__,
            '>': self.col.__gt__,
            'any': self.col.in_,
            'not_in': self.col.not_in,
            'ilike': self.col.ilike,
            'not_ilike': self.col.not_ilike
            }
        
        if self.value == 'bool_true':
            self.value = True
        if self.value == 'bool_false':
            self.value = False

    def get(self):
        return self.op_map[self.operator](self.value)
        #Later TODO: Error handling (e.g. throw exception(invalid operator, must be '==', '>=', etc...))


    def __repr__(self):
        return f'<DbFilter: "{self.key}" {self.operator} "{self.value}">'
    
    # Question: should be dataclass? Or perhaps just JobDBFilter as dataclass???
    


class JobDbFilter(DbFilter):

    def __init__(self, key: str, value, operator: str):
        super().__init__(model=JobPost, key=key, value=value, operator=operator) 


    def __repr__(self):
        return f'<JobDbFilter: "{self.key}" {self.operator} "{self.value}">'



class DbFilterGroup:
    """
    Creates group of filters and/or filter groups, connected by an operator (AND/OR), 
    that can be used in filtered queries to the db.
    """
    def __init__(self, operator: str, filters: list):
        self.operator = operator.upper()
        self.filters = filters
        self.expressions = []
        self.get_expressions_list()
    

    def get_expressions_list(self):
        for filter in self.filters:
            if isinstance(filter, JobDbFilter):
                self.expressions.append(filter.get())
            elif isinstance(filter, DbFilterGroup):
                self.expressions.append(filter.op_expression())
            

    def op_expression(self): 
        if self.operator == 'AND':
            return and_(true(), *self.expressions)
        if self.operator == 'OR':
            return or_(false(), *self.expressions)
        
    #Later TODO: Error handling (e.g. throw exception(invalid operator, must be 'AND' or 'OR'...))

    def __repr__(self):
        return f'<DbGroup: "{self.operator}": {self.filters} >'