import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
import re
import webbrowser

# --- BACKEND LOGIC (Copied/Adapted from manage_podcast.py) ---

def get_file_content(file_path):
    if not os.path.exists(file_path):
        return None
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def save_file_content(file_path, content):
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def extract_podcasts(content):
    podcasts = []
    # Regex consistent with manage_podcast.py
    pattern = re.compile(r'(<!-- NEUE EPISODE: .*? -->\s*)?<article class="podcast-card">(.*?)</article>', re.DOTALL)
    matches = list(pattern.finditer(content))
    
    for i, match in enumerate(matches):
        full_block = match.group(0)
        inner_html = match.group(2)
        
        # Helper to extract content
        def get_text(regex, default=""):
            m = re.search(regex, inner_html, re.DOTALL)
            return m.group(1).strip() if m else default

        title = get_text(r'<h3>(.*?)</h3>', "Unknown Title")
        # Remove moodle indicator from title if present
        title = re.sub(r'<span class="moodle-indicator">.*?</span>', '', title).strip()
        
        # Details: try structured p, fall back to generic p
        details = get_text(r'<p class="podcast-description">(.*?)</p>')
        if not details:
            details = get_text(r'<p>(.*?)</p>') 
            # Filter out "Hier klicken zum Anhören" junk if present from old entries
            if "Hier klicken" in details: details = ""
            
        link = ""
        m_link = re.search(r'<source src="(.*?)"', inner_html)
        if m_link: link = m_link.group(1)

        # Authors
        authors = []
        # New format p tag
        m_auth_p = re.search(r'<p class="podcast-author">(.*?)</p>', inner_html)
        if m_auth_p:
            text = m_auth_p.group(1).replace("von ", "")
            parts = text.split(" und ")
            if len(parts) > 1:
                authors = [x.strip() for x in ", ".join(parts[:-1]).split(",")] + [parts[-1].strip()]
            else:
                authors = [text.strip()]
        else:
            # Check old list format
            m_auth_ul = re.search(r'<ul class="author-list">(.*?)</ul>', inner_html, re.DOTALL)
            if m_auth_ul:
                authors = [x.strip() for x in re.findall(r'<li>(.*?)</li>', m_auth_ul.group(1))]
            elif re.search(r'<li class="podcast-item"><strong>Autoren:</strong>', inner_html):
                # Simple text extraction from li?
                li_text = get_text(r'<li class="podcast-item"><strong>Autoren:</strong> (.*?)</li>')
                if li_text and "<ul" not in li_text: authors = [li_text]

        if not authors: authors = ["Anonym"]

        # Sources
        sources = []
        m_source_ul = re.search(r'<ul class="source-list">(.*?)</ul>', inner_html, re.DOTALL)
        if m_source_ul:
            raw_items = re.findall(r'<li>(.*?)</li>', m_source_ul.group(1))
            for item in raw_items:
                m_href = re.search(r'href="(.*?)"', item)
                sources.append(m_href.group(1) if m_href else item.strip())

        podcasts.append({
            'index': i,
            'title': title,
            'details': details,
            'link': link,
            'authors': authors,
            'sources': sources,
            'full_block': full_block,
            'span': match.span()
        })
    return podcasts

