import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk # Import ttk for Notebook widget
import re # Import regex for syntax highlighting

class CodeEditor(tk.Tk):
    """
    A simple code editor application similar to Notepad++ using Tkinter.
    It provides basic functionalities like creating new files, opening existing files,
    saving files, saving files with a new name, line numbers, and basic syntax highlighting.
    Now with tabbed interface.
    """
    def __init__(self):
        super().__init__()
        self.title("Breeze Code Editor")
        self.geometry("1000x700") # Increased size for line numbers

        # --- Tab Control ---
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.tabs = [] # List to hold tab information: {'frame', 'text_area', 'line_numbers', 'current_file_path', 'file_type'}
        self.add_new_tab() # Start with one new tab

        # Create the menu bar
        self.create_menus()

        # Set a protocol for closing the window to handle unsaved changes
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Bind the tab change event
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)

    def add_new_tab(self, file_path=None, content=""):
        """
        Adds a new tab to the notebook.
        """
        tab_frame = tk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="Untitled" if file_path is None else file_path.split('/')[-1])

        # Configure tab_frame grid
        tab_frame.grid_rowconfigure(0, weight=1)
        tab_frame.grid_columnconfigure(1, weight=1)

        # --- Line Numbers Canvas for this tab ---
        line_numbers = tk.Canvas(tab_frame, width=40, bg="#282c34", highlightthickness=0) # Dark background
        line_numbers.grid(row=0, column=0, sticky="nswe")

        # --- Text Area for this tab ---
        text_area = tk.Text(
            tab_frame,
            wrap="word",
            undo=True,
            bg="#282c34", # Dark background
            fg="#abb2bf", # Light foreground
            insertbackground="#abb2bf", # Cursor color
            selectbackground="#4b5263", # Selection background
            font=("Consolas", 11) # Monospace font for code
        )
        text_area.grid(row=0, column=1, sticky="nsew")
        text_area.insert(1.0, content)

        # --- Scrollbar for this tab ---
        scrollbar = tk.Scrollbar(tab_frame, command=text_area.yview)
        scrollbar.grid(row=0, column=2, sticky="ns")
        text_area.config(yscrollcommand=scrollbar.set)

        # Bindings for this tab's text_area
        text_area.bind("<Configure>", lambda event, ta=text_area, ln=line_numbers: self._on_text_area_change(ta, ln))
        text_area.bind("<KeyRelease>", lambda event, ta=text_area, ln=line_numbers: self._on_text_area_change(ta, ln))
        text_area.bind("<ButtonRelease-1>", lambda event, ta=text_area, ln=line_numbers: self._on_text_area_change(ta, ln))
        # No need for <<Change>> or other virtual events unless explicitly emitted
        # text_area.bind("<<Change>>", lambda event, ta=text_area, ln=line_numbers: self._on_text_area_change(ta, ln))
        text_area.bind("<<Undo>>", lambda event, ta=text_area, ln=line_numbers: self._on_text_area_change(ta, ln))
        text_area.bind("<<Redo>>", lambda event, ta=text_area, ln=line_numbers: self._on_text_area_change(ta, ln))
        text_area.bind("<MouseWheel>", lambda event, ta=text_area, ln=line_numbers: self._on_mouse_wheel(event, ta, ln))
        
        # Add a binding for tab key to insert spaces
        text_area.bind("<Tab>", self.handle_tab_key)


        # Store tab information
        tab_info = {
            'frame': tab_frame,
            'text_area': text_area,
            'line_numbers': line_numbers,
            'current_file_path': file_path,
            'file_type': "txt"
        }
        self.tabs.append(tab_info)

        # Select the newly added tab
        self.notebook.select(tab_frame)
        self.set_file_type_for_tab(tab_info, file_path)
        self.configure_syntax_highlighting(text_area)
        self.apply_syntax_highlighting_for_tab(tab_info)
        self.update_line_numbers_for_tab(tab_info)
        self.update_title()

    def handle_tab_key(self, event):
        """
        Inserts 4 spaces when the Tab key is pressed.
        """
        current_tab = self.get_current_tab_info()
        if current_tab:
            current_tab['text_area'].insert(tk.INSERT, "    ") # Insert 4 spaces
            return "break" # Prevent default tab behavior (focus change)
        return None # Allow default behavior if no tab is active

    def _on_tab_change(self, event):
        """Called when a tab is changed."""
        self.update_title()
        current_tab_info = self.get_current_tab_info()
        if current_tab_info:
            self.update_line_numbers_for_tab(current_tab_info)
            self.apply_syntax_highlighting_for_tab(current_tab_info)

    def get_current_tab_info(self):
        """Returns the dictionary containing information about the currently selected tab."""
        current_tab_id = self.notebook.select()
        # FIX: Corrected from nametoawidget to nametowidget
        current_tab_widget = self.notebook.nametowidget(current_tab_id)
        for tab_info in self.tabs:
            if tab_info['frame'] == current_tab_widget:
                return tab_info
        return None

    def create_menus(self):
        """
        Creates the main menu bar with File, Edit, and Help options.
        """
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Tab", command=self.add_new_tab)
        file_menu.add_command(label="Open...", command=self.open_file)
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_command(label="Save As...", command=self.save_file_as)
        file_menu.add_command(label="Close Tab", command=self.close_current_tab)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)

        # Edit menu (basic undo/redo for demonstration)
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=lambda: self.get_current_tab_info()['text_area'].edit_undo() if self.get_current_tab_info() else None)
        edit_menu.add_command(label="Redo", command=lambda: self.get_current_tab_info()['text_area'].edit_redo() if self.get_current_tab_info() else None)
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", command=lambda: self.get_current_tab_info()['text_area'].event_generate("<<Cut>>") if self.get_current_tab_info() else None)
        edit_menu.add_command(label="Copy", command=lambda: self.get_current_tab_info()['text_area'].event_generate("<<Copy>>") if self.get_current_tab_info() else None)
        edit_menu.add_command(label="Paste", command=lambda: self.get_current_tab_info()['text_area'].event_generate("<<Paste>>") if self.get_current_tab_info() else None)


        # Help menu (optional)
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about_info)

    def new_file(self):
        """
        This method is now redundant as add_new_tab handles creating a new, empty file.
        Kept for backward compatibility if needed elsewhere.
        """
        self.add_new_tab()

    def open_file(self):
        """
        Opens an existing file and loads its content into a new tab.
        """
        file_path = filedialog.askopenfilename(
            defaultextension=".txt",
            filetypes=[
                ("All Files", "*.*"),
                ("Text Documents", "*.txt"),
                ("Python Files", "*.py"),
                ("HTML Files", "*.html"),
                ("CSS Files", "*.css"),
                ("JavaScript Files", "*.js")
            ]
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                self.add_new_tab(file_path=file_path, content=content)
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file: {e}")

    def save_file(self):
        """
        Saves the current content of the active tab to its current file path.
        If no file path is set, it calls save_file_as for the active tab.
        """
        current_tab = self.get_current_tab_info()
        if not current_tab:
            return

        if current_tab['current_file_path']:
            try:
                with open(current_tab['current_file_path'], "w", encoding="utf-8") as file:
                    file.write(current_tab['text_area'].get(1.0, tk.END))
                messagebox.showinfo("Save", f"File saved: {current_tab['current_file_path']}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not save file: {e}")
        else:
            self.save_file_as()

    def save_file_as(self):
        """
        Saves the current content of the active tab to a new file path chosen by the user.
        """
        current_tab = self.get_current_tab_info()
        if not current_tab:
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[
                ("All Files", "*.*"),
                ("Text Documents", "*.txt"),
                ("Python Files", "*.py"),
                ("HTML Files", "*.html"),
                ("CSS Files", "*.css"),
                ("JavaScript Files", "*.js")
            ]
        )
        if file_path:
            current_tab['current_file_path'] = file_path
            self.set_file_type_for_tab(current_tab, file_path)
            self.notebook.tab(current_tab['frame'], text=file_path.split('/')[-1]) # Update tab title
            self.save_file() # Call save_file to actually write the content
            self.update_title()
            self.apply_syntax_highlighting_for_tab(current_tab)

    def close_current_tab(self):
        """Closes the currently active tab after prompting to save changes."""
        current_tab_info = self.get_current_tab_info()
        if not current_tab_info:
            return

        if self.confirm_save_changes_for_tab(current_tab_info):
            self.notebook.forget(current_tab_info['frame'])
            self.tabs.remove(current_tab_info)
            if not self.tabs: # If no tabs left, open a new empty one
                self.add_new_tab()
            self.update_title()


    def confirm_save_changes_for_tab(self, tab_info):
        """
        Checks if the current text area content of a specific tab is different from the saved file content.
        If so, it prompts the user to save changes for that tab.
        Returns True if it's safe to proceed (either saved or user chose not to save),
        False if the operation should be cancelled.
        """
        current_content = tab_info['text_area'].get(1.0, tk.END).strip()
        saved_content = ""

        if tab_info['current_file_path']:
            try:
                with open(tab_info['current_file_path'], "r", encoding="utf-8") as file:
                    saved_content = file.read().strip()
            except FileNotFoundError:
                saved_content = "" # File might have been deleted externally

        if current_content != saved_content:
            response = messagebox.askyesnocancel(
                "Save Changes",
                f"Do you want to save changes to {'Untitled' if tab_info['current_file_path'] is None else tab_info['current_file_path'].split('/')[-1]}?"
            )
            if response is True:  # Yes
                # Activate the tab to ensure save_file operates on the correct one
                self.notebook.select(tab_info['frame'])
                self.save_file()
                return True
            elif response is False:  # No
                return True
            else:  # Cancel
                return False
        return True # No changes or no current file

    def on_closing(self):
        """
        Handles the window closing event, prompting to save unsaved changes for all tabs.
        """
        # Iterate over a copy of the list because tabs might be removed during the loop
        for tab_info in list(self.tabs):
            # Temporarily select the tab to ensure confirm_save_changes_for_tab operates on the correct one
            self.notebook.select(tab_info['frame'])
            if not self.confirm_save_changes_for_tab(tab_info):
                return # If user cancels saving for any tab, stop closing
        self.destroy() # Close the application

    def update_title(self):
        """Updates the main window title based on the active tab."""
        current_tab = self.get_current_tab_info()
        if current_tab:
            file_name = "Untitled"
            if current_tab['current_file_path']:
                file_name = current_tab['current_file_path'].split('/')[-1]
            self.title(f"Breeze Code Editor - {file_name}")
        else:
            self.title("Breeze Code Editor")

    def show_about_info(self):
        """
        Displays a simple 'About' message box.
        """
        messagebox.showinfo("About", "Breeze Code Editor\nVersion 1.0\nCreated by Mahendra.uk")

    # --- Line Number Functions (adapted for tabs) ---
    def _on_text_area_change(self, text_area, line_numbers, event=None):
        """
        Callback for text area changes. Updates line numbers and performs syntax highlighting.
        """
        self.update_line_numbers_for_tab({'text_area': text_area, 'line_numbers': line_numbers})
        # Only highlight if this is the active tab
        current_tab_info = self.get_current_tab_info()
        if current_tab_info and current_tab_info['text_area'] == text_area:
            self.apply_syntax_highlighting_for_tab(current_tab_info)

    def _on_mouse_wheel(self, event, text_area, line_numbers):
        """
        Handle mouse wheel scrolling to synchronize text area and line numbers for a specific tab.
        """
        text_area.yview_scroll(-1 * (event.delta // 120), "units")
        self.update_line_numbers_for_tab({'text_area': text_area, 'line_numbers': line_numbers})
        return "break" # Prevent default scroll behavior for Mac/Linux

    def update_line_numbers_for_tab(self, tab_info):
        """
        Updates the line numbers displayed in the line_numbers canvas for a specific tab.
        """
        line_numbers = tab_info['line_numbers']
        text_area = tab_info['text_area']

        line_numbers.delete("all") # Clear existing line numbers

        # Get the first and last visible line in the text area
        first_line_index = text_area.index("@0,0")
        last_line_index = text_area.index(f"@0,{text_area.winfo_height()}")

        # Get the actual line numbers from the text area
        first_line = int(first_line_index.split('.')[0])
        last_line = int(last_line_index.split('.')[0]) + 1 # Include the potentially partial last line

        # Iterate through visible lines and draw line numbers
        for i in range(first_line, last_line):
            dline = text_area.dlineinfo(f"{i}.0") # Get bounding box info for the line
            if dline:
                y = dline[1] # Y-coordinate of the line
                # Draw the line number text
                line_numbers.create_text(
                    35, y,
                    anchor="ne", # Align text to the top-right
                    text=str(i),
                    fill="#61afef", # Color for line numbers
                    font=("Consolas", 10)
                )

    # --- Syntax Highlighting Functions (adapted for tabs) ---
    def configure_syntax_highlighting(self, text_widget):
        """
        Configures the text area tags for different syntax elements.
        This method should be called for each new text_area.
        """
        # Define a base font for syntax highlighting
        base_font = ("Consolas", 11)

        # Python
        text_widget.tag_configure("python_keyword", foreground="#c678dd", font=base_font)
        text_widget.tag_configure("python_string", foreground="#98c379", font=base_font)
        text_widget.tag_configure("python_comment", foreground="#5c6370", font=(base_font[0], base_font[1], "italic"))
        text_widget.tag_configure("python_function", foreground="#61afef", font=base_font)
        text_widget.tag_configure("python_class", foreground="#e6c07b", font=base_font)
        text_widget.tag_configure("python_number", foreground="#d19a66", font=base_font)

        # HTML
        text_widget.tag_configure("html_tag", foreground="#e06c75", font=base_font)
        text_widget.tag_configure("html_attribute", foreground="#d19a66", font=base_font)
        text_widget.tag_configure("html_string", foreground="#98c379", font=base_font)
        text_widget.tag_configure("html_comment", foreground="#5c6370", font=(base_font[0], base_font[1], "italic"))

        # CSS
        text_widget.tag_configure("css_property", foreground="#61afef", font=base_font)
        text_widget.tag_configure("css_value", foreground="#98c379", font=base_font)
        text_widget.tag_configure("css_selector", foreground="#e06c75", font=base_font)
        text_widget.tag_configure("css_comment", foreground="#5c6370", font=(base_font[0], base_font[1], "italic"))

        # JavaScript
        text_widget.tag_configure("js_keyword", foreground="#c678dd", font=base_font)
        text_widget.tag_configure("js_string", foreground="#98c379", font=base_font)
        text_widget.tag_configure("js_comment", foreground="#5c6370", font=(base_font[0], base_font[1], "italic"))
        text_widget.tag_configure("js_function", foreground="#61afef", font=base_font)
        text_widget.tag_configure("js_number", foreground="#d19a66", font=base_font)
        text_widget.tag_configure("js_variable", foreground="#e6c07b", font=base_font) # let, const, var

        self.highlight_patterns = {
            "py": {
                "keywords": r'\b(False|None|True|and|as|assert|async|await|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)\b',
                "strings": r'"[^"]*"|\'[^\']*\'',
                "comments": r'#.*',
                "functions": r'\b(\w+)(?=\()', # Simple regex for function calls (not def)
                "classes": r'\b(class)\s+(\w+)\b',
                "numbers": r'\b\d+(\.\d*)?\b|\b\.\d+\b'
            },
            "html": {
                "tags": r'</?[\w\d]+>',
                "attributes": r'\b([\w\d-]+)=',
                "strings": r'"[^"]*"|\'[^\']*\'',
                "comments": r''
            },
            "css": {
                "properties": r'\b([\w-]+)(?=\s*:)',
                "values": r':\s*([^;]+)',
                "selectors": r'[\.#]?[\w\d_ -]+(\s*,\s*[\.#]?[\w\d_ -]+)*|\b[\w\d]+\b',
                "comments": r'/\*.*?\*/'
            },
            "js": {
                "keywords": r'\b(break|case|catch|class|const|continue|debugger|default|delete|do|else|export|extends|finally|for|function|if|import|in|instanceof|new|return|super|switch|this|throw|try|typeof|var|void|while|with|yield)\b',
                "strings": r'"[^"]*"|\'[^\']*\'|`[^`]*`', # Includes template literals
                "comments": r'//.*|/\*.*?\*/',
                "functions": r'\b(\w+)(?=\()',
                "numbers": r'\b\d+(\.\d*)?\b|\b\.\d+\b',
                "variables": r'\b(let|const|var)\s+(\w+)\b'
            }
        }

    def set_file_type_for_tab(self, tab_info, file_path):
        """Determines the file type for a specific tab based on its extension."""
        extension = file_path.split('.')[-1].lower() if file_path else "txt"
        if extension in ["py"]:
            tab_info['file_type'] = "py"
        elif extension in ["html", "htm"]:
            tab_info['file_type'] = "html"
        elif extension in ["css"]:
            tab_info['file_type'] = "css"
        elif extension in ["js"]:
            tab_info['file_type'] = "js"
        else:
            tab_info['file_type'] = "txt" # Default for unknown extensions

    def apply_syntax_highlighting_for_tab(self, tab_info):
        """
        Applies syntax highlighting to the text area of a specific tab based on its detected file type.
        """
        text_area = tab_info['text_area']
        file_type = tab_info['file_type']

        # Remove all existing tags first
        for tag in text_area.tag_names():
            if tag.startswith(("python_", "html_", "css_", "js_")):
                text_area.tag_remove(tag, "1.0", tk.END)

        if file_type == "txt":
            return # No highlighting for plain text

        text_content = text_area.get("1.0", tk.END)
        patterns = self.highlight_patterns.get(file_type, {})

        if file_type == "py":
            # Keywords
            for match in re.finditer(patterns.get("keywords", ""), text_content):
                text_area.tag_add("python_keyword", f"1.0+{match.start()}c", f"1.0+{match.end()}c")
            # Strings
            for match in re.finditer(patterns.get("strings", ""), text_content):
                text_area.tag_add("python_string", f"1.0+{match.start()}c", f"1.0+{match.end()}c")
            # Comments
            for match in re.finditer(patterns.get("comments", ""), text_content):
                text_area.tag_add("python_comment", f"1.0+{match.start()}c", f"1.0+{match.end()}c")
            # Functions (calls)
            for match in re.finditer(patterns.get("functions", ""), text_content):
                text_area.tag_add("python_function", f"1.0+{match.start()}c", f"1.0+{match.end()}c")
            # Class definitions (only the 'class' keyword and class name)
            for match in re.finditer(patterns.get("classes", ""), text_content):
                text_area.tag_add("python_keyword", f"1.0+{match.start(1)}c", f"1.0+{match.end(1)}c")
                text_area.tag_add("python_class", f"1.0+{match.start(2)}c", f"1.0+{match.end(2)}c")
            # Numbers
            for match in re.finditer(patterns.get("numbers", ""), text_content):
                text_area.tag_add("python_number", f"1.0+{match.start()}c", f"1.0+{match.end()}c")

        elif file_type == "html":
            # Tags
            for match in re.finditer(patterns.get("tags", ""), text_content):
                text_area.tag_add("html_tag", f"1.0+{match.start()}c", f"1.0+{match.end()}c")
            # Attributes (need to be careful not to highlight values)
            for match in re.finditer(patterns.get("attributes", ""), text_content):
                text_area.tag_add("html_attribute", f"1.0+{match.start(1)}c", f"1.0+{match.end(1)}c")
            # Strings (attribute values)
            for match in re.finditer(patterns.get("strings", ""), text_content):
                text_area.tag_add("html_string", f"1.0+{match.start()}c", f"1.0+{match.end()}c")
            # Comments
            for match in re.finditer(patterns.get("comments", ""), text_content, re.DOTALL):
                text_area.tag_add("html_comment", f"1.0+{match.start()}c", f"1.0+{match.end()}c")

        elif file_type == "css":
            # Properties
            for match in re.finditer(patterns.get("properties", ""), text_content):
                text_area.tag_add("css_property", f"1.0+{match.start(1)}c", f"1.0+{match.end(1)}c")
            # Values (basic, might need refinement)
            for match in re.finditer(patterns.get("values", ""), text_content):
                text_area.tag_add("css_value", f"1.0+{match.start(1)}c", f"1.0+{match.end(1)}c")
            # Selectors (basic)
            for match in re.finditer(patterns.get("selectors", ""), text_content):
                text_area.tag_add("css_selector", f"1.0+{match.start()}c", f"1.0+{match.end()}c")
            # Comments
            for match in re.finditer(patterns.get("comments", ""), text_content, re.DOTALL):
                text_area.tag_add("css_comment", f"1.0+{match.start()}c", f"1.0+{match.end()}c")

        elif file_type == "js":
            # Keywords
            for match in re.finditer(patterns.get("keywords", ""), text_content):
                text_area.tag_add("js_keyword", f"1.0+{match.start()}c", f"1.0+{match.end()}c")
            # Strings
            for match in re.finditer(patterns.get("strings", ""), text_content):
                text_area.tag_add("js_string", f"1.0+{match.start()}c", f"1.0+{match.end()}c")
            # Comments
            for match in re.finditer(patterns.get("comments", ""), text_content, re.DOTALL):
                text_area.tag_add("js_comment", f"1.0+{match.start()}c", f"1.0+{match.end()}c")
            # Functions (calls)
            for match in re.finditer(patterns.get("functions", ""), text_content):
                text_area.tag_add("js_function", f"1.0+{match.start()}c", f"1.0+{match.end()}c")
            # Numbers
            for match in re.finditer(patterns.get("numbers", ""), text_content):
                text_area.tag_add("js_number", f"1.0+{match.start()}c", f"1.0+{match.end()}c")
            # Variables (let, const, var declarations)
            for match in re.finditer(patterns.get("variables", ""), text_content):
                text_area.tag_add("js_keyword", f"1.0+{match.start(1)}c", f"1.0+{match.end(1)}c")
                text_area.tag_add("js_variable", f"1.0+{match.start(2)}c", f"1.0+{match.end(2)}c")


if __name__ == "__main__":
    editor = CodeEditor()
    editor.mainloop()