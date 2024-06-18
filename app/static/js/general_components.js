function iconSvg(svgHref, iconOptions) {
    const width = iconOptions.w ? iconOptions.w : '1rem'
    const height = iconOptions.h ? iconOptions.h : width

    const style_attr = iconOptions.style ? ` style="${iconOptions.style}"` : ''

    return `<svg class="svg-icon" aria-hidden="true" focusable="false" width="${width}" height="${height}"${style_attr}>
                <use href="${svgHref}" xlink:href="${svgHref}" width="${width}" height="${height}" />
            </svg>`
}

function iconBtnContent(svgHref, text, text_is_hidden=false, {iconOptions, spacer_style = 'width: .20rem;'}) {
    const icon_el = iconSvg(svgHref, iconOptions)
    const text_hidden_attr = 'class="visually-hidden"'
    let spacer_el = ''
    if (!text_is_hidden) {
        spacer = `<span class="spacer" aria-hidden="true" style="display: inline-block; ${spacer_style}"></span>`
    }

    return `    
            ${icon_el}
            ${spacer_el}
            <span ${text_hidden_attr}>${text}</span></button>`
}