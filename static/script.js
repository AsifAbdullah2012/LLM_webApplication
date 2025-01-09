// Function to dynamically add file input fields
function addFileFields() {
  const numVersions = document.getElementById("num_versions").value;
  const uploadContainer = document.getElementById("file_uploads");
  uploadContainer.innerHTML = ""; // Clear previous fields

  for (let i = 0; i < numVersions; i++) {
    const input = document.createElement("input");
    input.type = "file";
    input.name = "files";
    input.className = "file-input";
    uploadContainer.appendChild(input);
    uploadContainer.appendChild(document.createElement("br"));
  }
}

// Function to handle form submission
async function submitForm() {
  const formData = new FormData(document.getElementById("upload_form"));

  const response = await fetch("/process", {
    method: "POST",
    body: formData,
  });

  const results = await response.json();
  const output = document.getElementById("output");
  output.innerHTML = results.join("<br><hr><br>");
}
