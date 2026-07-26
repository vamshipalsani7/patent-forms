export async function checkBackend() {
    const response = await fetch("http://127.0.0.1:8000/")
    return await response.json()
}