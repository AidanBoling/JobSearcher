from filters_control import JobFiltersConverter
from db_control import DbControl
from user_settings import SavedViews, DataDisplayDefaults, SettingsControl
from utils import update_table_settings, update_list_settings


class ViewsControl:

    def __init__(self, db_control: DbControl, default_settings: DataDisplayDefaults):
        self.saved_views_controller = SettingsControl(SavedViews, 'saved_views')
        self.saved_views: SavedViews = self.saved_views_controller.get_as_dataclass()
        
        self.default_settings = default_settings
        self.default_view = self.default_settings.settings.default_view
        self.default_layout = self.default_settings.settings.default_display_layout
        
        self.filters_control = JobFiltersConverter(db_control, self.get_all_filters())

        self.current_view = {'name': str, 
                             'layout': str, 
                             'layout_options': {'table': dict, 'list': dict}, 
                             'filters': {'saved': {}, 'temp': {}}}
        
        self.set_current(self.default_view)


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
        # self.filters_control.current_filters_db = self.filters_control.view_db_filter_groups[view]


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
            self.filters_control.update_filters(self.get_all_filters())
            view = name
        
        return view


    def update_view_layout(self, view: str, layout: list):
        if not self.view_exists(view):
            return
        
        saved_view = self.saved_views.views[view]
        saved_view['layout'] = layout
        self.saved_views.views[view] = saved_view
        self.save_views()

        return layout


    def update_view_layout_settings(self, view: str, layout: str, options: dict):
        if not self.view_exists(view):
            return
       
        saved_view = self.saved_views.views[view]
        view_layout_options = saved_view['layout_options']
        
        if layout == 'table':
            if not view_layout_options.get('table'):
                view_layout_options['table'] = self.default_settings.table
            
            view_layout_options['table'] = update_table_settings(view_layout_options['table'], options)

        else:
            if not view_layout_options.get('list'):
                view_layout_options['list'] = self.default_settings.list
            
            view_layout_options['list'] = update_list_settings(view_layout_options['list'], options)

        self.saved_views.views[view] = view_layout_options['list']
        self.save_views()


    def update_view_data_filters(self, view: str, data: dict):

        filter_group_dict = self.filters_control.form_response_to_dict(data)
        print(f'\nUpdating filters for view "{view}": ', filter_group_dict)
        
        # if not view or view == 'current':
        #     self.filters_control.current_filters = filter_group_dict
        
        # Update and save view 
        self.saved_views.views[view]['job_filters'] = filter_group_dict
        self.save_views()

        # Update filters_control
        self.filters_control.view_filters[view] = self.saved_views.views[view]['job_filters']
        # self.filters_control.update_filters(self.get_all_filters())

        self.filters_control.update_view_db_filter_group(view)

        # Later TODO (maybe): Allow save view filters separate from "saving" filters
        # -- e.g. update filters temporarily, and user can decide if keep changes


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
                        'job_filters': {}}
            
            self.saved_views.views[name] = new_view
            self.saved_views.names.append(name)
            self.save_views()

            self.filters_control.update_filters(self.get_all_filters())

            return self.saved_views.views[name]
        
        # Later TODO (maybe): Make dataclass for view, use for create_view


    def delete_view(self, name: str):
        name = name.lower().strip()
        
        if name not in self.saved_views.names and not self.saved_views.views.get(name):
            print(f'View to be deleted, "{name}", does not exist.')
            return

        if name in self.saved_views.names:
            self.saved_views.names.remove(name)
        if self.saved_views.views.get(name):
            deleted_view = self.saved_views.views.pop(name)

        self.save_views()
        self.filters_control.update_filters(self.get_all_filters())

        return deleted_view
    
    # TODO: If view to delete is set as default, throw error


    def save_views(self):
        self.saved_views_controller.save_to_file(self.saved_views)
