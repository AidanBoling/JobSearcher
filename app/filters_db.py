from sqlalchemy.sql.expression import and_, or_
from sqlalchemy import true, false
from models.job_posts import column_map


class DbFilter:

    def __init__(self, col_map: dict, key: str, value, operator: str):
        self.col_map = col_map
        self.col = self.col_map[key]
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
            'any': self.col.any_,
            'not_in': self.col.not_in
            }
        

    def get(self):
        return self.op_map[self.operator](self.value)
        #Later TODO: Error handling (e.g. throw exception(invalid operator, must be '==', '>=', etc...))


    def __repr__(self):
        return f'<DbFilter: {self.key} {self.operator} {self.value}>'
    



class JobDbFilter(DbFilter):

    def __init__(self, key: str, value, operator: str):
        super().__init__(col_map=column_map, key=key, value=value, operator=operator)        
    
    def __repr__(self):
        return f'<JobDbFilter: {self.key} {self.operator} {self.value}>'




class DbFilterGroup:

    def __init__(self, operator: str, filters: list):
        self.operator = operator
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