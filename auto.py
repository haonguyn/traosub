import tkinter as tk
from tkinter import messagebox
import json, requests, os, re, time


def __init_app():
    load_token()
    load_cookie()
    load_info()


def exit_app():
    root.destroy()


def show_frame(frame):
    frame.tkraise()


def log_message(message: str):
    run_text.insert(tk.END, message + "\n")
    run_text.see(tk.END)
    run_text.update_idletasks()


def run_coint():
    selected = ""
    time_action = 10000
    time_job = 30000

    if ck_reaction.get() == 1:
        selected = "facebook_reaction"
        time_action = 10000
    if ck_reaction2.get() == 1:
        selected = "facebook_reaction2"
        time_action = 10000
    if ck_reactioncmt.get() == 1:
        selected = "facebook_reactioncmt"
        time_action = 20000
    if ck_share.get() == 1:
        selected = "facebook_share"
        time_action = 60000
    if ck_follow.get() == 1:
        selected = "facebook_follow"
        time_action = 20000
    if ck_page.get() == 1:
        selected = "facebook_page"
        time_action = 30000

    if not selected:
        messagebox.showwarning("Thông báo", "Bạn chưa chọn bất cứ mục nào!")
        return
    # messagebox.showinfo("info",selected)

    cookies = load_cookie()
    TDS_token = load_token()

    cookie_list = []
    for item in cookies:
        cookie_list.append(item["cookie"])

    type = f"{selected}_cache"
    for item in cookie_list:
        match = re.search(r"c_user=([^;]+)", item)
        if match:
            c_user = match.group(1)
            url = f"https://traodoisub.com/api/?fields=run&id={c_user}&access_token={TDS_token}"  # cauhinh
            response = requests.get(url).json()
            if response.get("success") == 200:
                log_message(response["data"]["msg"])
                log_message(
                    "Đang tiến hành lấy jobs......................"
                )

                url = f"https://traodoisub.com/api/?fields={selected}&access_token={TDS_token}&type=ALL"  # layjob
                response = requests.get(url).json()
                if "error" not in response:
                    cache = response["cache"]
                    jobs = response["data"]

                    for job in jobs:
                        type_job = job["type"]
                        link = f"https://facebook.com/{job["id"]}"
                        # thục hiện làm việc ở đây
                        if True:#gui duyet
                            url = f"https://traodoisub.com/api/coin/?type={type}&id={job["code"]}&access_token={TDS_token}"
                            response = requests.get(url).json()

                            if(response["error"] == ""):
                                id = ""
                                if(selected not in ("facebook_follow","facebook_page")):
                                    id = job["code"]
                                else:
                                    id = "facebook_api"

                                geturl = f"https://traodoisub.com/api/coin/?type={selected}&id={id}&access_token={TDS_token}"
                                rejon = requests.get(geturl).json()
                                if rejon.get("success") == 200:
                                    log_message("Hoàn thành nhiệm vụ "+rejon["data"]["msg"])

                else:
                    if response["countdown"]:
                        log_message(f"{response["error"]} {response["countdown"]}s")
                        # time.sleep(response["countdown"])
                        continue
                    err = response["error"]
                    messagebox.showerror("❌ Lỗi:", str(err))
                    return
            else:
                err = response["error"]
                messagebox.showerror("❌ Lỗi:", str(err))
                return


def save_cookie():
    data = cookie_text.get("1.0", tk.END).strip()
    if not data:
        messagebox.showwarning("Cảnh báo", "⚠️ Bạn chưa nhập cookie!")
        return
    cookies = [{"cookie": line.strip()} for line in data.splitlines() if line.strip()]

    with open("cookies.json", "w", encoding="utf-8") as f:
        json.dump(cookies, f, indent=4, ensure_ascii=False)

    messagebox.showinfo("Thông báo", "✅ Lưu cookies thành công!")


def load_cookie():
    if os.path.exists("cookies.json"):
        try:
            with open("cookies.json", "r", encoding="utf-8") as f:
                cookies = json.load(f)

            cookie_text.delete("1.0", tk.END)
        except Exception as e:
            return
        cookie_text.insert(
            tk.END, "\n".join(item.get("cookie", "") for item in cookies)
        )
        return cookies


def save_token():
    data = token_text.get("1.0", tk.END).strip()
    data = "".join(data.split())
    if not data:
        messagebox.showwarning("Cảnh báo", "⚠️ Bạn chưa nhập token!")
        return

    url = f"https://traodoisub.com/api/?fields=profile&access_token={data}"
    response = requests.get(url).json()
    if response.get("success") != 200:
        messagebox.showwarning("Cảnh báo", "Token không tồn tại!")
        return

    token = {"token": data}

    with open("token.json", "w", encoding="utf-8") as f:
        json.dump(token, f, indent=4, ensure_ascii=False)

    load_info()
    messagebox.showinfo("Thông báo", "✅ Lưu token thành công!")


