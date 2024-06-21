// OnChange and OnClick Actions

    // -- onClick (Buttons):

    function addFilter(type, element, elementId) {

        const { groupDiv, groupIdPost, itemsInGroup, groupNum } = getGroupElInfo(element)

        const groupOpElementName = groupDiv.querySelector('.group-operator select').name
        const groupNamePrefix = groupOpElementName.split('.').slice(0, -1).join('.')
        //console.log('groupNamePrefix: ', groupNamePrefix)

        const indexGroupItem = itemsInGroup

        if (indexGroupItem === 1) {
            // Delete hidden operator field element (will be replaced in row/group creation step)
            const hiddenGroupOpEl = groupDiv.querySelector('.group-operator')

            //console.log('Removing hidden group operator.')
            hiddenGroupOpEl.remove()
        }

        const groupOperatorEl = getRowGroupOpElement(indexGroupItem, groupNamePrefix, groupDiv, { idPost: groupIdPost })
        const idPost = getFilterIdPost(type, groupDiv, groupIdPost)
        const namePrefix = getFilterNamePrefix(type, groupNamePrefix, indexGroupItem)

        let text = ''
        if (type === 'row') {
            text = newFilterRowEl(groupOperatorEl, namePrefix, idPost, groupIdPost)
        }
        else if (type === 'group') {
            text = newFilterGroupEl(groupOperatorEl, namePrefix, idPost, groupIdPost)
        }

        const buttonDiv = element.closest('.filter-btn.row')
        buttonDiv.insertAdjacentHTML('beforebegin', text)
        
        // If adding first filter, un-disable the "clear all" button
        if (groupIdPost === '1' && itemsInGroup === 0) {
            const removeAllBtn = groupDiv.querySelector('.remove-all-btn')
            removeAllBtn.removeAttribute("disabled")
        }
    }


    function deleteFilter(btnElement, filterType) {
        // TODO: Check/add to documentation/notes for this function

        let filterRowDiv = ''
        if (filterType === 'group') {
            filterRowDiv = btnElement.closest('.group-inner.outer-row')
        }
        else if (filterType === 'row') {
            filterRowDiv = btnElement.closest('.filter-row.outer-row')
        }

        const { groupDiv, groupIdPost, itemsInGroup, groupNum } = getGroupElInfo(btnElement)

        // If filter to delete is only filter, disable the "clear all" button
        if (groupIdPost === '1' && itemsInGroup === 1) {
            const removeAllBtn = groupDiv.querySelector('.remove-all-btn')
            removeAllBtn.setAttribute("disabled", true)
        }

        // Determine if row to delete is 2nd row of group
        const allRowEls = groupDiv.querySelectorAll(`.outer-row.in-group-${groupIdPost}`)
        const groupRowsArray = Array.from(allRowEls)

        const rowIndex = groupRowsArray.indexOf(filterRowDiv)
        if (rowIndex === -1) { throw new Error('Element not found in group element list.') }

        const rowNumber = rowIndex + 1
        //console.log(`Row to delete is ${rowNumber}/${itemsInGroup} in group`)

        let isLastRow = false
        if (rowNumber === itemsInGroup) {
            isLastRow = true
            // console.log('Row is last row in group.')
        }

        let replaceGroupOp = false
        let groupOp = ''
        if (rowNumber === 2) {
            // If row being deleted is 2nd row of group, will need to replace the groupOp
            groupOp = groupDiv.querySelector('.group-operator')
            console.log('group-operator: ', groupOp)

            replaceGroupOp = true
            //console.log('Row to delete is 2nd child of group.')
        }


        // DELETE ROW
        console.log('Deleting row...')
        filterRowDiv.remove()

        //AFTER DELETE:
        const newGroupEls = groupDiv.querySelectorAll(`.outer-row.in-group-${groupIdPost}`)
        const newGroupArray = Array.from(newGroupEls)

        if (replaceGroupOp) {
            console.log('Replacing group op...')

            if (!isLastRow) {
                // Add groupOp to new 2nd row
                let groupOpDivRow2 = newGroupArray[1].querySelector('.group-op-echo')
                //console.log('New 2nd row current group-op: ', groupOpDivRow2)

                groupOpDivRow2.insertAdjacentElement('beforebegin', groupOp)
                groupOpDivRow2.remove()
            }
            else {
                //  Add groupOp as first child of first child under filterGroup
                console.log('Was last row, so adding group op to beginning of filterGroup')
                const firstDivInGroup = groupDiv.querySelector('div.row')
                firstDivInGroup.insertAdjacentElement('afterbegin', groupOp)

                // Then add additional class: 'd-none'
                const newGroupOp = groupDiv.querySelector('.group-operator')
                newGroupOp.classList.add('d-none')
                //console.log('inserted group-operator: ', newGroupOp)
            }
        }

        if (!isLastRow) {
            // Row deleted was not the last row of the group, so need to update the 
            // various appropriate numbers in the name, id, and class attributes of all 
            // the remaining rows and nested groups (recursively)
            const groupOpEl = groupDiv.querySelector('.group-operator select')
            const groupNamePrefix = groupOpEl.name.split('.').slice(0, -1).join('.')

            const groupElementInfo = {
                groupDiv: groupDiv,
                groupIdPost: groupIdPost,
                groupNamePrefix: groupNamePrefix,
                currentGroupIdPost: groupIdPost
            }

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

                        updateElementId(rowEl, index, rowIdPost)
                        updateRowNamesIds(rowEl, index, rowIdPost, namePrefix)
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
                            updateElementId(nestedGroupDiv, index, nestedIdPost)

                            const nestedGroupOp = nestedGroupDiv.querySelector('.group-operator select')
                            updateElementNamePrefix(nestedGroupOp, index, namePrefix)
                            updateElementId(nestedGroupOp, index, nestedIdPost)

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


            function updateElementNamePrefix(element, indexGroupItem, namePrefix) {
                name = element.name
                console.log('current element name: ', name)

                const nameEndStartIndex = name.lastIndexOf('.') + 1
                let nameEnd = name.slice(nameEndStartIndex)

                const newName = `${namePrefix}.${nameEnd}`

                element.name = newName
                console.log('updated element name: ', newName)
            }


            function updateElementId(element, indexGroupItem, idPost) {
                const elId = element.id
                console.log('current element id: ', element.id)

                let idPostStartIndex = elId.lastIndexOf('_g')
                if (idPostStartIndex === -1) {
                    idPostStartIndex = elId.lastIndexOf('_')
                }

                const idStart = elId.slice(0, idPostStartIndex)
                const newId = `${idStart}_${idPost}`

                element.id = newId
                console.log('updated element id: ', newId)
            }


            function updateRowNamesIds(row, index, idPost, namePrefix) {
                // Get all elements with attribute 'name'
                const childElementsWithName = row.querySelectorAll('[name]');
                childElementsWithName.forEach((element) => {
                    //console.log('Starting forEach loop for children w/ names...')
                    if (element.name.split('.').pop() === 'group_op') { return }
                    updateElementNamePrefix(element, index, namePrefix)
                })

                // Get all elements with attribute 'id'
                const childElementsWithId = row.querySelectorAll('[id]');
                childElementsWithId.forEach((element) => {
                    //console.log('Starting forEach loop for children w/ ids...')
                    if (element.id.split('_')[0] === 'group-operator') { return }
                    updateElementId(element, index, idPost)
                })
            }

            const rowsToUpdate = newGroupArray.slice(rowIndex)
            //console.log('Rows to update: ', rowsToUpdate)

            updateGroupFilters(rowsToUpdate, groupElementInfo, rowIndex)
        }

    }


    function removeAllFilters(element) {
        const filterForm = element.closest('form')
        const outerFilterGroup = filterForm.querySelector('.filter-group.in-group-0')
        
        // First, copy the group Operator element, and add to top-level of group (hidden)
        const groupOp = outerFilterGroup.querySelector('.group-operator')
        const firstDivInGroup = outerFilterGroup.querySelector('div.row')
        firstDivInGroup.insertAdjacentElement('afterbegin', groupOp)
        const newGroupOp = outerFilterGroup.querySelector('.group-operator')
        newGroupOp.classList.add('d-none')
        
        // Remove rows
        const filterRowsAll = filterForm.querySelectorAll('.outer-row.in-group-1')
        filterRowsAll.forEach((row) => row.remove())

        // Disable the "clear all" button
        element.setAttribute("disabled", true)
    }


    // -- onChange:

    function getFilterOptions(inputId, inputName, selectedOption) {

        //console.log('selected option: ', selectedOption)
        const idPost = inputId.split('_')[1]
        const filter = filterOptions[selectedOption]
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


        function getCheckboxText(idPost, namePrefix, isChecked = false) {
            const checkedAttr = isChecked ? 'checked' : ''
            const id = `filter-value_checkbox_${idPost}`
            const name = `${namePrefix}.values`
            const hiddenInputEl = uncheckedValueEl(id, name)
            
            return (`<input type="checkbox" id="${id}" aria-label="Value" class="form-check-input" name="${name}" value="bool_true" ${checkedAttr} onchange="toggleUncheckedValue(this, this.checked)" />
                    ${hiddenInputEl}`)
        }


        const filterRow = document.getElementById('filter-row_' + idPost)

        // Operator Options
        const operatorOptions = getOptionsText(filter['op_list'])
        const operatorSelect = filterRow.querySelector('.filter-operator .form-select')

        operatorSelect.innerHTML = operatorOptions
        operatorSelect.classList.remove('d-none')

        // Field Values
        const valueDiv = filterRow.querySelector('div.filter-value')
        if (filter['input_type'] === 'multi-select') {

            const valueOptions = getOptionsText(filter.values)
            const valueSelectText = `<select class="form-select" name="${namePrefix}.values" id="filter-value_multi-select_${idPost}" aria-label="Value">
                                    ${valueOptions}
                                    </select>`
            valueDiv.innerHTML = valueSelectText
        }
        else if (filter['input_type'] === 'boolean') {
            const valueText = getCheckboxText(idPost, namePrefix)
            valueDiv.innerHTML = valueText
        }
        else {
            let value = ''
            if (filter.values) {
                value = filter.values
            }
            const valueText = getInputText('text', idPost, namePrefix, value)
            valueDiv.innerHTML = valueText
        }

        // Un-hide element
        valueDiv.classList.remove('d-none')
    }


    function updateOpEchos(element, selectedVal) {

        const groupDiv = element.closest('.filter-group')
        const echoEls = groupDiv.querySelectorAll('.group-op-echo .op-text')
        // Note, could maybe replace below if can get selected option's text directly from onClick event (instead of selectedVal)
        const text = selectedVal[0].toUpperCase() + selectedVal.slice(1).toLowerCase()
        if (echoEls) {
            echoEls.forEach(el => { el.innerText = text })
        }
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


    // Filter Components

    function newFilterGroupEl(outerGroupOpEl, namePrefix, idPost, previousGroupIdPost) {
        const groupOpEl = groupOpElementHtml(namePrefix, idPost, { divClass: 'd-none' })
        const newFilterBtn = filterButtonElement('row', 'Add Filter', '#svg-bi-plus-lg', idPost)
        const newGroupBtn = filterButtonElement('group', 'Add Filter Group', '#svg-bi-subtract', idPost)

        // "Outside" of group
        const groupOuterColWrapper = (innerContent, classDivCols, classDivInner = 'row outer-row') => (`
                    <div class="col g-col-outer row-cap ${classDivCols}">
                        <div class="row">
                            <div class="col g-col-inner row-cap ${classDivCols}">
                                <div class="${classDivInner}">
                                    ${innerContent}
                                </div>
                            </div>
                        </div>
                    </div>`)

        const deleteBtn = deleteFilterBtnEl(classOuter = '', filterType = 'group')

        return `<div class="group-inner outer-row row in-group-${previousGroupIdPost}">
                    ${groupOuterColWrapper(outerGroupOpEl, 'row-start')}
                    <div class="filter-group in-group-${previousGroupIdPost} col g-col-outer"
                        id="filter-group_${idPost}">
                        ${groupOpEl}
                        <div class="row">
                            <div class="col g-col-inner">
                                <div class="filter-btn row">
                                    <div class="col btn-group filter-btn-group" role="group" aria-label="Add Filters">
                                        ${newFilterBtn}
                                        <div class="vr"></div>
                                        ${newGroupBtn}
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    ${groupOuterColWrapper(deleteBtn, 'row-end')}
                </div>`
    }


    function newFilterRowEl(groupOperatorEl, namePrefix, idPost, groupIdPost) {
        const rowDivClass = ''
        const colsDivClass = 'col-4'
        const fieldDivClass = 'col-4 filter-field'
        const operatorDivClass = 'col-2 filter-operator'
        const operatorSelectClass = 'd-none'
        const valueDivClass = 'col filter-value'

        const jobFields = viewOptions.table.job_fields
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
                <div class="${fieldDivClass}">
                    <select name="${namePrefix}.field" id="field-name_${idPost}"
                        class="form-select" aria-label="Field Name"
                        onchange="getFilterOptions(this.id, this.name, this.options[this.selectedIndex].value)">
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
                <div class="col-auto d-inline">
                    ${deleteButton}
                </div>
            </div>
            `
        )
    }


    function groupOpElementHtml(namePrefix, idPost, { itemClass = '', innerText = 'Where', divClass = '' }) {
        const divStyle = 'width: 80px;'
        const ariaLabel = 'Filter Group Operator'
        let innerElement = ''

        if (!itemClass) { itemClass = 'group-operator' }

        if (itemClass === 'group-operator') {
            innerElement = `<select class="form-select" name="${namePrefix}.group_op" id="group-operator_g${idPost}"
                        aria-label="${ariaLabel}" style="${divStyle}" onchange="updateOpEchos(this, this.options[this.selectedIndex].value)">
                            <option value="AND" selected>And</option>
                            <option value="OR">Or</option>
                        </select>`
        }
        else {
            innerElement = `<div class="op-text" style="${divStyle}">${innerText}</div>`
        }

        return (`<div class="col-auto d-inline ${itemClass} ${divClass}">
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
                    onclick="addFilter('${type}', this, this.id)">
                    ${btnContent}
                </button>`
    }


    function uncheckedValueEl(id, name) {
        return `<input type="hidden" id="${id}_unchecked" name="${name}" value="bool_false" />`
    }


    // Filter Helpers

    function getGroupElInfo(element) {

        const groupDiv = element.closest('.filter-group')

        const idPost = groupDiv.id.split('_').pop()
        console.log('groupIdPost: ', idPost)

        const totalGroupItems = groupDiv.querySelectorAll(`.outer-row.in-group-${idPost}`).length
        //console.log('infoFunc indexGroupItem: ', totalGroupItems)

        const groupNumList = idPost.split('-')
        const groupNumber = groupNumList.pop()
        //console.log('groupNum: ', groupNumber)

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

        const jobFields = viewOptions.job_fields
        const filterableFields = Object.keys(filterOptions)

        console.log('indexGroupItem (groupOp): ', indexGroupItem)

        let elVars = {
            itemClass: 'group-operator',
            innerText: 'Where',
            divClass: divClassInner
        }

        if (indexGroupItem < 1) {
            elVars.itemClass = 'group-op-first'
        }
        else if (indexGroupItem > 1) {
            elVars.itemClass = 'group-op-echo'

            // FIXME: "Echo" op does not seem to be picking up the selected option correctly
            const groupOpOptions = groupDiv.querySelectorAll('.group-operator option')
            groupOpOptions.forEach((option, index) => {
                if (option.hasAttribute('selected')) {
                    elVars.innerText = option.innerText
                }
            })
        }

        return groupOpElementHtml(namePrefix, idPost, elVars)
    }