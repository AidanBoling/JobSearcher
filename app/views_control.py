from copy import deepcopy
from filters_control import JobFiltersConverter
from user_settings import SavedViews, DataDisplayDefaults, SettingsControl
from utils import update_table_settings, update_list_settings


class ViewsControl:

    def __init__(self, default_settings: DataDisplayDefaults):
        self.saved_views_controller = SettingsControl(SavedViews, 'saved_views')
        self.saved_views: SavedViews = self.saved_views_controller.get_as_dataclass()
        
        self.default_settings = default_settings
        self.default_view = self.default_settings.settings.default_view
        self.default_layout = self.default_settings.settings.default_display_layout
        
        self.filters_control = JobFiltersConverter()
        self.all_filters: dict = {}
        self.db_filter_groups: dict = {}

        self.current_view = {'name': str, 
                             'layout': str, 
                             'layout_options': {'table': dict, 'list': dict}, 
                             'filters': {'saved': {}, 'temp': {}},
                             'sort': []} 
        # TODO: Add default sort to global settings

        self.set_current(self.default_view)
        self.update_all_filters()


    def view_exists(self, view: str):
        if view in self.saved_views.names:
            return True
        
        print('View not found.')
        return False       


    def set_current(self, view_name):
        if not self.view_exists(view_name):
            print('View doesn\'t exist -- using default.')
            view_name = self.default_view
            
        saved_view = self.saved_views.views[view_name]
        self.current_view['name'] = view_name
        self.current_view['layout'] = saved_view['layout']
        
        # If saved_view has custom overrides to global layout options, use those. Otherwise, use global defaults.
        for layout in ['table', 'list']:
            layout_options = ''
            if saved_view['layout_options'].get(layout):
                layout_options = saved_view['layout_options'][layout]
            else:
                if layout == 'list':
                    layout_options = self.default_settings.list
                elif layout == 'table': 
                    layout_options = self.default_settings.table
            
            self.current_view['layout_options'][layout] = layout_options

        self.current_view['filters']['saved'] = saved_view['job_filters']

        self.current_view['sort'] = saved_view['sort']


    def update_all_filters(self):
        self.all_filters = self.get_all_filters()
        for view in self.all_filters.keys():
            self.update_view_db_filter_group(view)


    def update_view_db_filter_group(self, view: str):
        view_filters = self.all_filters[view]
        view_db_group = self.filters_control.convert_saved_filters_to_db(view_filters)
        self.db_filter_groups.update({view: view_db_group})


    def get_all_filters(self):
        return {view_name: view['job_filters'] for view_name, view in self.saved_views.views.items()}


    def get_all_layouts(self):
        return {view_name: view['layout'] for view_name, view in self.saved_views.views.items()}


    def update_view_name(self, view: str, name: str):
        if not self.view_exists(view):
            return
        
        name = name.lower().strip()
        if view != name:
            view_data = self.saved_views.views.pop(view)
            view_data['name'] = name
            self.saved_views.views[name] = view_data
            
            self.saved_views.names.remove(view)
            self.saved_views.names.append(name)
            
            self.save_views()
            self.update_all_filters()
            view = name
        
        return view


    def update_view_layout(self, view: str, layout: list):
        if not self.view_exists(view):
            return
        
        saved_view = self.saved_views.views[view]
        saved_view['layout'] = layout
        self.save_views()

        return layout


    def update_view_layout_settings(self, view: str, layout: str, options: dict):
        if not self.view_exists(view):
            return
       
        layout_options = self.saved_views.views[view]['layout_options']
        
        # If view doesn't yet have options for the given layout, first pull defaults, THEN update accordingly 
        if layout == 'table':
            if not layout_options.get('table'):
                layout_options['table'] = self.default_settings.table
            
            layout_options['table'] = update_table_settings(layout_options['table'], options)

        else:
            if not layout_options.get('list'):
                layout_options['list'] = self.default_settings.list
            
            layout_options['list'] = update_list_settings(layout_options['list'], options)

        self.save_views()


    def update_view_data_filters(self, view: str, data: dict):
        if not self.view_exists(view):
            return
        
        filter_group_dict = self.filters_control.form_response_to_dict(data)
        if not filter_group_dict or not filter_group_dict.get('filters'):
            filter_group_dict = {}
        # print(f'\nUpdating filters for view "{view}": ', filter_group_dict)
                
        self.saved_views.views[view]['job_filters'] = filter_group_dict
        self.save_views()

        self.all_filters[view] = filter_group_dict
        self.update_view_db_filter_group(view)        

        # Later TODO (maybe): Allow save view filters separate from "saving" filters
        # -- e.g. update filters temporarily, and user can decide if keep changes


    def update_view_sort(self, view: str, data: dict): 
        if not self.view_exists(view):
            return
        
        # Get sort from form data
        sort = {}
        for key, value in data.items():
            order, type = key.split('.')
            if not sort.get(order):
                sort[f'{order}'] = [value]
            else:
                sort[f'{order}'].append(value)

        sort_list = [item for key, item in sort.items() if item[0]]
        
        # Save sort
        self.saved_views.views[view]['sort'] = sort_list
        self.save_views()


    def create_view(self, name: str):
        name = name.lower().strip()
        
        if self.saved_views.views.get(name):
            print(f'View with name "{name}" already exists.')
            return
            # TODO: Proper error handling

        else:
            new_view = {'name': name,
                        'layout': self.default_layout,
                        'layout_options': {},
                        'job_filters': {},
                        'sort': []}
            
            self.saved_views.views[name] = new_view
            self.saved_views.names.append(name)
            self.save_views()

            self.update_all_filters()

            return name
        
        # Later TODO (maybe): Make dataclass for view, use for create_view


    def delete_view(self, name: str):
        name = name.lower().strip()
        if name == self.default_view:
            print(f'View "{name}" can\'t be deleted while it is set as the default view.')
            return

        if name not in self.saved_views.names and not self.saved_views.views.get(name):
            print(f'View to be deleted, "{name}", does not exist.')
            return

        if name in self.saved_views.names:
            self.saved_views.names.remove(name)
        if self.saved_views.views.get(name):
            deleted_view = self.saved_views.views.pop(name)

        self.save_views()
        self.update_all_filters()

        return deleted_view
    
    # TODO: If view to delete is set as default, throw error


    def save_views(self):
        self.saved_views_controller.save_to_file(self.saved_views)
