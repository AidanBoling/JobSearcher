import os
from pathlib import Path
import json
import logging
import logging.config
from datetime import datetime, timedelta, timezone

ROOT_DIR = Path(__file__).parent

app_logs_dir = ROOT_DIR / 'logs'
if not os.path.exists(app_logs_dir):
    os.mkdir(app_logs_dir)


class LoggingManager:
    def __init__(self):
        self.log_filepath: Path
        # self.requested_logs: list: []
        self.filter_options = []

        self.setup_logging()

    def setup_logging(self):
        config_file = Path(ROOT_DIR / 'configs/logging_config.json')
        with open(config_file) as f_in:
            config = json.load(f_in)
        
        try:
            log_filename = config['handlers']['file']['filename']
            self.log_filepath = app_logs_dir / log_filename
            config['handlers']['file']['filename'] = self.log_filepath
            
            if not os.path.exists(self.log_filepath):
                with open(self.log_filepath, 'x') as log_file:
                    pass
        
        except KeyError:
            pass

        logging.config.dictConfig(config)
        self.filter_options = config['formatters']['json']['fmt_keys'].keys()


    def get_recent_logs(self, filters:dict={}, max_lines:int=50, lines:int=0, from_minutes_ago:int=0):
        logs = []
        filter_key_errors = {}
        total_lines = 0
        line_limit = max_lines if lines == 0 else lines
        now =  datetime.now(tz=timezone.utc)
        t_delta_max = timedelta(minutes=from_minutes_ago)

        def matches_filters(log: dict):
            for key, value in filters.items():
                try:
                    if type(value) == str and log[key] != value:
                        return False
                    elif type(value) == list and log[key] not in value:
                        return False
                except KeyError:
                    if filter_key_errors.get(key):
                        filter_key_errors[key] += 1
                    else: 
                        filter_key_errors[key] = 1
                    return False

            return True

        def process_line(line):
            log = json.loads(line)

            if not filters or matches_filters(log):
                logs.append(log)


        with open(self.log_filepath, 'r') as log_file:
            for i, line in enumerate(log_file, 1):
                total_lines = i

        with open(self.log_filepath, 'r') as log_file:

            read_start_index = total_lines - line_limit
            for i, line in enumerate(log_file, 1):
                if i > read_start_index:
                    
                    if from_minutes_ago > 0:
                        timestamp = json.loads(line)['timestamp']
                        difference = now - datetime.fromisoformat(timestamp)
                        
                        if difference < t_delta_max:
                            process_line(line)
                    
                    else:
                        process_line(line)
        
        if filter_key_errors:
            err_statements = [f'{filter} ({error_count})' for filter, error_count in filter_key_errors.items()]
            print('Filter key errors when retrieving logs:', ', '.join(err_statements))
            # Later TODO (maybe): Log as debug (or info?) 

        logs.reverse()
        return logs        
    


class MyJSONFormatter(logging.Formatter):
    def __init__(self, *, fmt_keys: dict[str, str] | None = None):
        super().__init__()
        self.fmt_keys = fmt_keys if fmt_keys is not None else {}


    def format(self, record: logging.LogRecord) -> str:
        message = self._prepare_log_dict(record)
        return json.dumps(message, default=str)


    def _prepare_log_dict(self, record: logging.LogRecord):
        always_fields = {
            'message': record.getMessage(),
            'timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()
            }
        
        if record.exc_info is not None:
            always_fields['exc_info'] = self.formatException(record.exc_info)
        
        if record.stack_info is not None:
            always_fields['stack_info'] = self.formatStack(record.stack_info)
        
        message = { key: msg_val 
                   if (msg_val := always_fields.pop(val, None)) is not None 
                   else getattr(record, val) 
                   for key, val in self.fmt_keys.items() }
        message.update(always_fields)

        return message
    


def test_logging(logger):
    logger.debug("debug message")
    logger.info("info message")
    logger.warning("warning message")
    logger.error("error message")
    logger.critical("critical message")

    try:
        1/0
    except ZeroDivisionError:
        logger.exception("exception message")