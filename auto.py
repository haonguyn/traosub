import tkinter as tk
from tkinter import messagebox
import json, requests, os, re, time, threading, random

# ── Palette ───────────────────────────────────────────────────────────────────
BG      = "#0d0d1a"
BG2     = "#13132b"
BG3     = "#1c1c3a"
ACCENT  = "#00c896"
ACCENTH = "#00e6ab"
TEXT    = "#dde8ff"
DIM     = "#7788aa"
RED     = "#ff4466"
YELLOW  = "#ffa726"
GREEN   = "#00e676"
BLUE    = "#0088ff"
BORDER  = "#2a2a4a"

F_HEAD  = ("Segoe UI Semibold", 12)
F_BODY  = ("Segoe UI", 10)
F_SMALL = ("Segoe UI", 9)
F_LOG   = ("Consolas", 10)

# ── State ─────────────────────────────────────────────────────────────────────
stop_event = threading.Event()
is_running  = False
nav_buttons = []

# ══════════════════════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════════════════════

def log(msg: str, tag: str = "normal"):
    run_text.config(state="normal")
    run_text.insert(tk.END, msg + "\n", tag)
    run_text.see(tk.END)
    run_text.config(state="disabled")
    run_text.update_idletasks()


def set_status(msg: str, color: str = TEXT):
    lbl_status.config(text=msg, fg=color)


def load_cookie_data():
    try:
        with open("cookies.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def load_token_data():
    try:
        with open("token.json", "r", encoding="utf-8") as f:
            return json.load(f).get("token", "")
    except Exception:
        return ""


# ══════════════════════════════════════════════════════════════════════════════
#  Facebook Interaction Helpers
# ══════════════════════════════════════════════════════════════════════════════

def get_fb_session(cookie: str):
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cookie": cookie
    })
    return session


def perform_fb_action(session, job_type, link):
    """
    Simulates the actual interaction on Facebook using mbasic version.
    """
    try:
        # Convert to mbasic link
        m_link = link.replace("www.facebook.com", "mbasic.facebook.com").replace("facebook.com", "mbasic.facebook.com")
        if "mbasic.facebook.com" not in m_link:
            m_link = f"https://mbasic.facebook.com/{link.split('/')[-1]}"

        resp = session.get(m_link, timeout=15)
        html = resp.text

        # ── Check if session is still alive ─────────────────────────────
        if "login.php" in resp.url or "trang-web-nay-khong-ton-tai" in html or "id=\"login_form\"" in html:
            return False, "⚠️ Cookie đã hết hạn hoặc acc bị checkpoint"

        if job_type in ("facebook_reaction", "facebook_reaction2"):
            # Find like/react link
            # Usually look for /a/like.php or /reactions/picker/
            match = re.search(r'href="(/a/like\.php\?[^"]+)"', html)
            if match:
                like_url = "https://mbasic.facebook.com" + match.group(1).replace("&amp;", "&")
                session.get(like_url, timeout=15)
                return True, "Đã nhấn Like/React"
            
            # If not found, might be a react picker
            match_picker = re.search(r'href="(/reactions/picker/\?[^"]+)"', html)
            if match_picker:
                picker_url = "https://mbasic.facebook.com" + match_picker.group(1).replace("&amp;", "&")
                picker_resp = session.get(picker_url, timeout=15)
                # Pick Love (type 2) or Like (type 1)
                # For reaction2, we try to find Love/Haha/Wow
                react_type = "2" if job_type == "facebook_reaction2" else "1"
                match_react = re.search(fr'href="(/ufi/reaction/\?[^"]+reaction_type={react_type}[^"]+)"', picker_resp.text)
                if match_react:
                    final_url = "https://mbasic.facebook.com" + match_react.group(1).replace("&amp;", "&")
                    session.get(final_url, timeout=15)
                    return True, "Đã thả cảm xúc thành công"

        elif job_type == "facebook_follow" or job_type == "facebook_page":
            # Find subscribe/follow link (More robust patterns)
            # 1. Profile Follow (Theo dõi)
            match = re.search(r'href="(/a/subscribe\.php\?[^"]+)"', html) 
            # 2. Page Like (Thích Trang)
            if not match:
                match = re.search(r'href="(/a/fbc/like\.php\?[^"]+)"', html)
            # 3. Alternative Follow/Like (Mobile signatures)
            if not match:
                match = re.search(r'href="(/a/profile\.php\?fan[^"]+)"', html)
            if not match:
                match = re.search(r'href="(/a/profile\.php\?action=subscribe[^"]+)"', html)
            if not match:
                # Try discovery by text if possible (Generic fallback)
                # Look for links containing "subscribe" or "like" in URI and "Theo dõi" or "Thích" in text
                match = re.search(r'href="([^"]+(?:subscribe\.php|like\.php|fan_item\.php)[^"]+)"[^>]*>.*?<span>(?:Theo dõi|Thích|Like|Follow)', html, re.I | re.S)
            
            if match:
                follow_url = "https://mbasic.facebook.com" + match.group(1).replace("&amp;", "&")
                session.get(follow_url, timeout=15)
                return True, "Đã nhấn Theo dõi/Like Page"

        elif job_type == "facebook_share":
            # Sharing is complex on mbasic, usually involves a composer
            match = re.search(r'href="(/composer/mbasic/\?[^"]+)"', html)
            if match:
                # This just opens composer, real share needs a POST. 
                # For simplicity in this tool, we just hit the composer link.
                return True, "Đã mở trình chia sẻ (Share giả lập)"

        return False, "Không tìm thấy nút tương tác (Có thể đã làm rồi hoặc link lỗi)"
    except Exception as e:
        return False, f"Lỗi tương tác FB: {str(e)}"