def load_token():
    if os.path.exists("token.json"):
        try:
            with open("token.json", "r", encoding="utf-8") as f:
                token = json.load(f)

            token_text.delete("1.0", tk.END)
        except Exception as e:
            return
        token_text.insert(tk.END, token.get("token", ""))
        return token["token"]


def load_info():
    TDS_token = load_token()
    url = f"https://traodoisub.com/api/?fields=profile&access_token={TDS_token}"
    response = requests.get(url)
    data = response.json()
    if data.get("success") == 200:
        user = data["data"]["user"]
        xu = data["data"]["xu"]
        xudie = data["data"]["xudie"]
        lbl_user.config(text=f"{user}")
        lbl_xu.config(text=f"Xu hiện tại: {xu}")
        lbl_xudie.config(text=f"Xu die: {xudie}")
    else:
        err = data["error"]
        messagebox.showerror("❌ Lỗi:", str(err))
        return


root = tk.Tk()
root.title("Tool API Tkinter")
root.geometry("450x500")
root.resizable(False, False)

# Container
container = tk.Frame(root)
container.pack(fill="both", expand=True)

# run
page_run = tk.Frame(container, bg="lightgreen")
page_run.place(relwidth=1, relheight=1)

run_lable = tk.Frame(page_run, bg="lightgreen")
run_lable.pack()

lbl_user = tk.Label(run_lable, bg="lightgreen")
lbl_user.pack(side="left", padx=20)
lbl_xu = tk.Label(run_lable, bg="lightgreen")
lbl_xu.pack(side="left", padx=20)
lbl_xudie = tk.Label(run_lable, bg="lightgreen")
lbl_xudie.pack(side="left", padx=20)

run_ck = tk.Frame(page_run)
run_ck.pack(pady=10)

ck_reaction = tk.IntVar()
ck_reaction2 = tk.IntVar()
ck_reactioncmt = tk.IntVar()
ck_share = tk.IntVar()
ck_follow = tk.IntVar()
ck_page = tk.IntVar()

tk.Checkbutton(run_ck, text="like", variable=ck_reaction).pack(side="left", padx=3)
tk.Checkbutton(run_ck, text="wow, tym, haha..", variable=ck_reaction2).pack(
    side="left", padx=3
)
tk.Checkbutton(run_ck, text="cmt", variable=ck_reactioncmt).pack(side="left", padx=3)
tk.Checkbutton(run_ck, text="share", variable=ck_share).pack(side="left", padx=3)
tk.Checkbutton(run_ck, text="follow", variable=ck_follow).pack(side="left", padx=3)
tk.Checkbutton(run_ck, text="page", variable=ck_page).pack(side="left", padx=3)

tk.Button(page_run, text="Chạy xu", command=run_coint).pack(pady=5)

text_frame_run = tk.Frame(page_run)
text_frame_run.pack(expand=True, fill="both", padx=10, pady=5)

scrollbar = tk.Scrollbar(text_frame_run)
scrollbar.pack(side="right", fill="y")

run_text = tk.Text(
    text_frame_run,
    wrap="word",
    yscrollcommand=scrollbar.set,
    bg="black",
    fg="white",
    font=("Lucida Console", 11),
)
run_text.pack(side="left", expand=True, fill="both")

scrollbar.config(command=run_text.yview)
# token
page_token = tk.Frame(container)
page_token.place(relwidth=1, relheight=1)
tk.Label(page_token, text="Nhập Token tại đây:", font=("Arial", 12)).pack(pady=10)

tk.Button(page_token, text="Lưu", command=save_token).pack(pady=5)

token_text = tk.Text(page_token, height=1, width=53)
token_text.pack(pady=10)

# cookie
page_cookie = tk.Frame(container)
page_cookie.place(relwidth=1, relheight=1)
tk.Label(page_cookie, text="Nhập Cookie tại đây:", font=("Arial", 12)).pack(pady=10)

tk.Button(page_cookie, text="Lưu", command=save_cookie).pack(pady=5)

text_frame_cookie = tk.Frame(page_cookie)
text_frame_cookie.pack(expand=True, fill="both", padx=10, pady=5)

scrollbar = tk.Scrollbar(text_frame_cookie)
scrollbar.pack(side="right", fill="y")

cookie_text = tk.Text(text_frame_cookie, wrap="word", yscrollcommand=scrollbar.set)
cookie_text.pack(side="left", expand=True, fill="both")

scrollbar.config(command=cookie_text.yview)

# ----- Menu -----
menubar = tk.Menu(root)
menubar.add_cascade(label="Run", command=lambda: show_frame(page_run))
menubar.add_cascade(label="Cấu hình Token", command=lambda: show_frame(page_token))
menubar.add_cascade(label="Cookie", command=lambda: show_frame(page_cookie))
root.config(menu=menubar)

show_frame(page_run)

__init_app()
root.mainloop()