def generate_html_block(title, details, link, authors, sources):
    # Authors Text
    authors_text = "Anonym"
    if authors:
        if len(authors) == 1:
            authors_text = f"von {authors[0]}"
        else:
            authors_text = f"von {', '.join(authors[:-1])} und {authors[-1]}"
    
    # Sources HTML
    sources_html_block = ""
    if sources:
        list_items = ""
        for s in sources:
            if s.startswith("http"):
                list_items += f'<li><a href="{s}" target="_blank">{s}</a></li>'
            else:
                list_items += f'<li>{s}</li>'
        sources_html_block = f'''
                <div class="podcast-extra">
                    <strong>Quellen:</strong>
                    <ul class="source-list">{list_items}</ul>
                </div>'''

    # Determine MIME type(s) and sources for Maximum Compatibility
    sources_block = ""
    link_lower = link.lower()
    
    # Check for Moodle link to add indicator
    moodle_indicator = ""
    if "moodle" in link_lower or "ksasz.ch" in link_lower:
        moodle_indicator = ' <span class="moodle-indicator" title="Requires Moodle Login">🔒 MOODLE</span>'
    
    if link_lower.endswith('.m4a'):
        # M4A / AAC Compatibility
        # 1. audio/mp4 (Modern Standard, Safari, iOS, Chrome, Edge)
        # 2. audio/x-m4a (Older implementation, some Android specifics)
        # 3. audio/aac (Raw AAC, sometimes used)
        sources_block = f"""<source src="{link}" type="audio/mp4">
        <source src="{link}" type="audio/x-m4a">
        <source src="{link}" type="audio/aac">"""
        
    elif link_lower.endswith('.mp3'):
        # MP3 Compatibility
        sources_block = f"""<source src="{link}" type="audio/mpeg">
        <source src="{link}" type="audio/mp3">"""
        
    elif link_lower.endswith('.ogg') or link_lower.endswith('.oga'):
        # OGG / Vorbis / Opus
        sources_block = f"""<source src="{link}" type="audio/ogg">
        <source src="{link}" type="audio/vorbis">"""
        
    elif link_lower.endswith('.wav'):
        # WAV
        sources_block = f"""<source src="{link}" type="audio/wav">
        <source src="{link}" type="audio/x-wav">"""
        
    else:
        # Fallback / Generic
        sources_block = f"""<source src="{link}" type="audio/mpeg">
        <source src="{link}" type="audio/mp4">"""

    return f"""<!-- NEUE EPISODE: {title} -->
<article class="podcast-card">
    <h3>{title}{moodle_indicator}</h3>
    <p class="podcast-description">{details}</p>
    
    <audio controls preload="metadata">
        {sources_block}
        Your browser does not support the audio element.
    </audio>

    <p class="podcast-author">{authors_text}</p>

    <details>
        <summary>Details & Infos</summary>
        <div class="details-content">
            <ul class="podcast-details">
                <li class="podcast-item"><strong>Titel:</strong> {title}</li>
                <li class="podcast-item"><strong>Info:</strong> {details}</li>
            </ul>{sources_html_block}
        </div>
    </details>
</article>"""

# --- GUI ---

# Theme Colors (Matching style.css)
COLORS = {
    'bg': '#121212',
    'card_bg': '#1e1e1e',
    'text': '#e0e0e0',
    'accent': '#bb86fc',
    'secondary': '#03dac6',
    'input_bg': '#2d2d2d',
    'input_fg': '#ffffff',
    'btn_bg': '#333333',
    'btn_hover': '#444444'
}

class DashboardBtn(tk.Button):
    """Custom Button for better styling control than ttk"""
    def __init__(self, parent, text, command, bg=COLORS['card_bg'], fg=COLORS['accent'], **kwargs):
        font = kwargs.pop('font', ("Segoe UI", 10, "bold"))
        super().__init__(parent, text=text, command=command, 
                         bg=bg, fg=fg, 
                         activebackground=COLORS['accent'], activeforeground='#000000',
                         relief='flat', bd=0, padx=15, pady=5, font=font, cursor="hand2", **kwargs)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.default_bg = bg
        self.default_fg = fg

    def on_enter(self, e):
        self['bg'] = COLORS['accent']
        self['fg'] = '#000000'

    def on_leave(self, e):
        self['bg'] = self.default_bg
        self['fg'] = self.default_fg

class PodcastDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Podcast Manager Dashboard")
        self.root.geometry("1000x800")
        self.root.configure(bg=COLORS['bg'])
        
        # Styles for ttk widgets
        style = ttk.Style()
        style.theme_use('clam')
        
        # Scrollbar styling
        style.configure("Vertical.TScrollbar", gripcount=0,
                        background=COLORS['card_bg'], darkcolor=COLORS['bg'], lightcolor=COLORS['bg'],
                        troughcolor=COLORS['bg'], bordercolor=COLORS['bg'], arrowcolor=COLORS['accent'])

        # Main Layout
        self.main_container = tk.Frame(root, bg=COLORS['bg'])
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Header / Section Selector
        self.header_frame = tk.Frame(self.main_container, bg=COLORS['bg'])
        self.header_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(self.header_frame, text="PODCAST MANAGER", font=("Segoe UI", 24, "bold"), bg=COLORS['bg'], fg=COLORS['accent']).pack(side=tk.LEFT)
        
        # Section Toggles
        self.section_var = tk.StringVar(value="m2a")
        
        controls_frame = tk.Frame(self.header_frame, bg=COLORS['bg'])
        controls_frame.pack(side=tk.RIGHT)

        self.btn_m2a = DashboardBtn(controls_frame, text="M2A PODCASTS", 
                                    command=lambda: self.switch_section("m2a"), bg=COLORS['accent'], fg='black')
        self.btn_m2a.pack(side=tk.LEFT, padx=5)
        
        self.btn_s2e = DashboardBtn(controls_frame, text="S2E PODCASTS", 
                                    command=lambda: self.switch_section("s2e"), bg=COLORS['card_bg'], fg=COLORS['text'])
        self.btn_s2e.pack(side=tk.LEFT, padx=5)
        
        DashboardBtn(controls_frame, text="REFRESH", command=self.load_podcasts, bg=COLORS['btn_bg'], fg=COLORS['text']).pack(side=tk.LEFT, padx=20)
        DashboardBtn(controls_frame, text="+ NEW EPISODE", command=self.add_podcast_dialog, bg=COLORS['secondary'], fg='black').pack(side=tk.LEFT)

        # Scrollable Area for Cards
        # Use a separate frame to hold canvas and scrollbar to ensure proper layout
        self.canvas_container = tk.Frame(self.main_container, bg=COLORS['bg'])
        self.canvas_container.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.canvas_container, bg=COLORS['bg'], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.canvas_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=COLORS['bg'])

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # Create window ONLY ONCE and store the ID
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Mousewheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.current_content = ""
        self.current_file_path = ""
        self.podcasts_data = []

        # Initial Load
        self.switch_section("m2a")

    def _on_canvas_configure(self, event):
        # Update the width of the window to match the canvas
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def switch_section(self, section):
        self.section_var.set(section)
        
        # Update Button Styles
        if section == "m2a":
            self.btn_m2a.configure(bg=COLORS['accent'], fg='black')
            self.btn_m2a.default_bg = COLORS['accent']
            self.btn_m2a.default_fg = 'black'
            
            self.btn_s2e.configure(bg=COLORS['card_bg'], fg=COLORS['text'])
            self.btn_s2e.default_bg = COLORS['card_bg']
            self.btn_s2e.default_fg = COLORS['text']
        else:
            self.btn_s2e.configure(bg=COLORS['accent'], fg='black')
            self.btn_s2e.default_bg = COLORS['accent']
            self.btn_s2e.default_fg = 'black'
            
            self.btn_m2a.configure(bg=COLORS['card_bg'], fg=COLORS['text'])
            self.btn_m2a.default_bg = COLORS['card_bg']
            self.btn_m2a.default_fg = COLORS['text']
            
        self.load_podcasts()


    def get_path(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        rel = f"podcasts/{self.section_var.get()}/index.html"
        return os.path.join(script_dir, rel)

    def load_podcasts(self):
        # Clear existing
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.current_file_path = self.get_path()
        self.current_content = get_file_content(self.current_file_path)
        
        if not self.current_content:
            tk.Label(self.scrollable_frame, text="File not found!", bg=COLORS['bg'], fg=COLORS['text']).pack()
            return

        self.podcasts_data = extract_podcasts(self.current_content)
        
        if not self.podcasts_data:
            tk.Label(self.scrollable_frame, text="No podcasts found.", bg=COLORS['bg'], fg=COLORS['text']).pack(pady=20)

        for p in self.podcasts_data:
            self.create_podcast_card(p)

    def create_podcast_card(self, p_data):
        card = tk.Frame(self.scrollable_frame, bg=COLORS['card_bg'], padx=20, pady=20)
        card.pack(fill=tk.X, pady=10)
        
        # Left Border Accent
        accent_strip = tk.Frame(card, bg=COLORS['accent'], width=4)
        accent_strip.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))

        # Content Container
        content_frame = tk.Frame(card, bg=COLORS['card_bg'])
        content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Header
        header = tk.Frame(content_frame, bg=COLORS['card_bg'])
        header.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(header, text=p_data['title'], font=("Segoe UI", 16, "bold"), bg=COLORS['card_bg'], fg=COLORS['accent']).pack(side=tk.LEFT)
        
        # Action Buttons
        btn_frame = tk.Frame(header, bg=COLORS['card_bg'])
        btn_frame.pack(side=tk.RIGHT)
        
        DashboardBtn(btn_frame, "EDIT", lambda p=p_data: self.edit_podcast_dialog(p), 
                     bg=COLORS['card_bg'], fg=COLORS['text'], font=("Segoe UI", 8)).pack(side=tk.LEFT, padx=2)
        DashboardBtn(btn_frame, "DELETE", lambda p=p_data: self.delete_podcast(p), 
                     bg=COLORS['card_bg'], fg='#ff5555', font=("Segoe UI", 8)).pack(side=tk.LEFT, padx=2)

        # Details
        tk.Label(content_frame, text=p_data['details'], wraplength=700, justify="left", 
                 bg=COLORS['card_bg'], fg=COLORS['text'], font=("Segoe UI", 10)).pack(anchor="w")
        
        # Meta
        meta_frame = tk.Frame(content_frame, bg=COLORS['card_bg'])
        meta_frame.pack(fill=tk.X, pady=(15, 0))
        
        auth_str = ", ".join(p_data['authors'])
        tk.Label(meta_frame, text=f"by {auth_str}", font=("Segoe UI", 9, "italic"), bg=COLORS['card_bg'], fg='#888888').pack(side=tk.LEFT)
        
        if p_data['link']:
            link_lbl = tk.Label(meta_frame, text="▶ Play Audio", fg=COLORS['secondary'], cursor="hand2", bg=COLORS['card_bg'], font=("Segoe UI", 9, "bold"))
            link_lbl.pack(side=tk.RIGHT)
            link_lbl.bind("<Button-1>", lambda e, l=p_data['link']: webbrowser.open(l))

    def delete_podcast(self, p_data):
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{p_data['title']}'?"):
            # We must reload content first to be safe, then find exact block
            self.current_content = get_file_content(self.current_file_path)
            # Find the block in current content using the exact strings we stored
            # (Note: if file changed externally, this might fail, simplistic approach)
            new_content = self.current_content.replace(p_data['full_block'], "")
            # Clean up empty lines
            new_content = re.sub(r'\n\s*\n\s*\n', '\n\n', new_content)
            
            save_file_content(self.current_file_path, new_content)
            self.load_podcasts()

    def edit_podcast_dialog(self, p_data):
        EditWindow(self.root, p_data, self)

    def add_podcast_dialog(self):
        # Empty data structure
        new_data = {
            'title': "",
            'details': "",
            'link': "",
            'authors': ["Anonym"],
            'sources': [],
            'full_block': None # Marker that it's new
        }
        EditWindow(self.root, new_data, self)

    def save_podcast_change(self, old_data, new_data):
        # Generate HTML content block first
        html_block = generate_html_block(
            new_data['title'],
            new_data['details'], 
            new_data['link'],
            new_data['authors'],
            new_data['sources']
        ).strip() # Important strip to remove execss surrounding newlines 

        file_path = self.get_path()
        content = get_file_content(file_path)
        
        if not content:
            messagebox.showerror("Error", "File not found.")
            return

        if old_data.get('full_block'):
            # Existing Edit
            # We must be careful about simple replace if multiple exist.
            # But here we assume unique blocks for simplicity.
            if old_data['full_block'] in content:
                content = content.replace(old_data['full_block'], html_block + "\n")
            else:
                 messagebox.showerror("Error", "Could not find original entry to update. Refresh list.")
                 return
        else:
            # Add New
            marker = "</main>"
            if marker in content:
                # Add newline before marker for spacing
                replacement = f"{html_block}\n\n{marker}"
                # Replace the LAST occurrence of marker
                parts = content.rsplit(marker, 1)
                content = parts[0] + replacement + parts[1]
            else:
                messagebox.showerror("Error", "</main> tag not found.")
                return

        save_file_content(file_path, content)
        # Reload List
        self.load_podcasts()