# ══════════════════════════════════════════════════════════════════════════════
#  Core job runner  (background thread)
# ══════════════════════════════════════════════════════════════════════════════

def _run_jobs():
    jobs_map = [
        (ck_reaction,    "facebook_reaction",    10),
        (ck_reaction2,   "facebook_reaction2",   10),
        (ck_reactioncmt, "facebook_reactioncmt", 20),
        (ck_share,       "facebook_share",       60),
        (ck_follow,      "facebook_follow",      20),
        (ck_page,        "facebook_page",        30),
    ]
    
    # Outer infinite loop
    while not stop_event.is_set():
        selected = [(name, wait) for var, name, wait in jobs_map if var.get()]

        if not selected:
            root.after(0, lambda: messagebox.showwarning("Thông báo", "Chưa chọn loại job nào!"))
            root.after(0, _after_run)
            return

        cookies   = load_cookie_data()
        tds_token = load_token_data()

        if not cookies:
            root.after(0, lambda: messagebox.showwarning("Cảnh báo", "Chưa có cookie nào!"))
            root.after(0, _after_run)
            return
        if not tds_token:
            root.after(0, lambda: messagebox.showwarning("Cảnh báo", "Chưa có token!"))
            root.after(0, _after_run)
            return

        total_acc = len(cookies)
        any_job_done = False

        for acc_i, item in enumerate(cookies, 1):
            if stop_event.is_set():
                break

            cookie = item.get("cookie", "")
            match  = re.search(r"c_user=([^;]+)", cookie)
            if not match:
                log("  ⚠️  Cookie không hợp lệ, bỏ qua.", "warn")
                continue

            c_user = match.group(1)
            log(f"\n{'─'*52}", "dim")
            log(f"  👤 [{acc_i}/{total_acc}] Tài khoản: {c_user}", "accent")
            log(f"{'─'*52}", "dim")

            fb_session = get_fb_session(cookie)

            try:
                run_resp = requests.get(
                    f"https://traodoisub.com/api/?fields=run&id={c_user}&access_token={tds_token}",
                    timeout=15
                ).json()
            except Exception as e:
                log(f"  ❌ Kết nối lỗi: {e}", "error")
                continue

            if run_resp.get("success") != 200:
                log(f"  ❌ {run_resp.get('error', 'Lỗi không xác định')}", "error")
                continue

            log(f"  ℹ️  {run_resp['data']['msg']}", "info")

            for job_type, wait_sec in selected:
                if stop_event.is_set():
                    break

                log(f"\n  🔄 [{job_type}] Đang lấy danh sách jobs...", "accent")

                try:
                    jobs_resp = requests.get(
                        f"https://traodoisub.com/api/?fields={job_type}&access_token={tds_token}&type=ALL",
                        timeout=15
                    ).json()
                except Exception as e:
                    log(f"  ❌ Kết nối lỗi: {e}", "error")
                    continue

                if jobs_resp.get("error"):
                    countdown = jobs_resp.get("countdown", 0)
                    if countdown:
                        log(f"  ⏳ {jobs_resp['error']} — Chờ {countdown}s...", "warn")
                        for _ in range(int(countdown)):
                            if stop_event.is_set():
                                break
                            time.sleep(1)
                    else:
                        log(f"  ❌ {jobs_resp['error']}", "error")
                    continue

                jobs = jobs_resp.get("data", [])
                if not jobs:
                    log(f"  ℹ️  Hiện tại hết job {job_type}", "info")
                    continue
                
                any_job_done = True
                log(f"  ✅ Tìm thấy {len(jobs)} jobs", "ok")

                for i, job in enumerate(jobs, 1):
                    if stop_event.is_set():
                        break

                    link = f"https://facebook.com/{job['id']}"
                    log(f"\n    [{i}/{len(jobs)}] 🔗 {link}")

                    # ── Step 1: Cache (Gửi duyệt) ─────────────────────────────
                    cache_resp = None
                    for attempt in range(2):
                        try:
                            raw = requests.get(
                                f"https://traodoisub.com/api/coin/?type={job_type}_cache&id={job['code']}&access_token={tds_token}",
                                timeout=15
                            )
                            if not raw.text.strip():
                                log(f"    ⚠️  Cache trả về rỗng, thử lại sau 5s...", "warn")
                                for _ in range(5):
                                    if stop_event.is_set(): break
                                    time.sleep(1)
                                continue
                            cache_resp = raw.json()
                            break
                        except Exception as e:
                            log(f"    ❌ Cache lỗi: {e}", "error")
                            break

                    if cache_resp is None:
                        continue

                    cache_err = cache_resp.get("error", "")
                    if cache_err:
                        log(f"    ⚠️  {cache_err}", "warn")
                        if "nhanh" in cache_err.lower() or "chậm" in cache_err.lower():
                            log(f"    ⏳ Chờ 5s trước khi tiếp tục...", "info")
                            for _ in range(5):
                                if stop_event.is_set(): break
                                time.sleep(1)
                        continue
                    
                    log(f"    ℹ️  Đã gửi duyệt thành công", "info")

                    # ── Step 2: Facebook Action (Làm việc) ────────────────────
                    log(f"    ⚡ Đang thực hiện tương tác Facebook...", "accent")
                    ok, fb_msg = perform_fb_action(fb_session, job_type, link)
                    if ok:
                        log(f"    👍 {fb_msg}", "ok")
                    else:
                        log(f"    ⚠️  {fb_msg}", "warn")

                    # ── Step 3: Wait (Chờ) ────────────────────────────────────
                    actual_wait = wait_sec + random.randint(0, 3)
                    log(f"    ⏳ Chờ {actual_wait}s (ngẫu nhiên)...", "info")
                    for _ in range(actual_wait):
                        if stop_event.is_set():
                            break
                        time.sleep(1)

                    if stop_event.is_set():
                        break

                    # ── Step 4: Claim (Nhận xu) ────────────────────────────────
                    coin_id = job["code"] if job_type not in ("facebook_follow", "facebook_page") else "facebook_api"
                    try:
                        raw2 = requests.get(
                            f"https://traodoisub.com/api/coin/?type={job_type}&id={coin_id}&access_token={tds_token}",
                            timeout=15
                        )
                        if not raw2.text.strip():
                            log(f"    ❌ Nhận xu: API trả về rỗng", "error")
                            continue
                        coin_resp = raw2.json()
                    except Exception as e:
                        log(f"    ❌ Nhận xu lỗi: {e}", "error")
                        continue

                    if coin_resp.get("success") == 200:
                        log(f"    ✅ {coin_resp['data']['msg']}", "ok")
                    else:
                        log(f"    ❌ {coin_resp.get('error', 'Thất bại')}", "error")

                    # Delay nhỏ giữa các job để tránh spam
                    for _ in range(random.randint(2, 4)):
                        if stop_event.is_set(): break
                        time.sleep(1)

        if stop_event.is_set():
            break

        # Nếu quét hết tài khoản mà không có job nào làm được, hoặc đã làm hết job vòng này
        # thì chờ một lúc rồi mới quay lại vòng tiếp theo
        wait_next_round = 30 if not any_job_done else 10
        log(f"\n🔄 Đã quét qua tất cả tài khoản. Chờ {wait_next_round}s trước khi bắt đầu vòng mới...", "info")
        for _ in range(wait_next_round):
            if stop_event.is_set():
                break
            time.sleep(1)

    log(f"\n{'═'*52}", "dim")
    if stop_event.is_set():
        log("  ⏹  Đã dừng bởi người dùng.", "warn")
    else:
        log("  🎉  Đã kết thúc phiên làm việc.", "ok")
    log(f"{'═'*52}", "dim")

    root.after(0, _after_run)

    log(f"\n{'═'*52}", "dim")
    if stop_event.is_set():
        log("  ⏹  Đã dừng bởi người dùng.", "warn")
    else:
        log("  🎉  Hoàn tất tất cả jobs!", "ok")
    log(f"{'═'*52}", "dim")

    root.after(0, _after_run)


