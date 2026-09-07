
import os
import sys
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


class ISOMounterApp:

  def __init__(self, root):
    self.root = root
    self.root.title("Linux Disk Image Mounter")
    self.root.geometry("620x520")
    self.root.resizable(False, False)

    # Image File Selection
    tk.Label(root, text="Select ISO / IMG File:", font=("Arial", 10, "bold")).pack(
        anchor="w", padx=20, pady=(15, 0)
    )
    iso_frame = tk.Frame(root)
    iso_frame.pack(fill="x", padx=20, pady=5)

    self.iso_entry = tk.Entry(iso_frame, width=52)
    self.iso_entry.pack(side="left", expand=True, fill="x")
    tk.Button(iso_frame, text="Browse", command=self.browse_image).pack(
        side="right", padx=(5, 0)
    )

    # Mount Point Selection
    tk.Label(root, text="Mount Destination:", font=("Arial", 10, "bold")).pack(
        anchor="w", padx=20, pady=(10, 0)
    )
    mnt_frame = tk.Frame(root)
    mnt_frame.pack(fill="x", padx=20, pady=5)

    self.mnt_entry = tk.Entry(mnt_frame, width=52)
    self.mnt_entry.pack(side="left", expand=True, fill="x")
    self.mnt_entry.insert(0, "/run/media/mounted_iso")
    tk.Button(mnt_frame, text="Browse", command=self.browse_mnt).pack(
        side="right", padx=(5, 0)
    )

    # Action Buttons
    btn_frame = tk.Frame(root)
    btn_frame.pack(fill="x", padx=20, pady=10)

    tk.Button(
        btn_frame,
        text="Mount Image",
        command=self.mount_image,
        bg="#2e7d32",
        fg="white",
        font=("Arial", 9, "bold"),
        width=13,
    ).pack(side="left", padx=2)
    tk.Button(
        btn_frame,
        text="Unmount Selected",
        command=self.unmount_selected,
        bg="#c62828",
        fg="white",
        font=("Arial", 9, "bold"),
        width=15,
    ).pack(side="left", padx=2)
    tk.Button(
        btn_frame,
        text="Unmount All",
        command=self.unmount_all,
        bg="#d32f2f",
        fg="white",
        font=("Arial", 9, "bold"),
        width=13,
    ).pack(side="left", padx=2)
    tk.Button(
        btn_frame,
        text="Refresh List",
        command=self.refresh_mounts,
        bg="#1976d2",
        fg="white",
        font=("Arial", 9, "bold"),
        width=11,
    ).pack(side="right", padx=2)

    # Mounted List Table (Treeview)
    tk.Label(root, text="Currently Mounted Images:", font=("Arial", 10, "bold")).pack(
        anchor="w", padx=20, pady=(10, 0)
    )

    tree_frame = tk.Frame(root)
    tree_frame.pack(fill="both", expand=True, padx=20, pady=5)

    columns = ("Image Path", "Mount Point")
    self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=8)
    self.tree.heading("Image Path", text="Image Path")
    self.tree.heading("Mount Point", text="Mount Point")
    self.tree.column("Image Path", width=340)
    self.tree.column("Mount Point", width=220)

    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
    self.tree.configure(yscrollcommand=scrollbar.set)

    self.tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Initial population of mounted list
    self.refresh_mounts()

  def browse_image(self):
    filename = filedialog.askopenfilename(
        filetypes=[
            ("All Disk Images", "*.iso *.img *.ISO *.IMG"),
            ("ISO Files", "*.iso *.ISO"),
            ("IMG Files", "*.img *.IMG"),
            ("All Files", "*.*")
        ]
    )
    if filename:
      self.iso_entry.delete(0, tk.END)
      self.iso_entry.insert(0, filename)

  def browse_mnt(self):
    dirname = filedialog.askdirectory()
    if dirname:
      self.mnt_entry.delete(0, tk.END)
      self.mnt_entry.insert(0, dirname)

  def mount_image(self):
    iso_path = self.iso_entry.get()
    mnt_point = self.mnt_entry.get()

    if not iso_path or not mnt_point:
      messagebox.showerror("Error", "Please select both an image file and mount path.")
      return

    try:
      subprocess.run(["sudo", "mkdir", "-p", mnt_point], check=True)
      cmd = ["sudo", "mount", "-o", "loop", iso_path, mnt_point]
      subprocess.run(cmd, capture_output=True, text=True, check=True)
      messagebox.showinfo("Success", f"Image mounted successfully at:\n{mnt_point}")
      self.refresh_mounts()
    except subprocess.CalledProcessError as e:
      err_msg = e.stderr.strip() if hasattr(e, 'stderr') and e.stderr else "Authentication failed or invalid image."
      messagebox.showerror("Mount Failed", err_msg)
    except Exception as e:
      messagebox.showerror("Error", str(e))

  def unmount_selected(self):
    selected_item = self.tree.selection()
    if not selected_item:
      messagebox.showerror("Error", "Please select a mounted image from the list to unmount.")
      return

    item_values = self.tree.item(selected_item, "values")
    mnt_point = item_values[1]

    try:
      cmd = ["sudo", "umount", mnt_point]
      subprocess.run(cmd, capture_output=True, text=True, check=True)
      subprocess.run(["sudo", "rmdir", mnt_point], capture_output=True)
      messagebox.showinfo("Success", f"Unmounted successfully from:\n{mnt_point}")
      self.refresh_mounts()
    except subprocess.CalledProcessError as e:
      err_msg = e.stderr.strip() if hasattr(e, 'stderr') and e.stderr else "Could not unmount. Ensure files aren't in use."
      messagebox.showerror("Unmount Failed", err_msg)
    except Exception as e:
      messagebox.showerror("Error", str(e))

  def unmount_all(self):
    items = self.tree.get_children()
    if not items:
      messagebox.showinfo("Info", "No active ISO/IMG mounts found.")
      return

    if not messagebox.askyesno("Confirm", "Are you sure you want to unmount all listed ISO/IMG files?"):
      return

    failed = []
    for item in items:
      mnt_point = self.tree.item(item, "values")[1]
      try:
        cmd = ["sudo", "umount", mnt_point]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        subprocess.run(["sudo", "rmdir", mnt_point], capture_output=True)
      except Exception:
        failed.append(mnt_point)

    self.refresh_mounts()
    if failed:
      messagebox.showwarning("Partial Success", f"Could not unmount the following points:\n" + "\n".join(failed))
    else:
      messagebox.showinfo("Success", "All listed images unmounted successfully.")

  def refresh_mounts(self):
    for item in self.tree.get_children():
      self.tree.delete(item)

    try:
      if os.path.exists("/proc/mounts"):
        with open("/proc/mounts", "r") as f:
          for line in f:
            parts = line.split()
            if len(parts) >= 4:
              device, mnt_pt, fstype, options = parts[0], parts[1], parts[2], parts[3]
              if "loop" in options or device.startswith("/dev/loop"):
                backing_file = self.get_loop_backing_file(device)
                if backing_file and (backing_file.lower().endswith(".iso") or backing_file.lower().endswith(".img")):
                  self.tree.insert("", "end", values=(backing_file, mnt_pt))
                elif ".iso" in mnt_pt.lower() or ".img" in mnt_pt.lower() or ".iso" in device.lower() or ".img" in device.lower():
                  self.tree.insert("", "end", values=(device, mnt_pt))
    except Exception:
      pass

  def get_loop_backing_file(self, device):
    try:
      res = subprocess.run(["sudo", "losetup", device], capture_output=True, text=True)
      if res.returncode == 0 and ("data=" in res.stdout or "(" in res.stdout):
        start = res.stdout.find("(")
        end = res.stdout.find(")", start)
        if start != -1 and end != -1:
          return res.stdout[start+1:end]
    except Exception:
      pass
    return ""


def authenticate_and_run():
  try:
    result = subprocess.run(["sudo", "-v"], capture_output=True)
    if result.returncode != 0:
      root = tk.Tk()
      root.withdraw()
      messagebox.showerror("Authentication Required", "Root privileges are required to run this application.")
      sys.exit(1)
  except Exception:
    sys.exit(1)

  root = tk.Tk()
  app = ISOMounterApp(root)
  root.mainloop()


if __name__ == "__main__":
  authenticate_and_run()




