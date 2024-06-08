const filterOptions = '{{ filter_options | tojson }}'
const viewOptions = '{{ options | tojson }}'


function getFilterOptions(inputId, inputName, selectedOption) {

    console.log('selected option: ', selectedOption)
    const filterNum = inputId.split('_')[1]
    //console.log('all_filters: ', all_filters)
    const filter = filterOptions[selectedOption]
    //console.log('selected_filter: ', filter)
    const namePrefix = inputName.split('.').slice(0, -1).join('.')

    function getOptionsText(valuesLabelsList) {
        let options = ''
        valuesLabelsList.forEach((valueLabel, i) => {
            selected = ''
            if (i === 0) { selected = 'selected ' }
            options += `<option ${selected}value="${valueLabel[0]}">${valueLabel[1]}</option>`
        })
        return options
    }


    function getInputText(type, id, namePrefix, value = '') {
        return (`<input type="${type}" id="filter-value_${type}_${id}" aria-label="Value" class="form-control" name="${namePrefix}.values" value="${value}"  />`)
    }


    const filterRow = document.getElementById('filter-row_' + filterNum)

    // Operator options
    const operatorOptions = getOptionsText(filter['op_list'])
    const operatorSelect = filterRow.querySelector('.filter-operator .form-select')
    operatorSelect.innerHTML = operatorOptions
    operatorSelect.classList.remove('d-none')

    // Field Values

    const valueDiv = filterRow.querySelector('div.filter-value')

    // Make modifications to value element
    if (filter['input_type'] === 'multi-select') {

        const valueOptions = getOptionsText(filter.values)
        const valueSelectText = `<select class="form-select" name="${namePrefix}.values" id="filter-value_multi-select_${filterNum}" aria-label="Value">
                                ${valueOptions}
                                </select>`
        valueDiv.innerHTML = valueSelectText
    }
    else {
        let value = ''
        if (filter.values) {
            value = filter.values
        }
        valueText = getInputText('text', filterNum, namePrefix, value)
        valueDiv.innerHTML = valueText
    }

    // Un-hide element
    valueDiv.classList.remove('d-none')

}

//{# const addRowUrl = {{ url_for('add_new_filter', unit = 'row') | tojson }} #}


function addFilterRow(element, elementId) {

    const groupNum = elementId.split('_g')[1]
    const groupDiv = element.closest('.filter-group')

    const filterRows = groupDiv.querySelectorAll(`.filter-row.in-group-${Number.parseInt(groupNum)}`)
    const filterNum = filterRows.length + 1
    //console.log('filterNum: ', filterNum)

    const groupOpElementName = groupDiv.querySelector('.group-operator select').name
    const groupNamePrefix = groupOpElementName.split('.').slice(0, -1).join('.')
    //console.log('groupNamePrefix: ', groupNamePrefix)

    const filterGroups = groupDiv.querySelectorAll(`.filter-group.in-group-${Number.parseInt(groupNum)}`)
    const groupItemIndex = filterRows.length + filterGroups.length
    //console.log('groupItemIndex: ', groupItemIndex)

    const buttonDiv = element.closest('.filter-button')
    text = newRowEl(groupNum, filterNum, groupNamePrefix, groupItemIndex)
    buttonDiv.insertAdjacentHTML('beforebegin', text)
}


function newRowEl(groupNum, filterNum, groupNamePrefix, groupItemIndex) {
    const idPost = `g${groupNum}-${filterNum}`
    const namePrefix = `${groupNamePrefix}.${groupItemIndex}.filter`

    const rowDivClass = 'gx-2 my-2'
    const colsDivClass = 'col-4'
    const operatorSelectClass = 'd-none'

    const jobFields = viewOptions.job_fields
    const filterableFields = Object.keys(filterOptions)

    let options = ''
    jobFields.forEach((field) => {
        if (filterableFields.includes(field.name)) {
            options += `
                    <option value=${field.name}>${field.label}</option>`
        }
    })

    return (
        `<div class="filter-row row in-group-${groupNum} ${rowDivClass}" id="filter-row_${idPost}">

            <div class="${colsDivClass} filter-field">
                <select name="${namePrefix}.field" id="field-name_${idPost}"
                    class="form-select" aria-label="Field Name"
                    onchange="getFilterOptions(this.id, this.name, this.options[this.selectedIndex].value)">
                    <option value="" selected>Select field</option>
                    ${options}
                </select>
            </div>
            <div class="${colsDivClass} filter-operator">
                <select class="form-select ${operatorSelectClass}" name="${namePrefix}.operator" id="filter-operator_${idPost}"
                    aria-label="Operator">
                </select>
            </div>
            <div class='${colsDivClass} filter-value d-none'>
            </div>
        </div>
        `
    )
}


function oldAddFilterRow(element, elementId) {

    const groupNum = elementId.split('_g')[1]

    const parentDiv = element.parentElement

    const filterRows = parentDiv.getElementsByClassName('filter-row')
    const filterNum = filterRows.length()
    console.log('filterNum: ', filterNum)

    // filter num is the number of divs with class filter-row within parent div

    // const filterNum = ''
    // groupNamePrefix = ''
    // groupItemIndex = ''

    // {# getHtml(url, selected_option).then(text => element.innerHTML = text) #}


    //let data = new FormData()
    //data.append('group_number', groupNum)
    //data.append('filter_number', filterNum)
    //data.append('group_name_prefix', groupNamePrefix)
    //data.append('group_item_index', groupItemIndex)
    //data.append('name_prefix', newRowNamePrefix)

    //getHtml(addRowUrl, data).then((text) => { console.log(text); return newRowEl.outerHTML = text })

}


function getHtml(url, data) {

    request = {
        "method": "POST",
        "body": data,
        "headers": { "Accept": "text/html" },
    }

    return fetch(url, request)
        .then(response => response.text)
    // .then(text => element.innerHTML = text)
}
