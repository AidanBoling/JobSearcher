from dataclasses import asdict
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

            # filter = FrontendFilter(self.db_control, column, settings['filter_type'], values, settings.get('get_values'))
            self.filters[column] = asdict(filter)


    def get_col_unique_values(self, column: str) -> list:
        unique_vals = self.db_control.get_from_col(column, unique=True)

        sorted_values = sorted(unique_vals, key=str.lower)
        if '' in sorted_values:
            sorted_values.remove('')
        # print(f'Unique values for {column}: ', sorted_values)
        return sorted_values



# TODO: Rename to FiltersConverter

class FiltersConverter:

    def __init__(self, db_control: DbControl, db_filter_class: DbFilter, fe_filter_settings: dict, saved_view_filters: dict):
        # self.fe_settings = fe_filter_settings #options
        # self.db_control = db_control
        self.db_filter = db_filter_class
        self.frontend_filters = {}  # Frontend filter form options
        self.global_filters = []
        
        self.view_filters: dict = saved_view_filters
        self.db_filter_groups: dict = {}

        list = FrontendFilterOptionsList(db_control, fe_filter_settings)
        self.frontend_filters = list.filters 

        # self.get_view_filters()
        self.get_view_db_filter_groups()
        
        print(self.db_filter_groups)


    def get_view_db_filter_groups(self):
        for view in self.view_filters.keys():
            self.update_view_db_filter_group(view)
        

    def update_view_db_filter_group(self, view: str):
        view_group = self.nested_filter_group_to_db(self.view_filters[view], self.db_filter)
        self.db_filter_groups.update({view: view_group})


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
                    if item['operator'] in ['any', 'not_in']: 
                        if type(item['values']) is not list:
                            item['values'] = [item['values']]
                    # FIXME: added the above lines for testing; remove when fix the frontend input for select multiple (so returns an array)
                
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
            for filter_field in filter_data:
                # Separate path from key, value for each item

                path_list = filter_field.split('.')
                key = path_list.pop(-1)
                value = filter_data[filter_field]
                
                path = '.'.join(path_list)
                
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
            # print('paths: ', path_list)
            
            path_start = path_list.pop(0)
            path = '.'.join(path_list)
            return path_start, path
        

        filters_dict = filters_from_form(filter_data)
        print('\nfilters: ', filters_dict)
        f_group = get_group(filters_dict)

        return f_group
    


class JobFiltersConverter(FiltersConverter):

    def __init__(self, db_control: DbControl, saved_view_filters: dict):
        super().__init__(db_control=db_control, db_filter_class=JobDbFilter, fe_filter_settings=available_job_filters, saved_view_filters=saved_view_filters)