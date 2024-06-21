function toggleBookmark(btnElement) {
    const jobRow = btnElement.closest('tr')
    const jobId = btnElement.id.split('-').pop()

    updateBookmarkBtn(isChecked=btnElement.checked, jobRow, btnElement)

    toggleJobField(rowId=jobId, fieldName='bookmarked', value=btnElement.checked)
    .then(json => {
        // console.log('Response: ', json)
        let isChecked = value
        
        if (json.status === 'Error') {
            isChecked = !value;
            // Later TODO: If error -> notification 
            btnElement.checked = isChecked
            updateBookmarkBtn(isChecked, jobRow, btnElement);
        }
        else {
            if (!json.in_view) {    // Job is no longer in current view after change
                removeJobFromView(jobId)               
            }
            else {
                updateBookmarkBtn(isChecked, jobRow, btnElement);
            //  updateJobModals(jobId, fieldName)
            }
        }
        
    })
}


function updateBookmarkBtn(isChecked, jobRow, btnElement) {
    icon_href = ''
    if (isChecked) { icon_href = '#svg-bi-bookmark-fill' }
    else { icon_href = '#svg-bi-bookmark' }
    
    const btnLabelUseEl = jobRow.querySelector(`[for="${btnElement.id}"] use`)
    console.log('btnLabel: ', btnLabelUseEl)

    btnLabelUseEl.setAttribute('href', icon_href)
    btnLabelUseEl.setAttribute('xlink:href', icon_href)
}


function toggleJobField(rowId, fieldName, value) {
    let data = new FormData()
    data.append('id', rowId)
    data.append('field_name', fieldName)
    data.append('value', value)

    request = {
        'method': 'POST',
        'body': data,
    }

    return fetch(toggleBooleanUrl, request)
        .then(response => {
            return response.json();
        })   
}


function removeJobFromView(jobId) {
    const jobItem = document.querySelector(`#dataviewItem-${jobId}`)
    const jobModalsGroup = document.querySelector(`#modalsJob-${jobId}`)
    if (jobItem) { jobItem.remove() }
    if (jobModalsGroup) { jobModalsGroup.remove() }

    // TODO: Make sure that focus correctly moves to next item after change+remove. And there
    // should probably be a live region announcement of change...
}


function updateJobModals(jobId) {
    const jobModalsGroup = document.querySelector(`modalsJob-${jobId}`)
    
    // TODO: Do fetch to get+render page with updated info, and then replace modalsGroup Element

}