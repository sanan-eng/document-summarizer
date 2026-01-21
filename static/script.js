const fileInput = document.getElementById("fileInput");
const textInput = document.getElementById("textInput");
const charCount = document.getElementById("charCount");
const summaryOutput = document.getElementById("summaryOutput");
const resultCard = document.getElementById("resultCard");
const loading = document.getElementById("loading");

textInput.addEventListener("input", () => {
    charCount.innerText = `${textInput.value.length} chars`;
    fileInput.value = "";
});

async function generateSummary() {
    resultCard.style.display = "none";
    loading.style.display = "block";

    const formData = new FormData();
    if (fileInput.files[0]) formData.append("file", fileInput.files[0]);
    formData.append("text_input", textInput.value);
    formData.append("summary_type", document.getElementById("summaryType").value);

    const res = await fetch("/summarize", { method: "POST", body: formData });
    const data = await res.json();

    loading.style.display = "none";

    if (res.ok) {
        summaryOutput.innerHTML = data.summary.replace(/\n/g, "<br>");
        resultCard.style.display = "block";
    } else {
        alert(data.error);
    }
}

function copySummary() {
    navigator.clipboard.writeText(summaryOutput.innerText);
}
