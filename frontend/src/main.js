import './style.css'

document.querySelector('#app').innerHTML = `
<div class="container">
    <h1>Patent Forms</h1>

    <p class="subtitle">
        Prepare Indian Patent Office forms in minutes.
    </p>

    <button class="upload-btn" id="uploadBtn">
        Select PDF
    </button>

    <p class="status" id="status">
        No document selected.
    </p>

    <input
        type="file"
        id="pdfInput"
        accept=".pdf"
        hidden
    />
</div>
`

const uploadBtn = document.getElementById("uploadBtn")
const pdfInput = document.getElementById("pdfInput")
const status = document.getElementById("status")

uploadBtn.addEventListener("click", () => {
    pdfInput.click()
})

pdfInput.addEventListener("change", () => {
    if (pdfInput.files.length > 0) {
        status.textContent = pdfInput.files[0].name
    }
})