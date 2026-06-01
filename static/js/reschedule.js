document.addEventListener('DOMContentLoaded', function () {

    // --- GEMBOK MASA LALU ---
    const inputTanggalBaru = document.querySelector('input[name="tanggal_baru"]');
    if (inputTanggalBaru) {
        const hariIni = new Date().toISOString().split('T')[0];
        inputTanggalBaru.setAttribute('min', hariIni);
    }

    // --- MODAL ---
    const modal = document.getElementById('rescheduleModal');
    const btnOpen = document.getElementById('btnOpenModal');
    const btnClose = document.getElementById('btnCloseModal');
    const btnCancel = document.getElementById('btnCancelModal');

    btnOpen.addEventListener('click', () => modal.classList.add('open'));

    const closeModal = () => modal.classList.remove('open');
    btnClose.addEventListener('click', closeModal);
    btnCancel.addEventListener('click', closeModal);
    modal.addEventListener('click', (e) => { if (e.target === modal) closeModal(); });

    // --- RADAR RUANGAN KOSONG ---
    const inputSesi = document.querySelector('select[name="sesi_lama"]');
    const inputTanggal = document.querySelector('input[name="tanggal_baru"]');
    const inputJam = document.querySelector('input[name="jam_mulai_baru"]');
    const inputTipe = document.querySelector('select[name="tipe_pengganti"]');
    const selectRuangan = document.getElementById('selectRuangan');
    const containerRuangan = document.getElementById('containerRuangan');
    const teksInfo = document.getElementById('teksInfoRuang');

    async function fetchRuanganKosong() {
        const sesiId = inputSesi.value;
        const tanggal = inputTanggal.value;
        const jam = inputJam.value;

        if (inputTipe.value === 'ONLINE') {
            containerRuangan.style.display = 'none';
            selectRuangan.required = false;
            return;
        } else {
            containerRuangan.style.display = '';
            selectRuangan.required = true;
        }

        if (sesiId && tanggal && jam) {
            teksInfo.textContent = 'Mencari ruangan kosong...';
            teksInfo.className = 'form-hint';
            selectRuangan.disabled = true;

            try {
                const response = await fetch(`/schedules/api/cek-ruang/?sesi_id=${sesiId}&tanggal=${tanggal}&jam_mulai=${jam}`);
                const data = await response.json();

                selectRuangan.innerHTML = '<option value="">— Pilih Ruangan Kosong —</option>';

                if (data.ruangan && data.ruangan.length > 0) {
                    data.ruangan.forEach(ruang => {
                        const opt = document.createElement('option');
                        opt.value = ruang.id;
                        opt.textContent = `${ruang.nama} (Kapasitas: ${ruang.kapasitas})`;
                        selectRuangan.appendChild(opt);
                    });
                    selectRuangan.disabled = false;
                    teksInfo.textContent = 'Ditemukan! Silakan pilih ruangan.';
                    teksInfo.className = 'form-hint success';
                } else {
                    selectRuangan.innerHTML = '<option value="">— Tidak ada ruangan kosong —</option>';
                    teksInfo.textContent = 'Semua ruangan penuh di jam tersebut.';
                    teksInfo.className = 'form-hint error';
                }
            } catch (error) {
                console.error('Error fetching ruangan:', error);
            }
        } else {
            selectRuangan.innerHTML = '<option value="">— Isi tanggal & jam dulu —</option>';
            selectRuangan.disabled = true;
            teksInfo.textContent = 'Isi tanggal & jam untuk melihat ruangan kosong.';
            teksInfo.className = 'form-hint warning';
        }
    }

    inputSesi.addEventListener('change', fetchRuanganKosong);
    inputTanggal.addEventListener('change', fetchRuanganKosong);
    inputJam.addEventListener('change', fetchRuanganKosong);
    inputTipe.addEventListener('change', fetchRuanganKosong);

});