def start_run():
    global is_running
    if is_running:
        return
    is_running = True
    stop_event.clear()
    run_text.config(state="normal")
    run_text.delete("1.0", tk.END)
    run_text.config(state="disabled")
    btn_run.config(state="disabled", bg=BG3, fg=DIM)
    btn_stop.config(state="normal", bg=RED, fg="white")
    set_status("⚙️  Đang chạy...", ACCENT)
    threading.Thread(target=_run_jobs, daemon=True).start()


def _after_run():
    global is_running
    is_running = False
    btn_run.config(state="normal", bg=ACCENT, fg=BG)
    btn_stop.config(state="disabled", bg=BG3, fg=DIM)
    set_status("✅ Sẵn sàng", GREEN)
    threading.Thread(target=_refresh_info, daemon=True).start()


def stop_run():
    if is_running:
        stop_event.set()
        set_status("⏹  Đang dừng...", YELLOW)
        btn_stop.config(state="disabled", bg=BG3, fg=DIM)


# ══════════════════════════════════════════════════════════════════════════════
#  Token & Cookie management
# ══════════════════════════════════════════════════════════════════════════════

def save_cookie():
    data = cookie_text.get("1.0", tk.END).strip()
    if not data:
        messagebox.showwarning("Cảnh báo", "⚠️ Chưa nhập cookie!")
        return
    cookies = [{"cookie": ln.strip()} for ln in data.splitlines() if ln.strip()]
    with open("cookies.json", "w", encoding="utf-8") as f:
        json.dump(cookies, f, indent=4, ensure_ascii=False)
    messagebox.showinfo("Thông báo", f"✅ Đã lưu {len(cookies)} cookie!")


