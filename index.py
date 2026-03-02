import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np
import os


class SignatureToPNGApp:
    def __init__(self, root):
        self.root = root
        root.title("Sign2PNG - Transparent Signature")
        root.geometry("800x700")
        root.resizable(True, True)

        # Variables
        self.threshold = tk.IntVar(value=200)
        self.auto_crop = tk.BooleanVar(value=True)
        self.original_image = None          # numpy array (RGBA)
        self.processed_image = None         # PIL Image for display
        self.image_tk = None                 # ImageTk for canvas
        self.filename = None

        # Max dimension for resizing
        self.MAX_DIM = 1200

        self.create_widgets()

    def create_widgets(self):
        # Title
        title_frame = tk.Frame(self.root)
        title_frame.pack(fill='x', padx=20, pady=(20, 0))
        title = tk.Label(title_frame, text="✍️ Sign2PNG",
                         font=('Inter', 24, 'bold'), fg="#0a2c3d")
        title.pack(side='left')
        badge = tk.Label(title_frame, text="transparent",
                         bg="#0a2c3d", fg="white",
                         font=('Inter', 10, 'bold'), padx=8, pady=2)
        badge.pack(side='left', padx=10)

        # Subtitle
        sub = tk.Label(self.root,
                       text="Upload a photo of your signature – white / light background works best. "
                            "Dark ink stays, background becomes see‑through.",
                       wraplength=700, justify='left', fg="#3e5e6f",
                       font=('Inter', 10), padx=20)
        sub.pack(pady=(5, 10))

        # File selection
        file_frame = tk.Frame(self.root)
        file_frame.pack(fill='x', padx=20, pady=10)

        self.file_btn = tk.Button(file_frame, text="📁 Choose signature image",
                                  command=self.load_image,
                                  bg="white", bd=2, relief='groove',
                                  font=('Inter', 10))
        self.file_btn.pack(side='left')
        self.file_label = tk.Label(file_frame, text="No file selected",
                                   fg="#2b6f84", font=('Inter', 9))
        self.file_label.pack(side='left', padx=10)

        # Preview area (solid light gray background simulates transparency)
        preview_frame = tk.Frame(self.root, bg="#e0e7eb", bd=1, relief='sunken')
        preview_frame.pack(padx=20, pady=10, fill='both', expand=True)

        self.canvas = tk.Canvas(preview_frame, bg="#e0e7eb", highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)

        # Control panel
        control_frame = tk.Frame(self.root, bg="#ffffffd6", bd=1, relief='flat')
        control_frame.pack(fill='x', padx=20, pady=10)

        # Slider row
        slider_frame = tk.Frame(control_frame)
        slider_frame.pack(fill='x', padx=20, pady=10)

        tk.Label(slider_frame, text="🔆 Threshold",
                 font=('Inter', 10, 'bold'), fg="#1a495a").pack(side='left')
        self.threshold_slider = tk.Scale(slider_frame, from_=0, to=255,
                                         orient='horizontal',
                                         variable=self.threshold,
                                         command=self.on_threshold_change,
                                         length=300, showvalue=False)
        self.threshold_slider.pack(side='left', padx=10)
        self.threshold_display = tk.Label(slider_frame,
                                          text=str(self.threshold.get()),
                                          bg="#0f4b5e", fg="white",
                                          font=('Inter', 9, 'bold'), width=5)
        self.threshold_display.pack(side='left')

        # Auto‑crop checkbox
        self.crop_check = tk.Checkbutton(slider_frame,
                                         text="✂️ Auto‑crop to signature",
                                         variable=self.auto_crop,
                                         font=('Inter', 9),
                                         command=self.on_crop_change)
        self.crop_check.pack(side='left', padx=20)

        # Download button
        self.download_btn = tk.Button(control_frame,
                                      text="⬇️ Download transparent PNG (lossless)",
                                      command=self.save_image,
                                      bg="#0f4b5e", fg="white",
                                      font=('Inter', 12, 'bold'),
                                      padx=20, pady=8, bd=0, cursor='hand2')
        self.download_btn.pack(pady=(0, 15))

        # Note
        note_frame = tk.Frame(control_frame)
        note_frame.pack(fill='x', padx=20, pady=(0, 10))
        note_label = tk.Label(note_frame,
                              text="ⓘ Move threshold until background disappears. "
                                   "Darker = more transparent. Auto‑crop removes empty space.",
                              font=('Inter', 8), fg="#3a606e")
        note_label.pack()

        # Footer
        footer = tk.Label(self.root,
                          text="⚡ instant processing · no upload · pure Python",
                          fg="#5e7e8c", font=('Inter', 8))
        footer.pack(pady=(0, 10))

    def on_threshold_change(self, val):
        self.threshold_display.config(text=str(self.threshold.get()))
        self.process_image()

    def on_crop_change(self):
        self.process_image()

    def load_image(self):
        file_path = filedialog.askopenfilename(
            title="Select signature image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.webp"),
                       ("All files", "*.*")]
        )
        if not file_path:
            return

        self.filename = os.path.basename(file_path)
        self.file_label.config(text=self.filename)

        try:
            img = Image.open(file_path).convert("RGBA")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load image:\n{e}")
            return

        # Resize if too large (keep aspect ratio)
        width, height = img.size
        if width > self.MAX_DIM or height > self.MAX_DIM:
            ratio = min(self.MAX_DIM / width, self.MAX_DIM / height)
            new_size = (int(width * ratio), int(height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        # Convert to numpy array and force alpha to 255 (opaque)
        arr = np.array(img)
        arr[:, :, 3] = 255   # ensure full opacity (image may have had alpha)

        self.original_image = arr
        self.process_image()

    def process_image(self):
        if self.original_image is None:
            return

        arr = self.original_image.copy()
        threshold = self.threshold.get()

        # Compute luminance (Rec. 709)
        r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
        luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b

        # Background = luminance above threshold → transparent
        mask = luminance > threshold
        arr[mask, 3] = 0

        # Auto‑crop if enabled
        if self.auto_crop.get():
            alpha = arr[:, :, 3]
            rows = np.any(alpha > 0, axis=1)
            cols = np.any(alpha > 0, axis=0)
            if np.any(rows) and np.any(cols):
                y_min, y_max = np.where(rows)[0][[0, -1]]
                x_min, x_max = np.where(cols)[0][[0, -1]]
                arr = arr[y_min:y_max + 1, x_min:x_max + 1, :]
            # else: no opaque pixels – keep current (will be fully transparent)

        self.processed_image = Image.fromarray(arr, 'RGBA')
        self.display_image(self.processed_image)

    def display_image(self, pil_image):
        # Get current canvas size
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width <= 1 or canvas_height <= 1:
            # Canvas not ready yet – try again after a short delay
            self.root.after(100, lambda: self.display_image(pil_image))
            return

        img_width, img_height = pil_image.size
        # Scale to fit canvas while preserving aspect ratio (no enlargement)
        scale = min(canvas_width / img_width, canvas_height / img_height, 1)
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)

        if scale < 1:
            pil_resized = pil_image.resize((new_width, new_height),
                                           Image.Resampling.LANCZOS)
        else:
            pil_resized = pil_image

        self.image_tk = ImageTk.PhotoImage(pil_resized)

        # Clear canvas and draw image centered
        self.canvas.delete("all")
        self.canvas.create_image(canvas_width // 2, canvas_height // 2,
                                 image=self.image_tk, anchor='center')

    def save_image(self):
        if self.processed_image is None:
            messagebox.showwarning("No image",
                                   "Please load and process an image first.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
            initialfile="signature_transparent.png"
        )
        if file_path:
            self.processed_image.save(file_path, "PNG")
            messagebox.showinfo("Saved", f"Image saved to:\n{file_path}")


if __name__ == "__main__":
    root = tk.Tk()
    app = SignatureToPNGApp(root)
    root.mainloop()
