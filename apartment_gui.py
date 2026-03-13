# Anna Boychenko - 24030024
# Apartment Management GUI - PAMS group project
# this file builds the actual screens the user sees using tkinter
# i used tkinter because thats what we used in labs and i know how it works
# the brief said desktop app so no flask or html here

import tkinter as tk
from tkinter import ttk, messagebox
from apartment import ApartmentManager

# main class for the apartment management window
# everything the user sees and does goes through here
class ApartmentApp:

    def __init__(self, root):
        self.root = root
        self.root.title("PAMS - Apartment Management")
        self.root.geometry("900x600")
        self.root.configure(bg="#f0f0f0")

        # create an instance of ApartmentManager to handle all the db stuff
        self.manager = ApartmentManager()

        # load in the mock data when app first starts
        self.manager.insert_mock_data()

        # build the two main parts of the layout
        self.build_sidebar()
        self.build_main_area()

        # default screen when you open the app
        self.show_apartments()

    # builds the left side navigation bar
    def build_sidebar(self):
        sidebar = tk.Frame(self.root, bg="#2c3e50", width=200)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)  # stops the sidebar shrinking to fit content

        # app title at top of sidebar
        tk.Label(sidebar, text="PAMS", font=("Arial", 18, "bold"),
                 bg="#2c3e50", fg="white").pack(pady=20)

        tk.Label(sidebar, text="Apartment Management", font=("Arial", 9),
                 bg="#2c3e50", fg="#bdc3c7", wraplength=160).pack(pady=5)

        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", pady=10)

        # list of buttons and what they do when clicked
        buttons = [
            ("View Apartments", self.show_apartments),
            ("Register Apartment", self.show_register_form),
            ("Assign Tenant", self.show_assign_tenant),
            ("Maintenance Requests", self.show_maintenance),
            ("Add Maintenance Request", self.show_maintenance_form),
        ]

        # create each button from the list above
        for text, command in buttons:
            tk.Button(sidebar, text=text, command=command,
                      bg="#34495e", fg="white", font=("Arial", 10),
                      relief="flat", cursor="hand2", pady=8,
                      activebackground="#1abc9c", activeforeground="white"
                      ).pack(fill="x", padx=10, pady=3)

    # builds the right side where the content changes
    def build_main_area(self):
        self.main_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.main_frame.pack(side="right", fill="both", expand=True)

    # clears the main area before showing something new
    # have to do this or all the screens stack on top of each other
    def clear_main(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    # shows all apartments in a table
    # colour coded so vacant = green, occupied = red - makes it easy to see at a glance
    def show_apartments(self):
        self.clear_main()

        tk.Label(self.main_frame, text="All Apartments", font=("Arial", 16, "bold"),
                 bg="#f0f0f0").pack(pady=15)

        frame = tk.Frame(self.main_frame, bg="#f0f0f0")
        frame.pack(fill="both", expand=True, padx=20)

        # scrollbar for if there are loads of apartments
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")

        # treeview is tkinters table widget
        cols = ("ID", "Location", "Type", "Rent (£)", "Rooms", "Status", "Tenant ID")
        tree = ttk.Treeview(frame, columns=cols, show="headings",
                            yscrollcommand=scrollbar.set)

        # set up each column header and width
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=110, anchor="center")

        scrollbar.config(command=tree.yview)

        # load all apartments and add them to the table
        apartments = self.manager.get_all_apartments()
        for apt in apartments:
            tag = "occupied" if apt.status == "occupied" else "vacant"
            tree.insert("", "end", values=(
                apt.apartment_id, apt.location, apt.apt_type,
                f"£{apt.monthly_rent:.2f}", apt.num_rooms,
                apt.status, apt.tenant_id or "-"
            ), tags=(tag,))

        # set the row colours based on the tag
        tree.tag_configure("occupied", background="#fadbd8")   # light red for occupied
        tree.tag_configure("vacant", background="#d5f5e3")     # light green for vacant
        tree.pack(fill="both", expand=True)

        # buttons at the bottom for actions on selected rows
        btn_frame = tk.Frame(self.main_frame, bg="#f0f0f0")
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Delete Selected",
                  command=lambda: self.delete_apartment(tree),
                  bg="#e74c3c", fg="white", font=("Arial", 10), padx=10).pack(side="left", padx=5)

        tk.Button(btn_frame, text="Edit Selected",
                  command=lambda: self.edit_apartment(tree),
                  bg="#3498db", fg="white", font=("Arial", 10), padx=10).pack(side="left", padx=5)

        tk.Button(btn_frame, text="Remove Tenant",
                  command=lambda: self.remove_tenant(tree),
                  bg="#e67e22", fg="white", font=("Arial", 10), padx=10).pack(side="left", padx=5)

    # form for registering a new apartment
    def show_register_form(self):
        self.clear_main()

        tk.Label(self.main_frame, text="Register New Apartment",
                 font=("Arial", 16, "bold"), bg="#f0f0f0").pack(pady=15)

        form = tk.Frame(self.main_frame, bg="#f0f0f0")
        form.pack(padx=40, pady=10)

        # fields - some are dropdowns with set options, some are free text entry
        fields = [
            ("Location", ["Bristol", "London", "Manchester", "Cardiff"]),
            ("Type", ["1-bedroom flat", "2-bedroom flat", "3-bedroom house", "Studio"]),
            ("Monthly Rent (£)", None),   # None means free text entry
            ("Number of Rooms", None),
        ]

        # store all the input variables so i can read them when the form is submitted
        self.reg_vars = {}

        for i, (label, options) in enumerate(fields):
            tk.Label(form, text=label, font=("Arial", 11),
                     bg="#f0f0f0", anchor="w").grid(row=i, column=0, pady=8, sticky="w")

            if options:
                # dropdown for fields with set choices
                var = tk.StringVar(value=options[0])
                ttk.Combobox(form, textvariable=var, values=options,
                             state="readonly", width=25).grid(row=i, column=1, pady=8, padx=10)
            else:
                # text box for number fields
                var = tk.StringVar()
                tk.Entry(form, textvariable=var, width=27,
                         font=("Arial", 11)).grid(row=i, column=1, pady=8, padx=10)

            self.reg_vars[label] = var

        tk.Button(self.main_frame, text="Register Apartment",
                  command=self.submit_register,
                  bg="#1abc9c", fg="white", font=("Arial", 12), padx=20, pady=8
                  ).pack(pady=20)

    # called when the register form is submitted
    def submit_register(self):
        try:
            location = self.reg_vars["Location"].get()
            apt_type = self.reg_vars["Type"].get()
            # need to convert to float/int - will throw ValueError if not a number
            monthly_rent = float(self.reg_vars["Monthly Rent (£)"].get())
            num_rooms = int(self.reg_vars["Number of Rooms"].get())

            self.manager.add_apartment(location, apt_type, monthly_rent, num_rooms)
            messagebox.showinfo("Success", "Apartment registered successfully!")
            self.show_apartments()  # go back to the list after registering

        except ValueError as e:
            messagebox.showerror("Error", str(e))

    # form to assign a tenant to an apartment
    # only shows vacant apartments in the dropdown
    def show_assign_tenant(self):
        self.clear_main()

        tk.Label(self.main_frame, text="Assign Tenant to Apartment",
                 font=("Arial", 16, "bold"), bg="#f0f0f0").pack(pady=15)

        form = tk.Frame(self.main_frame, bg="#f0f0f0")
        form.pack(padx=40, pady=10)

        # filter to only show vacant apartments
        apartments = self.manager.get_all_apartments()
        vacant = [f"{a.apartment_id} - {a.location} ({a.apt_type})"
                  for a in apartments if a.status == "vacant"]

        # if there are no vacant ones show a message instead
        if not vacant:
            tk.Label(form, text="No vacant apartments available.",
                     font=("Arial", 12), bg="#f0f0f0", fg="red").pack(pady=20)
            return

        tk.Label(form, text="Select Apartment", font=("Arial", 11),
                 bg="#f0f0f0").grid(row=0, column=0, pady=8, sticky="w")
        self.assign_apt_var = tk.StringVar(value=vacant[0])
        ttk.Combobox(form, textvariable=self.assign_apt_var, values=vacant,
                     state="readonly", width=35).grid(row=0, column=1, pady=8, padx=10)

        tk.Label(form, text="Tenant ID", font=("Arial", 11),
                 bg="#f0f0f0").grid(row=1, column=0, pady=8, sticky="w")
        self.assign_tenant_var = tk.StringVar()
        tk.Entry(form, textvariable=self.assign_tenant_var, width=37,
                 font=("Arial", 11)).grid(row=1, column=1, pady=8, padx=10)

        tk.Button(self.main_frame, text="Assign Tenant",
                  command=self.submit_assign_tenant,
                  bg="#1abc9c", fg="white", font=("Arial", 12), padx=20, pady=8
                  ).pack(pady=20)

    # handles the assign tenant form submission
    def submit_assign_tenant(self):
        try:
            # the dropdown shows "1 - Bristol (2-bedroom flat)" so split to get just the id
            apt_id = int(self.assign_apt_var.get().split(" - ")[0])
            tenant_id = int(self.assign_tenant_var.get())
            self.manager.assign_tenant(apt_id, tenant_id)
            messagebox.showinfo("Success", f"Tenant {tenant_id} assigned to apartment {apt_id}!")
            self.show_apartments()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    # shows all maintenance requests in a table
    # colour coded - orange for open, green for resolved
    def show_maintenance(self):
        self.clear_main()

        tk.Label(self.main_frame, text="Maintenance Requests",
                 font=("Arial", 16, "bold"), bg="#f0f0f0").pack(pady=15)

        frame = tk.Frame(self.main_frame, bg="#f0f0f0")
        frame.pack(fill="both", expand=True, padx=20)

        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")

        cols = ("ID", "Apartment ID", "Description", "Priority", "Status",
                "Date Raised", "Date Resolved", "Cost (£)", "Time (hrs)")
        tree = ttk.Treeview(frame, columns=cols, show="headings",
                            yscrollcommand=scrollbar.set)

        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor="center")

        scrollbar.config(command=tree.yview)

        # load all requests and add to table
        requests = self.manager.get_all_maintenance_requests()
        for req in requests:
            tag = "open" if req.status == "open" else "resolved"
            tree.insert("", "end", values=(
                req.request_id, req.apartment_id, req.description,
                req.priority, req.status, req.date_raised,
                req.date_resolved or "-", req.cost or "-", req.time_taken or "-"
            ), tags=(tag,))

        tree.tag_configure("open", background="#fdebd0")      # orange for open
        tree.tag_configure("resolved", background="#d5f5e3")  # green for resolved
        tree.pack(fill="both", expand=True)

        tk.Button(self.main_frame, text="Resolve Selected Request",
                  command=lambda: self.resolve_request(tree),
                  bg="#1abc9c", fg="white", font=("Arial", 10), padx=10
                  ).pack(pady=10)

    # form to add a new maintenance request
    def show_maintenance_form(self):
        self.clear_main()

        tk.Label(self.main_frame, text="Add Maintenance Request",
                 font=("Arial", 16, "bold"), bg="#f0f0f0").pack(pady=15)

        form = tk.Frame(self.main_frame, bg="#f0f0f0")
        form.pack(padx=40, pady=10)

        # show all apartments in dropdown so user can pick which one has the issue
        apartments = self.manager.get_all_apartments()
        apt_options = [f"{a.apartment_id} - {a.location} ({a.apt_type})"
                       for a in apartments]

        tk.Label(form, text="Apartment", font=("Arial", 11),
                 bg="#f0f0f0").grid(row=0, column=0, pady=8, sticky="w")
        self.maint_apt_var = tk.StringVar(value=apt_options[0] if apt_options else "")
        ttk.Combobox(form, textvariable=self.maint_apt_var, values=apt_options,
                     state="readonly", width=35).grid(row=0, column=1, pady=8, padx=10)

        tk.Label(form, text="Description", font=("Arial", 11),
                 bg="#f0f0f0").grid(row=1, column=0, pady=8, sticky="w")
        self.maint_desc_var = tk.StringVar()
        tk.Entry(form, textvariable=self.maint_desc_var, width=37,
                 font=("Arial", 11)).grid(row=1, column=1, pady=8, padx=10)

        tk.Label(form, text="Priority", font=("Arial", 11),
                 bg="#f0f0f0").grid(row=2, column=0, pady=8, sticky="w")
        self.maint_priority_var = tk.StringVar(value="medium")
        ttk.Combobox(form, textvariable=self.maint_priority_var,
                     values=["low", "medium", "high"],
                     state="readonly", width=35).grid(row=2, column=1, pady=8, padx=10)

        tk.Button(self.main_frame, text="Submit Request",
                  command=self.submit_maintenance,
                  bg="#1abc9c", fg="white", font=("Arial", 12), padx=20, pady=8
                  ).pack(pady=20)

    # handle maintenance form submission
    def submit_maintenance(self):
        try:
            apt_id = int(self.maint_apt_var.get().split(" - ")[0])
            description = self.maint_desc_var.get()
            priority = self.maint_priority_var.get()
            self.manager.add_maintenance_request(apt_id, description, priority)
            messagebox.showinfo("Success", "Maintenance request submitted!")
            self.show_maintenance()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    # resolve a selected maintenance request
    # opens a popup to get cost and time from the user
    def resolve_request(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a request to resolve")
            return

        # get the request id from the first column of the selected row
        request_id = tree.item(selected[0])["values"][0]

        # popup window for entering cost and time
        popup = tk.Toplevel(self.root)
        popup.title("Resolve Request")
        popup.geometry("300x200")
        popup.configure(bg="#f0f0f0")

        tk.Label(popup, text="Cost (£)", font=("Arial", 11), bg="#f0f0f0").pack(pady=5)
        cost_var = tk.StringVar()
        tk.Entry(popup, textvariable=cost_var, font=("Arial", 11)).pack()

        tk.Label(popup, text="Time Taken (hours)", font=("Arial", 11), bg="#f0f0f0").pack(pady=5)
        time_var = tk.StringVar()
        tk.Entry(popup, textvariable=time_var, font=("Arial", 11)).pack()

        # inner function to handle the confirm button in the popup
        def confirm():
            try:
                cost = float(cost_var.get())
                time_taken = int(time_var.get())
                self.manager.resolve_maintenance_request(request_id, cost, time_taken)
                messagebox.showinfo("Success", "Request resolved successfully!")
                popup.destroy()
                self.show_maintenance()  # refresh the list
            except ValueError as e:
                messagebox.showerror("Error", str(e))

        tk.Button(popup, text="Confirm", command=confirm,
                  bg="#1abc9c", fg="white", font=("Arial", 11), padx=15).pack(pady=15)

    # delete a selected apartment
    def delete_apartment(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an apartment to delete")
            return

        apt_id = tree.item(selected[0])["values"][0]

        # ask user to confirm before actually deleting
        if messagebox.askyesno("Confirm", f"Delete apartment {apt_id}?"):
            try:
                self.manager.delete_apartment(apt_id)
                messagebox.showinfo("Success", "Apartment deleted successfully!")
                self.show_apartments()
            except ValueError as e:
                messagebox.showerror("Error", str(e))

    # edit a selected apartment - opens a popup form with current values filled in
    def edit_apartment(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an apartment to edit")
            return

        values = tree.item(selected[0])["values"]
        apt_id = values[0]

        popup = tk.Toplevel(self.root)
        popup.title(f"Edit Apartment {apt_id}")
        popup.geometry("350x300")
        popup.configure(bg="#f0f0f0")

        # pre fill the form with the current apartment values
        fields = [
            ("Location", values[1], ["Bristol", "London", "Manchester", "Cardiff"]),
            ("Type", values[2], ["1-bedroom flat", "2-bedroom flat", "3-bedroom house", "Studio"]),
            ("Monthly Rent", str(values[3]).replace("£", ""), None),
            ("Rooms", str(values[4]), None),
        ]

        vars = {}
        for i, (label, default, options) in enumerate(fields):
            tk.Label(popup, text=label, font=("Arial", 11),
                     bg="#f0f0f0").grid(row=i, column=0, padx=10, pady=8, sticky="w")
            var = tk.StringVar(value=default)
            if options:
                ttk.Combobox(popup, textvariable=var, values=options,
                             state="readonly", width=20).grid(row=i, column=1, padx=10, pady=8)
            else:
                tk.Entry(popup, textvariable=var, width=22,
                         font=("Arial", 11)).grid(row=i, column=1, padx=10, pady=8)
            vars[label] = var

        def save_edit():
            try:
                self.manager.update_apartment(
                    apt_id,
                    vars["Location"].get(),
                    vars["Type"].get(),
                    float(vars["Monthly Rent"].get()),
                    int(vars["Rooms"].get())
                )
                messagebox.showinfo("Success", "Apartment updated successfully!")
                popup.destroy()
                self.show_apartments()
            except ValueError as e:
                messagebox.showerror("Error", str(e))

        tk.Button(popup, text="Save Changes", command=save_edit,
                  bg="#1abc9c", fg="white", font=("Arial", 11), padx=15
                  ).grid(row=len(fields), column=0, columnspan=2, pady=15)

    # remove tenant from a selected apartment
    def remove_tenant(self, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an apartment")
            return

        apt_id = tree.item(selected[0])["values"][0]
        status = tree.item(selected[0])["values"][5]

        # cant remove a tenant if theres no tenant there
        if status == "vacant":
            messagebox.showwarning("Warning", "This apartment has no tenant to remove")
            return

        if messagebox.askyesno("Confirm", f"Remove tenant from apartment {apt_id}?"):
            self.manager.remove_tenant(apt_id)
            messagebox.showinfo("Success", "Tenant removed successfully!")
            self.show_apartments()


# entry point - run this file directly to open the apartment management window
if __name__ == "__main__":
    root = tk.Tk()
    app = ApartmentApp(root)
    root.mainloop()