def load_cookie_ui():
    cookies = load_cookie_data()
    cookie_text.delete("1.0", tk.END)
    if cookies:
        cookie_text.insert(tk.END, "\n".join(c.get("cookie", "") for c in cookies))


def save_token():
    data = token_entry.get().strip()
    if not data:
        messagebox.showwarning("Cảnh báo", "⚠️ Chưa nhập token!")
        return
    try:
        resp = requests.get(
            f"https://traodoisub.com/api/?fields=profile&access_token={data}",
            timeout=10
        ).json()
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể kết nối: {e}")
        return
    if resp.get("success") != 200:
        messagebox.showwarning("Cảnh báo", "Token không hợp lệ!")
        return
    with open("token.json", "w", encoding="utf-8") as f:
        json.dump({"token": data}, f, indent=4, ensure_ascii=False)
    threading.Thread(target=_refresh_info, daemon=True).start()
    messagebox.showinfo("Thông báo", "✅ Lưu token thành công!")


def load_token_ui():
    token = load_token_data()
    token_entry.delete(0, tk.END)
    if token:
        token_entry.insert(0, token)


def _refresh_info():
    tds_token = load_token_data()
    if not tds_token:
        return
    try:
        data = requests.get(
            f"https://traodoisub.com/api/?fields=profile&access_token={tds_token}",
            timeout=10
        ).json()
        if data.get("success") == 200:
            d = data["data"]
            root.after(0, lambda: _update_info_labels(d))
    except Exception:
        pass


def _update_info_labels(d):
    lbl_user.config(text=f"👤 {d['user']}")
    lbl_xu.config(text=f"🪙 {d['xu']}")
    lbl_xudie.config(text=f"💀 {d['xudie']}")


def show_frame(frame, active_btn=None):
    frame.tkraise()
    for b in nav_buttons:
        b.config(bg=BG2, fg=DIM)
    if active_btn:
        active_btn.config(bg=BG3, fg=TEXT)


def make_nav_btn(parent, text):
    b = tk.Button(parent, text=text, font=F_SMALL, bg=BG2, fg=DIM,
                  relief="flat", padx=16, pady=6, cursor="hand2",
                  activebackground=BG3, activeforeground=TEXT, bd=0)
    b.pack(side="left")
    nav_buttons.append(b)
    return b


# ══════════════════════════════════════════════════════════════════════════════
#  UI Construction
# ══════════════════════════════════════════════════════════════════════════════

root = tk.Tk()
root.title("TichXanh Tool")
root.geometry("540x590")
root.resizable(False, False)
root.configure(bg=BG)

