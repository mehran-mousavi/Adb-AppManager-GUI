import os
import tkinter as tk
from tkinter import messagebox, ttk
from ttkthemes import ThemedTk

def list_apps():
    apps = os.popen('adb shell pm list packages').read().split('\n')
    apps = [app.replace('package:', '') for app in apps]
    return apps

def disable_app(app):
    os.system(f'adb shell pm disable-user {app}')

def enable_app(app):
    os.system(f'adb shell pm enable {app}')

def update_listbox(listbox, apps):
    listbox.delete(0, tk.END)
    for app in apps:
        listbox.insert(tk.END, app)

def disable():
    app = listbox.get(tk.ANCHOR)
    if app:
        disable_app(app)
        messagebox.showinfo("Info", f"{app} disabled")

def enable():
    app = listbox.get(tk.ANCHOR)
    if app:
        enable_app(app)
        messagebox.showinfo("Info", f"{app} enabled")

def search():
    query = search_var.get()
    apps = list_apps()
    matches = [app for app in apps if query in app]
    update_listbox(listbox, matches)

root = ThemedTk(theme="black")  # Use the 'black' theme
root.title("Android App Manager")

root.columnconfigure(0, weight=1)  # Column with Listbox
root.rowconfigure(1, weight=1)  # Row with Listbox

search_var = tk.StringVar()
search_box = ttk.Entry(root, textvariable=search_var)
search_box.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

search_button = ttk.Button(root, text="Search", command=search)
search_button.grid(row=0, column=1, padx=10, pady=10)

listbox = tk.Listbox(root)
listbox.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

update_button = ttk.Button(root, text="Update List", command=lambda: update_listbox(listbox, list_apps()))
update_button.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

disable_button = ttk.Button(root, text="Disable App", command=disable)
disable_button.grid(row=2, column=1, padx=10, pady=10, sticky="ew")

enable_button = ttk.Button(root, text="Enable App", command=enable)
enable_button.grid(row=3, column=0, padx=10, pady=10, sticky="ew")

root.mainloop()
