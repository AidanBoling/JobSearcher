from pathlib import Path
import yaml
from dataclasses import dataclass, asdict
from dacite import from_dict

ROOT_DIR = Path(__file__).parent
CONFIG_FILE_PATH = ROOT_DIR / 'instance/user_config.yaml'


@dataclass
class SearchSettings:
    search_phrases: list
    exclude_companies: list


@dataclass
class DataDisplayTable:
    job_fields: list


# Q: Move DataDisplaySettings into DataDisplayDefaults?
@dataclass
class DataDisplaySettings:
    default_display_layout: str
    default_view: str


@dataclass
class DataDisplayDefaults:
    list: dict      # Later TODO: Update this to a dataclass (like table) once have list view
    table: DataDisplayTable
    settings: DataDisplaySettings


@dataclass
class DataFiltersTitle:
    exclude_keywords: list
    regex: str


# TODO: Change this to GlobalFilters
@dataclass
class DataFilters:    # global data filters
    post_title: DataFiltersTitle
    job_filters: dict


# @dataclass
# class SavedView:
#     name: str
#     job_filters: dict
#     layout: dict
#     layout_options: dict


@dataclass
class SavedViews:
    names: list[str]
    views: dict
    
    # def __post_init__(self):
    #     self.filters = {view.name: view.job_filters for view in self.views}
    #     self.views = {view['name']: view for view in self.views}

    def all_filters(self):
        return {view_name: view['job_filters'] for view_name, view in self.views.items()}

    def all_layouts(self):
        return {view_name: view['layout'] for view_name, view in self.views.items()}


@dataclass
class JobSearch:
    search_settings: SearchSettings
    linked_accounts: dict


# Q: Change to ConfigControl?
class SettingsControl:
    def __init__(self, data_class, section):
        self.data_class = data_class
        self.section = section
        self.config = ''
        
        self.get_raw_config()

    
    def get_raw_config(self):
        with open(CONFIG_FILE_PATH, 'r') as file:
            config = yaml.safe_load(file)
        self.config = config  
    

    def get_section_config(self):
        return self.config[self.section]


    def get_as_dataclass(self):
        with open(CONFIG_FILE_PATH, 'r') as file:
            config = yaml.safe_load(file)

        settings_obj = from_dict(data_class=self.data_class, data=config[self.section])
        
        return settings_obj


    def save_to_file(self, settings_object: object):
        if not isinstance(settings_object, self.data_class):
            raise TypeError('Invalid argument -- does not match data_class attribute of instance')

        settings = asdict(settings_object)
        self.config[self.section] = settings

        with open(CONFIG_FILE_PATH, 'w') as file:
            yaml.dump(self.config, file)


    # def test_save_to_file(self, settings_object: object):
    #     if not isinstance(settings_object, self.data_class):
    #         raise TypeError('Invalid argument -- does not match data_class attribute of instance')

    #     print('Config before: ', self.config[self.section])
    #     settings = asdict(settings_object)
    #     # settings = {key: value.__dict__ if type(value) is object else value for (key, value) in settings.items()}
    #     # print(type(settings['post_title']) is object)
    #     self.config[self.section] = settings

    #     print('Config after: ', self.config[self.section])





# config = dacite.from_dict(
#     data_class=Configuration, data=raw_cfg,
#       config=dacite.Config(type_hooks=converters),
# )


#   settings = data_display_options.__dict__
    # if data_display_options.__class__.__name__ == 'DataDisplay':
    #     print('Match!')

    # print('setting object class: ', data_display_options.__class__.__name__)