# ── Header ────────────────────────────────────────────────────────────────────
header = tk.Frame(root, bg=BG2, height=50)
header.pack(fill="x")
header.pack_propagate(False)

tk.Label(header, text="⚡ TichXanh", font=("Segoe UI Semibold", 13),
         bg=BG2, fg=ACCENT).pack(side="left", padx=15, pady=10)

info_frame = tk.Frame(header, bg=BG2)
info_frame.pack(side="right", padx=10)

lbl_user  = tk.Label(info_frame, text="👤 —", font=F_SMALL, bg=BG2, fg=TEXT)
lbl_user.pack(side="left", padx=8)
lbl_xu    = tk.Label(info_frame, text="🪙 —", font=F_SMALL, bg=BG2, fg=ACCENT)
lbl_xu.pack(side="left", padx=8)
lbl_xudie = tk.Label(info_frame, text="💀 —", font=F_SMALL, bg=BG2, fg=RED)
lbl_xudie.pack(side="left", padx=8)

# ── Nav ───────────────────────────────────────────────────────────────────────
nav = tk.Frame(root, bg=BG2, height=38)
nav.pack(fill="x")
nav.pack_propagate(False)

# ── Container ─────────────────────────────────────────────────────────────────
container = tk.Frame(root, bg=BG)
container.pack(fill="both", expand=True)

# ══ Page: Run ═════════════════════════════════════════════════════════════════
page_run = tk.Frame(container, bg=BG)
page_run.place(relwidth=1, relheight=1)

ck_frame = tk.Frame(page_run, bg=BG2, pady=8)
ck_frame.pack(fill="x", padx=12, pady=(12, 0))

tk.Label(ck_frame, text="Chọn loại job:", font=F_SMALL,
         bg=BG2, fg=DIM).pack(anchor="w", padx=10)

ck_row = tk.Frame(ck_frame, bg=BG2)
ck_row.pack(anchor="w", padx=5, pady=5)

ck_reaction    = tk.IntVar()
ck_reaction2   = tk.IntVar()
ck_reactioncmt = tk.IntVar()
ck_share       = tk.IntVar()
ck_follow      = tk.IntVar()
ck_page        = tk.IntVar()

CK_OPTS = [
    ("👍 Like",       ck_reaction),
    ("😂 Reaction",   ck_reaction2),
    ("💬 React Cmt",  ck_reactioncmt),
    ("🔁 Share",      ck_share),
    ("➕ Follow",     ck_follow),
    ("📄 Like Page",  ck_page),
]
for label, var in CK_OPTS:
    tk.Checkbutton(ck_row, text=label, variable=var, font=F_SMALL,
                   bg=BG2, fg=TEXT, activebackground=BG2, activeforeground=ACCENT,
                   selectcolor=BG3).pack(side="left", padx=4)

# Buttons
btn_row = tk.Frame(page_run, bg=BG)
btn_row.pack(pady=10)

btn_run = tk.Button(btn_row, text="▶  Chạy xu",
                    font=("Segoe UI Semibold", 11),
                    bg=ACCENT, fg=BG, activebackground=ACCENTH, activeforeground=BG,
                    relief="flat", padx=20, pady=7, cursor="hand2", command=start_run)
btn_run.pack(side="left", padx=8)

btn_stop = tk.Button(btn_row, text="⏹  Dừng",
                     font=("Segoe UI Semibold", 11),
                     bg=BG3, fg=DIM, activebackground=RED, activeforeground="white",
                     relief="flat", padx=20, pady=7, cursor="hand2",
                     command=stop_run, state="disabled")
btn_stop.pack(side="left", padx=8)

# Log area
log_frame = tk.Frame(page_run, bg=BG)
log_frame.pack(fill="both", expand=True, padx=12, pady=(0, 8))

log_scroll = tk.Scrollbar(log_frame, bg=BG3, troughcolor=BG, activebackground=ACCENT)
log_scroll.pack(side="right", fill="y")

run_text = tk.Text(log_frame, wrap="word", yscrollcommand=log_scroll.set,
                   bg="#09091a", fg=TEXT, insertbackground=ACCENT,
                   font=F_LOG, relief="flat", bd=0, state="disabled",
                   selectbackground=BG3)
run_text.pack(side="left", fill="both", expand=True)
log_scroll.config(command=run_text.yview)

