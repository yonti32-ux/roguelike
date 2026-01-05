import os

# Files to IGNORE (so we don't crash the chat with images or huge files)
IGNORE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.wav', '.mp3', '.ogg', '.pyc', '.git'}
IGNORE_DIRS = {'venv', '.idea', '__pycache__', '.git', 'build', 'dist'}


def pack_project():
    project_text = "Here is my full project structure and code:\n\n"

    # Get the current folder
    start_dir = os.getcwd()

    for root, dirs, files in os.walk(start_dir):
        # Remove ignored directories so we don't walk into them
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in IGNORE_EXTENSIONS:
                continue

            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, start_dir)

            # Skip the packer script itself
            if "pack_project.py" in file:
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                project_text += f"--- START OF FILE: {rel_path} ---\n"
                project_text += content + "\n"
                project_text += f"--- END OF FILE: {rel_path} ---\n\n"
            except Exception as e:
                print(f"Skipping {rel_path} (could not read file).")

    # Save to a text file
    with open("full_project_code.txt", "w", encoding="utf-8") as f:
        f.write(project_text)

    print("Done! Open 'full_project_code.txt' and copy-paste it to the AI.")


if __name__ == "__main__":
    pack_project()