def update_table_settings(layout_options: dict, data: dict):
    # For job_fields
    fields_to_display = data.getlist('display')
    for field in layout_options['job_fields']:
        if field['name'] in fields_to_display:
            field['hidden'] = False
        else:
            field['hidden'] = True
    
    return layout_options


def update_list_settings(layout_options: dict, data: dict):
    # TODO

    return layout_options