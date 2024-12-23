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
        else { 
            refreshElementHtml(viewSettingsUrl, accountBtnDiv, btnId)
            // openUpdateCredentialsModal(account) 
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


function refreshElementHtml(endpointUrl, accountBtnEl, elId) {
    getAsHTMLDoc(endpointUrl)
    .then(doc => {
        updateAccountListItem(doc, accountBtnEl, elId)
        })
}


function openUpdateCredentialsModal(account) {
// TODO
}


async function getAsHTMLDoc(endpointUrl) {
    return await fetch(endpointUrl)
    .then(response => {return response.text()})
    .then(text => {
        const parser = new DOMParser();
        return parser.parseFromString(text, 'text/html');
        })
}


function updateAccountListItem(doc, btnEl, btnId) {
    const currentAccountListEl = btnEl.closest('li')
    const updatedList = doc.getElementById(btnId).closest('li')
    // console.log(updatedList)

    currentAccountListEl.innerHTML = updatedList.innerHTML
}