class EditWindow:
    def __init__(self, parent, data, dashboard):
        self.data = data
        self.dashboard = dashboard
        self.parent = parent
        
        # Create Toplevel Window
        self.win = tk.Toplevel(parent)
        title_txt = f"Edit: {data['title']}" if data.get('full_block') else "Add New Podcast"
        self.win.title(title_txt)
        self.win.geometry("600x750")
        self.win.configure(bg=COLORS['bg'])
        
        # Main Container
        container = tk.Frame(self.win, bg=COLORS['bg'], padx=30, pady=30)
        container.pack(fill=tk.BOTH, expand=True)

        # Title Input
        tk.Label(container, text="PODCAST TITLE", font=("Segoe UI", 10, "bold"), bg=COLORS['bg'], fg=COLORS['accent']).pack(anchor="w", pady=(0, 5))
        self.title_var = tk.StringVar(value=data.get('title', ''))
        tk.Entry(container, textvariable=self.title_var, bg=COLORS['input_bg'], fg=COLORS['input_fg'], 
                 insertbackground=COLORS['accent'], relief="flat", font=("Segoe UI", 11)).pack(fill=tk.X, pady=(0, 20), ipady=5)
        
        # Link Input
        tk.Label(container, text="AUDIO URL", font=("Segoe UI", 10, "bold"), bg=COLORS['bg'], fg=COLORS['accent']).pack(anchor="w", pady=(0, 5))
        self.link_var = tk.StringVar(value=data.get('link', ''))
        tk.Entry(container, textvariable=self.link_var, bg=COLORS['input_bg'], fg=COLORS['input_fg'], 
                 insertbackground=COLORS['accent'], relief="flat", font=("Segoe UI", 11)).pack(fill=tk.X, pady=(0, 20), ipady=5)

        # Details Input
        tk.Label(container, text="DESCRIPTION", font=("Segoe UI", 10, "bold"), bg=COLORS['bg'], fg=COLORS['accent']).pack(anchor="w", pady=(0, 5))
        self.details_txt = tk.Text(container, height=6, bg=COLORS['input_bg'], fg=COLORS['input_fg'], 
                                   insertbackground=COLORS['accent'], relief="flat", font=("Segoe UI", 11))
        self.details_txt.pack(fill=tk.X, pady=(0, 20))
        if data.get('details'):
             self.details_txt.insert("1.0", data['details'])
        
        # Authors Input
        tk.Label(container, text="AUTHORS (One per line)", font=("Segoe UI", 10, "bold"), bg=COLORS['bg'], fg=COLORS['accent']).pack(anchor="w", pady=(0, 5))
        self.authors_txt = tk.Text(container, height=4, bg=COLORS['input_bg'], fg=COLORS['input_fg'], 
                                   insertbackground=COLORS['accent'], relief="flat", font=("Segoe UI", 11))
        self.authors_txt.pack(fill=tk.X, pady=(0, 20))
        # Default authors if empty
        existing_authors = data.get('authors', [])
        if existing_authors:
             self.authors_txt.insert("1.0", "\n".join(existing_authors))

        # Buttons
        btn_frame = tk.Frame(container, bg=COLORS['bg'])
        btn_frame.pack(fill=tk.X, pady=10)
        
        DashboardBtn(btn_frame, "CANCEL", self.win.destroy, bg=COLORS['card_bg'], fg=COLORS['text']).pack(side=tk.RIGHT, padx=10)
        DashboardBtn(btn_frame, "SAVE PODCAST", self.save_action, bg=COLORS['accent'], fg='#000000').pack(side=tk.RIGHT)

    def save_action(self):
        # Gather data
        new_title = self.title_var.get().strip()
        new_link = self.link_var.get().strip()
        new_details = self.details_txt.get("1.0", "end-1c").strip()
        
        # Default description logic
        if not new_details: 
             new_details = f"Ein Podcast über {new_title}" if new_title else ""
        
        raw_authors = self.authors_txt.get("1.0", tk.END).strip().split('\n')
        clean_authors = [x.strip() for x in raw_authors if x.strip()]
        if not clean_authors: clean_authors = ["Anonym"]
        
        if not new_title or not new_link:
             messagebox.showwarning("Missing Info", "Title and Link are required!")
             return

        new_data_dict = {
            'title': new_title,
            'link': new_link,
            'details': new_details,
            'authors': clean_authors,
            'sources': [] # Sources UI removed for cleaner look, usually empty or advanced usage
        }
        
        # Pass back to dashboard to handle file I/O
        self.dashboard.save_podcast_change(self.data, new_data_dict)
        self.win.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = PodcastDashboard(root)
    root.mainloop()
