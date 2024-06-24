function handleToggleBookmark(btnElement) {
    const jobRow = btnElement.closest('tr')
    const jobId = btnElement.id.split('-').pop()
    const isChecked = btnElement.checked
    const btnId = btnElement.id

    updateBookmarkBtn(isChecked, jobRow, btnId)

    const formData = {
        'id': jobId,
        'field_name': 'bookmarked',
        'value': isChecked
    }

    submitForm(formData, toggleBooleanUrl)
    .then(response => {
        // TODO: Notification 
        console.log(response.message)    
        
        if (response.status === 'Error') {
            updateBookmarkBtn(!isChecked, jobRow, btnId)
        }
        else if (!response.in_view) { removeJobFromView(jobId) }
        else { updateJobModals(jobId, fieldName) }        
    })
}


function handleDeleteJob(job) {
    const formData = { 'job': JSON.stringify(job) }

    submitForm(formData, deleteJobUrl)
    .then(response => {
        console.log(response.message)
        // Later TODO: Notification 

        if (response.status === 'Success') {
            removeJobFromView(job.id)
        }
    })
}


function updateBookmarkBtn(isChecked, jobRow, btnElementId) {
    let icon_href = '#svg-bi-bookmark'
    if (isChecked) { icon_href = '#svg-bi-bookmark-fill' }
    
    const btnLabelUseEl = jobRow.querySelector(`[for="${btnElementId}"] use`)
    console.log('btnLabel: ', btnLabelUseEl)

    btnLabelUseEl.setAttribute('href', icon_href)
    btnLabelUseEl.setAttribute('xlink:href', icon_href)
}


function submitForm(formData, endpointUrl) {
    const data = new FormData()
    for (const [key, value] of Object.entries(formData)) {
        data.append(key, value)
    }
    
    const request = {
        'method': 'POST',
        'body': data,
    }

    return fetch(endpointUrl, request)
        .then(response => {
            return response.json();
        })      
}


function removeJobFromView(jobId) {
    const jobItem = document.querySelector(`#dataviewItem-${jobId}`)
    const jobModalsGroup = document.querySelector(`#modalsJob-${jobId}`)
    
    if (jobItem) { 
        const jobResultsEl = document.getElementById('resultsInfo')
        const resultsTextArray = jobResultsEl.innerText.split()
        const newResultsNum = parseInt(resultsTextArray[0]) - 1
        
        jobItem.remove()
        jobResultsEl.innerText = `${newResultsNum} Jobs`
    }
    if (jobModalsGroup) {
        // Close any open modal in group, then remove group
        let jobModalOpen = jobModalsGroup.querySelector('.modal.show')
        const modal = bootstrap.Modal.getInstance(jobModalOpen)

        jobModalOpen.addEventListener('hidden.bs.modal', event => { 
            jobModalsGroup.remove()
        })

        modal.hide()
    }

    // TODO: Make sure that focus correctly moves to next item after change+remove. 
    // And there should probably be a live region announcement of change...
}


function updateJobModals(jobId) {
    const jobModalsGroup = document.querySelector(`modalsJob-${jobId}`)
    
    // TODO: Do fetch to get+render page with updated info, and then replace modalsGroup Element

}