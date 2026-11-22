// Generic modal functions
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'block';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    }
}

// Close modal when clicking outside
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
}

// Tugas functions
function editTugas(id, judul, matkulId, deadline, status) {
    openModal('addTugasModal');
    document.getElementById('modalTitle').textContent = 'Edit Tugas';
    document.getElementById('tugasForm').action = '/admin/tugas/edit/' + id;
    document.getElementById('tugasId').value = id;
    document.getElementById('judul').value = judul;
    document.getElementById('matkulId').value = matkulId;
    document.getElementById('deadline').value = deadline;
}

function deleteTugas(id, judul) {
    if (confirm(`Hapus tugas "${judul}"?\n\nTindakan ini tidak dapat dibatalkan!`)) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/admin/tugas/delete/' + id;
        document.body.appendChild(form);
        form.submit();
    }
}

// Mata Kuliah functions
function editMatkul(id, nama, kode, color, icon, dosen, semester) {
    openModal('addMatkulModal');
    document.getElementById('modalTitleMatkul').textContent = 'Edit Mata Kuliah';
    document.getElementById('matkulForm').action = '/admin/matkul/edit/' + id;
    document.getElementById('matkulId').value = id;
    document.getElementById('nama').value = nama;
    document.getElementById('kode').value = kode;
    document.getElementById('dosen').value = dosen;
    document.getElementById('semester').value = semester;
    document.getElementById('color').value = color;
    document.getElementById('icon').value = icon;
}

function deleteMatkul(id, nama) {
    if (confirm(`Hapus mata kuliah "${nama}"?\n\nPeringatan: Pastikan tidak ada tugas yang menggunakan mata kuliah ini!`)) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/admin/matkul/delete/' + id;
        document.body.appendChild(form);
        form.submit();
    }
}

// Anggota Tim functions
function editTim(id, nama, nim, email, peran) {
    openModal('addTimModal');
    document.getElementById('modalTitleTim').textContent = 'Edit Anggota Tim';
    document.getElementById('timForm').action = '/admin/tim/edit/' + id;
    document.getElementById('timId').value = id;
    document.getElementById('namaTim').value = nama;
    document.getElementById('nim').value = nim;
    document.getElementById('email').value = email;
    document.getElementById('peran').value = peran;
}

function deleteTim(id, nama) {
    if (confirm(`Hapus anggota "${nama}" dari tim?\n\nTindakan ini tidak dapat dibatalkan!`)) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/admin/tim/delete/' + id;
        document.body.appendChild(form);
        form.submit();
    }
}