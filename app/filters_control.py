from dataclasses import asdict
from filters_frontend import FrontendFilter
from db_control import DbControl


class FiltersControl:

    def __init__(self, db_control: DbControl, fe_filter_settings: dict):
        self.fe_settings = fe_filter_settings
        self.db_control = db_control
        self.frontend_filters = {}
        self.global_filters = []
        self.current_filters = []

        self.build_frontend_filter_list()
    

    def build_frontend_filter_list(self):

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
            self.frontend_filters[column] = asdict(filter)


    def get_col_unique_values(self, column: str) -> list:
        unique_vals = self.db_control.get_from_col(column, unique=True)

        sorted_values = sorted(unique_vals, key=str.lower)
        if '' in sorted_values:
            sorted_values.remove('')
            # sorted_values.append('')
        # print(f'Unique values for {column}: ', sorted_values)
        return sorted_values