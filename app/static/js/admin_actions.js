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
        // TODO: Notification (in notification area) -- account [enabled/disabled]
        console.log(response.message)    
        if (response.status === 'Error') {
            updateAccountBtn(!isChecked, accountBtnDiv, btnId)
        }
        else { 
            getAsHTMLDoc(viewSettingsUrl)
                .then(doc => {
                    updateAccountListItem(doc, btnId)
                    updateSectionMessages(doc, elId='section-messages-accounts') 
                    })

            if (isChecked && response.account.required_missing) {
            openUpdateCredentialsModal(account) }
        }
    })
}


function updateAccountBtn(isChecked, containingEl, btnElementId) {    
    const btnLabelEl = containingEl.querySelector(`[for="${btnElementId}"]`)
    console.log('btnLabel: ', btnLabelEl)

    btnLabelEl.setAttribute('checked', isChecked)
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


function openUpdateCredentialsModal(account) {
    const accountConfigModal = new bootstrap.Modal(`#editModal-admin-account-${account}`)
    accountConfigModal.show()
}


async function getAsHTMLDoc(endpointUrl) {
    return await fetch(endpointUrl)
    .then(response => {return response.text()})
    .then(text => {
        const parser = new DOMParser();
        return parser.parseFromString(text, 'text/html');
        })
}


function updateAccountListItem(doc, btnId) {
    const currentAccountListEl = document.getElementById(btnId).closest('li')
    const updatedList = doc.getElementById(btnId).closest('li')
    
    currentAccountListEl.innerHTML = updatedList.innerHTML
}


function updateSectionMessages(doc, elId) {
    const currentEl = document.getElementById(elId)
    const updatedEl = doc.getElementById(elId)

    currentEl.innerHTML = updatedEl.innerHTML
}