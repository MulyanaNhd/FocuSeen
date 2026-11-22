// Update current date
function updateDate() {
    const days = ['Minggu', 'Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu'];
    const months = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 
                  'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'];
    const now = new Date();
    const dayName = days[now.getDay()];
    const day = now.getDate();
    const month = months[now.getMonth()];
    const year = now.getFullYear();
    document.getElementById('currentDate').textContent = dayName + ', ' + day + ' ' + month + ' ' + year;
}
updateDate();

// Navbar scroll effect
window.addEventListener('scroll', function() {
    const navbar = document.getElementById('navbar');
    if (window.scrollY > 50) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
});

// Tim dropdown
const timLink = document.querySelector('.tim-link');
const timDropdown = document.querySelector('.tim-dropdown');
if (timLink && timDropdown) {
    timLink.addEventListener('click', function(e) {
        e.preventDefault();
        timDropdown.classList.toggle('show');
    });
    
    document.addEventListener('click', function(e) {
        if (!timLink.contains(e.target) && !timDropdown.contains(e.target)) {
            timDropdown.classList.remove('show');
        }
    });
}

// Modal functions
function showAddTugasModal() {
    document.getElementById('addTugasModal').style.display = 'block';
}

function closeAddTugasModal() {
    document.getElementById('addTugasModal').style.display = 'none';
}

// Add tugas via AJAX
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('addTugasForm');
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            const data = {
                matkul_id: document.getElementById('matkulId').value,
                judul: document.getElementById('judul').value,
                deadline: document.getElementById('deadline').value
            };
            
            const response = await fetch('/api/tugas', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
            
            if (response.ok) {
                location.reload();
            }
        });
    }
});

// Delete tugas
async function deleteTugas(id) {
    if (confirm('Hapus tugas ini?')) {
        const response = await fetch('/api/tugas/' + id, {
            method: 'DELETE'
        });
        if (response.ok) {
            location.reload();
        }
    }
}

// Toggle status
async function toggleStatus(id) {
    const response = await fetch('/api/tugas/' + id + '/toggle', {
        method: 'POST'
    });
    if (response.ok) {
        location.reload();
    }
}

// Close modal when clicking outside
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
}