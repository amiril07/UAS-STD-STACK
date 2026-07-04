from itertools import count
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, db
import os

# 1. KONEKSI CLOUD DATABASE FIREBASE
try:
    cred = credentials.Certificate("uas-std-firebase-adminsdk-fbsvc-3e424c64d9.json") 
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://uas-std-default-rtdb.firebaseio.com/'
    })
    ref = db.reference('data_list')
except Exception as e:
    print(f"Peringatan Koneksi Firebase: {e}")
    print("Pastikan file JSON kredensial dan URL Firebase sudah benar!")


# 2. LOGIKA STRUKTUR DATA STACK (LIFO)
class AssignmentStack:
    def __init__(self):
        self.stack = []
        self.data_keys = []
        self.sync_from_firebase()

    def _normalize_assignment(self, item):
        if not isinstance(item, dict): return None
        npm = item.get("npm") or item.get("nim")
        if not npm or not item.get("nama") or not item.get("kelas") or not item.get("tugas") or not item.get("prodi"):
            return None
        return {
            "nama": item["nama"],
            "npm": npm,
            "prodi": item["prodi"],
            "kelas": item["kelas"],
            "tugas": item["tugas"],
            "jam": item.get("jam", "-"),
            "nilai": item.get("nilai", "Belum Dinilai"),
        }

    def sync_from_firebase(self):
        try:
            snapshot = ref.get()
            self.stack = []
            self.data_keys = []
            if snapshot:
                if isinstance(snapshot, dict):
                    for key, value in snapshot.items():
                        normalized = self._normalize_assignment(value)
                        if normalized:
                            self.stack.append(normalized)
                            self.data_keys.append(key)
                else:
                    for index, value in enumerate   (snapshot):
                        normalized = self._normalize_assignment(value)
                        if normalized:
                            self.stack.append(normalized)
                            self.data_keys.append(str(index))
        except Exception:
            self.stack = []
            self.data_keys = []

    def is_empty(self):
        return len(self.stack) == 0

    def push(self, nama, npm, kelas, judul_tugas, prodi):

        if len(self.stack) >= 5:
            messagebox.showwarning("Kuota Penuh", "Gagal menambahkan! Batas maksimal tumpukan di meja adalah 5 tugas.")
            return False
            
        jam_sekarang = datetime.now().strftime("%H:%M:%S")
        data_tugas = {
            "nama": nama,
            "npm": npm,
            "prodi": prodi,
            "kelas": kelas,
            "tugas": judul_tugas,
            "jam": jam_sekarang,
            "nilai": "Belum Dinilai"
        }

        try:
            ref.push(data_tugas)
            self.sync_from_firebase()
            return True
        except Exception as e:
            messagebox.showerror("Firebase Error", f"Gagal mengunggah data: {e}")
            return False

    def pop(self):
        if self.is_empty(): return None
        self.sync_from_firebase()
        tugas_terpop = self.stack[-1]
        try:
            if self.data_keys:
                ref.child(self.data_keys[-1]).delete()
            else:
                all_data = ref.get()
                if isinstance(all_data, list):
                    all_data.pop()
                    ref.set(all_data)
            self.sync_from_firebase()
            return tugas_terpop
        except Exception as e:
            messagebox.showerror("Firebase Error", f"Gagal menghapus data: {e}")
            return None

    def peek(self):
        if self.is_empty(): return None
        return self.stack[-1]

    def get_all_assignments(self):
        return self.stack

    def clear_stack(self):
        try:
            ref.set({})
            self.stack.clear()
            self.data_keys.clear()
            return True
        except Exception:
            return False