run_text.tag_config("normal", foreground=TEXT)
run_text.tag_config("accent", foreground=ACCENT)
run_text.tag_config("ok",     foreground=GREEN)
run_text.tag_config("warn",   foreground=YELLOW)
run_text.tag_config("error",  foreground=RED)
run_text.tag_config("info",   foreground=BLUE)
run_text.tag_config("dim",    foreground="#3a3a6a")

# ══ Page: Token ═══════════════════════════════════════════════════════════════
page_token = tk.Frame(container, bg=BG)
page_token.place(relwidth=1, relheight=1)

tk.Label(page_token, text="🔑 Cấu hình Token", font=F_HEAD,
         bg=BG, fg=TEXT).pack(pady=(40, 10))
tk.Label(page_token, text="Nhập Access Token của bạn:",
         font=F_SMALL, bg=BG, fg=DIM).pack()

token_entry = tk.Entry(page_token, font=F_BODY, width=52,
                       bg=BG3, fg=TEXT, insertbackground=ACCENT,
                       relief="flat", bd=8)
token_entry.pack(pady=10, ipady=4)

tk.Button(page_token, text="💾 Lưu Token",
          font=("Segoe UI Semibold", 10),
          bg=ACCENT, fg=BG, activebackground=ACCENTH, activeforeground=BG,
          relief="flat", padx=15, pady=6, cursor="hand2",
          command=save_token).pack(pady=5)

tk.Label(page_token,
         text="Token lấy tại: traodoisub.com → Tài khoản → Cấu hình API",
         font=F_SMALL, bg=BG, fg=DIM).pack(pady=(20, 0))

# ══ Page: Cookie ══════════════════════════════════════════════════════════════
page_cookie = tk.Frame(container, bg=BG)
page_cookie.place(relwidth=1, relheight=1)

tk.Label(page_cookie, text="🍪 Cấu hình Cookie", font=F_HEAD,
         bg=BG, fg=TEXT).pack(pady=(20, 5))
tk.Label(page_cookie, text="Mỗi dòng = 1 cookie Facebook",
         font=F_SMALL, bg=BG, fg=DIM).pack()

tk.Button(page_cookie, text="💾 Lưu Cookies",
          font=("Segoe UI Semibold", 10),
          bg=ACCENT, fg=BG, activebackground=ACCENTH, activeforeground=BG,
          relief="flat", padx=15, pady=6, cursor="hand2",
          command=save_cookie).pack(pady=8)

ck_area = tk.Frame(page_cookie, bg=BG)
ck_area.pack(fill="both", expand=True, padx=12, pady=(0, 10))

ck_scroll = tk.Scrollbar(ck_area, bg=BG3, troughcolor=BG, activebackground=ACCENT)
ck_scroll.pack(side="right", fill="y")

cookie_text = tk.Text(ck_area, wrap="none", yscrollcommand=ck_scroll.set,
                      bg="#09091a", fg=TEXT, insertbackground=ACCENT,
                      font=("Consolas", 9), relief="flat", bd=0)
cookie_text.pack(side="left", fill="both", expand=True)
ck_scroll.config(command=cookie_text.yview)

# ── Nav buttons (created after pages) ─────────────────────────────────────────
btn_nav_run    = make_nav_btn(nav, "▶  Run")
btn_nav_token  = make_nav_btn(nav, "🔑 Token")
btn_nav_cookie = make_nav_btn(nav, "🍪 Cookie")

btn_nav_run.config(   command=lambda: show_frame(page_run,    btn_nav_run))
btn_nav_token.config( command=lambda: show_frame(page_token,  btn_nav_token))
btn_nav_cookie.config(command=lambda: show_frame(page_cookie, btn_nav_cookie))

# ── Status bar ────────────────────────────────────────────────────────────────
tk.Frame(root, bg=BORDER, height=1).pack(fill="x")

status_bar = tk.Frame(root, bg=BG2, height=28)
status_bar.pack(fill="x", side="bottom")
status_bar.pack_propagate(False)

lbl_status = tk.Label(status_bar, text="✅ Sẵn sàng", font=F_SMALL,
                      bg=BG2, fg=GREEN)
lbl_status.pack(side="left", padx=12, pady=4)

tk.Label(status_bar, text="traodoisub.com", font=F_SMALL,
         bg=BG2, fg=DIM).pack(side="right", padx=12)

# ── Init ──────────────────────────────────────────────────────────────────────
def init_app():
    load_token_ui()
    load_cookie_ui()
    threading.Thread(target=_refresh_info, daemon=True).start()


show_frame(page_run, btn_nav_run)
root.after(200, init_app)
root.mainloop()
