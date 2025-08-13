import json
import os
import sys
from nintendo_image_scraper import main as scrape_game

# Try to import PIL for image processing
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: PIL (Pillow) not available. Image conversion will be skipped.")
    print("To enable image conversion, install Pillow: pip install Pillow")

def load_games_data(filepath):
    """Load games data from JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File {filepath} not found.")
        return []
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {filepath}: {e}")
        return []

def get_processed_games(output_dir):
    """Get list of already processed games by checking existing files"""
    processed = set()
    
    # Check both square and main directories
    for subdir in ['square', 'main']:
        subdir_path = os.path.join(output_dir, subdir)
        if os.path.exists(subdir_path):
            for filename in os.listdir(subdir_path):
                if filename.endswith('.jpg'):
                    # Extract game name from filename (remove _square.jpg or _main.jpg)
                    game_name = filename.replace('_square.jpg', '').replace('_main.jpg', '')
                    processed.add(game_name)
    
    return processed

def save_progress(progress_file, processed_games):
    """Save progress to a file"""
    try:
        with open(progress_file, 'w') as f:
            json.dump(list(processed_games), f)
    except Exception as e:
        print(f"Warning: Could not save progress: {e}")

def load_progress(progress_file):
    """Load progress from a file"""
    if not os.path.exists(progress_file):
        return set()
    
    try:
        with open(progress_file, 'r') as f:
            return set(json.load(f))
    except Exception as e:
        print(f"Warning: Could not load progress file: {e}")
        return set()

def convert_square_images(output_dir, size=(512, 512)):
    """Convert square images to WebP format and resize to specified dimensions"""
    if not PIL_AVAILABLE:
        print("Skipping image conversion (PIL not available)")
        return
    
    square_dir = os.path.join(output_dir, 'square')
    converted_dir = os.path.join(output_dir, 'square-converted')
    
    # Create the converted directory if it doesn't exist
    if not os.path.exists(converted_dir):
        os.makedirs(converted_dir)
    
    # Check if square directory exists
    if not os.path.exists(square_dir):
        print(f"Square directory not found: {square_dir}")
        return
    
    print(f"\nConverting square images to WebP ({size[0]}x{size[1]})...")
    
    converted_count = 0
    for filename in os.listdir(square_dir):
        if filename.endswith('.jpg'):
            input_path = os.path.join(square_dir, filename)
            output_filename = filename.replace('.jpg', '.webp')
            output_path = os.path.join(converted_dir, output_filename)
            
            try:
                # Open the image
                with Image.open(input_path) as img:
                    # Resize the image
                    img_resized = img.resize(size, Image.Resampling.LANCZOS)
                    
                    # Save as WebP with good quality
                    img_resized.save(output_path, 'WEBP', quality=85, method=6)
                    converted_count += 1
                    print(f"Converted: {filename} -> {output_filename}")
            except Exception as e:
                print(f"Error converting {filename}: {e}")
    
    print(f"Converted {converted_count} images to WebP format in {converted_dir}")

def process_games(games_file='games.json', output_dir='images', resume=True):
    """Process all games from JSON file, skipping already processed ones"""
    # Load games data
    games = load_games_data(games_file)
    if not games:
        print("No games data found. Exiting.")
        return
    
    print(f"Found {len(games)} games in {games_file}")
    
    # Create output directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Track processed games
    progress_file = os.path.join(output_dir, 'processed_games.json')
    processed_games = load_progress(progress_file) if resume else set()
    
    print(f"Already processed {len(processed_games)} games.")
    
    # Process each game
    for i, game in enumerate(games, 1):
        title = game.get('title', '')
        if not title:
            print(f"Skipping game {i}/{len(games)}: No title found")
            continue
        
        # Clean title for filename comparison
        clean_title = ''.join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip().lower().replace(' ', '_')
        
        # Check if already processed
        if clean_title in processed_games:
            print(f"Skipping game {i}/{len(games)}: {title} (already processed)")
            continue
        
        print(f"\nProcessing game {i}/{len(games)}: {title}")
        
        try:
            # Process the game (this will prompt for selection if needed)
            result = scrape_game(title, output_dir, auto_select=False)
            
            # Mark as processed if successful
            if result:
                processed_games.add(result)  # Use the actual clean name returned by the function
                save_progress(progress_file, processed_games)
                print(f"Successfully processed: {title}")
            else:
                print(f"Failed to process: {title}")
            
        except KeyboardInterrupt:
            print(f"\nInterrupted by user while processing: {title}")
            print("Progress saved. You can resume by running the script again.")
            return
        except Exception as e:
            print(f"Error processing {title}: {e}")
            print("Continuing with next game...")
            continue
    
    print(f"\nFinished processing all games. {len(processed_games)} games processed in total.")
    
    # Convert square images to WebP
    convert_square_images(output_dir)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Process all games from games.json and scrape images")
    parser.add_argument("--games-file", "-g", default="games.json", help="Path to games JSON file")
    parser.add_argument("--output", "-o", default="images", help="Output directory for images")
    parser.add_argument("--no-resume", action="store_true", help="Start from beginning, ignore previous progress")
    
    args = parser.parse_args()
    
    process_games(args.games_file, args.output, resume=not args.no_resume)