function handleToggleAccount(btnElement) {
    const accountBtnDiv = btnElement.closest('div')
    const account = btnElement.id.split('-').pop()
    const isChecked = btnElement.checked
    const btnId = btnElement.id

    updateAccountBtn(isChecked, accountBtnDiv, btnId)

    const formData = {
        'account': account,
        'value': isChecked
    }

    submitForm(formData, toggleAccountUrl)
    .then(response => {
        // TODO: Notification 
        console.log(response.message)    
        
        if (response.status === 'Error') {
            updateAccountBtn(!isChecked, accountBtnDiv, btnId)
        }
        else if (!response.account.has_credentials || !response.account.search_url) { 
            // updateAccountItem(account, accountBtnDiv);
            // openUpdateCredentialsModal(account) 
        }
    })
}


function updateAccountBtn(isChecked, containingEl, btnElementId) {    
    const btnLabelUseEl = containingEl.querySelector(`[for="${btnElementId}"]`)
    console.log('btnLabel: ', btnLabelUseEl)

    btnLabelUseEl.setAttribute('checked', isChecked)
}


// function updateAccountItem(account, accountBtnDiv) {
//     settingsAsJson = getAsJson(viewSettingsUrl)
//     console.log(settingsAsJson)
// }

// async function getAsJson(endpointUrl) {
//     const response = await fetch(endpointUrl, { 'method': 'GET' })
//     return await response.json()
// }


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


// function updateJobModals(jobId) {
//     const jobModalsGroup = document.querySelector(`modalsJob-${jobId}`)
    
//     // TODO: Do fetch to get+render page with updated info, and then replace modalsGroup Element

// }