// ONCHANGE AND ONCLICK ACTIONS

    // -- onClick (Buttons):

    function addFilter(type, element) {

        const { groupDiv, groupIdPost, itemsInGroup } = getGroupElInfo(element)
        
        const groupOpElement = groupDiv.querySelector(`select#group-operator_g${groupIdPost}`)
        const groupNamePrefix = groupOpElement.name.split('.').slice(0, -1).join('.')
        //console.log('groupNamePrefix: ', groupNamePrefix)

        const indexGroupItem = itemsInGroup

        const rowGroupOperatorEl = getRowGroupOpElement(indexGroupItem, groupNamePrefix, groupDiv, { idPost: groupIdPost })
        const idPost = getFilterIdPost(type, groupDiv, groupIdPost)
        const namePrefix = getFilterNamePrefix(type, groupNamePrefix, indexGroupItem)

        let text = ''
        if (type === 'row') {
            text = newFilterRowEl(rowGroupOperatorEl, namePrefix, idPost, groupIdPost)
        }
        else if (type === 'group') {
            text = newFilterGroupEl(rowGroupOperatorEl, namePrefix, idPost, groupIdPost)
        }

        const buttonDiv = element.closest('.filter-btn.row')
        buttonDiv.insertAdjacentHTML('beforebegin', text)
        
        if (indexGroupItem === 1) {
            // Delete hidden operator field element (replaced in row/group creation step)
            const hiddenGroupOpEl = groupOpElement.closest('.group-operator')
            hiddenGroupOpEl.remove()
        }

        // If adding first filter, enable the "clear all" button
        if (groupIdPost === '1' && itemsInGroup === 0) {
            const removeAllBtn = groupDiv.querySelector('.remove-all-btn')
            removeAllBtn.removeAttribute("disabled")
        }
    }


    function deleteFilter(btnElement, filterType) {
        // Later TODO: Check/add to documentation/notes for this function
        // Later TODO: Rename to handleDeleteFilter
        
        let rowDivSelector = '.filter-row.outer-row'
        if (filterType === 'group') { rowDivSelector = '.group-inner.outer-row' }
        const filterRowDiv = btnElement.closest(rowDivSelector)

        const { groupDiv, groupIdPost, itemsInGroup, groupNum } = getGroupElInfo(btnElement)
        console.log('groupDiv: ', groupDiv)

        const groupOpSelectEl = groupDiv.querySelector(`select#group-operator_g${groupIdPost}`)
        const groupNamePrefix = groupOpSelectEl.name.split('.').slice(0, -1).join('.')

        if (groupIdPost === '1' && itemsInGroup === 1) {
            // If filter to delete is the only filter, disable the "clear all" button
            const removeAllBtn = groupDiv.querySelector('.remove-all-btn')
            removeAllBtn.setAttribute("disabled", true)
        }

        const allRowEls = groupDiv.querySelectorAll(`.outer-row.in-group-${groupIdPost}`)
        const groupRowsArray = Array.from(allRowEls)

        const rowIndex = groupRowsArray.indexOf(filterRowDiv)
        const rowNumber = rowIndex + 1
        //console.log(`Row to delete is ${rowNumber}/${itemsInGroup} in group`)

        let deletedLastRow = false
        if (rowNumber === itemsInGroup) { deletedLastRow = true }

        let deletedFirstOrSecondRow = false
        if (rowNumber <= 2) { deletedFirstOrSecondRow = true }

        let groupOp = ''
        if (itemsInGroup === 2) {
            // 1 of only 2 rows will be deleted; group op will be moved to beginning of filterGroup
            groupOp = groupOpSelectEl.closest('.group-operator')
            groupOp.classList.add('d-none')

            if (deletedLastRow) { groupDiv.insertAdjacentElement('afterbegin', groupOp) }
        } 


        // DELETE ROW
        console.log('Deleting row...')
        filterRowDiv.remove()


        // AFTER DELETE:
        if (!deletedLastRow) {
            // If row deleted was not the last row of the group, need to:
            // - update the group ops for the first 2 rows (if deleted row was one of first 2 rows)
            // - recursively update the various appropriate numbers in the name, id, and class attributes of all 
            // remaining rows and nested groups

            const newGroupEls = groupDiv.querySelectorAll(`.outer-row.in-group-${groupIdPost}`)
            const newGroupArray = Array.from(newGroupEls)
            const rowsToUpdate = newGroupArray.slice(rowIndex)
            //console.log('Rows to update: ', rowsToUpdate)
            
            const groupElementInfo = {
                groupDiv: groupDiv,
                groupIdPost: groupIdPost,
                groupNamePrefix: groupNamePrefix,
                currentGroupIdPost: groupIdPost
            }

            if (deletedFirstOrSecondRow) {
                console.log('Updating group ops...')
                
                for (let newRowIndex = 0; newRowIndex < 2; newRowIndex++) {
                    const currentRowEl = newGroupEls[newRowIndex]
                    const groupOpDiv = currentRowEl.querySelector('.group-op')
                    const newRowGroupOp = getRowGroupOpElement(newRowIndex, groupNamePrefix, groupDiv, { idPost: groupIdPost })

                    groupOpDiv.insertAdjacentHTML('beforebegin', newRowGroupOp)
                    
                    if (newGroupArray.length < 2) {
                        groupDiv.insertAdjacentElement('afterbegin', groupOp)
                        break
                    }
                    else { groupOpDiv.remove() }
                }
            }
            
            updateGroupFilters(rowsToUpdate, groupElementInfo, rowIndex)
        }
    }


    function removeAllFilters(element) {
        // Later TODO: Rename to handleRemoveAllFilters

        const filterForm = element.closest('form')
        const outerFilterGroup = filterForm.querySelector('.filter-group.in-group-0')
        
        // Copy the first group Operator element, and add to top-level of group (hidden)
        const groupOp = outerFilterGroup.querySelector('.group-operator')
        groupOp.classList.add('d-none')
        outerFilterGroup.insertAdjacentElement('afterbegin', groupOp)
        
        // Remove rows
        const filterRowsAll = filterForm.querySelectorAll('.outer-row.in-group-1')
        filterRowsAll.forEach((row) => row.remove())

        // Disable the "clear all" button
        element.setAttribute("disabled", true)
    }


    // -- onChange:

    function getFilterOptions(fieldElement, selectedOption) {
        const elementId = fieldElement.id
        const inputName = fieldElement.name
        const filterRow = fieldElement.closest('.filter-row')

        const filter = filterOptions[selectedOption]
        const idPost = elementId.split('_')[1]
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

        // Operator Options
        const operatorOptions = getOptionsText(filter.op_list)
        const operatorSelect = filterRow.querySelector('.filter-operator .form-select')

        operatorSelect.innerHTML = operatorOptions
        operatorSelect.classList.remove('d-none')

        // Field Values
        const valueDiv = filterRow.querySelector('div.filter-value')
        const inputType = filter.input_type
        let valueText = ''

        if (inputType === 'multi-select') {
            const valueOptions = getOptionsText(filter.values)
            valueText = `<select class="form-select" name="${namePrefix}.values" id="filter-value_multi-select_${idPost}" aria-label="Value">
                            ${valueOptions}
                        </select>`
        }
        else if (inputType === 'date') {
            const valueOptions = getOptionsText(filter.values)
            valueText = `<select class="form-select" name="${namePrefix}.values" id="filter-value_date_${idPost}" aria-label="Value" onchange="handleDateOptionChange(this, this.options[this.selectedIndex])">
                            ${valueOptions}
                        </select>`
        }
        else if (inputType === 'boolean') {
            valueText = getCheckboxText(idPost, namePrefix)
        }
        else if (inputType === 'number') {
            valueText = getInputText('number', idPost, namePrefix, {})
        }
        else {
            let options = {value: ''}
            if (filter.values) { options.value = filter.values }

            valueText = getInputText('text', idPost, namePrefix, options)
        }

        valueDiv.innerHTML = valueText

        if (inputType === 'date') {
            const dateOptionsSelectEl = valueDiv.querySelector('select')
            const selectedOptionEl = dateOptionsSelectEl.options[0]
            setDateValueInputs(dateOptionsSelectEl, selectedOptionEl)
        }
        
        valueDiv.classList.remove('d-none')
    }


    function handleDateOptionChange(selectElement, selectedOptionEl) {
        updateSelected(selectedOptionEl)
        setDateValueInputs(selectElement, selectedOptionEl)
    }


    function handleGroupOpChange(optionElement) {
        
        function updateOpEchos(selectedOptionElement) {
            const groupDiv = selectedOptionElement.closest('.filter-group')
            const groupIdPost = groupDiv.id.split('_').pop()
            const echoEls = groupDiv.querySelectorAll(`.outer-row.in-group-${groupIdPost}>.group-op-echo .op-text`)
    
            if (echoEls) {
                echoEls.forEach(el => { el.innerText = selectedOptionElement.innerText })
            }
        }

        updateSelected(optionElement)
        updateOpEchos(optionElement)
    }


    function toggleUncheckedValue(checkboxEl, isChecked) {
        if (isChecked) {
            const parentEl = checkboxEl.closest('.filter-value')
            const hiddenInputId = checkboxEl.id + '_unchecked'
            const hiddenInput = parentEl.querySelector(`#${hiddenInputId}`)
            hiddenInput.remove()
        }
        else {
            const hiddenInputId = checkboxEl.id
            const hiddenInputName = checkboxEl.name
            const text = uncheckedValueEl(hiddenInputId, hiddenInputName)
            checkboxEl.insertAdjacentHTML('afterend', text)
        }
    }


    // COMPONENTS

    function newFilterGroupEl(outerGroupOpEl, namePrefix, idPost, previousGroupIdPost) {
        const groupOpEl = groupOpElementHtml(namePrefix, idPost, { divClass: 'd-none' })
        const newFilterBtn = filterButtonElement('row', 'Add Filter', '#svg-bi-plus-lg', idPost)
        const newGroupBtn = filterButtonElement('group', 'Add Group', '#svg-bi-subtract', idPost)

        // "Outside" of group
        const groupOuterColWrapper = (innerContent, classDivCols, classDivInner = 'row outer-row') => (`
                    <div class="col g-col-outer row-cap ${classDivCols}">
                        <div class="row">
                            ${innerContent}
                        </div>
                    </div>`)

        const deleteBtn = deleteFilterBtnEl(classOuter = '', filterType = 'group')

        return `<div class="group-inner outer-row row in-group-${previousGroupIdPost}">
                    ${groupOuterColWrapper(outerGroupOpEl, 'row-start')}
                    <div class="filter-group in-group-${previousGroupIdPost} col g-col-outer"
                        id="filter-group_${idPost}">
                        ${groupOpEl}
                        <div class="filter-btn row">
                            <div class="col btn-group filter-btn-group" role="group" aria-label="Add Filters">
                                ${newFilterBtn}
                                <div class="vr"></div>
                                ${newGroupBtn}
                            </div>
                        </div>
                    </div>
                    ${groupOuterColWrapper(deleteBtn, 'row-end')}
                </div>`
    }


    function newFilterRowEl(groupOperatorEl, namePrefix, idPost, groupIdPost) {
        const rowDivClass = ''
        const fieldDivClass = 'col-auto filter-field'
        const operatorDivClass = 'col-auto filter-operator'
        const operatorSelectClass = 'd-none'
        const valueDivClass = 'col filter-value'

        // const jobFields = viewOptions.table.job_fields
        const filterableFields = Object.keys(filterOptions)
        
        let options = ''
        jobFields.forEach((field) => {
            if (filterableFields.includes(field.name)) {
                options += `
                        <option value=${field.name}>${field.label}</option>`
            }
        })

        const deleteButton = deleteFilterBtnEl(classOuter = 'col-auto d-inline', filterType = 'row')

        return (
            `<div class="filter-row row outer-row in-group-${groupIdPost} ${rowDivClass}" id="filter-row_${idPost}">
                ${groupOperatorEl}
                <div class="filter col">
                    <div class="row">
                        <div class="${fieldDivClass}">
                            <select name="${namePrefix}.field" id="field-name_${idPost}"
                                class="form-select" aria-label="Field Name"
                                onchange="getFilterOptions(this, this.options[this.selectedIndex].value)">
                                <option value="" selected>Select field</option>
                                ${options}
                            </select>
                        </div>
                        <div class="${operatorDivClass}">
                            <select class="form-select ${operatorSelectClass}" name="${namePrefix}.operator" id="filter-operator_${idPost}"
                                aria-label="Operator">
                            </select>
                        </div>
                        <div class="${valueDivClass}"></div>
                    </div>
                </div>
                <div class="col-auto d-inline">
                    ${deleteButton}
                </div>
            </div>
            `
        )
    }


    function groupOpElementHtml(namePrefix, idPost, { itemClass = '', innerText = 'Where', divClass = '', selected = 'AND' }) {
        // const divStyle = 'width: 80px;'
        const divStyle = ''
        const ariaLabel = 'Filter Group Operator'
        let innerElement = ''

        if (!itemClass) { itemClass = 'group-operator' }

        if (itemClass === 'group-operator') {
            const andSelected = selected === 'AND' ? 'selected' : ''
            const orSelected = selected === 'OR' ? 'selected' : ''

            innerElement = `<select class="form-select" name="${namePrefix}.group_op" id="group-operator_g${idPost}"
                                aria-label="${ariaLabel}" style="${divStyle}" onchange="handleGroupOpChange(this.options[this.selectedIndex])">
                                <option value="AND" ${andSelected}>And</option>
                                <option value="OR" ${orSelected}>Or</option>
                            </select>`
        }
        else {
            innerElement = `<div class="op-text" style="${divStyle}">${innerText}</div>`
        }

        return (`<div class="col-auto d-inline group-op ${itemClass} ${divClass}">
                    ${innerElement}
                </div>`)

    }


    function deleteFilterBtnEl(outerClass, filterType) {
        const iconOptions = { w: '16' }
        const btnContent = iconBtnContent(svgHref = '#svg-bi-trash3', text = 'Remove', text_is_hidden = true, { iconOptions })

        return `<div class="remove-button">
                    <button class="btn ab-btn-light start-grey" type="button"
                    onclick="deleteFilter(this, '${filterType}')">
                        ${btnContent}
                    </button>
                </div>
        `
    }


    function filterButtonElement(type, label, svgHref, groupIdPost) {
        const idType = type === 'row' ? 'add-filter' : 'add-filter-group'
        const btnClass = 'filter-btn btn ab-btn-dark-color with-hover-border'
        
        const iconOptions = { w: '16' }
        const btnContent = iconBtnContent(svgHref, text = label, text_is_hidden = false, { iconOptions })

        return `<button type="button" class="${btnClass}" id='${idType}_g${groupIdPost}'
                    onclick="addFilter('${type}', this)">
                    ${btnContent}
                </button>`
    }


    function uncheckedValueEl(id, name) {
        return `<input type="hidden" id="${id}_unchecked" name="${name}" value="bool_false" />`
    }


    function getInputText(type, idPost, namePrefix, options) {
        const {value = '', label = 'Value', placeholder = ''} = options
        const valueAttr = value ? ` value=${value}` : ''
        const placeholderAttr = placeholder ? ` placeholder="${placeholder}"` : ''

        return (`<input type="${type}" id="filter-value_${type}_${idPost}" aria-label="${label}" class="form-control" name="${namePrefix}.values"${valueAttr}${placeholderAttr}/>`)
    }


    function getCheckboxText(idPost, namePrefix, isChecked = false) {
        const checkedAttr = isChecked ? 'checked' : ''
        const id = `filter-value_checkbox_${idPost}`
        const name = `${namePrefix}.values`
        const hiddenInputEl = uncheckedValueEl(id, name)
        
        return (`<input type="checkbox" id="${id}" aria-label="Value" class="form-check-input" name="${name}" value="bool_true" ${checkedAttr} onchange="toggleUncheckedValue(this, this.checked)" />
                ${hiddenInputEl}`)
    }


    function updateSelected(optionElement) {
        const parentEl = optionElement.parentElement
        const options = parentEl.querySelectorAll('option')
        
        options.forEach(option => { 
            if (option.hasAttribute('selected')) { 
                option.removeAttribute('selected') 
            }
        });

        optionElement.setAttribute('selected', 'true')
    }


    // HELPERS

    function getGroupElInfo(element) {

        const groupDiv = element.closest('.filter-group')

        const idPost = groupDiv.id.split('_').pop()
        console.log('groupIdPost: ', idPost)

        const totalGroupItems = groupDiv.querySelectorAll(`.outer-row.in-group-${idPost}`).length

        const groupNumList = idPost.split('-')
        const groupNumber = groupNumList.pop()

        return {
            groupDiv: groupDiv,
            groupIdPost: idPost,
            itemsInGroup: totalGroupItems,
            groupNum: groupNumber,
        }
    }


    function getFilterIdPost(filterType, parentGroupDiv, parentGroupIdPost, filterEl = '') {
        let idPost = ''
        if (filterType === 'row') {
            const filterRows = parentGroupDiv.querySelectorAll(`.filter-row.in-group-${parentGroupIdPost}`)
            const rowNumber = filterEl ? Array.from(filterRows).indexOf(filterEl) + 1 : filterRows.length + 1

            idPost = `g${parentGroupIdPost}-${rowNumber}`
            console.log('generated row IdPost: ', idPost)
        }
        else if (filterType === 'group') {
            const filterGroups = parentGroupDiv.querySelectorAll(`.in-group-${parentGroupIdPost} .filter-group`)
            const nestedGroupNumber = filterEl ? Array.from(filterGroups).indexOf(filterEl) + 1 : filterGroups.length + 1

            idPost = `${parentGroupIdPost}-${nestedGroupNumber}`
            console.log('generated nested group idPost: ', idPost)
        }
        else { throw new Error('Invalid filterType argument -- value must be "row" or "group"') }

        if (filterEl) {
            console.log('filter Element: ', filterEl)
        }

        return idPost
    }


    function getFilterNamePrefix(filterType, parentGroupNamePrefix, indexGroupItem) {
        let namePrefix = `${parentGroupNamePrefix}.${indexGroupItem}`

        if (filterType === 'row') { namePrefix += '.filter' }
        else if (filterType === 'group') { namePrefix += '.group' }

        console.log('generated name prefix: ', namePrefix)
        return namePrefix
    }


    function getRowGroupOpElement(indexGroupItem, namePrefix, groupDiv, { idPost = '', divClassInner = '' }) {

        if (!idPost) {
            idPost = groupDiv.id.split('_').pop()
            console.log('idPost for groupOp from groupDiv: ', idPost)
        }

        // const jobFields = viewOptions.job_fields
        // const filterableFields = Object.keys(filterOptions)

        console.log('indexGroupItem (groupOp): ', indexGroupItem)

        let elVars = {
            itemClass: 'group-operator',
            innerText: 'Where',
            divClass: divClassInner,
            selected: 'AND',
        }
        
        if (indexGroupItem < 1) {
            elVars.itemClass = 'group-op-first'
        }
        else if (indexGroupItem >= 1) {
            const groupOpOptions = groupDiv.querySelectorAll(`select#group-operator_g${idPost} option`)

            groupOpOptions.forEach((option) => {
                if (option.hasAttribute('selected')) {
                    elVars.innerText = option.innerText
                    elVars.selected = option.value
                }
            })

            if (indexGroupItem > 1) { elVars.itemClass = 'group-op-echo' }
        }

        return groupOpElementHtml(namePrefix, idPost, elVars)
    }


    function setDateValueInputs(selectElement, selectedOptionEl) {
        const valueDiv = selectElement.closest('div.filter-value')
        const valueDivClasses = valueDiv.classList
        const idPost = selectElement.id.split('_')[1]
        const namePrefix = selectElement.name.split('.').slice(0, -1).join('.')
        
        const isExactDate = selectedOptionEl.value.toLowerCase().includes('exact')
        const isCustomRelativeDate = selectedOptionEl.value.toLowerCase().includes('relative')
        
        if (valueDivClasses.contains('value-group')) {
            valueDivClasses.remove('value-group') }
        
        if (valueDiv.childElementCount > 1) {
            const valueDivChildren = valueDiv.children
            for (let child of valueDivChildren) {
                if (child != selectElement) { child.remove() }
            }
        }

        if (isExactDate || isCustomRelativeDate) {      // Add inputs right after option element

            let options = {}
            let type = 'text'
            
            if (isExactDate) {
                options = {label: 'Date Picker', placeholder: 'Select a date...'}
                type = 'date'
            }
            if (isCustomRelativeDate) {
                options = {label: 'Custom Relative Date', placeholder: 'e.g. 3 months ago'}
            }
            
            valueDivClasses.add('value-group')

            const valueText = getInputText(type, idPost, namePrefix, options)
            valueDiv.insertAdjacentHTML('beforeend', valueText)
        }
    }


    // --- Remove-Filter Helper

    function updateGroupFilters(groupArray, groupElementInfo, startIndex = 0) {
        console.log('Starting group filter update...')
        const { groupDiv, groupIdPost, groupNamePrefix, currentGroupIdPost } = groupElementInfo

        // First, update the in-group-* class for each item (needed to 
        // correctly generate the idPost for each in next step).
        const currentInGroupClass = `in-group-${currentGroupIdPost}`
        const newInGroupClass = `in-group-${groupIdPost}`

        //console.log('current in-group class: ', currentInGroupClass)
        //console.log('newInGroupClass: ', newInGroupClass)

        if (currentInGroupClass != newInGroupClass) {
            console.log('Updating the in-group classes...')
            groupArray.forEach((rowEl) => {
                rowEl.classList.remove(currentInGroupClass)
                rowEl.classList.add(newInGroupClass)
            })
        }

        // Update each item, according to whether is row or nested group
        groupArray.forEach((rowEl, i) => {
            index = i + startIndex
            console.log('row (new) index: ', index)

            const rowIdPost = getFilterIdPost('row', groupDiv, groupIdPost, rowEl)

            if (rowEl.matches('.filter-row')) {
                console.log('Row is a filter row')

                const namePrefix = getFilterNamePrefix('row', groupNamePrefix, index)

                updateElementId(rowEl, rowIdPost)
                updateRowNamesIds(rowEl, rowIdPost, namePrefix)
            }
            else {
                console.log('Row is a nested group')
                const namePrefix = getFilterNamePrefix('group', groupNamePrefix, index)

                const nestedGroupDiv = rowEl.querySelector('.filter-group')

                if (nestedGroupDiv) {
                    // Update the in-group class for the nested group
                    nestedGroupDiv.classList.remove(currentInGroupClass)
                    nestedGroupDiv.classList.add(newInGroupClass)

                    // Get the pre-updated idPost for this nested group 
                    const currentNestedIdPost = nestedGroupDiv.id.split('_').pop()

                    // Get the new array using the pre-updated idPost
                    const nestedGroupEls = nestedGroupDiv.querySelectorAll(`.outer-row.in-group-${currentNestedIdPost}`)
                    const nestedGroupArray = Array.from(nestedGroupEls)

                    // Get updated idPost, then update the main group element, and the groupOp element
                    const nestedIdPost = getFilterIdPost('group', groupDiv, groupIdPost, nestedGroupDiv)
                    updateElementId(nestedGroupDiv, nestedIdPost)

                    const nestedGroupOp = nestedGroupDiv.querySelector('.group-operator select')
                    updateElementNamePrefix(nestedGroupOp, namePrefix)
                    updateElementId(nestedGroupOp, `g${nestedIdPost}`)

                    // Current group info, to pass to next iteration
                    const parentGroupInfo = {
                        groupDiv: nestedGroupDiv,
                        groupIdPost: nestedIdPost,
                        groupNamePrefix: namePrefix,
                        currentGroupIdPost: currentNestedIdPost
                    }

                    updateGroupFilters(nestedGroupArray, parentGroupInfo)
                }
            }
        })
    }


    function updateElementNamePrefix(element, namePrefix) {
        const name = element.name
        // console.log('current element name: ', name)

        const nameEndStartIndex = name.lastIndexOf('.') + 1
        let nameEnd = name.slice(nameEndStartIndex)

        const newName = `${namePrefix}.${nameEnd}`

        element.name = newName
        console.log('updated element name: ', newName)
    }


    function updateElementId(element, idPost) {
        const elId = element.id
        // console.log('current element id: ', element.id)

        let idPostStartIndex = elId.lastIndexOf('_g')
        if (idPostStartIndex === -1) {
            idPostStartIndex = elId.lastIndexOf('_')
        }

        const idStart = elId.slice(0, idPostStartIndex)
        const newId = `${idStart}_${idPost}`

        element.id = newId
        console.log('updated element id: ', newId)
    }


    function updateRowNamesIds(row, idPost, namePrefix) {
        // Get all elements with attribute 'name'
        const childElementsWithName = row.querySelectorAll('[name]');
        childElementsWithName.forEach((element) => {
            //console.log('Starting forEach loop for children w/ names...')
            if (element.name.split('.').pop() === 'group_op') { return }
            updateElementNamePrefix(element, namePrefix)
        })

        // Get all elements with attribute 'id'
        const childElementsWithId = row.querySelectorAll('[id]');
        childElementsWithId.forEach((element) => {
            //console.log('Starting forEach loop for children w/ ids...')
            if (element.id.split('_')[0] === 'group-operator') { return }
            updateElementId(element, idPost)
        })
    }