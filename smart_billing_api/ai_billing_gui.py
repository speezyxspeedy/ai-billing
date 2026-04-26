import tkinter as tk
from tkinter import ttk, messagebox
import requests

API_BASE_URL = "http://127.0.0.1:8000"


class AIBillingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Billing GUI")
        self.root.geometry("950x650")
        self.root.configure(bg="#f4f4f4")

        self.create_widgets()

    def create_widgets(self):
        title = tk.Label(
            self.root,
            text="AI BILLING AGENT",
            font=("Arial", 20, "bold"),
            bg="#f4f4f4",
            fg="#222"
        )
        title.pack(pady=15)

        input_frame = tk.Frame(self.root, bg="#f4f4f4")
        input_frame.pack(pady=10, fill="x", padx=20)

        tk.Label(
            input_frame,
            text="Enter Bill Text:",
            font=("Arial", 12, "bold"),
            bg="#f4f4f4"
        ).pack(anchor="w")

        self.bill_input = tk.Text(input_frame, height=4, font=("Arial", 12))
        self.bill_input.pack(fill="x", pady=8)

        example_label = tk.Label(
            input_frame,
            text='Example: 2 sugar, 1 milk, 3 tea',
            font=("Arial", 10),
            bg="#f4f4f4",
            fg="gray"
        )
        example_label.pack(anchor="w")

        button_frame = tk.Frame(self.root, bg="#f4f4f4")
        button_frame.pack(pady=10)

        tk.Button(
            button_frame,
            text="Generate AI Bill",
            width=18,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 11, "bold"),
            command=self.generate_bill
        ).grid(row=0, column=0, padx=8)

        tk.Button(
            button_frame,
            text="Clear",
            width=12,
            bg="#f44336",
            fg="white",
            font=("Arial", 11, "bold"),
            command=self.clear_screen
        ).grid(row=0, column=1, padx=8)

        tk.Button(
            button_frame,
            text="Get Products",
            width=12,
            bg="#2196F3",
            fg="white",
            font=("Arial", 11, "bold"),
            command=self.load_products
        ).grid(row=0, column=2, padx=8)

        self.status_label = tk.Label(
            self.root,
            text="Ready",
            font=("Arial", 11),
            bg="#f4f4f4",
            fg="blue"
        )
        self.status_label.pack(pady=5)

        table_frame = tk.Frame(self.root)
        table_frame.pack(fill="both", expand=True, padx=20, pady=15)

        columns = ("item_name", "quantity", "price", "gst", "line_total")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=14)

        self.tree.heading("item_name", text="Item")
        self.tree.heading("quantity", text="Qty")
        self.tree.heading("price", text="Price")
        self.tree.heading("gst", text="GST %")
        self.tree.heading("line_total", text="Line Total")

        self.tree.column("item_name", width=260)
        self.tree.column("quantity", width=80)
        self.tree.column("price", width=100)
        self.tree.column("gst", width=80)
        self.tree.column("line_total", width=120)

        self.tree.pack(fill="both", expand=True)

        self.total_label = tk.Label(
            self.root,
            text="Grand Total: ₹0.00",
            font=("Arial", 18, "bold"),
            bg="#f4f4f4",
            fg="green"
        )
        self.total_label.pack(pady=12)

        self.products_box = tk.Text(self.root, height=8, font=("Arial", 10))
        self.products_box.pack(fill="x", padx=20, pady=10)
        self.products_box.insert("1.0", "Products list will appear here...")
        self.products_box.config(state="disabled")

    def clear_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

    def clear_screen(self):
        self.bill_input.delete("1.0", tk.END)
        self.clear_table()
        self.total_label.config(text="Grand Total: ₹0.00")
        self.status_label.config(text="Cleared", fg="blue")

    def generate_bill(self):
        bill_text = self.bill_input.get("1.0", tk.END).strip()

        if not bill_text:
            messagebox.showwarning("Warning", "Please enter bill text.")
            return

        self.status_label.config(text="Generating AI bill...", fg="orange")
        self.root.update_idletasks()

        try:
            response = requests.post(
                f"{API_BASE_URL}/ai/auto-bill",
                json={"text": bill_text},
                timeout=15
            )

            data = response.json()

            self.clear_table()

            if "items" not in data or not data["items"]:
                self.total_label.config(text="Grand Total: ₹0.00")
                self.status_label.config(
                    text=data.get("message", "No items matched"),
                    fg="red"
                )
                return

            for item in data["items"]:
                self.tree.insert("", tk.END, values=(
                    item["item_name"],
                    item["quantity"],
                    f"{item['price']:.2f}",
                    f"{item['gst']:.2f}",
                    f"{item['line_total']:.2f}"
                ))

            grand_total = data.get("grand_total", 0)
            bill_id = data.get("bill_id", "-")

            self.total_label.config(text=f"Grand Total: ₹{grand_total:.2f}")
            self.status_label.config(
                text=f"Bill generated successfully | Bill ID: {bill_id}",
                fg="green"
            )

        except requests.exceptions.ConnectionError:
            messagebox.showerror(
                "Connection Error",
                "API server is not running.\n\nFirst start server with:\npython -m uvicorn billing_api:app --reload"
            )
            self.status_label.config(text="API connection failed", fg="red")

        except Exception as e:
            messagebox.showerror("Error", f"Something went wrong:\n{str(e)}")
            self.status_label.config(text="Error generating bill", fg="red")

    def load_products(self):
        self.status_label.config(text="Loading products...", fg="orange")
        self.root.update_idletasks()

        try:
            response = requests.get(f"{API_BASE_URL}/products", timeout=15)
            data = response.json()

            self.products_box.config(state="normal")
            self.products_box.delete("1.0", tk.END)

            if not data:
                self.products_box.insert("1.0", "No products found.")
            else:
                for item in data:
                    line = f"{item['item_name']} | ₹{item['price']} | GST {item['gst']}%\n"
                    self.products_box.insert(tk.END, line)

            self.products_box.config(state="disabled")
            self.status_label.config(text="Products loaded", fg="green")

        except requests.exceptions.ConnectionError:
            messagebox.showerror(
                "Connection Error",
                "API server is not running.\n\nFirst start server with:\npython -m uvicorn billing_api:app --reload"
            )
            self.status_label.config(text="API connection failed", fg="red")

        except Exception as e:
            messagebox.showerror("Error", f"Could not load products:\n{str(e)}")
            self.status_label.config(text="Error loading products", fg="red")


if __name__ == "__main__":
    root = tk.Tk()
    app = AIBillingGUI(root)
    root.mainloop()