let galleryData = [];

async function fetchGallery() {
  try {
    const res = await fetch('gallery.json');
    if (!res.ok) return;
    galleryData = await res.json();
    renderGallery();
  } catch (e) {
    console.error('Failed to load gallery:', e);
  }
}

function renderGallery() {
  const grid = document.getElementById('gallery-grid');
  grid.innerHTML = '';
  galleryData.forEach((filename) => {
    const img = document.createElement('img');
    img.src = filename + '?t=' + Date.now();
    img.alt = filename;
    img.loading = 'lazy';
    grid.appendChild(img);
  });
}

function refreshLatest() {
  const img = document.getElementById('latest-img');
  const timestamp = new Date().getTime();
  img.src = `latest.jpg?t=${timestamp}`;
}

document.addEventListener('DOMContentLoaded', () => {
  fetchGallery();
  refreshLatest();
  setInterval(refreshLatest, 2000);
});
