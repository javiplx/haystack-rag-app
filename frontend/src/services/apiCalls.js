const API_URL = process.env.REACT_APP_HAYSTACK_API_URL || 'http://localhost:8000'

export async function fetchFileList() {
  const response = await fetch(`${API_URL}/files`);
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
  }
  const data = await response.json();
  return data.files;
}

export async function searchQuery(query) {
  const response = await fetch(`${API_URL}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
  }
  const data = await response.json();
  return data.results[0].answers[0].answer;
}

export async function uploadFiles(files) {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append("files", file);
  });
  const response = await fetch(`${API_URL}/files`, {
    method: 'POST',
    body: formData,
  });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
  }
  return await response.json();
}
