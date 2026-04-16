#GUI - PAMS group project

#
# pages in this file:
#   - apartments overview (with stats)
#   - register new apartment
#   - create a tenant
#   - assign tenant to apartment
#   - maintenance requests list
#   - new maintenance request form
#   - payment overview
#   - generate invoice
#   - record payment
#
# TODO: might add a search/filter bar to the apartments table 

#pip install python-dateutil
#pip install tkcalendar
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime
from dateutil.relativedelta import relativedelta

from apartmentAndTenant import ApartmentManager
from payments import FinanceManager
import platform

from tenant_management import (
    edit_tenant,
    delete_tenant,
    calculate_early_termination_fee,
    get_lease_details,
    check_late_payment_tenant
)

# fixes the blurry font issue on windows - found this fix on stack overflow
# it crashes silently on mac/linux so wrapping in try/except
if platform.system() == "Windows":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass


BG_BASE     ="#111318"   # main background - almost black
BG_SURFACE  ="#181b24"   # sidebar background
BG_CARD     ="#1e2130"   # cards and table background
BG_INPUT    ="#252a3a"   # entry field background
BG_ROW_ODD  ="#222638"   # alternate row colour for the tables

TEAL        ="#ffffff"   # changed accent to white
TEAL_DIM    ="#f2f2f2"   # changed hover to slightly different white
TEAL_BG     ="#0d2622"   # teal tinted background for buttons

AMBER       ="#f59e0b"   # used for warnings and open maintenance requests
AMBER_BG    ="#2a1f06"

RED         ="#f87171"   # used for occupied status and danger actions
RED_BG      ="#2a1010"

TEXT_BRIGHT ="#f1f5f9"   # headings
TEXT_MAIN   ="#cbd5e1"   # normal text
TEXT_MUTED  ="#64748b"   # labels and secondary text
TEXT_DIVIDER="#374151"   # dividers and section labels

BORDER      ="#2d3347"   # card and input borders


class PillButton(tk.Frame):
    """
    custom button class because tkinter's built-in Button widget looks awful
    on dark backgrounds - the relief and default grey just cant be styled properly
    so i build it from a Frame + Label instead and handle hover manually
    saw this technique in a youtube tutorial and adapted it for this project
    """
    def __init__(self, parent, text, command,
                 bg=TEAL, fg=BG_BASE, hover_bg=TEAL_DIM,
                 padx=18, pady=7, font_size=10, **kw):
        super().__init__(parent, bg=bg, cursor="hand2", **kw)
        self._bg      =bg
        self._hover_bg=hover_bg
        self._lbl=tk.Label(self, text=text,
                             font=("Helvetica", font_size,),
                             bg=bg, fg=fg, padx=padx, pady=pady,
                             cursor="hand2")
        self._lbl.pack()
        for w in (self, self._lbl):
            w.bind("<Button-1>", lambda e: command())
            w.bind("<Enter>",    self._on_enter)
            w.bind("<Leave>",    self._on_leave)

    def _on_enter(self, _):
        self.configure(bg=self._hover_bg)
        self._lbl.configure(bg=self._hover_bg)

    def _on_leave(self, _):
        self.configure(bg=self._bg)
        self._lbl.configure(bg=self._bg)


class StatCard(tk.Frame):
    """small summary card - shows a number and a label, with a coloured top bar"""
    def __init__(self, parent, value, label, accent, **kw):
        super().__init__(parent, bg=BG_CARD,
                         highlightthickness=1,
                         highlightbackground=BORDER, **kw)
        # the coloured top bar is what makes these look like proper stat cards
        tk.Frame(self, bg=accent, height=3).pack(fill="x")
        inner=tk.Frame(self, bg=BG_CARD)
        inner.pack(padx=24, pady=(12, 14))
        tk.Label(inner, text=str(value),
                 font=("Helvetica", 24, "bold"),
                 bg=BG_CARD, fg=accent).pack()
        tk.Label(inner, text=label,
                 font=("Helvetica", 9),
                 bg=BG_CARD, fg=TEXT_MUTED).pack()


