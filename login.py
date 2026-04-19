import tkinter as tk
from tkinter import messagebox
from database import get_connection
from apartment_gui import ApartmentApp


class LoginApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PAMS Login")
        
        self.root.state("zoomed")
        self.root.minsize (700,600)
        self.root.configure(bg="#111318")

        self._build_ui()


    def _build_ui(self):
        tk.Label(
            self.root,
            text="PAMS Login",
            font=("Helvetica", 18, "bold"),
            bg="#111318",
            fg="white"
        ).pack(pady=20)

        tk.Label(
            self.root,
            text="Username",
            bg="#111318",
            fg="white"
        ).pack()
        self.username_entry = tk.Entry(self.root)
        self.username_entry.pack(pady=5)

        tk.Label(
            self.root,
            text="Password",
            bg="#111318",
            fg="white"
        ).pack()
        self.password_entry = tk.Entry(self.root, show="*")
        self.password_entry.pack(pady=5)

        tk.Button(
            self.root,
            text="Login",
            command=self.login
        ).pack(pady=20)

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT role, full_name
            FROM users
            WHERE username = ? AND password = ?
            """,
            (username, password)
        )

        user = cursor.fetchone()
        conn.close()

        if user:
            role, name = user
            messagebox.showinfo("Success", f"Welcome {name} ({role})")


            self.open_main_app(role)
        else:
            messagebox.showerror("Error", "Invalid username or password")

    def open_main_app(self, role):
    # Clear login UI instead of destroying the window
        for widget in self.root.winfo_children():
            widget.destroy()

        # Load the main application inside the same root
        app = ApartmentApp(self.root)
        app.user_role = role


if __name__ == "__main__":
    root = tk.Tk()
    app = LoginApp(root)
    root.mainloop()