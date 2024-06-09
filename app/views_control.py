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
                             'layout_options': dict, 
                             'filters': {'saved': {}, 'temp': {}}}
        
        self.set_current(self.default_view)

    def check_view(self, view: str):
        if not view in self.saved_views.names:
            print('View doesn\'t exist -- using default')
            view = self.default_view
        return view

    def set_current(self, view_name):
        view_name = self.check_view(view_name)
            
        saved_view = self.saved_views.views[view_name]
        self.current_view['name'] = view_name
        self.current_view['layout'] = saved_view['layout']
        
        # If saved_view has custom overrides to global layout options, use that. Otherwise, use global default.
        if saved_view.get('layout_options'):
            self.current_view['layout_options'] = saved_view['layout_options']
        else:
            if self.current_view['layout'] == 'list':
                self.current_view['layout_options'] = self.default_settings.list
            else: 
                self.current_view['layout_options'] = self.default_settings.table
        

        self.current_view['filters']['saved'] = saved_view['job_filters']
        # self.filters_control.current_filters_db = self.filters_control.view_db_filter_groups[view]

    def get_all_filters(self):
        return {view_name: view['job_filters'] for view_name, view in self.saved_views.views.items()}

    def get_all_layouts(self):
        return {view_name: view['layout'] for view_name, view in self.saved_views.views.items()}

    def update_view_data_filters(self, data: dict, view: str):

        # print(data)
        
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


    def update_view_layout_settings(self, view: str, setting: str, data: dict):

        saved_view = self.saved_views.views[view]
        if setting == 'layout_selection':
            saved_view['layout'] = setting

        if setting == 'layout_options':

            if saved_view['layout'] == 'table':
                if not saved_view.get('layout_options'):
                    saved_view['layout_options'] = self.default_settings.table
                
                saved_view['layout_options'] = update_table_settings(saved_view['layout_options'], data)
            
            else:
                if not saved_view.get('layout_options'):
                    saved_view['layout_options'] = self.default_settings.list
                
                update_list_settings(saved_view['layout_options'], data)

        self.saved_views.views[view] = saved_view
        self.save_views()


    def create_view(self, name: str):
        name = name.lower().strip()
        
        if not self.saved_views.views.get(name):
            new_view = {'name': name,
                        'layout': self.default_layout,
                        'job_filters': {}}
            
            self.saved_views.views[name] = new_view
            self.saved_views.names.append(name)
            self.save_views()

            self.filters_control.update_filters(self.get_all_filters())

            return self.saved_views.views[name]
        
        else:
            print(f'View with name "{name}" already exists.')
        # TODO: Proper error handling
        # Later TODO (probably): Make dataclass for view, use for create_view


    def delete_view(self, name: str):
        name = name.lower().strip()
        if name not in self.saved_views.names and not self.saved_views.views.get(name):
            print(f'View to be deleted, "{name}", does not exist.')
            return
        # TODO: Proper error handling

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
