

function addSort(element) {
    //Get number --> i.e. index number + 1, or, length of all sort rows.
    const parentEl = element.closest('.sort-container')

    const sortRows = parentEl.querySelectorAll('.sort-row')
    const numRows = sortRows.length

    let number = 0
    if (numRows > 0) {
        const lastRow = sortRows[numRows - 1]
        number = parseInt(lastRow.id.split('-').pop()) + 1
    }

    const text = newSortEl(number)

    const sortRowsDiv = parentEl.querySelector('.sort-rows')
    sortRowsDiv.insertAdjacentHTML('beforeend', text)

    // If adding first sort, enable the "clear all" button
    if (numRows === 0) {
        const removeAllBtn = parentEl.querySelector('.remove-all-btn')
        removeAllBtn.removeAttribute("disabled")
    }
}


function removeOneSort(element) {
    const sortRowDiv = element.closest('.sort-row')

    // If removing the last/only sort, disable the "clear all" button
    const parentEl = element.closest('.sort-container')
    const sortRows = parentEl.querySelectorAll('.sort-row')
    if (sortRows.length === 1) {
        const removeAllBtn = parentEl.querySelector('.remove-all-btn')
        removeAllBtn.setAttribute("disabled", true)
    }

    sortRowDiv.remove()
}


function removeAllSort(element) {
    const sortContainer = element.closest('.sort-container')
    const sortRowsAll = sortContainer.querySelectorAll('.sort-row')
    console.log('sortrowsAll: ', sortRowsAll)
    sortRowsAll.forEach((row) => row.remove())

    // Disable the "clear all" button
    element.setAttribute("disabled", true)
}


function newSortEl(number) {
    function sortSelectEl(item, number, ariaLabel, options, divClass) {
        let options_els = ''
        console.log('options: ', options)
        options.forEach((option) => {
            console.log('option[0]', option[0])
            options_els += `
                    <option value=${option[0]}>${option[1]}</option>`
        })

        return (
            `<div class="sort-${item} ${divClass}">
                <select class="form-select" name="${number}.${item}" aria-label="${ariaLabel}">
                    ${options_els}
                </select>
            </div>
            `
        )
    }

    const fieldDivClass = 'col ps-0 pe-1'
    const orderDivClass = 'col-auto px-2'

    const fieldSelectInput = sortSelectEl('field', number, 'Field Name', sortOptions.fields, fieldDivClass)
    const orderSelectInput = sortSelectEl('order', number, 'Sort Order', sortOptions.order, orderDivClass)

    const deleteButton = deleteSortBtnEl('col-auto d-inline')

    return (
        `<div class="sort-row row" id="sort-${number}">
                ${fieldSelectInput}
                ${orderSelectInput}
                ${deleteButton}
            </div>
            `
    )
}


function deleteSortBtnEl(outerClass) {
    const iconOptions = { w: '16' }
    const btnContent = iconBtnContent(svgHref = '#svg-bi-trash3', text = 'Remove', text_is_hidden = true, { iconOptions })

    return `<div class="btn-remove-one ${outerClass}">
                <button class="btn ab-btn-light start-grey" type="button"
                onclick="removeOneSort(this)">
                    ${btnContent}
                </button>
            </div>
    `
}

