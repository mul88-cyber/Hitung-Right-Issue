<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Pantau Rights Issue</title>
    <!-- Memuat Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        /* Sembunyikan panah di input number */
        input[type=number]::-webkit-inner-spin-button,
        input[type=number]::-webkit-outer-spin-button {
            -webkit-appearance: none;
            margin: 0;
        }
        input[type=number] {
            -moz-appearance: textfield;
        }
    </style>
</head>
<body class="bg-gray-900 text-gray-100 font-sans p-4 md:p-8">

    <div class="max-w-6xl mx-auto">
        <!-- JUDUL -->
        <div class="flex items-center justify-between mb-6">
            <h1 class="text-3xl font-bold text-white">Dashboard Pantau Rights Issue</h1>
            <div id="auth-status" class="text-xs text-gray-500">
                Connecting...
            </div>
        </div>

        <!-- USER ID (PENTING UNTUK SHARING) -->
        <div class="mb-4 p-3 bg-gray-800 rounded-lg shadow-md">
            <label for="userIdDisplay" class="block text-sm font-medium text-gray-400 mb-1">User ID Anda (untuk sinkronisasi):</label>
            <input type="text" id="userIdDisplay" readonly class="w-full bg-gray-700 text-gray-200 rounded-md p-2 text-xs" value="Mengautentikasi...">
        </div>

        <!-- FORM INPUT -->
        <div class="bg-gray-800 p-6 rounded-lg shadow-xl mb-8">
            <h2 class="text-xl font-semibold mb-4 text-white">Tambah Saham Untuk Dipantau</h2>
            <form id="issueForm" class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
                
                <!-- Info Utama -->
                <div class="md:col-span-1">
                    <label for="stockCode" class="block text-sm font-medium text-gray-300">Kode Saham</label>
                    <input type="text" id="stockCode" placeholder="Contoh: BBYB" class="mt-1 block w-full bg-gray-700 border-gray-600 text-white rounded-md shadow-sm p-3 focus:ring-blue-500 focus:border-blue-500" required>
                </div>
                <div class="md:col-span-1">
                    <label for="hargaTebus" class="block text-sm font-medium text-gray-300">Harga Tebus (Rp)</label>
                    <input type="number" id="hargaTebus" placeholder="250" class="mt-1 block w-full bg-gray-700 border-gray-600 text-white rounded-md shadow-sm p-3" required>
                </div>
                <div class="md:col-span-1">
                    <label for="hargaTeori" class="block text-sm font-medium text-gray-300">Harga Teori (Rp)</label>
                    <input type="number" id="hargaTeori" placeholder="363.57" class="mt-1 block w-full bg-gray-700 border-gray-600 text-white rounded-md shadow-sm p-3">
                </div>

                <!-- Tanggal Penting -->
                <div class="md:col-span-1">
                    <label for="cumDate" class="block text-sm font-medium text-gray-300">Cum Date</label>
                    <input type="date" id="cumDate" class="mt-1 block w-full bg-gray-700 border-gray-600 text-white rounded-md shadow-sm p-3" required>
                </div>
                <div class="md:col-span-1">
                    <label for="exDate" class="block text-sm font-medium text-gray-300">Ex Date</label>
                    <input type="date" id="exDate" class="mt-1 block w-full bg-gray-700 border-gray-600 text-white rounded-md shadow-sm p-3" required>
                </div>
                <div class="md:col-span-1">
                    <label for="startTrading" class="block text-sm font-medium text-gray-300">Start Trading</label>
                    <input type="date" id="startTrading" class="mt-1 block w-full bg-gray-700 border-gray-600 text-white rounded-md shadow-sm p-3" required>
                </div>
                <div class="md:col-span-1">
                    <label for="lastTrading" class="block text-sm font-medium text-gray-300">Last Trading (Warning!)</label>
                    <input type="date" id="lastTrading" class="mt-1 block w-full bg-gray-700 border-gray-600 text-white rounded-md shadow-sm p-3" required>
                </div>

                <!-- Tombol Submit -->
                <div class="md:col-span-3 lg:col-span-4 text-right">
                    <button type="submit" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg shadow-md transition duration-200">
                        Tambah Pantauan
                    </button>
                </div>
            </form>
        </div>

        <!-- DAFTAR PANTAUAN -->
        <div>
            <h2 class="text-2xl font-semibold mb-4 text-white">Daftar Pantauan Saham</h2>
            <div id="loadingIndicator" class="text-gray-400">Memuat data...</div>
            <div id="issueList" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                <!-- Kartu Pantauan akan muncul di sini -->
            </div>
        </div>
    </div>

    <!-- Firebase SDK -->
    <script type="module">
        import { initializeApp } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-app.js";
        import { 
            getAuth, 
            signInAnonymously, 
            signInWithCustomToken, 
            onAuthStateChanged 
        } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-auth.js";
        import { 
            getFirestore, 
            doc, 
            addDoc, 
            deleteDoc, 
            collection, 
            query, 
            onSnapshot, 
            serverTimestamp,
            setLogLevel
        } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-firestore.js";

        // --- Variabel Global Firebase ---
        let db, auth;
        let userId = null;
        let issuesCollectionRef;
        let unsubscribeSnapshot = null; // Untuk listener onSnapshot
        
        // --- Konfigurasi Firebase ---
        const appId = typeof __app_id !== 'undefined' ? __app_id : 'default-app-id';
        const firebaseConfig = JSON.parse(typeof __firebase_config !== 'undefined' ? __firebase_config : '{}');
        const initialAuthToken = typeof __initial_auth_token !== 'undefined' ? __initial_auth_token : null;

        // --- Elemen DOM ---
        const issueForm = document.getElementById('issueForm');
        const issueList = document.getElementById('issueList');
        const loadingIndicator = document.getElementById('loadingIndicator');
        const authStatus = document.getElementById('auth-status');
        const userIdDisplay = document.getElementById('userIdDisplay');

        // --- Fungsi Utama ---

        async function initFirebase() {
            try {
                const app = initializeApp(firebaseConfig);
                db = getFirestore(app);
                auth = getAuth(app);
                setLogLevel('Debug'); // Aktifkan log untuk debugging

                console.log("Firebase app diinisialisasi.");
                authStatus.textContent = "Mengautentikasi...";

                // Listener status autentikasi
                onAuthStateChanged(auth, async (user) => {
                    if (user) {
                        console.log("User terautentikasi:", user.uid);
                        userId = user.uid;
                        authStatus.textContent = "Online";
                        userIdDisplay.value = userId;
                        
                        // Setup collection reference setelah userId didapat
                        const collectionPath = `artifacts/${appId}/users/${userId}/rights_issues`;
                        console.log("Path Koleksi:", collectionPath);
                        issuesCollectionRef = collection(db, collectionPath);
                        
                        // Mulai mendengarkan data
                        await setupSnapshotListener();
                    } else {
                        console.log("User tidak terautentikasi.");
                        userId = null;
                        authStatus.textContent = "Offline";
                        userIdDisplay.value = "Tidak terautentikasi";
                        if (unsubscribeSnapshot) {
                            unsubscribeSnapshot(); // Hentikan listener jika logout
                        }
                    }
                });

                // Coba login dengan custom token jika ada
                if (initialAuthToken) {
                    console.log("Mencoba login dengan Custom Token...");
                    await signInWithCustomToken(auth, initialAuthToken);
                } else {
                    console.log("Mencoba login secara anonim...");
                    await signInAnonymously(auth);
                }
                
            } catch (error) {
                console.error("Error saat inisialisasi Firebase:", error);
                authStatus.textContent = "Error";
                loadingIndicator.textContent = "Error memuat data. Cek konsol.";
            }
        }

        // Setup listener realtime ke Firestore
        async function setupSnapshotListener() {
            if (!issuesCollectionRef) {
                console.warn("Koleksi belum siap. Menunggu auth...");
                return;
            }

            // Hentikan listener lama jika ada
            if (unsubscribeSnapshot) {
                unsubscribeSnapshot();
            }

            console.log("Memasang snapshot listener...");
            loadingIndicator.textContent = "Memuat data...";

            const q = query(issuesCollectionRef);
            
            unsubscribeSnapshot = onSnapshot(q, (querySnapshot) => {
                console.log("Menerima snapshot data...");
                const issues = [];
                querySnapshot.forEach((doc) => {
                    issues.push({ id: doc.id, ...doc.data() });
                });
                renderIssues(issues);
                loadingIndicator.style.display = 'none';
            }, (error) => {
                console.error("Error saat mengambil data snapshot:", error);
                loadingIndicator.textContent = "Gagal mengambil data.";
            });
        }

        // Render data ke halaman
        function renderIssues(issues) {
            issueList.innerHTML = ''; // Kosongkan list
            if (issues.length === 0) {
                issueList.innerHTML = `<p class="text-gray-400 col-span-full">Belum ada saham yang dipantau. Silakan tambahkan.</p>`;
                return;
            }

            issues.forEach(issue => {
                const card = document.createElement('div');
                card.className = "bg-gray-800 shadow-lg rounded-lg p-5 border-l-4";
                
                const { daysLeft, warningClass, warningText } = getWarningStatus(issue.lastTrading);

                // Set warna border berdasarkan warning
                card.classList.add(warningClass);

                card.innerHTML = `
                    <div class="flex justify-between items-start mb-3">
                        <h3 class="text-2xl font-bold text-white">${issue.stockCode.toUpperCase()}</h3>
                        <button data-id="${issue.id}" class="delete-btn text-gray-500 hover:text-red-500 transition duration-150">&times;</button>
                    </div>
                    
                    <!-- WARNING -->
                    <div class="mb-4 p-3 rounded-md ${warningClass.replace('border-', 'bg-').replace('gray-700', 'gray-700').replace('yellow-400', 'yellow-900').replace('red-500', 'red-900').replace('green-500', 'green-900')}">
                        <p class="font-bold text-lg ${warningClass.replace('border-', 'text-').replace('gray-700', 'gray-300').replace('yellow-400', 'yellow-300').replace('red-500', 'red-300').replace('green-500', 'green-300')}">
                            ${warningText}
                        </p>
                    </div>

                    <!-- HARGA -->
                    <div class="grid grid-cols-2 gap-2 mb-4 text-sm">
                        <div>
                            <span class="text-gray-400 block">Harga Tebus</span>
                            <span class="text-lg font-medium text-white">Rp ${formatNumber(issue.hargaTebus)}</span>
                        </div>
                        <div>
                            <span class="text-gray-400 block">Harga Teori</span>
                            <span class="text-lg font-medium text-white">Rp ${formatNumber(issue.hargaTeori)}</span>
                        </div>
                    </div>
                    
                    <!-- TANGGAL -->
                    <div class="text-sm space-y-2">
                        <div class="flex justify-between">
                            <span class="text-gray-400">Cum Date:</span>
                            <span class="font-medium text-gray-200">${formatDate(issue.cumDate)}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">Ex Date:</span>
                            <span class="font-medium text-gray-200">${formatDate(issue.exDate)}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">Start Trading:</span>
                            <span class="font-medium text-gray-200">${formatDate(issue.startTrading)}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400 font-bold">Last Trading:</span>
                            <span class="font-bold text-white">${formatDate(issue.lastTrading)}</span>
                        </div>
                    </div>
                `;
                
                issueList.appendChild(card);
            });

            // Tambah event listener untuk tombol delete
            document.querySelectorAll('.delete-btn').forEach(button => {
                button.addEventListener('click', async (e) => {
                    const id = e.target.getAttribute('data-id');
                    // Ganti konfirmasi alert dengan custom UI jika diperlukan di production
                    // Tapi untuk internal tool, console log/disable sementara sudah cukup
                    // if (confirm('Yakin ingin menghapus item ini?')) {
                        await deleteIssue(id);
                    // }
                });
            });
        }

        // Tambah data ke Firestore
        async function handleFormSubmit(e) {
            e.preventDefault();
            if (!issuesCollectionRef) {
                console.error("Koleksi tidak siap. Tidak bisa menambah data.");
                // Tampilkan pesan error ke user di sini
                return;
            }

            const newIssue = {
                stockCode: document.getElementById('stockCode').value,
                hargaTebus: parseFloat(document.getElementById('hargaTebus').value),
                hargaTeori: parseFloat(document.getElementById('hargaTeori').value),
                cumDate: document.getElementById('cumDate').value,
                exDate: document.getElementById('exDate').value,
                startTrading: document.getElementById('startTrading').value,
                lastTrading: document.getElementById('lastTrading').value,
                createdAt: serverTimestamp()
            };

            try {
                await addDoc(issuesCollectionRef, newIssue);
                console.log("Data berhasil ditambahkan.");
                issueForm.reset(); // Reset form setelah sukses
            } catch (error) {
                console.error("Error menambah data:", error);
                // Tampilkan pesan error ke user di sini
            }
        }

        // Hapus data dari Firestore
        async function deleteIssue(id) {
            if (!issuesCollectionRef) {
                console.error("Koleksi tidak siap. Tidak bisa menghapus data.");
                return;
            }
            
            try {
                const docRef = doc(db, issuesCollectionRef.path, id);
                await deleteDoc(docRef);
                console.log("Data berhasil dihapus.");
            } catch (error) {
                console.error("Error menghapus data:", error);
            }
        }

        // --- Fungsi Helper ---

        // Fungsi untuk kalkulasi warning
        function getWarningStatus(lastDateStr) {
            if (!lastDateStr) {
                return { daysLeft: null, warningClass: 'border-gray-700', warningText: 'Tanggal tidak valid' };
            }
            
            const today = new Date();
            today.setHours(0, 0, 0, 0); // Normalisasi hari ini ke awal hari
            
            // Input date (lastDateStr) dalam format YYYY-MM-DD
            // Kita perlu parsing manual untuk menghindari masalah timezone
            const parts = lastDateStr.split('-');
            const lastDate = new Date(parts[0], parts[1] - 1, parts[2]);
            lastDate.setHours(0, 0, 0, 0); // Normalisasi tanggal akhir

            const diffTime = lastDate.getTime() - today.getTime();
            const daysLeft = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

            if (daysLeft < 0) {
                return { daysLeft, warningClass: 'border-gray-700', warningText: 'Selesai / Terlewat' };
            }
            if (daysLeft === 0) {
                return { daysLeft, warningClass: 'border-red-500', warningText: 'HARI TERAKHIR!' };
            }
            if (daysLeft <= 3) {
                return { daysLeft, warningClass: 'border-yellow-400', warningText: `Sisa ${daysLeft} hari!` };
            }
            return { daysLeft, warningClass: 'border-green-500', warningText: `Sisa ${daysLeft} hari` };
        }

        // Format tanggal (DD MMM YYYY)
        function formatDate(dateStr) {
            if (!dateStr) return 'N/A';
            try {
                const parts = dateStr.split('-');
                const date = new Date(parts[0], parts[1] - 1, parts[2]);
                return date.toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' });
            } catch (e) {
                return dateStr; // Kembalikan string asli jika format salah
            }
        }

        // Format angka (1,234.56)
        function formatNumber(num) {
            if (num === null || isNaN(num)) return 'N/A';
            return num.toLocaleString('id-ID', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
        }


        // --- Inisialisasi ---
        issueForm.addEventListener('submit', handleFormSubmit);
        document.addEventListener('DOMContentLoaded', initFirebase);

    </script>
</body>
</html>
