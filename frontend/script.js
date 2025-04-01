const form = document.getElementById('fontForm');
const previewElement = document.getElementById('preview');
const downloadLink = document.getElementById('downloadLink');
const darkModeToggle = document.getElementById('darkModeToggle');

// Check if dark mode was previously set
if (localStorage.getItem('darkMode') === 'enabled') {
  document.body.classList.add('dark-mode');
  document.getElementById('container').classList.add('dark-mode');
  darkModeToggle.checked = true;
}

// Dark mode toggle functionality
darkModeToggle.addEventListener('change', (e) => {
  if (e.target.checked) {
    document.body.classList.add('dark-mode');
    document.getElementById('container').classList.add('dark-mode');
    localStorage.setItem('darkMode', 'enabled');
  } else {
    document.body.classList.remove('dark-mode');
    document.getElementById('container').classList.remove('dark-mode');
    localStorage.setItem('darkMode', 'disabled');
  }
});

// Handle font generation on form submit
form.addEventListener('submit', async (e) => {
  e.preventDefault();

  const formData = new FormData(form);
  
  try {
    const response = await fetch('/generate-font', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error('Failed to generate font');
    }

    const data = await response.json();

    // Display success message and enable download link
    if (data.fontUrl) {
      previewElement.innerText = "Font generated successfully!";
      downloadLink.href = data.fontUrl;
      downloadLink.style.display = 'inline';
    }
  } catch (error) {
    console.error('Error:', error);
    previewElement.innerText = 'Error generating font';
  }
});