class ApartmentApp:
    """main application class - builds the whole gui"""

    def __init__(self, root):
        self.root=root
        self.root.title("PAMS - Apartment Management")
        self.root.geometry("1200x740")
        self.root.minsize(960, 600)
        self.root.configure(bg=BG_BASE)

        self._setup_styles()

        # create the manager and load mock data for the demo
        # the manager talks to the sqlite database through the methods in apartment.py
        self.manager=ApartmentManager()
        self.finance=FinanceManager ()
        self.manager.insert_mock_data()

        self._nav_rows={}   # stores references to nav buttons so we can highlight them
        self._build_sidebar()
        self._build_main_area()
        self.show_apartments()   # start on the apartments page

    # ================================================================= #
    #  TTK STYLES                                                        #
    # ================================================================= #

    def _setup_styles(self):
        # ttk widgets need custom styles to match the dark theme
        # the "clam" theme is the only one that actually lets you override colours properly
        # "default" and "alt" both ignore the background settings for some reason
        s=ttk.Style()
        s.theme_use("clam")

        s.configure("Apt.Treeview",
                    background=BG_CARD, foreground=TEXT_MAIN,
                    fieldbackground=BG_CARD, borderwidth=0,
                    rowheight=42, font=("Helvetica", 10))

        s.configure("Apt.Treeview.Heading",
                    background=BG_SURFACE, foreground=TEXT_MUTED,
                    borderwidth=0, relief="flat",
                    font=("Helvetica", 9, "bold"), padding=(14, 12))

        s.map("Apt.Treeview",
              background=[("selected", "#2a2f45")],
              foreground=[("selected", TEXT_BRIGHT)])
        s.map("Apt.Treeview.Heading",
              background=[("active", BG_CARD)],
              relief=[("active", "flat")])

        # skinny scrollbar - width=5 makes it look modern, default is way too chunky
        s.configure("Apt.Vertical.TScrollbar",
                    background=BG_CARD, troughcolor=BG_BASE,
                    borderwidth=0, arrowcolor=TEXT_MUTED, width=5)

        s.configure("Apt.TCombobox",
                    background=BG_INPUT, foreground=TEXT_MAIN,
                    fieldbackground=BG_INPUT, borderwidth=0,
                    selectbackground=TEAL, padding=(10, 7))
        s.map("Apt.TCombobox",
              fieldbackground=[("readonly", BG_INPUT)],
              foreground=[("readonly", TEXT_MAIN)],
              selectbackground=[("readonly", "#2a2f45")])
        
        self.root.option_add("*TCombobox*Listbox.background", BG_INPUT)
        self.root.option_add("*TCombobox*Listbox.foreground", TEXT_MAIN)

    # ================================================================= #
    #  SIDEBAR                                                           #
    # ================================================================= #

    def _build_sidebar(self):
        # width=222 and pack_propagate(False) stops the sidebar from shrinking
        # to fit its contents - took me ages to figure out why it kept collapsing
        sb=tk.Frame(self.root, bg=BG_SURFACE, width=300)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)
        self._sb=sb

        # logo area at the top of the sidebar
        logo=tk.Frame(sb, bg=BG_SURFACE)
        logo.pack(fill="x", padx=22, pady=(30, 20))

        # using place() here instead of pack because its the only way to properly
        # centre the letter inside the fixed-size frame
        txt=tk.Frame(logo, bg=BG_SURFACE)
        txt.pack(side="left", padx=(10, 0))
        tk.Label(txt, text="PAMS", font=("Helvetica", 14),
                 bg=BG_SURFACE, fg=TEXT_BRIGHT).pack(anchor="w")
        tk.Label(txt, text="Management System", font=("Helvetica", 7),
                 bg=BG_SURFACE, fg=TEXT_MUTED).pack(anchor="w")

        tk.Frame(sb, bg=BORDER, height=1).pack(fill="x", padx=16)

        # nav groups
        self._section_lbl(sb, "APARTMENTS")
        self._nav_row(sb, "  Apartments",   self.show_apartments)
        self._nav_row(sb, "  Register",      self.show_register_form)
        self._nav_row(sb, "  Create Tenant", self.show_create_tenant)
        self._nav_row(sb, "  Assign Tenant", self.show_assign_tenant)

        tk.Frame(sb, bg=BG_SURFACE, height=4).pack()
        self._section_lbl(sb, "MAINTENANCE")
        self._nav_row(sb, "  All Requests",  self.show_maintenance)
        self._nav_row(sb, "  New Request",   self.show_maintenance_form)

        self._section_lbl(sb, "PAYMENTS")
        self._nav_row(sb, "  Payments Overview", self.show_payments)
        self._nav_row(sb, "  Generate Invoice", self.show_invoice_form)
        self._nav_row(sb, "  Record Payment", self.show_record_payment)


        # spacer then credit

    def _section_lbl(self, parent, text):
        tk.Label(parent, text=text,
                 font=("Helvetica", 7, "bold"),
                 bg=BG_SURFACE, fg=TEXT_DIVIDER
                 ).pack(anchor="w", padx=22, pady=(12, 4))

    def _nav_row(self, parent, label, command):
        outer=tk.Frame(parent, bg=BG_SURFACE, cursor="hand2")
        outer.pack(fill="x", padx=8, pady=1)

        # the 3px indicator bar on the left - only visible when the row is active
        ind=tk.Frame(outer, bg=BG_SURFACE, width=3)
        ind.pack(side="left", fill="y")

        lbl=tk.Label(outer, text=label,
                       font=("Helvetica", 10), bg=BG_SURFACE,
                       fg=TEXT_MUTED, anchor="w", pady=11,
                       padx=10, cursor="hand2")
        lbl.pack(side="left", fill="x", expand=True)

        # store a reference so _activate() can find and update all nav rows
        self._nav_rows[label]=(outer, ind, lbl)

        def activate():
            self._activate(label)
            command()

        # binding to both outer and lbl so clicking anywhere on the row works
        def hover_on(e):
            if outer.cget("bg") == BG_SURFACE:
                outer.configure(bg="#1e2338")
                lbl.configure(bg="#1e2338", fg=TEXT_MAIN)

        def hover_off(e):
            if outer.cget("bg") == "#1e2338":
                outer.configure(bg=BG_SURFACE)
                lbl.configure(bg=BG_SURFACE, fg=TEXT_MUTED)

        for w in (outer, lbl):
            w.bind("<Button-1>", lambda e: activate())
            w.bind("<Enter>", hover_on)
            w.bind("<Leave>", hover_off)

    def _activate(self, active_label):
        # loop through all nav rows and update their styling
        # active one gets the teal indicator + bright text, others get reset
        for label, (outer, ind, lbl) in self._nav_rows.items():
            if label == active_label:
                outer.configure(bg=BG_CARD)
                ind.configure(bg=TEAL)
                lbl.configure(bg=BG_CARD, fg=TEXT_BRIGHT,
                               font=("Helvetica", 10, "bold"))
            else:
                outer.configure(bg=BG_SURFACE)
                ind.configure(bg=BG_SURFACE)
                lbl.configure(bg=BG_SURFACE, fg=TEXT_MUTED,
                               font=("Helvetica", 10))

    # ================================================================= #
    #  MAIN AREA                                                         #
    # ================================================================= #

    def _build_main_area(self):
        self.main=tk.Frame(self.root, bg=BG_BASE)
        self.main.pack(side="right", fill="both", expand=True)

    def _clear(self):
        # wipe all widgets from the main area before loading a new page
        # simpler than trying to hide/show frames - just destroy and rebuild
        for w in self.main.winfo_children():
            w.destroy()

    # ================================================================= #
    #  LAYOUT HELPERS                                                    #
    # ================================================================= #

    def _page_header(self, title, subtitle=""):
        # teal left bar next to the title - gives it that dashboard look
        # i tried doing this with a border-left but tkinter doesnt support that
        # so a thin Frame widget is the workaround
        wrap=tk.Frame(self.main, bg=BG_BASE)
        wrap.pack(fill="x", padx=32, pady=(28, 20))

        tk.Frame(wrap, bg=TEAL, width=4).pack(side="left", fill="y")

        txt=tk.Frame(wrap, bg=BG_BASE)
        txt.pack(side="left", padx=(14, 0))
        tk.Label(txt, text=title, font=("Helvetica", 20, "bold"),
                 bg=BG_BASE, fg=TEXT_BRIGHT).pack(anchor="w")
        if subtitle:
            tk.Label(txt, text=subtitle, font=("Helvetica", 10),
                     bg=BG_BASE, fg=TEXT_MUTED).pack(anchor="w", pady=(3, 0))

    def _stats_row(self, items):
        # renders a row of StatCard widgets at the top of a page
        bar=tk.Frame(self.main, bg=BG_BASE)
        bar.pack(fill="x", padx=32, pady=(0, 16))
        for val, lbl, color in items:
            StatCard(bar, val, lbl, color).pack(side="left", padx=(0, 10))

    def _table_frame(self, cols, widths, anchors=None):
        # builds a treeview table with a scrollbar and returns the tree widget
        # the wrap frame is needed so the scrollbar sits flush against the table
        wrap=tk.Frame(self.main, bg=BG_BASE)
        wrap.pack(fill="both", expand=True, padx=32, pady=(0, 6))

        sb=ttk.Scrollbar(wrap, style="Apt.Vertical.TScrollbar")
        sb.pack(side="right", fill="y")

        if anchors is None:
            anchors=["center"] * len(cols)

        tree=ttk.Treeview(wrap, columns=cols, show="headings",
                            yscrollcommand=sb.set, style="Apt.Treeview",
                            selectmode="browse")
        for col, w, a in zip(cols, widths, anchors):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor=a, minwidth=w)

        sb.config(command=tree.yview)

        tree.tag_configure("odd",      background=BG_ROW_ODD)
        tree.tag_configure("occupied", foreground=RED)
        tree.tag_configure("vacant",   foreground=TEAL)
        tree.tag_configure("open",     foreground=AMBER)
        tree.tag_configure("resolved", foreground=TEAL)
        tree.tag_configure("overdue", foreground=AMBER)


        tree.pack(fill="both", expand=True)
        return tree

    def _btn_row(self, buttons):
        bar=tk.Frame(self.main, bg=BG_BASE)
        bar.pack(fill="x", padx=32, pady=(8, 20))
        for text, cmd, bg, fg, hover in buttons:
            PillButton(bar, text, cmd,
                       bg=bg, fg=fg, hover_bg=hover
                       ).pack(side="left", padx=(0, 8))

    def _form_card(self):
        c=tk.Frame(self.main, bg=BG_CARD,
                     highlightthickness=1, highlightbackground=BORDER)
        c.pack(fill="x", padx=32, pady=8)
        return c

    def _form_row(self, parent, label, widget_fn, hint=""):
        row=tk.Frame(parent, bg=BG_CARD)
        row.pack(fill="x", pady=8)
        tk.Label(row, text=label, font=("Helvetica", 10),
                 bg=BG_CARD, fg=TEXT_MUTED, width=20, anchor="w"
                 ).pack(side="left")
        w=widget_fn(row)
        w.pack(side="left", padx=(10, 0), ipady=5)
        if hint:
            tk.Label(row, text=hint, font=("Helvetica", 8),
                     bg=BG_CARD, fg=TEXT_DIVIDER
                     ).pack(side="left", padx=(8, 0))
        return w

    def _entry(self, parent, var, width=34):
        # insertbackground sets the cursor colour inside the entry field
        # without this the cursor is black and invisible on the dark background
        return tk.Entry(parent, textvariable=var,
                        bg=BG_INPUT, fg=TEXT_MAIN,
                        insertbackground=TEAL,
                        relief="flat", font=("Helvetica", 11),
                        bd=0, width=width,
                        highlightthickness=1,
                        highlightcolor=TEAL,
                        highlightbackground=BORDER)

    def _combo(self, parent, var, values, width=30):
        return ttk.Combobox(parent, textvariable=var, values=values,
                            state="readonly", style="Apt.TCombobox",
                            font=("Helvetica", 11), width=width)

    # ================================================================= #
    #  APARTMENTS PAGE                                                   #
    # ================================================================= #

    def show_apartments(self):
        self._clear()
        self._activate("  Apartments")
        self._page_header("Apartments",
                          "All registered properties across locations")

        apts    =self.manager.get_all_apartments()
        occupied=sum(1 for a in apts if a.status == "occupied")

        # stat cards at the top - pulling live counts from the database
        self._stats_row([
            (len(apts),          "Total",    TEXT_MUTED),
            (occupied,           "Occupied", RED),
            (len(apts)-occupied, "Vacant",   TEAL),
        ])

        cols   =("ID", "Location", "Type", "Rent (£)", "Rooms", "Status", "Tenant ID")
        widths =[52, 120, 200, 100, 70, 108, 90]
        anchors=["center","w","w","center","center","center","center"]
        tree=self._table_frame(cols, widths, anchors)

        for i, a in enumerate(apts):
            row_tag="odd" if i % 2 else ""
            status ="● Occupied" if a.status == "occupied" else "● Vacant"
            tree.insert("", "end", values=(
                a.apartment_id, a.location, a.apt_type,
                f"£{a.monthly_rent:,.2f}", a.num_rooms,
                status, a.tenant_id if a.tenant_id else "-"
            ), tags=(a.status, row_tag))


        self._btn_row([

            ("✏  Edit Apartment",
             lambda: self._edit_popup(tree),
             BG_CARD, TEXT_MAIN, "#272c3e"),
            ("✕  Delete Apartment",
             lambda: self._delete_apartment(tree),
             RED_BG, RED, "#3a1818"),
             ("→  Remove Tenant from Apartment",
             lambda: self._remove_tenant(tree),
             AMBER_BG, AMBER, "#3a2a0a"),


            ("📄 View Lease",
            lambda: self._view_lease_popup(tree),
            BG_CARD, TEXT_MAIN, "#272c3e"),
            ("👤 Manage Tenant",
            lambda: self._tenant_popup(tree),
            BG_CARD, TEXT_MAIN, "#272c3e"),
            ("⚠ Check Late & Notify",
            lambda: self._check_late_popup(tree),
            AMBER_BG, AMBER, "#3a2a0a"),
            ("✕ Delete Tenant",
            lambda: self._delete_tenant_popup(tree),
            RED_BG, RED, "#3a1818"),
        ])


    # ================================================================= #
    #  REGISTER PAGE                                                     #
    # ================================================================= #

    def show_register_form(self):
        self._clear()
        self._activate("  Register")
        self._page_header("Register Apartment",
                          "Add a new property to the system")

        card=self._form_card()
        form=tk.Frame(card, bg=BG_CARD, padx=32, pady=24)
        form.pack(fill="x")

        locs =["Bristol", "London", "Manchester", "Cardiff"]
        types=["Studio","1-bedroom flat","2-bedroom flat",
                 "3-bedroom house","4-bedroom house"]

        self._rv_loc  =tk.StringVar(value=locs[0])
        self._rv_type =tk.StringVar(value=types[1])
        self._rv_rent =tk.StringVar()
        self._rv_rooms=tk.StringVar()

        self._form_row(form, "Location",
            lambda r: self._combo(r, self._rv_loc, locs, 34))
        self._form_row(form, "Property Type",
            lambda r: self._combo(r, self._rv_type, types, 34))
        self._form_row(form, "Monthly Rent (£)",
            lambda r: self._entry(r, self._rv_rent, 36))
        self._form_row(form, "Number of Rooms",
            lambda r: self._entry(r, self._rv_rooms, 36))

        btn_row=tk.Frame(card, bg=BG_CARD, padx=32, pady=16)
        btn_row.pack(fill="x")
        PillButton(btn_row, "Register Apartment",
                   self._submit_register).pack(side="left")

    def _submit_register(self):
        try:
            rent_s =self._rv_rent.get().strip()
            rooms_s=self._rv_rooms.get().strip()
            if not rent_s:
                raise ValueError("monthly rent cannot be empty")
            if not rooms_s:
                raise ValueError("number of rooms cannot be empty")
            # float() for rent because rents can have pence (e.g. 1200.50)
            # int() for rooms because you cant have 2.5 rooms
            self.manager.add_apartment(
                self._rv_loc.get(), self._rv_type.get(),
                float(rent_s), int(rooms_s))
            messagebox.showinfo("Success", "Apartment registered successfully!")
            self.show_apartments()
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))





    # ================================================================= #
    #  CREATE TENANT PAGE                                                #
    # ================================================================= #

    def show_create_tenant(self):
        self._clear()
        self._activate("  Create Tenant")
        self._page_header("Create Tenant", "Add a new tenant to the system")

        card=self._form_card()
        form=tk.Frame(card, bg=BG_CARD, padx=32, pady=24)
        form.pack(fill="x")

        # form variables
        self._ct_name  =tk.StringVar()
        self._ct_email =tk.StringVar()
        self._ct_phone =tk.StringVar()
        self._ct_ni    =tk.StringVar()
        self._ct_occ   =tk.StringVar()
        self._ct_ref   =tk.StringVar()

        self._form_row(form, "Full Name", lambda r: self._entry(r, self._ct_name, 40))
        self._form_row(form, "Email", lambda r: self._entry(r, self._ct_email, 40))
        self._form_row(form, "Phone", lambda r: self._entry(r, self._ct_phone, 40))
        self._form_row(form, "NI Number", lambda r: self._entry(r, self._ct_ni, 40))
        self._form_row(form, "Occupation", lambda r: self._entry(r, self._ct_occ, 40))
        self._form_row(form, "Reference", lambda r: self._entry(r, self._ct_ref, 40))



        btn_row=tk.Frame(card, bg=BG_CARD, padx=32, pady=16)
        btn_row.pack(fill="x")
        PillButton(btn_row, "Create Tenant", 
                   self._submit_create_tenant).pack(side="left")
    
    def _submit_create_tenant(self):
        try:
            name =self._ct_name.get().strip()
            email=self._ct_email.get().strip()
            phone=self._ct_phone.get().strip()
            ni   =self._ct_ni.get().strip()
            occ  =self._ct_occ.get().strip()
            ref  =self._ct_ref.get().strip()

            # security to check if all fields are filled
            if not name or not email or not phone or not ni or not occ or not ref:
                messagebox.showerror("Error", "All fields must be filled.")
                return
            
            # email format validation
            if "@" not in email or "." not in email.split("@")[-1]:
                messagebox.showerror("Error", "Invalid email format.")
                return

            self.manager.add_tenant(name, email, phone, ni, occ, ref)

            messagebox.showinfo("Success", "Tenant created successfully!")
            self.show_assign_tenant()

        except Exception as e:
            messagebox.showerror("Error", str(e))

     

    # ================================================================= #
    #  ASSIGN TENANT PAGE                                                #
    # ================================================================= #

    def _update_lease_end(self):
        try:
            period=self._av_period.get()
            start_str=self._av_start.get()

            if not period or not start_str:
                return

            # parse inputs
            months=int(period.split()[0])
            start=datetime.strptime(start_str, "%d-%m-%Y")

            # calculate end date
            end=start + relativedelta(months=months)
            end_str=end.strftime("%d-%m-%Y")

            # update label
            self._av_end_display.set(end_str)

        except Exception:
            self._av_end_display.set("Invalid date")

    def show_assign_tenant(self):
        self._clear()
        self._activate("  Assign Tenant")
        self._page_header("Assign Tenant",
                          "Link a tenant to a vacant apartment")

        card=self._form_card()
        form=tk.Frame(card, bg=BG_CARD, padx=32, pady=24)
        form.pack(fill="x")

        # find vacant apartments
        vacant=[
            f"{a.apartment_id}  -  {a.location}  ({a.apt_type})"
            for a in self.manager.get_all_apartments()
            if a.status == "vacant"
        ]
        if not vacant:
            tk.Label(form, text="No vacant apartments available.",
                    font=("Helvetica", 12),
                    bg=BG_CARD, fg=RED, pady=20).pack()
            return

        self._av_apt=tk.StringVar(value=vacant[0])
        self._form_row(form, "Vacant Apartment",
            lambda r: self._combo(r, self._av_apt, vacant, 42))

        # getting unassigned tenants
        tenants=self.manager.get_all_tenants()
        tenant_opts=[
            f"{t.tenant_id} - {t.full_name}"
            for t in tenants
            if t.apartment_id is None
        ]

        if not tenant_opts:
            tk.Label(form, text="No unassigned tenants available.",
                    font=("Helvetica", 12),
                    bg=BG_CARD, fg=RED, pady=20).pack()
            return

        self._av_tenant=tk.StringVar(value="Select Tenant")
        self._form_row(form, "Tenant",
            lambda r: self._combo(r, self._av_tenant, tenant_opts, 42))

        
        # lease dates
        self._av_period=tk.StringVar()
        periods=["1 month", "2 months", "3 months", "6 months", "12 months"]

        self._form_row(form, "Lease Period",
            lambda r: self._combo(r, self._av_period, periods, 42))

        self._av_start=tk.StringVar()
        start_widget=self._form_row(form, "Lease Start",
            lambda r: DateEntry(r, textvariable=self._av_start, date_pattern="dd-mm-yyyy"))

        
        self._av_period.trace_add("write", lambda *args: self._update_lease_end())
        start_widget.bind("<<DateEntrySelected>>", lambda e: self._update_lease_end())


        # Lease End (auto-calculated)
        self._av_end_display=tk.StringVar(value="Select start date")
        self._form_row(form, "Lease End",
            lambda r: tk.Label(r, textvariable=self._av_end_display,
                            bg=BG_CARD, fg=TEXT_MAIN, font=("Helvetica", 11)))
        
        
        # button
        btn_row=tk.Frame(card, bg=BG_CARD, padx=32, pady=16)
        btn_row.pack(fill="x")
        PillButton(btn_row, "Assign Tenant",
                self._submit_assign).pack(side="left")
    

    def _submit_assign(self):
        try:
            apt_id=int(self._av_apt.get().split("-")[0].strip())
            apt=self.manager.get_apartment_by_id(apt_id)

            # tenant
            raw_tenant=self._av_tenant.get()
            tenant_id=int(raw_tenant.split("-")[0].strip())

            # lease dates
            start=self._av_start.get().strip()
            end_str=self._av_end_display.get()
            period=self._av_period.get().strip()


            # rent from apartment
            rent=apt.monthly_rent

            # update tenant
            self.manager.assign_tenant(
                tenant_id=tenant_id,
                apartment_id=apt_id,
                lease_period=period,
                lease_start=start,
                lease_end=end_str,
            )

            messagebox.showinfo("Success", f"Tenant assigned to apartment {apt_id}.")
            self.show_apartments()
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))

    # ================================================================= #
    #  MAINTENANCE REQUESTS PAGE                                         #
    # ================================================================= #

    def show_maintenance(self):
        self._clear()
        self._activate("  All Requests")
        self._page_header("Maintenance Requests",
                          "Track and resolve property issues")

        reqs  =self.manager.get_all_maintenance_requests()
        open_n=sum(1 for r in reqs if r.status == "open")
        self._stats_row([
            (len(reqs),        "Total",    TEXT_MUTED),
            (open_n,           "Open",     AMBER),
            (len(reqs)-open_n, "Resolved", TEAL),
        ])

        cols   =("ID","Apt","Description","Priority",
                   "Status","Raised","Resolved","Cost (£)","Hrs")
        widths =[48,48,240,88,82,90,90,85,52]
        anchors=["center","center","w","center",
                   "center","center","center","center","center"]
        tree=self._table_frame(cols, widths, anchors)

        # unicode icons make the priority column easier to read at a glance
        prio_icons={"High": "▲ HIGH", "Medium": "◆ MED", "Low": "▼ LOW"}

        for i, r in enumerate(reqs):
            row_tag="odd" if i % 2 else ""
            prio   =prio_icons.get(r.priority, r.priority.upper())
            tree.insert("", "end", values=(
                r.request_id, r.apartment_id, r.description,
                prio, r.status.upper(), r.date_raised,
                r.date_resolved or "-",
                f"£{r.cost:.2f}" if r.cost is not None else "-",
                r.time_taken or "-"
            ), tags=(r.status, row_tag))

        self._btn_row([
            ("✔  Resolve Selected",
             lambda: self._resolve_popup(tree),
             TEAL_BG, TEAL, "#0f2e2a"),
        ])

    # ================================================================= #
    #  NEW MAINTENANCE REQUEST PAGE                                      #
    # ================================================================= #

    def show_maintenance_form(self):
        self._clear()
        self._activate("  New Request")
        self._page_header("New Maintenance Request",
                          "Report an issue with a property")

        card=self._form_card()
        form=tk.Frame(card, bg=BG_CARD, padx=32, pady=24)
        form.pack(fill="x")

        apts=self.manager.get_all_apartments()
        opts=[f"{a.apartment_id}  -  {a.location}  ({a.apt_type})"
                for a in apts]

        if not opts:
            tk.Label(form, text="No apartments registered yet.",
                     font=("Helvetica", 12),
                     bg=BG_CARD, fg=RED, pady=20).pack()
            return

        self._mv_apt =tk.StringVar(value=opts[0])
        self._mv_prio=tk.StringVar(value="Medium")
        self._mv_desc=tk.StringVar()

        self._form_row(form, "Apartment",
            lambda r: self._combo(r, self._mv_apt, opts, 44))
        self._form_row(form, "Priority",
            lambda r: self._combo(r, self._mv_prio,
                                  ["Low","Medium","High"], 24))
        self._form_row(form, "Description",
            lambda r: self._entry(r, self._mv_desc, 46))

        btn_row=tk.Frame(card, bg=BG_CARD, padx=32, pady=16)
        btn_row.pack(fill="x")
        PillButton(btn_row, "Submit Request",
                   self._submit_maintenance).pack(side="left")

    def _submit_maintenance(self):
        try:
            raw   =self._mv_apt.get()
            apt_id=int(raw.split("-")[0].strip())
            desc  =self._mv_desc.get().strip()
            prio  =self._mv_prio.get().strip()
            if not desc:
                raise ValueError("description cannot be empty")
            self.manager.add_maintenance_request(apt_id, desc, prio)
            messagebox.showinfo("Success", "Maintenance request submitted.")
            self.show_maintenance()
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))

    # ================================================================= #
    #  POPUPS                                                            #
    # ================================================================= #

    def _popup(self, title, w, h):
        # toplevel creates a new window on top of the main one
        # grab_set() makes it modal so you have to close it before using the main window
        # the geometry calculation centres it over the parent window
        p=tk.Toplevel(self.root)
        p.title(title)
        p.configure(bg=BG_SURFACE)
        p.resizable(False, False)
        p.grab_set()

        # update_idletasks() forces tkinter to recalculate window sizes
        # without this winfo_x() and winfo_width() return 0
        self.root.update_idletasks()
        x=self.root.winfo_x() + (self.root.winfo_width()  - w) // 2
        y=self.root.winfo_y() + (self.root.winfo_height() - h) // 2
        p.geometry(f"{w}x{h}+{x}+{y}")

        # same title bar style as the main pages
        hdr=tk.Frame(p, bg=BG_SURFACE)
        hdr.pack(fill="x", padx=36, pady=(22, 0))
        tk.Frame(hdr, bg=TEAL, width=3).pack(side="left", fill="y")
        tk.Label(hdr, text=title, font=("Helvetica", 13, "bold"),
                 bg=BG_SURFACE, fg=TEXT_BRIGHT, padx=10).pack(side="left")
        tk.Frame(p, bg=BORDER, height=1).pack(fill="x", padx=36, pady=(10, 8))

        return p

    def _resolve_popup(self, tree):
        sel=tree.selection()
        if not sel:
            messagebox.showwarning("Nothing selected",
                                   "Select a request to resolve.")
            return
        vals=tree.item(sel[0])["values"]

        # vals[4] is the Status column - check its not already resolved
        if "RESOLVED" in str(vals[4]):
            messagebox.showinfo("Already resolved",
                                "This request is already resolved.")
            return

        p   =self._popup(f"Resolve Request #{vals[0]}", 460, 500)
        form=tk.Frame(p, bg=BG_SURFACE, padx=36)
        form.pack(fill="x")

        tk.Label(p, text=f"Apt {vals[1]}  ·  {vals[2]}",
                 font=("Helvetica", 9), bg=BG_SURFACE, fg=TEXT_MUTED
                 ).pack(pady=(0, 14))

        cost_v=tk.StringVar()
        time_v=tk.StringVar()
        for lbl, var in [("Cost (£)", cost_v), ("Time taken (hrs)", time_v)]:
            row=tk.Frame(form, bg=BG_SURFACE)
            row.pack(fill="x", pady=6)
            tk.Label(row, text=lbl, font=("Helvetica", 10),
                     bg=BG_SURFACE, fg=TEXT_MUTED,
                     width=18, anchor="w").pack(side="left")
            self._entry(row, var, 20).pack(side="left", padx=(8,0), ipady=5)

        def confirm():
            try:
                c=cost_v.get().strip()
                t=time_v.get().strip()
                if not c or not t:
                    raise ValueError("both fields are required")
                self.manager.resolve_maintenance_request(
                    vals[0], float(c), int(t))
                messagebox.showinfo("Done", "Request marked as resolved.")
                p.destroy()
                self.show_maintenance()
            except ValueError as e:
                messagebox.showerror("Input Error", str(e))

        PillButton(p, "Confirm Resolution", confirm).pack(pady=20)

    def _edit_popup(self, tree):
        sel=tree.selection()
        if not sel:
            messagebox.showwarning("Nothing selected",
                                   "Select an apartment to edit.")
            return
        vals  =tree.item(sel[0])["values"]
        apt_id=vals[0]

        p   =self._popup(f"Edit Apartment #{apt_id}", 460, 500)
        form=tk.Frame(p, bg=BG_SURFACE, padx=36)
        form.pack(fill="x", pady=8)

        # the rent value comes in formatted as "£1,200.00" from the table
        # so we need to strip the £ and commas before putting it back in an entry field
        rent_str=str(vals[3]).replace("£","").replace(",","").strip()
        v_loc   =tk.StringVar(value=vals[1])
        v_type  =tk.StringVar(value=vals[2])
        v_rent  =tk.StringVar(value=rent_str)
        v_rooms =tk.StringVar(value=str(vals[4]))

        locs =["Bristol","London","Manchester","Cardiff"]
        types=["Studio","1-bedroom flat","2-bedroom flat",
                 "3-bedroom house","4-bedroom house"]

        for lbl, var, opts in [
            ("Location",      v_loc,  locs),
            ("Property Type", v_type, types),
        ]:
            row=tk.Frame(form, bg=BG_SURFACE)
            row.pack(fill="x", pady=6)
            tk.Label(row, text=lbl, font=("Helvetica", 10),
                     bg=BG_SURFACE, fg=TEXT_MUTED,
                     width=18, anchor="w").pack(side="left")
            self._combo(row, var, opts, 28).pack(
                side="left", padx=(8,0), ipady=5)

        for lbl, var in [("Monthly Rent (£)", v_rent), ("Rooms", v_rooms)]:
            row=tk.Frame(form, bg=BG_SURFACE)
            row.pack(fill="x", pady=6)
            tk.Label(row, text=lbl, font=("Helvetica", 10),
                     bg=BG_SURFACE, fg=TEXT_MUTED,
                     width=18, anchor="w").pack(side="left")
            self._entry(row, var, 30).pack(
                side="left", padx=(8,0), ipady=5)

        def save():
            try:
                r_s=v_rent.get().strip()
                r_n=v_rooms.get().strip()
                if not r_s or not r_n:
                    raise ValueError("rent and rooms cannot be empty")
                self.manager.update_apartment(
                    apt_id, v_loc.get(), v_type.get(),
                    float(r_s), int(r_n))
                messagebox.showinfo("Updated", "Apartment saved.")
                p.destroy()
                self.show_apartments()
            except ValueError as e:
                messagebox.showerror("Input Error", str(e))

        PillButton(p, "Save Changes", save).pack(pady=20)

    def _delete_apartment(self, tree):
        sel=tree.selection()
        if not sel:
            messagebox.showwarning("Nothing selected",
                                   "Select an apartment to delete.")
            return
        apt_id=tree.item(sel[0])["values"][0]
        # confirm before deleting - the manager will also block it if there are open requests
        if messagebox.askyesno("Confirm Delete",
                f"Delete apartment {apt_id}?\nThis cannot be undone."):
            try:
                self.manager.delete_apartment(apt_id)
                messagebox.showinfo("Deleted", "Apartment removed.")
                self.show_apartments()
            except ValueError as e:
                # this catches the "open maintenance requests" error from apartment.py
                messagebox.showerror("Cannot Delete", str(e))

    def _remove_tenant(self, tree):
        sel=tree.selection()
        if not sel:
            messagebox.showwarning("Nothing selected", "Select an apartment.")
            return
        vals  =tree.item(sel[0])["values"]
        apt_id=vals[0]
        # vals[5] is the Status column - check the dot symbol for vacant
        if "Vacant" in str(vals[5]):
            messagebox.showinfo("Already vacant",
                                "This apartment has no tenant.")
            return
        if messagebox.askyesno("Confirm",
                f"Remove tenant from apartment {apt_id}?"):
            self.manager.remove_tenant(apt_id)
            messagebox.showinfo("Done", "Tenant removed. Apartment is now vacant.")
            self.show_apartments()

    # ============================= #
    # TENANT MANAGEMENT FEATURES
    # ============================= #

    def _tenant_popup(self, tree):
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select an apartment first")
            return

        vals = tree.item(sel[0])["values"]
        tenant_id = vals[6]

        if tenant_id == "-" or tenant_id is None:
            messagebox.showinfo("No Tenant", "No tenant assigned")
            return

        p = self._popup(f"Edit Tenant #{tenant_id}", 400, 300)
        # payment status label
        status = "⚠ Overdue" if check_late_payment_tenant(tenant_id) else "✅ Up to date"

        tk.Label(p,
            text=f"Payment Status: {status}",
            bg=BG_SURFACE,
            fg=RED if "Overdue" in status else TEAL,
            font=("Helvetica", 10, "bold")
        ).pack(pady=5)

        name = tk.StringVar()
        email = tk.StringVar()
        phone = tk.StringVar()

        for lbl, var in [("Name", name), ("Email", email), ("Phone", phone)]:
            row = tk.Frame(p, bg=BG_SURFACE)
            row.pack(pady=6)
            tk.Label(row, text=lbl, bg=BG_SURFACE, fg=TEXT_MUTED, width=10).pack(side="left")
            tk.Entry(row, textvariable=var).pack(side="left")

        def save():
            if not messagebox.askyesno("Confirm", "Save changes to tenant details?"):
                return

            edit_tenant(tenant_id, name.get(), email.get(), phone.get())
            messagebox.showinfo("Success", "Tenant updated")
            p.destroy()

        PillButton(p, "Save", save).pack(pady=10)
        PillButton(p, "Payment History",
           lambda: self._payment_history_popup(tree)).pack(pady=5)


    def _view_lease_popup(self, tree):
        sel = tree.selection()
        if not sel:
            return

        tenant_id = tree.item(sel[0])["values"][6]

        if tenant_id == "-":
            messagebox.showinfo("No tenant", "No tenant assigned")
            return

        data = get_lease_details(tenant_id)

        if not data:
            messagebox.showinfo("No lease", "No lease found")
            return

        p = self._popup("Lease Details", 350, 300)

        for k, v in data.items():
            if k == "Monthly Rent":
                v = f"£{float(v):.2f}"
            tk.Label(p, text=f"{k}: {v}",
                     bg=BG_SURFACE, fg=TEXT_MAIN).pack(pady=3)
        try:
            fee = calculate_early_termination_fee(tenant_id)

            tk.Label(p,
                text=f"Termination Fee: £{fee:.2f} + One months notice",
                bg=BG_SURFACE, fg=AMBER).pack(pady=10)

        except Exception:
            tk.Label(p,
                text="Could not calculate termination fee",
                bg=BG_SURFACE, fg=RED).pack(pady=10)
        
        

