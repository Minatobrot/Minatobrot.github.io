import os
import re

def get_file_content(file_path):
    if not os.path.exists(file_path):
        return None
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def save_file_content(file_path, content):
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def update_file_safely(original_content, old_block_span, new_block, file_path):
    """
    Replaces the content at specific span to avoid duplicate replacements.
    """
    start, end = old_block_span
    
    # Verify the span content matches
    if original_content[start:end] != original_content[start:end]:
         print("Error: content mismatch during save. Aborting.")
         return False
         
    new_full = original_content[:start] + new_block + original_content[end:]
    save_file_content(file_path, new_full)
    return True

def extract_podcasts(content):
    """
    Returns a list of dictionaries containing podcast details and their full HTML block.
    """
    podcasts = []
    # Regex to find article blocks. 
    # We look for the comment (optional) + article block
    pattern = re.compile(r'(<!-- NEUE EPISODE: .*? -->\s*)?<article class="podcast-card">(.*?)</article>', re.DOTALL)
    
    matches = list(pattern.finditer(content))
    
    for i, match in enumerate(matches):
        full_block = match.group(0) # The whole match including comment if present
        inner_html = match.group(2)
        
        # Extract Title
        title_match = re.search(r'<h3>(.*?)</h3>', inner_html)
        title = title_match.group(1) if title_match else "Unknown Title"
        
        podcasts.append({
            'index': i,
            'title': title,
            'full_block': full_block,
            'span': match.span(),
            'inner_html': inner_html
        })
    
    return podcasts

def parse_authors_from_block(block):
    """
    Attempts to extract a list of authors from the HTML block.
    """
    # Check for new format: <p class="podcast-author">von A, B und C</p>
    match = re.search(r'<p class="podcast-author">(.*?)</p>', block)
    if match:
        text = match.group(1).replace("von ", "")
        # Split by " und " first to get the last part
        parts = text.split(" und ")
        if len(parts) > 1:
            last = parts[-1]
            others = " und ".join(parts[:-1]) # Rejoin just in case multiple "und" (unlikely)
            list_authors = [x.strip() for x in others.split(",")]
            list_authors.append(last.strip())
            return list_authors
        else:
            return [text.strip()]
            
    # Check for old list format
    list_match = re.search(r'<ul class="author-list">(.*?)</ul>', block, re.DOTALL)
    if list_match:
        items = re.findall(r'<li>(.*?)</li>', list_match.group(1))
        return [item.strip() for item in items]

    return []

def parse_sources_from_block(block):
    """
    Attempts to extract a list of sources from the HTML block.
    """
    list_match = re.search(r'<ul class="source-list">(.*?)</ul>', block, re.DOTALL)
    if list_match:
        # Extract text or href from <li>...</li>
        # <li><a href="...">...</a></li> OR <li>...</li>
        items = []
        raw_items = re.findall(r'<li>(.*?)</li>', list_match.group(1))
        for item in raw_items:
            # Check for anchor
            a_match = re.search(r'<a href=".*?">(.*?)</a>', item)
            if a_match:
                items.append(a_match.group(1))
            else:
                items.append(item)
        return items
    return []

def edit_list_interactive(current_list, item_name="Item"):
    """
    Interactive menu to edit a list of strings.
    """
    working_list = list(current_list)
    
    while True:
        print(f"\nCurrent {item_name}s:")
        if not working_list:
            print("  (None)")
        for i, item in enumerate(working_list):
            print(f"  {i+1}. {item}")
            
        print("\nOptions:")
        print("  a. Add new")
        if working_list:
            print("  r. Remove specific (by number)")
            print("  e. Edit specific (by number)")
            print("  w. Wipe all and overwrite")
        print("  d. Done (Save changes)")
        print("  c. Cancel (Discard changes)")
        
        choice = input("Choice: ").strip().lower()
        
        if choice == 'c':
            return None # Cancel
            
        if choice == 'd':
            return working_list
            
        if choice == 'a':
            val = input(f"New {item_name}: ").strip()
            if val:
                working_list.append(val)
                
        elif choice == 'w' and working_list:
            print(f"Enter new {item_name}s (one per line, empty line to finish):")
            new_items = []
            while True:
                v = input("- ").strip()
                if not v: break
                new_items.append(v)
            working_list = new_items

        elif (choice == 'r' or choice == 'e') and working_list:
            try:
                idx = int(input("Number: ").strip()) - 1
                if 0 <= idx < len(working_list):
                    if choice == 'r':
                        removed = working_list.pop(idx)
                        print(f"Removed: {removed}")
                    else: # edit
                        new_val = input(f"Edit '{working_list[idx]}': ").strip()
                        if new_val:
                            working_list[idx] = new_val
                else:
                    print("Invalid number.")
            except ValueError:
                print("Invalid input.")
                
    return working_list

