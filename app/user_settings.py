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
class DataDisplay:
    view: str
    job_fields: list
# Note: Probably move "view" to another dataclass (like GeneralSettings, or something)


@dataclass
class TitleDataFilters:
    exclude_keywords: list
    regex: str


@dataclass
class DataFilters:
    post_title: TitleDataFilters


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