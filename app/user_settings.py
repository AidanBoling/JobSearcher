from pathlib import Path
from dataclasses import dataclass, field, asdict
from dacite import from_dict
from utils import YamlFile
from yaml.error import YAMLError
from logger import LoggingManager

ROOT_DIR = Path(__file__).parent
CONFIG_FILE_PATH = ROOT_DIR / 'instance/user_config.yaml'


logging_manager = LoggingManager()
logger = logging_manager.logger


@dataclass
class SearchSettings:
    search_phrases: list = field(default_factory=list)
    exclude_companies: list = field(default_factory=list)


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
    search_settings: SearchSettings = field(default_factory=SearchSettings)
    linked_accounts: dict = field(default_factory=dict)



# TODO (probably): Change to UserConfigControl
class SettingsControl:
    def __init__(self, data_class, section):
        self.data_class = data_class
        self.section = section
        self.config:dict = {}
        self.yaml_file = YamlFile(CONFIG_FILE_PATH)
        
        self.get_raw_config()

    
    def get_raw_config(self) -> dict:
        self.config = self.yaml_file.get_data()
    

    def get_section_config(self):
        return self.config[self.section]


    def get_as_dataclass(self):
        config = self.yaml_file.get_data()
        section_config = {k: v for k, v in config[self.section].items() if v is not None}
        settings_obj = from_dict(data_class=self.data_class, data=section_config)

        return settings_obj


    def save_to_file(self, settings_object: object):
        if not isinstance(settings_object, self.data_class):
            raise TypeError('Invalid argument -- does not match data_class attribute of instance')

        settings = asdict(settings_object)
        self.config[self.section] = settings
        try:
            self.yaml_file.save_data(self.config)
        except YAMLError as e:
            logger.exception('Error saving settings to file: {e}')

        
        


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