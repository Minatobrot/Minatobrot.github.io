import os

def get_input(prompt_text):
    """
    Get input from the user with a prompt.
    """
    try:
        val = input(f"{prompt_text}: ").strip()
        while not val:
            print("Input cannot be empty. Please try again.")
            val = input(f"{prompt_text}: ").strip()
        return val
    except EOFError:
        return ""

def format_podcast_entry(title, details, archive_link, authors):
    """
    Formats the podcast entry as HTML.
    """
    # Create HTML entry
    return f"""
    <!-- NEUE EPISODE: {title} -->
    <article class="podcast-card">
        <h3>{title}</h3>
        <p>{details}</p>
        
        <audio controls preload="none">
            <source src="{archive_link}" type="audio/mpeg">
            Your browser does not support the audio element.
        </audio>

        <details>
            <summary>Details & Infos</summary>
            <ul class="podcast-details">
                <li class="podcast-item"><strong>Titel:</strong> {title}</li>
                <li class="podcast-item"><strong>Info:</strong> {details}</li>
                <li class="podcast-item"><strong>Autoren:</strong> {authors}</li>
            </ul>
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

def main():
    print("========================================")
    print("      PODCAST MANAGER - SIMPLE ADD      ")
    print("========================================")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    while True:
        print("\nChoose the podcast section to add to:")
        print("1. M2A (podcasts/m2a/index.html)")
        print("2. S2A (podcasts/s2a/index.html)")
        print("q. Quit")
        
        choice = input("Enter your choice (1/2/q): ").strip().lower()
        
        if choice == 'q':
            print("Goodbye!")
            break
            
        if choice == '1':
            target_rel_path = os.path.join("podcasts", "m2a", "index.html")
        elif choice == '2':
            target_rel_path = os.path.join("podcasts", "s2a", "index.html")
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
        details = get_input("Details and Infos")
        authors = get_input("Authors")
        
        # Format HTML
        entry_html = format_podcast_entry(title, details, archive_link, authors)
        
        # Review
        print("\n--- Preview ---")
        print(f"Title:   {title}")
        print(f"Details: {details}")
        print(f"Link:    {archive_link}")
        print(f"Authors: {authors}")
        
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
