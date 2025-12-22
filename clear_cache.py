"""Clear Python cache files"""
import os
import shutil

def clear_pycache(directory):
    """Recursively delete __pycache__ directories"""
    count = 0
    for root, dirs, files in os.walk(directory):
        if '__pycache__' in dirs:
            cache_path = os.path.join(root, '__pycache__')
            print(f"Removing: {cache_path}")
            shutil.rmtree(cache_path)
            count += 1

        # Also remove .pyc files
        for file in files:
            if file.endswith('.pyc'):
                file_path = os.path.join(root, file)
                print(f"Removing: {file_path}")
                os.remove(file_path)
                count += 1

    print(f"\nCleared {count} cache items!")
    return count

if __name__ == "__main__":
    import sys
    directory = os.path.dirname(os.path.abspath(__file__))
    print(f"Clearing cache in: {directory}\n")
    clear_pycache(directory)
    print("\nCache cleared! Now you can run the app with fresh code.")