def edit_podcast_logic(podcast, content, file_path):
    print(f"\nEditing: {podcast['title']}")
    print("What would you like to edit?")
    print("1. Title")
    print("2. Description (Details)")
    print("3. Audio Link")
    print("4. Authors (Manage List)")
    print("5. Sources/Quellen (Manage List)")
    print("c. Cancel")
    
    choice = input("Choice: ").strip().lower()
    
    if choice == 'c':
        return
    
    new_block = podcast['full_block']
    
    if choice == '1': # Title
        new_title = get_input("New Title")
        if new_title:
             new_block = re.sub(r'<h3>(.*?)</h3>', f'<h3>{new_title}</h3>', new_block)
             new_block = re.sub(r'<!-- NEUE EPISODE: .*? -->', f'<!-- NEUE EPISODE: {new_title} -->', new_block)
             new_block = re.sub(r'<li class="podcast-item"><strong>Titel:</strong> .*?</li>', f'<li class="podcast-item"><strong>Titel:</strong> {new_title}</li>', new_block)

    elif choice == '2': # Details
        print(f"Current Description: {re.search(r'<p class=\"podcast-description\">(.*?)</p>', new_block).group(1) if re.search(r'<p class=\"podcast-description\">(.*?)</p>', new_block) else 'Unknown'}")
        p_input = input(f"New Details (Leave empty for default 'Ein Podcast über {podcast['title']}'): ").strip()
        
        new_details = p_input if p_input else f"Ein Podcast über {podcast['title']}"

        # Try to replace the <p> tag content
        if '<p class="podcast-description">' in new_block:
             new_block = re.sub(r'<p class="podcast-description">.*?</p>', f'<p class="podcast-description">{new_details}</p>', new_block, flags=re.DOTALL)
        else:
             new_block = re.sub(r'<p>.*?</p>', f'<p>{new_details}</p>', new_block, count=1, flags=re.DOTALL)
             
        # Also update the list item
        new_block = re.sub(r'<li class="podcast-item"><strong>Info:</strong> .*?</li>', f'<li class="podcast-item"><strong>Info:</strong> {new_details}</li>', new_block, flags=re.DOTALL)

    elif choice == '3': # Link
        new_link = get_input("New Audio Link")
        if new_link:
            new_block = re.sub(r'<source src=".*?"', f'<source src="{new_link}"', new_block)

    elif choice == '4': # Authors
        current_authors = parse_authors_from_block(new_block)
        new_authors = edit_list_interactive(current_authors, "Author")
        
        if new_authors is None: # Cancelled
            return

        authors_text = "Anonym"
        if new_authors:
            if len(new_authors) == 1:
                authors_text = f"von {new_authors[0]}"
            else:
                all_but_last = ", ".join(new_authors[:-1])
                last = new_authors[-1]
                authors_text = f"von {all_but_last} und {last}"

        # Logic to update authors
        # Case 1: Authors are in the new spot (p.podcast-author)
        if '<p class="podcast-author">' in new_block:
             new_block = re.sub(r'<p class="podcast-author">.*?</p>', f'<p class="podcast-author">{authors_text}</p>', new_block)
        
        # Case 2: Authors are in the old spot (div.podcast-extra)
        elif '<div class="podcast-extra">' in new_block and '<strong>Autoren:</strong>' in new_block:
             pattern = r'<div class="podcast-extra">\s*<strong>Autoren:</strong>\s*.*?</div>'
             new_block = re.sub(pattern, "", new_block, flags=re.DOTALL)
             if '</audio>' in new_block:
                  new_block = new_block.replace('</audio>', f'</audio>\n\n        <p class="podcast-author">{authors_text}</p>')
        
        # Case 3: Very old format
        elif '<li class="podcast-item"><strong>Autoren:</strong>' in new_block:
             new_block = re.sub(r'<li class="podcast-item"><strong>Autoren:</strong> .*?</li>', "", new_block)
             if '</audio>' in new_block:
                  new_block = new_block.replace('</audio>', f'</audio>\n\n        <p class="podcast-author">{authors_text}</p>')
        else:
             if '</audio>' in new_block:
                  new_block = new_block.replace('</audio>', f'</audio>\n\n        <p class="podcast-author">{authors_text}</p>')

    elif choice == '5': # Sources
        current_sources = parse_sources_from_block(new_block)
        new_sources = edit_list_interactive(current_sources, "Source")
        
        if new_sources is None: # Cancelled
            return
            
        sources_html = ""
        if new_sources:
             sources_html = '<ul class="source-list">' + ''.join([f'<li><a href="{s}" target="_blank">{s}</a></li>' if s.startswith('http') else f'<li>{s}</li>' for s in new_sources]) + '</ul>'
        else:
            sources_html = "Keine"

        if '<strong>Quellen:</strong>' in new_block:
             pattern = r'(<strong>Quellen:</strong>\s*)(.*?)(?=\s*</div>)'
             new_block = re.sub(pattern, f'\\1\n                    {sources_html}', new_block, flags=re.DOTALL)
        else:
             # Add sources if not present
             if '<div class="details-content">' in new_block:
                 print("Source section not found. Creating new...")
                 sources_block = f"""
                <div class="podcast-extra">
                    <strong>Quellen:</strong>
                    {sources_html}
                </div>"""
                 # Insert before the closing div of details-content
                 # We look for the last </div> before </details>
                 new_block = re.sub(r'(\s*</div>\s*</details>)', f'{sources_block}\\1', new_block, count=1)
             else:
                 print("Cannot determine where to place sources. Update manually might be needed.")

    update_file_safely(content, podcast['span'], new_block, file_path)
    print("Entry updated successfully!")


