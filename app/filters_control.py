from dataclasses import asdict
from copy import deepcopy
from dateparser import parse
from filters_frontend import FrontendFilter
from db_control import DbControl, DbFilterGroup
from filters_db import JobDbFilter, DbFilter
from models.job_posts import job_filters as available_job_filters

class FrontendFilterOptionsList:

    def __init__(self, db_control: DbControl, fe_filter_settings: dict):
        self.fe_settings = fe_filter_settings #options
        self.db_control = db_control
        self.filters = {}

        self.build()


    def build(self):

        filterable_columns = self.fe_settings.keys()

        for column in filterable_columns:
            settings = self.fe_settings[column]
            values = None
            if not settings.get('values') and settings['filter_type'] in ['list'] and settings.get('get_values') is None:
                values = self.get_col_unique_values(column)
                values.insert(0, '')
                values = list(zip(values, values))

            filter = FrontendFilter(name=column, type=settings['filter_type'], values=values)
            self.filters[column] = asdict(filter)


    def get_col_unique_values(self, column: str) -> list:
        unique_vals = self.db_control.get_from_col(column, unique=True)
        if None in unique_vals:
            unique_vals.remove(None)
        if '' in unique_vals:
            unique_vals.remove('')

        sorted_values = sorted(unique_vals, key=str.lower)
        # print(f'Unique values for {column}: ', sorted_values)
        return sorted_values



class FiltersConverter:

    def __init__(self, db_filter_class: DbFilter, fe_filter_settings: dict):
        self.db_filter = db_filter_class        
        self.filter_settings = fe_filter_settings

        self.list_operators = ['any', 'not_in']
        self.list_field_types = ['date']
        self.list_fields = [key for key in fe_filter_settings.keys() if fe_filter_settings[key]['filter_type'] in self.list_field_types]


    def convert_saved_filters_to_db(self, filters: dict):
        dict_filter_group = deepcopy(filters)
        db_filter_group = self.nested_filter_group_to_db(dict_filter_group, self.db_filter)
        return db_filter_group


    def nested_filter_group_to_db(self, group: dict, dbFilter: DbFilter) -> DbFilterGroup:
        """
        Takes group of nested filters and filter groups in dictionary form and converts into nested DbFilters
        and DbFilterGroups.
        """
        if group.get('filters'):
            filters = []
            # Check filters list for nested groups and filters. Convert as needed
            for item in group['filters']:
                
                if isinstance(item, dbFilter) or isinstance(item, DbFilterGroup):
                    filters.append(item)

                elif item.get('field'):
                    field = item['field']
                    field_type = self.filter_settings[field]['filter_type']
                    
                    if field in self.list_fields:
                        values = item['values']

                        if field_type == 'date':
                            first_value = values[0].lower()

                            if len(values) > 1 and ('exact' in first_value or 'relative' in first_value):
                                values.pop(0)
                            value = ' '.join(values)
                            item['values'] = parse(value, settings={'RETURN_AS_TIMEZONE_AWARE': True})
                
                    filter = dbFilter(item['field'], item['values'], item['operator'])
                    filters.append(filter)

                else:
                    # If nested group, call same func to recursively drill down to inner-most group 
                    filter_group = self.nested_filter_group_to_db(item, dbFilter)
                    filters.append(filter_group)
            
            # print('nested_filters: ', filters)
            return DbFilterGroup(group['group_op'], filters)
        
        return group    


    def form_response_to_dict(self, filter_data: dict):

        def filters_from_form(filter_data: dict):
            filters = {}
            for filter_item in filter_data:
                # Separate path from key, value for each item
                path_list = filter_item.split('.')
                key = path_list.pop(-1)
                path = '.'.join(path_list)
                value = filter_data[filter_item]

                if key == 'values':
                    filter_field = filters[path]['field']
                    filter_operator = filters[path]['operator']
                    if filter_field in self.list_fields or filter_operator in self.list_operators:
                        value = filter_data.getlist(filter_item)
                
                # Consolidate items into filters
                if not filters.get(path):
                    filters[path] = {}
                filters[path][key] = value

            return filters


        # Iterate items into nested filters/group dicts
        def get_group(filter_data: dict):
            group = filter_data.get('group')
            if group:
                filter_data.pop('group')
                g_filters = {}
                for path, item in filter_data.items():
                    path_start, path = split_path(path)
                    g_filters.update({path: item})
                
                group['filters'] = get_group_filters(g_filters)

            return group
                                

        def get_group_filters(filter_data: dict):
            filters = {}

            for path, item in filter_data.items():
                path_start, path = split_path(path)

                if path_start not in ['filter', 'group']:
                    index = int(path_start)
                    filter = ''
                    
                    if path == 'filter':
                        filter = item
                    else:
                        filter = {path: item}

                    if not filters.get(index):
                        filters[index] = filter
                    else:
                        filters[index].update(filter)

            filters = [item if isinstance(item, JobDbFilter) or item.get('field') else get_group(item) for key, item in filters.items()]
            return filters
        

        def split_path(path):
            # Pop off front segment from path, return segment and new path 
            path_list = path.split('.')            
            path_start = path_list.pop(0)
            path = '.'.join(path_list)
            return path_start, path
        

        filters_dict = filters_from_form(filter_data)
        print('\nfilters: ', filters_dict)
        f_group = get_group(filters_dict)

        return f_group
    


class JobFiltersConverter(FiltersConverter):

    def __init__(self):
        super().__init__(db_filter_class=JobDbFilter, fe_filter_settings=available_job_filters)