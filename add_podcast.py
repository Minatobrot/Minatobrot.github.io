import os

def get_input(prompt_text, allow_empty=False, default=None):
    """
    Get input from the user with a prompt.
    """
    try:
        val = input(f"{prompt_text}: ").strip()
        while not val and not allow_empty:
            print("Input cannot be empty. Please try again.")
            val = input(f"{prompt_text}: ").strip()
        
        if not val and default:
            return default
            
        return val
    except EOFError:
        return ""

def format_podcast_entry(title, details, archive_link, authors, sources):
    """
    Formats the podcast entry as HTML.
    """
    # Format Authors naturally: "von Autor1, Autor2 und Autor3"
    authors_text = "Anonym"
    if isinstance(authors, list) and authors:
        if len(authors) == 1:
            authors_text = f"von {authors[0]}"
        else:
            # Join all except last with comma, and last with " und "
            all_but_last = ", ".join(authors[:-1])
            last = authors[-1]
            authors_text = f"von {all_but_last} und {last}"
    elif authors:
         authors_text = f"von {authors}"

    # Create HTML formatted list for sources if multiple
    sources_html = ""
    if isinstance(sources, list) and sources:
        sources_html = '<ul class="source-list">' + ''.join([f'<li><a href="{s}" target="_blank">{s}</a></li>' if s.startswith('http') else f'<li>{s}</li>' for s in sources]) + '</ul>'
    else:
        sources_html = sources

    # Determine MIME type(s) and sources for Maximum Compatibility
    sources_block = ""
    link_lower = archive_link.lower()
    
    if link_lower.endswith('.m4a'):
        # M4A / AAC Compatibility
        sources_block = f"""<source src="{archive_link}" type="audio/mp4">
            <source src="{archive_link}" type="audio/x-m4a">
            <source src="{archive_link}" type="audio/aac">"""
        
    elif link_lower.endswith('.mp3'):
        # MP3 Compatibility
        sources_block = f"""<source src="{archive_link}" type="audio/mpeg">
            <source src="{archive_link}" type="audio/mp3">"""
        
    elif link_lower.endswith('.ogg') or link_lower.endswith('.oga'):
        # OGG
        sources_block = f"""<source src="{archive_link}" type="audio/ogg">"""
        
    elif link_lower.endswith('.wav'):
        # WAV
        sources_block = f"""<source src="{archive_link}" type="audio/wav">"""
        
    else:
        # Fallback
        sources_block = f"""<source src="{archive_link}" type="audio/mpeg">
            <source src="{archive_link}" type="audio/mp4">"""

    return f"""
    <!-- NEUE EPISODE: {title} -->
    <article class="podcast-card">
        <h3>{title}</h3>
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
                </ul>
                <div class="podcast-extra">
                    <strong>Quellen:</strong>
                    {sources_html}
                </div>
            </div>
        </details>
    </article>
"""

def add_podcast_to_file(file_path, entry_html):
    """
    Adds the podcast entry to the end of the <main> section in the HTML file.
    """
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return False

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the closing tag of the main section
        insert_marker = "</main>"
        if insert_marker not in content:
            print(f"Error: Could not find '{insert_marker}' in {file_path}")
            return False
            
        # Insert the new entry before the closing tag
        parts = content.rsplit(insert_marker, 1)
        if len(parts) != 2:
             print(f"Error: Multiple or no '{insert_marker}' found properly.")
             return False
             
        new_content = parts[0] + entry_html + "\n" + insert_marker + parts[1]
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        return True
        
    except Exception as e:
        print(f"Error processing file: {e}")
        return False

def get_multiline_input(prompt_text):
    """
    Get multiple items as input until empty line.
    """
    items = []
    print(f"{prompt_text} (Enter one by one, press Enter on empty line to finish):")
    while True:
        try:
            val = input(f" - ").strip()
            if not val:
                break
            items.append(val)
        except EOFError:
            break
    return items

def main():
    print("========================================")
    print("      PODCAST MANAGER - SIMPLE ADD      ")
    print("========================================")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    while True:
        print("\nChoose the podcast section to add to:")
        print("1. M2A (podcasts/m2a/index.html)")
        print("2. S2E (podcasts/s2e/index.html)")
        print("q. Quit")
        
        choice = input("Enter your choice (1/2/q): ").strip().lower()
        
        if choice == 'q':
            print("Goodbye!")
            break
            
        if choice == '1':
            target_rel_path = os.path.join("podcasts", "m2a", "index.html")
        elif choice == '2':
            target_rel_path = os.path.join("podcasts", "s2e", "index.html")
        else:
            print("Invalid choice. Please try again.")
            continue
            
        # Construct absolute path
        target_file = os.path.join(script_dir, target_rel_path)
        
        if not os.path.exists(target_file):
            print(f"ERROR: Could not find file at: {target_file}")
            print("Make sure this script is in the root of your website folder.")
            continue

        print(f"\n--- Adding to {choice.upper()} ---")
        
        # Collection Inputs
        archive_link = get_input("Archive Link")
        title = get_input("Title of Podcast")
        
        # Details with default behavior
        details = get_input(f"Details and Infos (Press Enter for default: 'Ein Podcast über {title}')", allow_empty=True, default=f"Ein Podcast über {title}")
        
        # Get multiple authors
        print("Authors (Enter one by one, press Enter on empty line to finish):")
        authors = []
        while True:
            val = input(" - ").strip()
            if not val:
                break
            authors.append(val)
        if not authors:
            authors = ["Anonym"]

        # Get multiple sources/references
        print("Sources (Quellen) (Enter one by one, press Enter on empty line to finish):")
        sources = []
        while True:
            val = input(" - ").strip()
            if not val:
                break
            sources.append(val)

        # Format HTML
        entry_html = format_podcast_entry(title, details, archive_link, authors, sources)
        
        # Review
        print("\n--- Preview ---")
        print(f"Title:   {title}")
        print(f"Details: {details}")
        print(f"Link:    {archive_link}")
        print(f"Authors: {', '.join(authors)}")
        print(f"Sources: {len(sources)} items")
        
        confirm = input("Add this entry? (y/n): ").strip().lower()
        if confirm == 'y':
            if add_podcast_to_file(target_file, entry_html):
                print("Successfully added podcast entry!")
            else:
                print("Failed to add entry. Check file permissions or content.")
        else:
            print("Operation cancelled.")
        
        print("\n----------------------------------------")

if __name__ == "__main__":
    main()
