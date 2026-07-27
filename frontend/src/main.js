import './styles/main.css'

document.querySelector('#app').innerHTML = `
<div class="container">

    <h1>Patent Forms</h1>

    <p class="subtitle">
        Prepare Indian Patent Office forms in minutes.
    </p>

    <button id="uploadBtn" class="upload-btn">
        Select PDF
    </button>
    <button id="processBtn" class="upload-btn">
    Process PDF
    </button>

    <input
        type="file"
        id="pdfInput"
        accept=".pdf"
        hidden
    >

    <p id="status" class="status">
        No document selected.
    </p>

</div>
`

const uploadBtn = document.getElementById("uploadBtn")
const pdfInput = document.getElementById("pdfInput")
const status = document.getElementById("status")

uploadBtn.addEventListener("click", () => {
    pdfInput.click()
})

pdfInput.addEventListener("change", () => {

    if (pdfInput.files.length === 0) return

    status.textContent = pdfInput.files[0].name

})
fetch("http://127.0.0.1:8000/")
    .then(response => response.json())
    .then(data => {
        console.log(data)
    })
    .catch(error => {
        console.error(error)
    })
    const processBtn = document.getElementById("processBtn")

processBtn.addEventListener("click", async () => {

    if (pdfInput.files.length === 0) {
        alert("Please select a PDF first.")
        return
    }

    const formData = new FormData()

    formData.append("file", pdfInput.files[0])

    const response = await fetch("http://127.0.0.1:8000/upload", {
        method: "POST",
        body: formData
    })

    const result = await response.json()

    alert(result.message + "\n" + result.filename)

})