#fix here 
    def _check_late_popup(self, tree):
        sel = tree.selection()
        if not sel:
            return

        tenant_id = tree.item(sel[0])["values"][6]

        if tenant_id == "-":
            return

        if check_late_payment_tenant(tenant_id):
            messagebox.showwarning("Late Payment", "⚠ This tenant has overdue payments")

            # simulate notification being sent to tenant
            messagebox.showinfo("Notification Sent", "Tenant has been notified of late payment via email and SMS")
        else:
            messagebox.showinfo("OK", "No late payments")


    def _delete_tenant_popup(self, tree):
        sel = tree.selection()
        if not sel:
            return

        tenant_id = tree.item(sel[0])["values"][6]

        if tenant_id == "-":
            return

        if messagebox.askyesno("Confirm", "Delete this tenant completely?"):
            delete_tenant(tenant_id)
            messagebox.showinfo("Deleted", "Tenant removed from system")
            self.show_apartments()


# Payment history and early termination fee popups, which are accessible from the apartment page but pull data from the finance module
    def _payment_history_popup(self, tree):
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select an apartment first")
            return

        tenant_id = tree.item(sel[0])["values"][6]

        if tenant_id == "-" or tenant_id is None:
            messagebox.showinfo("No Tenant", "No tenant assigned")
            return

        # get invoices for tenant
        invoices = self.finance.get_all_invoices()

        tenant_invoices = [i for i in invoices if i["tenant_id"] == tenant_id]

        if not tenant_invoices:
            messagebox.showinfo("No Data", "No payment history found")
            return

        p = self._popup(f"Payment History - Tenant {tenant_id}", 500, 400)

        for inv in tenant_invoices:
            text = f"Invoice {inv['invoice_id']} | £{inv['amount']:.2f} | {inv['status']} | Due: {inv['due_date']}"
            tk.Label(p, text=text, bg=BG_SURFACE, fg=TEXT_MAIN).pack(anchor="w", padx=10, pady=3)


    def _termination_fee_popup(self, tree):
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select an apartment first")
            return

        tenant_id = tree.item(sel[0])["values"][6]

        if tenant_id == "-" or tenant_id is None:
            messagebox.showinfo("No Tenant", "No tenant assigned")
            return

        try:
            fee = calculate_early_termination_fee(tenant_id)

            messagebox.showinfo(
                "Early Termination Fee",
                f"Tenant must pay:\n\n£{fee:.2f}\n\n(1 month notice + 5%)"
            )

        except Exception as e:
            messagebox.showerror("Error", str(e))



    # ================================================================= #
    #  PAYMENTS                                                         #
    # ================================================================= #


    def show_payments(self):
        self._clear()
        self._activate("  Payments Overview")
        self._page_header("Payments & Billing", "All invoices and payment statuses")

        #from payments import get_all_invoices  

        invoices=self.finance.get_all_invoices()
        paid=sum(1 for i in invoices if i["status"] == "paid" or i["status"] == "paid (late)")
        overdue=sum(1 for i in invoices if i["status"] == "overdue")

        if overdue > 0:
            tk.Label(self.main,
                    text=f"⚠ {overdue} late payment(s) detected",
                    font=("Helvetica", 12, "bold"),
                    bg=BG_BASE, fg=AMBER).pack(padx=32, pady=(10, 0))
        else:
            tk.Label(self.main,
                    text="No overdue payments",
                    font=("Helvetica", 10),
                    bg=BG_BASE, fg=TEXT_MUTED).pack(padx=32, pady=(10, 0))

        self._stats_row([
            (len(invoices), "Total Invoices", TEXT_MUTED),
            (paid, "Paid", TEAL),
            (overdue, "Overdue", RED),
        ])

        cols=("ID", "Tenant", "Apt", "Amount", "Due", "Status")
        widths=[60, 160, 80, 100, 120, 120]
        tree=self._table_frame(cols, widths)

        for i, inv in enumerate(invoices):
            tag="odd" if i % 2 else ""
            tree.insert("", "end", values=(
                inv["invoice_id"],
                inv["tenant_name"],
                inv["apartment_id"],
                f"£{inv['amount']:.2f}",
                inv["due_date"],
                inv["status"].upper()
            ), tags=(inv["status"], tag))


    def _date_entry(self, parent):
        wrapper=tk.Frame(parent, bg=BG_CARD)
        wrapper.bind_all("<Button-1>", lambda e: None)

        entry=DateEntry(
            wrapper,
            textvariable=self._inv_due,
            date_pattern="dd-mm-yyyy",
            showweeknumbers=False,
            borderwidth=1,
            width=37
        )
        entry.pack()
        return wrapper


    def _update_invoice_amount(self, event=None):
        raw=self._inv_tenant.get()

        # extract apartment_id from "(Apt X)"
        apt_id=int(raw.split("Apt")[1].strip().replace(")", ""))

        # get rent from apartment
        apt=self.manager.get_apartment_by_id(apt_id)
        rent=apt.monthly_rent

        # update the label
        self._inv_amount.set(f"£{rent:.2f}")


    def show_invoice_form(self):
        self._clear()
        self._activate("  Generate Invoice")
        self._page_header("Generate Invoice", "Create a new rent invoice")

        card=self._form_card()
        form=tk.Frame(card, bg=BG_CARD, padx=32, pady=24)
        form.pack(fill="x")

        #from payments import get_active_tenants

        tenants=self.finance.get_active_tenants()
        opts=[f"{t['tenant_id']} - {t['full_name']} (Apt {t['apartment_id']})" for t in tenants]

        self._inv_tenant=tk.StringVar(value="Select Tenant")
        self._inv_amount=tk.StringVar(value="£0.00")
        self._inv_due=tk.StringVar()

        tenant_combo=self._form_row(form, "Tenant", lambda r: self._combo(r, self._inv_tenant, opts, 42))
        tenant_combo.bind("<<ComboboxSelected>>", self._update_invoice_amount)
        self._form_row(form, "Amount (£)", lambda r: tk.Label(
            r, textvariable=self._inv_amount,
            bg=BG_CARD, fg=TEXT_MAIN, font=("Helvetica", 11)
        ))
        self._form_row(form, "Due Date", self._date_entry)


        btn_row=tk.Frame(card, bg=BG_CARD, padx=32, pady=16)
        btn_row.pack(fill="x")
        PillButton(btn_row, "Create Invoice", self._submit_invoice).pack(side="left")


    def _submit_invoice(self):
        #from payments import create_invoice, create_pending_payment

        try:
            raw=self._inv_tenant.get()
            # extract tenant_id
            tenant_id=int(raw.split("-")[0].strip())

            # extract apartment_id from "(Apt X)"
            apt_id=int(raw.split("Apt")[1].strip().replace(")", ""))

          # get monthly rent from apartment manager
            apt=self.manager.get_apartment_by_id(apt_id)
            amount=apt.monthly_rent
            due=self._inv_due.get()

            invoice_id=self.finance.create_invoice(tenant_id, apt_id, amount, due)
            self.finance.create_pending_payment(invoice_id, tenant_id, apt_id, amount, due)

            messagebox.showinfo("Success", "Invoice created successfully!")
            self.show_payments()

        except Exception as e:
            messagebox.showerror("Error", str(e))

    #record payment page

    def show_record_payment(self):
        self._clear()
        self._activate("  Record Payment")
        self._page_header("Record Payment", "Mark an invoice as paid")

        card=self._form_card()
        form=tk.Frame(card, bg=BG_CARD, padx=32, pady=24)
        form.pack(fill="x")

        #from payments import get_unpaid_invoices

        invoices=self.finance.get_unpaid_invoices()
        opts=[f"{i['invoice_id']} - {i['tenant_name']} (£{i['amount']:.2f})" for i in invoices]

        self._pay_invoice=tk.StringVar(value=opts[0])

        self._form_row(form, "Invoice", lambda r: self._combo(r, self._pay_invoice, opts, 42))

        btn_row=tk.Frame(card, bg=BG_CARD, padx=32, pady=16)
        btn_row.pack(fill="x")
        PillButton(btn_row, "Mark as Paid", self._submit_payment).pack(side="left")

    def _submit_payment(self):
        #from payments import mark_payment_as_paid

        invoice_id=int(self._pay_invoice.get().split("-")[0].strip())
        self.finance.mark_payment_as_paid(invoice_id)

        payment_id=self.finance.get_payment_id_by_invoice(invoice_id)

        messagebox.showinfo("Success", "Payment recorded successfully!")
        # show receipt popup
        if payment_id:
            self._show_receipt(payment_id)

        self.show_payments()

    def _show_receipt(self, payment_id):
        #from payments import generate_receipt
        data=self.finance.generate_receipt(payment_id)
        paid_date=datetime.strptime(data['paid_date'], "%Y-%m-%d").strftime("%d-%m-%Y")

        p=self._popup("Payment Receipt", 420, 360)
        tk.Label(p, text=f"Tenant: {data['tenant']}", bg=BG_SURFACE, fg=TEXT_MAIN).pack(pady=4)
        tk.Label(p, text=f"Apartment: {data['apartment']}", bg=BG_SURFACE, fg=TEXT_MAIN).pack(pady=4)
        tk.Label(p, text=f"Amount Paid: £{data['amount']:.2f}", bg=BG_SURFACE, fg=TEXT_MAIN).pack(pady=4)
        tk.Label(p, text=f"Paid Date: {paid_date}", bg=BG_SURFACE, fg=TEXT_MAIN).pack(pady=4)


# ------------------------------------------------------------------ #
#  entry point                                                        #
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    root=tk.Tk()
    app =ApartmentApp(root)
    root.mainloop()