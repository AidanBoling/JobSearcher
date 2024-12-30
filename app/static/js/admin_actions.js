function handleToggleAccount(btnElement) {
    const accountBtnDiv = btnElement.closest('div')
    const account = btnElement.id.split('-').pop()
    const isChecked = btnElement.checked
    const btnId = btnElement.id
    // const sectionMessagesId = 'section-messages-accounts'
    const sectionId = 'section-accounts'

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
                    // updateAccountListItem(doc, btnId)
                    updateElementHTML(doc, sectionId) 
                    })

            if (isChecked && response.account.required_missing) {
                const accountConfigModalId = `editModal-admin-account-${account}`
                setModalIsVisible(accountConfigModalId, true) 
            }
        }
    })
}


function handleClearCredentials(btnElement) {
    const account = btnElement.id.split('-').pop()
    const btnId = btnElement.id
    const accountConfigModalId = `editModal-admin-account-${account}`
    const sectionId = 'section-accounts'

    setButtonIsDisabled(btnElement, true)

    const formData = {
        'account': account,
    }

    submitForm(formData, unsetCredentialsUrl)
    .then(response => {
        
        // TODO: Notification (in notification area) -- account [enabled/disabled]
        console.log(response.message)  
        
        if (response.status != 'Error') {

            getAsHTMLDoc(viewSettingsUrl)
                .then(doc => {
                    updateElementHTML(doc, accountConfigModalId)
                    updateElementHTML(doc, sectionId) 
                    })
        }


    })
    
    setButtonIsDisabled(btnElement, false)  
}


function updateAccountBtn(isChecked, containingEl, btnElementId) {    
    const btnLabelEl = containingEl.querySelector(`[for="${btnElementId}"]`)
    console.log('btnLabel: ', btnLabelEl)

    btnLabelEl.setAttribute('checked', isChecked)
}


function setButtonIsDisabled(btnElement, disable) {
    if (disable) {
        btnElement.setAttribute('disabled', 'true')
    }
    else {
        btnElement.removeAttribute('disabled')
    }
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


async function getAsHTMLDoc(endpointUrl) {
    return await fetch(endpointUrl)
    .then(response => {return response.text()})
    .then(text => {
        const parser = new DOMParser();
        return parser.parseFromString(text, 'text/html');
        })
}


function updateElementHTML(doc, elId) {
    const currentEl = document.getElementById(elId)
    const updatedEl = doc.getElementById(elId)
    
    currentEl.innerHTML = updatedEl.innerHTML
}


function setModalIsVisible(modalId, open) {
    const modal = new bootstrap.Modal(modalId)
    if (open) {
        modal.show()
    }
    else {
        modal.hide()
    }
}


// function updateAccountListItem(doc, btnId) {
//     const currentAccountListEl = document.getElementById(btnId).closest('li')
//     const updatedList = doc.getElementById(btnId).closest('li')
    
//     currentAccountListEl.innerHTML = updatedList.innerHTML
// }