def delete_podcast_logic(podcast, content, file_path):
    print(f"\nDeleting: {podcast['title']}")
    print("What to delete?")
    print("1. Entire Podcast Entry")
    print("2. Remove all Authors (Set to Anonym)")
    print("3. Remove all Sources (Set to None)")
    print("c. Cancel")
    
    choice = input("Choice: ").strip().lower()
    
    if choice == 'c':
        return
        
    new_block = podcast['full_block']
    
    if choice == '1':
        # Removing entire block
        update_file_safely(content, podcast['span'], "", file_path)
        print("Podcast deleted.")
        return

    elif choice == '2': # Remove Authors
        if '<div class="podcast-extra">' in new_block and '<strong>Autoren:</strong>' in new_block:
             # Remove old block, insert new p tag
             pattern = r'<div class="podcast-extra">\s*<strong>Autoren:</strong>.*?</div>'
             new_block = re.sub(pattern, "", new_block, flags=re.DOTALL)
             if '</audio>' in new_block:
                 new_block = new_block.replace('</audio>', '</audio>\n        <p class="podcast-author">Anonym</p>')
        elif '<p class="podcast-author">' in new_block:
             new_block = re.sub(r'<p class="podcast-author">.*?</p>', '<p class="podcast-author">Anonym</p>', new_block)
        else:
             new_block = re.sub(r'<li class="podcast-item"><strong>Autoren:</strong> .*?</li>', f'<li class="podcast-item"><strong>Autoren:</strong> Anonym</li>', new_block)

    elif choice == '3': # Remove Sources
         if '<strong>Quellen:</strong>' in new_block:
             pattern = r'(<strong>Quellen:</strong>\s*)(.*?)(?=\s*</div>)'
             new_block = re.sub(pattern, f'\\1 Keine', new_block, flags=re.DOTALL)
         else:
             print("No sources section found.")
             return

    update_file_safely(content, podcast['span'], new_block, file_path)
    print("Updated podcast entry.")

# --- MAIN ---
def main():
    print("========================================")
    print("      PODCAST MANAGER - EDIT/DELETE     ")
    print("========================================")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    while True:
        print("\nChoose section to manage:")
        print("1. M2A")
        print("2. S2A")
        print("q. Quit")
        
        section_choice = input("Choice: ").strip().lower()
        if section_choice == 'q':
            break
            
        rel_path = ""
        if section_choice == '1': rel_path = os.path.join("podcasts", "m2a", "index.html")
        elif section_choice == '2': rel_path = os.path.join("podcasts", "s2a", "index.html")
        else: continue
        
        file_path = os.path.join(script_dir, rel_path)
        content = get_file_content(file_path)
        
        if not content:
            print(f"File not found at {file_path}")
            continue
            
        podcasts = extract_podcasts(content)
        
        if not podcasts:
            print("No podcasts found in this file.")
            continue
            
        print(f"\nFound {len(podcasts)} podcasts:")
        for i, p in enumerate(podcasts):
            print(f"{i+1}. {p['title']}")
            
        p_choice = input("\nSelect number to manage (or 'b' for back): ").strip()
        if p_choice == 'b': continue
        
        try:
            idx = int(p_choice) - 1
            if idx < 0 or idx >= len(podcasts): raise ValueError
            target_podcast = podcasts[idx]
        except ValueError:
            print("Invalid selection.")
            continue
            
        # Action Menu
        print(f"\nSelected: {target_podcast['title']}")
        print("Mode:")
        print("1. EDIT (Title, Links, Authors...)")
        print("2. DELETE (Remove entry or clear fields)")
        print("b. Back")
        
        mode = input("Mode: ").strip().lower()
        
        if mode == '1':
            # Re-read content to ensure freshness if we looped (though we break to reload usually)
            # But here we are inside loop.
            # Ideally we reload content every main loop iteration.
            # Passing current 'content' is risky if we edited something else? 
            # No, we only edit one at a time then loop back.
            edit_podcast_logic(target_podcast, content, file_path)
        elif mode == '2':
            delete_podcast_logic(target_podcast, content, file_path)
        
        # Determine if we want to loop back to file selection or podcast selection?
        # Simpler to loop back to file selection to reload content fresh.
        
if __name__ == "__main__":
    main()