# 3. APLIKASI UTAMA (SATU JENDELA - DUA LAYAR TAB)
class AssignmentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("UAS Struktur Data - Sistem Cloud Tugas (Satu Jendela)")
        
        self.root.geometry("1100x680")
        self.root.minsize(1050, 650)
        self.root.configure(bg="#f8fafc")

        self.stack = AssignmentStack()
        self.graded_assignments = []

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.setup_student_tab()
        self.setup_lecturer_tab()

        self.root.bind("<Configure>", self.on_window_resize)

        self.update_student_view()
        self.update_lecturer_view()

    def on_window_resize(self, event):
        if event.widget == self.root:
            self.update_student_view()
            self.update_lecturer_view()

    # LAYAR 1: MAHASISWA (TAB 1)
    def setup_student_tab(self):
        self.tab_mahasiswa = tk.Frame(self.notebook, bg="#f8fafc")
        self.notebook.add(self.tab_mahasiswa, text="  🎓 LAYAR MAHASISWA  ")

        header = tk.Frame(self.tab_mahasiswa, bg="#0284c7", pady=12)
        header.pack(fill=tk.X)
        tk.Label(header, text="🎓 Portal Pengumpulan Tugas Mahasiswa", font=("Segoe UI", 14, "bold"), fg="#ffffff", bg="#0284c7").pack()

        main_frame = tk.Frame(self.tab_mahasiswa, bg="#f8fafc", padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = tk.LabelFrame(main_frame, text=" FORM INPUT MAHASISWA ", font=("Segoe UI", 11, "bold"), bg="#ffffff", padx=15, pady=15, bd=1, relief=tk.SOLID, width=340)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 15))
        left_frame.pack_propagate(False)

        tk.Label(left_frame, text="NPM Mahasiswa:", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#334155").pack(anchor=tk.W, pady=(5, 2))
        self.entry_npm = tk.Entry(left_frame, font=("Segoe UI", 10), bd=1, relief=tk.SOLID, bg="#f1f5f9")
        self.entry_npm.pack(fill=tk.X, pady=(0, 10))

        tk.Label(left_frame, text="Nama Lengkap:", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#334155").pack(anchor=tk.W, pady=(5, 2))
        self.entry_nama = tk.Entry(left_frame, font=("Segoe UI", 10), bd=1, relief=tk.SOLID, bg="#f1f5f9")
        self.entry_nama.pack(fill=tk.X, pady=(0, 10))

        tk.Label(left_frame, text="Prodi:", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#334155").pack(anchor=tk.W, pady=(5, 2))
        self.entry_prodi = tk.Entry(left_frame, font=("Segoe UI", 10), bd=1, relief=tk.SOLID, bg="#f1f5f9")
        self.entry_prodi.pack(fill=tk.X, pady=(0, 10))

        tk.Label(left_frame, text="Kelas:", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#334155").pack(anchor=tk.W, pady=(5, 2))
        self.entry_kelas = tk.Entry(left_frame, font=("Segoe UI", 10), bd=1, relief=tk.SOLID, bg="#f1f5f9")
        self.entry_kelas.pack(fill=tk.X, pady=(0, 10))

        tk.Label(left_frame, text="Pilih Dokumen Tugas:", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#334155").pack(anchor=tk.W, pady=(5, 2))
        file_frame = tk.Frame(left_frame, bg="#ffffff")
        file_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.entry_tugas = tk.Entry(file_frame, font=("Segoe UI", 10), bd=1, relief=tk.SOLID, bg="#f1f5f9", state="readonly")
        self.entry_tugas.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        btn_browse = tk.Button(file_frame, text="📁 File", font=("Segoe UI", 8, "bold"), bg="#475569", fg="#ffffff", bd=0, command=self.pilih_dokumen, cursor="hand2", padx=6)
        btn_browse.pack(side=tk.RIGHT)

        btn_push = tk.Button(left_frame, text="📥 Kirim Tugas (Push)", font=("Segoe UI", 11, "bold"), bg="#0284c7", fg="#ffffff", bd=0, command=self.handle_push, cursor="hand2", pady=6)
        btn_push.pack(fill=tk.X)

        right_frame = tk.LabelFrame(main_frame, text=" STATUS TUMPUKAN DI MEJA ", font=("Segoe UI", 11, "bold"), bg="#ffffff", padx=10, pady=10, bd=1, relief=tk.SOLID)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.canvas_mhs = tk.Canvas(right_frame, bg="#f8fafc", bd=0, highlightthickness=0)
        self.canvas_mhs.pack(fill=tk.BOTH, expand=True)

    # LAYAR 2: DOSEN (TAB 2)
    def setup_lecturer_tab(self):
        self.tab_dosen = tk.Frame(self.notebook, bg="#f8fafc")
        self.notebook.add(self.tab_dosen, text="  👨‍🏫 LAYAR DOSEN  ")

        header = tk.Frame(self.tab_dosen, bg="#0f172a", pady=12)
        header.pack(fill=tk.X)
        tk.Label(header, text="👨‍🏫 Panel Kendali & Penilaian Dosen", font=("Segoe UI", 14, "bold"), fg="#38bdf8", bg="#0f172a").pack()

        main_frame = tk.Frame(self.tab_dosen, bg="#f8fafc", padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = tk.LabelFrame(main_frame, text=" PANEL PENILAIAN DOSEN ", font=("Segoe UI", 11, "bold"), bg="#ffffff", padx=15, pady=15, bd=1, relief=tk.SOLID, width=280)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 15))
        left_frame.pack_propagate(False)

        tk.Label(left_frame, text="Input Nilai Kelulusan (0-100):", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#334155").pack(anchor=tk.W, pady=(5, 2))
        self.entry_nilai_dosen = tk.Entry(left_frame, font=("Segoe UI", 14, "bold"), bd=1, relief=tk.SOLID, bg="#fffbeb", fg="#b45309", justify="center")
        self.entry_nilai_dosen.pack(fill=tk.X, pady=(0, 15))

        btn_pop = tk.Button(left_frame, text="🔍 Beri Nilai Tugas (Pop)", font=("Segoe UI", 11, "bold"), bg="#d97706", fg="#ffffff", bd=0, command=self.handle_pop, cursor="hand2", pady=8)
        btn_pop.pack(fill=tk.X, pady=(0, 10))

        btn_clear = tk.Button(left_frame, text="🗑️ Kosongkan Database", font=("Segoe UI", 10), bg="#ef4444", fg="#ffffff", bd=0, command=self.handle_clear, cursor="hand2", pady=4)
        btn_clear.pack(fill=tk.X, pady=(20, 0))

        center_frame = tk.LabelFrame(main_frame, text=" MONITOR FISIK TUMPUKAN MEJA DOSEN ", font=("Segoe UI", 11, "bold"), bg="#ffffff", padx=10, pady=10, bd=1, relief=tk.SOLID)
        center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))

        self.lbl_status_dosen = tk.Label(center_frame, text="Status Meja: Sinkronisasi Cloud...", font=("Segoe UI", 9, "bold"), fg="#475569", bg="#f1f5f9", pady=4)
        self.lbl_status_dosen.pack(fill=tk.X, pady=(0, 10))

        self.canvas_dsn = tk.Canvas(center_frame, bg="#f8fafc", bd=0, highlightthickness=0)
        self.canvas_dsn.pack(fill=tk.BOTH, expand=True)

        right_frame = tk.LabelFrame(main_frame, text=" DAFTAR MAHASISWA SUDAH DINILAI ", font=("Segoe UI", 11, "bold"), bg="#ffffff", padx=10, pady=10, bd=1, relief=tk.SOLID, width=320)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)
        right_frame.pack_propagate(False)

        self.history_container = tk.Canvas(right_frame, bg="#f8fafc", bd=0, highlightthickness=0)
        self.history_container.pack(fill=tk.BOTH, expand=True)


    # 4. KONTROLLER DAN LOGIKA AKSI APLIKASI
    def pilih_dokumen(self):
        tipe_file = [('Dokumen Tugas', '*.pdf *.docx *.doc *.zip *.rar'), ('Semua File', '*.*')]
        file_path = filedialog.askopenfilename(title="Pilih Berkas Tugas", filetypes=tipe_file)
        if file_path:
            nama_file_saja = os.path.basename(file_path)
            self.entry_tugas.config(state="normal")
            self.entry_tugas.delete(0, tk.END)
            self.entry_tugas.insert(0, nama_file_saja)
            self.entry_tugas.config(state="readonly")

    def get_grade_info(self, score_int):
        if 0 <= score_int <= 40: return "D", "#ef4444", "#fef2f2"
        elif 41 <= score_int <= 60: return "C", "#f59e0b", "#fffbeb"
        elif 61 <= score_int <= 80: return "B", "#3b82f6", "#eff6ff"
        elif 81 <= score_int <= 100: return "A", "#22c55e", "#f0fdf4"
        return "N/A", "#64748b", "#f1f5f9"

    def update_student_view(self):
        self.canvas_mhs.delete("all")
        all_items = self.stack.get_all_assignments()
        if not all_items:
            self.canvas_mhs.create_text(250, 150, text="📭 Belum ada tugas terkumpul.", font=("Segoe UI", 11, "italic"), fill="#94a3b8")
            return

        canvas_width = self.canvas_mhs.winfo_width()
        card_width = (canvas_width if canvas_width > 100 else 650) - 35
        
        for index, item in enumerate(reversed(all_items)):
            y0 = 10 + (index * 65)
            y1 = y0 + 55
            bg_c, border_c = ("#e0f2fe", "#0284c7") if index == 0 else ("#ffffff", "#cbd5e1")
            
            self.canvas_mhs.create_rectangle(10, y0, card_width, y1, fill=bg_c, outline=border_c, width=1.5)
            
            self.canvas_mhs.create_text(20, y0 + 15, text=f"{item['nama']} ({item['kelas']})", font=("Segoe UI", 10, "bold"), fill="#1e293b", anchor=tk.W)
            self.canvas_mhs.create_text(20, y0 + 35, text=f"📄 Berkas: {item['tugas']}", font=("Segoe UI", 8, "italic"), fill="#475569", anchor=tk.W)
            
            tag = "⭐ TERATAS (LIFO)" if index == 0 else f"Antrean #{len(all_items) - index}"
            self.canvas_mhs.create_text(card_width - 15, y0 + 15, text=tag, font=("Segoe UI", 8, "bold"), fill=border_c, anchor=tk.E)

    def update_lecturer_view(self):
        self.canvas_dsn.delete("all")
        all_items = self.stack.get_all_assignments()
        
        canvas_width = self.canvas_dsn.winfo_width()
        card_width = (canvas_width if canvas_width > 100 else 550) - 35
        
        if not all_items:
            self.lbl_status_dosen.config(text="Status Meja: Kosong", fg="#64748b", bg="#f1f5f9")
            self.canvas_dsn.create_text(180, 150, text="📭 Tidak Ada Berkas di Meja Dosen", font=("Segoe UI", 11, "italic"), fill="#94a3b8")
        else:
            top_item = self.stack.peek()
            self.lbl_status_dosen.config(text=f"🟢 Terhubung | Total: {len(all_items)} Tugas | TOP: {top_item['nama']}", fg="#0369a1", bg="#e0f2fe")
            
            for index, item in enumerate(reversed(all_items)):
                y0 = 10 + (index * 70)
                y1 = y0 + 60
                bg_c, border_c = ("#fef3c7", "#d97706") if index == 0 else ("#ffffff", "#cbd5e1")
                
                self.canvas_dsn.create_rectangle(10, y0, card_width, y1, fill=bg_c, outline=border_c, width=2)
                self.canvas_dsn.create_text(20, y0 + 15, text=f"{item['npm']} - {item['nama']}", font=("Segoe UI", 10, "bold"), fill="#1e293b", anchor=tk.W)
                self.canvas_dsn.create_text(20, y0 + 35, text=f"Kelas: {item['kelas']} | Berkas: {item['tugas']}", font=("Segoe UI", 8), fill="#475569", anchor=tk.W)
                
                self.canvas_dsn.create_text(card_width - 15, y0 + 15, text=f"⏱️ {item['jam']}", font=("Segoe UI", 8), fill="#94a3b8", anchor=tk.E)

        self.history_container.delete("all")
        if not self.graded_assignments:
            self.history_container.create_text(150, 150, text="📭 Belum ada tugas yang dinilai", font=("Segoe UI", 9, "italic"), fill="#94a3b8")
        else:
            for index, item in enumerate(self.graded_assignments):
                y0 = 10 + (index * 68)
                y1 = y0 + 58
                self.history_container.create_rectangle(5, y0, 295, y1, fill=item['bg_color'], outline=item['border_color'], width=1.5)
                self.history_container.create_text(15, y0 + 15, text=f"{item['npm']} - {item['nama']}", font=("Segoe UI", 9, "bold"), fill="#1e293b", anchor=tk.W)
                self.history_container.create_text(15, y0 + 35, text=f"Kelas: {item['kelas']} | Berkas: {item['tugas']}", font=("Segoe UI", 8), fill="#475569", anchor=tk.W)
                self.history_container.create_text(280, y0 + 15, text=f"Skor: {item['score_num']} ({item['grade_letter']})", font=("Segoe UI", 8, "bold"), fill=item['border_color'], anchor=tk.E)

    def handle_push(self):

        npm = self.entry_npm.get().strip()
        nama = self.entry_nama.get().strip()
        prodi = self.entry_prodi.get().strip()
        kelas = self.entry_kelas.get().strip()
        tugas = self.entry_tugas.get().strip()

        if not npm or not nama or not kelas or not tugas:
            messagebox.showwarning("Peringatan", "Semua data input wajib diisi!")
            return

        if self.stack.push(nama, npm, kelas, tugas, prodi):
            self.entry_npm.delete(0, tk.END)
            self.entry_nama.delete(0, tk.END)
            self.entry_prodi.delete(0, tk.END)
            self.entry_kelas.delete(0, tk.END)
            self.entry_tugas.config(state="normal")
            self.entry_tugas.delete(0, tk.END)
            self.entry_tugas.config(state="readonly")
            
            self.update_student_view()
            self.update_lecturer_view()
            messagebox.showinfo("Sukses Push", f"Tugas '{nama}' sukses disimpan ke Firebase!")

    def handle_pop(self):
        if self.stack.is_empty():
            messagebox.showerror("Underflow Error", "Meja kosong! Tidak ada tugas di cloud server.")
            return

        nilai_raw = self.entry_nilai_dosen.get().strip()
        if not nilai_raw:
            messagebox.showwarning("Nilai Kosong", "Dosen wajib mengisi kolom Nilai sebelum melakukan POP!")
            return

        try:
            nilai_int = int(nilai_raw)
            if not (0 <= nilai_int <= 100): raise ValueError
        except ValueError:
            messagebox.showerror("Input Salah", "Nilai harus berupa angka 0 hingga 100!")
            return

        grade_letter, border_clr, bg_clr = self.get_grade_info(nilai_int)
        tugas_terpop = self.stack.pop()
        
        if tugas_terpop:
            tugas_terpop.update({
                "nilai": f"{nilai_int} ({grade_letter})", 
                "grade_letter": grade_letter, 
                "score_num": nilai_int, 
                "border_color": border_clr, 
                "bg_color": bg_clr
            })
            self.graded_assignments.insert(0, tugas_terpop)
            self.entry_nilai_dosen.delete(0, tk.END)
            
            self.update_student_view()
            self.update_lecturer_view()
            messagebox.showinfo("Cloud Pop Sukses", f"Tugas '{tugas_terpop['nama']}' berhasil dinilai!")

    def handle_clear(self):
        if messagebox.askyesno("Konfirmasi", "Apakah Anda yakin ingin menghapus seluruh data pada node Firebase?"):
            if self.stack.clear_stack():
                self.graded_assignments.clear()  
                self.update_student_view()
                self.update_lecturer_view()
                messagebox.showinfo("Sukses", "Seluruh data di cloud server Firebase berhasil dikosongkan.")


# 5. INITIALIZATION RUNNER
if __name__ == "__main__":
    root = tk.Tk()
    app = AssignmentApp(root)
    root.mainloop()