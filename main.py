import tkinter as tk
from ctypes import windll  # For Windows blur effect
from PIL import Image, ImageTk, ImageDraw, ImageFilter, ImageSequence
import os
import random
import pygame  # For music playback
import pygame.event
import time
import threading

# Create a custom event for song end
SONG_END_EVENT = pygame.USEREVENT + 1

def apply_blur(root):
    hwnd = windll.user32.GetParent(root.winfo_id())
    windll.dwmapi.DwmEnableBlurBehindWindow(hwnd, 1)

def get_random_image():
    image_folder = "image_folder"  # Folder containing images
    if not os.path.exists(image_folder):
        print(f"Error: Folder '{image_folder}' not found.")
        return None
    
    images = [f for f in os.listdir(image_folder) if f.endswith((".png", ".jpg", ".jpeg"))]
    if images:
        return os.path.join(image_folder, random.choice(images))
    print("Error: No images found in the folder.")
    return None

def load_image():
    img_path = get_random_image()
    if img_path:
        img = Image.open(img_path).convert("RGBA")
        # Reduced image size for compact layout
        img = img.resize((160, 160), Image.LANCZOS)  
        
        # Create a rounded rectangle mask with corner radius
        mask = Image.new("L", (160, 160), 0)
        draw = ImageDraw.Draw(mask)
        
        # Draw rounded rectangle with 20px corner radius (reduced)
        corner_radius = 20
        draw.rounded_rectangle([(0, 0), (160, 160)], radius=corner_radius, fill=255)
        
        # Apply mask to image
        img.putalpha(mask)
        
        # Create a soft shadow effect
        shadow = Image.new("RGBA", (170, 170), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.rounded_rectangle([(5, 5), (165, 165)], radius=corner_radius, fill=(0, 0, 0, 80))
        shadow = shadow.filter(ImageFilter.GaussianBlur(4))
        
        # Create white border frame
        border = Image.new("RGBA", (170, 170), (0, 0, 0, 0))
        border_draw = ImageDraw.Draw(border)
        
        # Draw white border with rounded corners
        border_draw.rounded_rectangle([(5, 5), (165, 165)], radius=corner_radius, 
                                     outline=(255, 255, 255, 180), width=2)
        
        # Composite shadow and image
        final_image = Image.new("RGBA", (170, 170), (0, 0, 0, 0))
        final_image.paste(shadow, (0, 0), shadow)
        final_image.paste(img, (5, 5), img)
        
        # Paste border on top
        final_image.paste(border, (0, 0), border)
        
        img_tk = ImageTk.PhotoImage(final_image)
        image_label.config(image=img_tk)
        image_label.image = img_tk

# Add function to handle GIF animation
def load_cat_gif():
    try:
        # Load the cat GIF
        cat_gif_path = "icon/cat.gif"  # Make sure to have a cat.gif file in your project directory
        
        # Open the GIF file
        cat_gif = Image.open(cat_gif_path)
        
        # Extract frames from the GIF
        frames = []
        for frame in ImageSequence.Iterator(cat_gif):
            # Convert to RGBA and resize as needed
            frame = frame.convert("RGBA")
            frame = frame.resize((80, 80), Image.LANCZOS)  # Adjust size as needed
            
            # Create PhotoImage
            frame_tk = ImageTk.PhotoImage(frame)
            frames.append(frame_tk)
        
        return frames
    except Exception as e:
        print(f"Error loading cat GIF: {e}")
        return None

# Function to animate the cat GIF
def animate_cat_gif(frame_index=0):
    if cat_frames:
        # Update the frame
        cat_label.config(image=cat_frames[frame_index])
        
        # Schedule next frame update
        next_frame = (frame_index + 1) % len(cat_frames)
        # Animation speed (in milliseconds)
        delay = 100  # Adjust for faster or slower animation
        
        # Schedule next frame
        root.after(delay, animate_cat_gif, next_frame)

def update_image():
    load_image()
    update_song_title()

def update_song_title():
    if music_list:
        song_title = os.path.basename(music_list[current_index])
        # Trim long titles with ellipsis
        title_text = os.path.splitext(song_title)[0]
        if len(title_text) > 25:  # Limit title length
            title_text = title_text[:22] + "..."
        song_label.config(text=title_text)

def get_music_list():
    music_folder = "music"  # Folder containing music
    if not os.path.exists(music_folder):
        print(f"Error: Folder '{music_folder}' not found.")
        return []
    
    songs = [f for f in os.listdir(music_folder) if f.endswith((".mp3", ".wav"))]
    return [os.path.join(music_folder, song) for song in songs]

def format_time(seconds):
    """Convert seconds to mm:ss format"""
    if seconds < 0:
        seconds = 0
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

def update_progress():
    """Update progress bar and time labels while song is playing"""
    global is_playing, song_length
    
    while True:
        if is_playing and pygame.mixer.music.get_busy():
            current_pos = pygame.mixer.music.get_pos() / 1000  # Current position in seconds
            
            # Adding the start position if we resumed from pause
            if paused_pos > 0:
                current_pos += paused_pos
                
            # Update progress bar
            if song_length > 0:  # Avoid division by zero
                progress = current_pos / song_length
                progress_bar.set(progress)
                
            # Update time labels
            current_time_label.config(text=format_time(current_pos))
            total_time_label.config(text=format_time(song_length))
            
        time.sleep(0.1)  # Small delay to reduce CPU usage

def progress_click(event):
    """Handle click on progress bar to seek in the song"""
    global paused_pos, song_length
    
    if not music_list or song_length <= 0:
        return
        
    # Calculate the position to seek to based on where user clicked
    width = progress_bar.winfo_width()
    click_position = event.x / width
    seek_time = click_position * song_length
    
    # Update the position
    pygame.mixer.music.play(start=seek_time)
    paused_pos = seek_time
    
    # If we're paused, we need to pause again after seeking
    if not is_playing:
        pygame.mixer.music.pause()

def get_song_length(song_path):
    """Get the duration of a song in seconds"""
    # Initialize a temporary pygame mixer if needed
    if not pygame.mixer.get_init():
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        
    # Use pygame to get the length
    try:
        temp_sound = pygame.mixer.Sound(song_path)
        length = temp_sound.get_length()  # Length in seconds
        return length
    except:
        print(f"Could not get duration for {song_path}")
        return 0

def check_music_events():
    """Check if music has ended and play next song automatically"""
    global is_playing
    
    # Only check if we're currently playing music
    if is_playing and pygame.mixer.get_init() and not pygame.mixer.music.get_busy():
        # Current song has ended (not busy anymore), play the next one
        play_next()
    
    # Schedule this function to run again after 200ms
    root.after(200, check_music_events)

def play_music():
    global is_playing, paused, current_index, paused_pos, song_length
    
    if not pygame.mixer.get_init():
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    
    if is_playing:
        paused_pos = pygame.mixer.music.get_pos() / 1000
        if paused_pos > 0:  # Add previous pause position if any
            paused_pos += paused_pos
        pygame.mixer.music.pause()
        play_button.config(image=play_icon)
        is_playing = False
        paused = True
    else:
        if paused:
            pygame.mixer.music.unpause()
        else:
            if music_list:
                pygame.mixer.music.load(music_list[current_index])
                song_length = get_song_length(music_list[current_index])
                pygame.mixer.music.play()
                # Set up the end event for the current song
                pygame.mixer.music.set_endevent(SONG_END_EVENT)
                paused_pos = 0
                update_song_title()
        
        play_button.config(image=pause_icon)
        is_playing = True
        paused = False

def play_next():
    global current_index, is_playing, paused, paused_pos, song_length
    if music_list:
        current_index = (current_index + 1) % len(music_list)
        pygame.mixer.music.load(music_list[current_index])
        song_length = get_song_length(music_list[current_index])
        pygame.mixer.music.play()
        # Set end event for the new song
        pygame.mixer.music.set_endevent(SONG_END_EVENT)
        play_button.config(image=pause_icon)
        is_playing = True
        paused = False
        paused_pos = 0
        update_image()
        update_heart_icon()  # Update heart icon for the new song

def play_prev():
    global current_index, is_playing, paused, paused_pos, song_length
    if music_list:
        current_index = (current_index - 1) % len(music_list)
        pygame.mixer.music.load(music_list[current_index])
        song_length = get_song_length(music_list[current_index])
        pygame.mixer.music.play()
        # Set end event for the new song
        pygame.mixer.music.set_endevent(SONG_END_EVENT)
        play_button.config(image=pause_icon)
        is_playing = True
        paused = False
        paused_pos = 0
        update_image()
        update_heart_icon()  # Update heart icon for the new song

# Add this to your global variables section (at the bottom of your code)
# Initialize a dictionary to track liked songs
liked_songs = {}

def toggle_like():
    global liked_songs, current_index
    
    # Get current song path as a unique identifier
    if not music_list:
        return
        
    current_song = music_list[current_index]
    
    # Toggle liked status for this specific song
    if current_song in liked_songs:
        # If song is already in liked_songs, remove it (unlike)
        del liked_songs[current_song]
        heart_button.config(image=heart_icon)
    else:
        # Add song to liked_songs
        liked_songs[current_song] = True
        # Use the existing heart_filled_icon
        heart_button.config(image=heart_filled_icon)

def update_heart_icon():
    """Update the heart icon based on whether the current song is liked"""
    if not music_list:
        return
        
    current_song = music_list[current_index]
    
    if current_song in liked_songs:
        # This song is liked, show filled heart
        heart_button.config(image=heart_filled_icon)
    else:
        # This song is not liked, show regular heart
        heart_button.config(image=heart_icon)

# Create custom progress bar style
class AestheticProgressBar(tk.Canvas):
    def __init__(self, master=None, **kwargs):
        self.height = kwargs.pop('height', 6)  # Slightly thicker bar
        self.width = kwargs.pop('width', 200)
        self.bg_color = kwargs.pop('bg_color', "#d8e2dc")
        self.fg_color = kwargs.pop('fg_color', "#ffb5a7")
        self.indicator_color = kwargs.pop('indicator_color', "#735d78")
        self.progress = 0

        super().__init__(master, width=self.width, height=self.height + 12, 
                         bg="#344e41", highlightthickness=0, **kwargs)

        self.bg_rect = self.create_rounded_rectangle(0, 6, self.width, self.height + 6, 
                                                     radius=self.height/2, fill=self.bg_color)
        self.progress_rect = self.create_rounded_rectangle(0, 6, 0, self.height + 6, 
                                                           radius=self.height/2, fill=self.fg_color,)
        self.indicator = self.create_oval(-2, 2, 12, 16, fill=self.indicator_color, outline="")

        self.bind("<Button-1>", self._on_click)

    def create_rounded_rectangle(self, x1, y1, x2, y2, radius=0, **kwargs):
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1
        ]
        return self.create_polygon(points, **kwargs, smooth=True)

    def set(self, value):
        self.progress = max(0, min(value, 1))
        progress_width = int(self.width * self.progress)

        if progress_width > 0:
            self.coords(self.progress_rect, 0, 6, progress_width, self.height + 6)
            self.itemconfig(self.progress_rect, state="normal")
        else:
            self.itemconfig(self.progress_rect, state="hidden")

        indicator_pos = progress_width - 7
        if indicator_pos < -2:
            indicator_pos = -2
        elif indicator_pos > self.width - 12:
            indicator_pos = self.width - 12
        
        self.coords(self.indicator, indicator_pos, 2, indicator_pos + 14, 16)

    def _on_click(self, event):
        self.event_generate("<<ProgressClick>>", x=event.x, y=event.y)


# Create main window
root = tk.Tk()
root.geometry("400x440")  # Increased height slightly to accommodate the cat GIF
root.title("Meowsic Player")
root.configure(bg="#588157")  # Background color
root.resizable(False, False)  # Disable resizing for consistent layout

# Apply blur effect (only works on Windows 10+)
try:
    apply_blur(root)
except:
    print("Blur effect is not supported on this OS")

# Main container frame
main_frame = tk.Frame(root, bg="#344e41")
main_frame.pack(padx=10, pady=10, expand=True, fill="both")

title_label = tk.Label(main_frame, text="✧˚ ༘ ⋆。˚ Meowsic Player ⋆.ೃ࿔*:･", 
                      bg="#344e41", fg="black", 
                      font=("Comic Sans MS", 14, "bold"))
title_label.pack()


# Frame for aesthetic image (centered)
image_frame = tk.Frame(main_frame, bg="#344e41", bd=0, relief="flat")
image_frame.pack(pady=10)

# Image label
image_label = tk.Label(image_frame, bg="#344e41")
image_label.pack()

# Create a frame for the cat GIF at the bottom left
cat_frame = tk.Frame(main_frame, bg="#344e41", bd=0)
cat_frame.place(x=20, y=340)  # Position at bottom left

# Label for cat GIF
cat_label = tk.Label(cat_frame, bg="#344e41", bd=0)
cat_label.pack()

# Song title label with smaller font and less padding
song_label = tk.Label(main_frame, text="No song playing", bg="#344e41", fg="white", 
                      font=("Segoe UI", 12, "bold"))
song_label.pack(pady=5)



progress_frame = tk.Frame(main_frame, bg="#344e41")
progress_frame.pack(pady=5, padx=40, fill="x")

progress_bar = AestheticProgressBar(progress_frame, width=300, height=6, 
                                    bg_color="#d8e2dc", fg_color="#ffb5a7")
progress_bar.pack(fill="x")
progress_bar.bind("<<ProgressClick>>", progress_click)

# Time labels frame with less spacing
time_frame = tk.Frame(progress_frame, bg="#344e41")
time_frame.pack(fill="x", pady=2)

# Smaller font for time labels
current_time_label = tk.Label(time_frame, text="00:00", bg="#344e41", fg="white", 
                            font=("Segoe UI", 8))
current_time_label.pack(side="left")

total_time_label = tk.Label(time_frame, text="00:00", bg="#344e41", fg="white", 
                          font=("Segoe UI", 8))
total_time_label.pack(side="right")

# Combine controls and heart in one frame to save space
combined_controls_frame = tk.Frame(main_frame, bg="#344e41")
combined_controls_frame.place(relx=0.52, rely=0.78, anchor="center")

# Load icons for buttons - smaller sizes for compact design
prev_icon = ImageTk.PhotoImage(Image.open("icon/prev.png").resize((40, 40), Image.LANCZOS))
play_icon = ImageTk.PhotoImage(Image.open("icon/play.png").resize((48, 48), Image.LANCZOS))
pause_icon = ImageTk.PhotoImage(Image.open("icon/pause.png").resize((48, 48), Image.LANCZOS))
next_icon = ImageTk.PhotoImage(Image.open("icon/next.png").resize((40, 40), Image.LANCZOS))
heart_icon = ImageTk.PhotoImage(Image.open("icon/heart.png").resize((32, 32), Image.LANCZOS))

# Try to create a filled heart icon for liked state
try:
    heart_filled_icon = ImageTk.PhotoImage(Image.open("icon/heart_filled.png").resize((32, 32), Image.LANCZOS))
except:
    # If filled heart icon doesn't exist, use regular heart icon
    heart_filled_icon = heart_icon

# Create playback buttons with heart button in same row
prev_button = tk.Button(combined_controls_frame, image=prev_icon, bg="#344e41", bd=0, 
                       activebackground="#344e41", command=play_prev)
prev_button.grid(row=0, column=0, padx=12)

play_button = tk.Button(combined_controls_frame, image=play_icon, bg="#344e41", bd=0, 
                       activebackground="#344e41", command=play_music)
play_button.grid(row=0, column=1, padx=12)

next_button = tk.Button(combined_controls_frame, image=next_icon, bg="#344e41", bd=0, 
                       activebackground="#344e41", command=play_next)
next_button.grid(row=0, column=2, padx=12)

# Heart button in the same row as controls
heart_button = tk.Button(combined_controls_frame, image=heart_icon, bg="#344e41", bd=0, 
                        activebackground="#344e41", command=toggle_like)
heart_button.grid(row=0, column=3, padx=12)

# Initialize global variables
liked = False
is_playing = False
paused = False
current_index = 0
paused_pos = 0
song_length = 0
music_list = get_music_list()
loop_active = False 

# Load initial image
load_image()

# Load and start the cat GIF animation
cat_frames = load_cat_gif()
if cat_frames:
    animate_cat_gif()
else:
    print("Could not load cat GIF animation")

# Start progress update thread
progress_thread = threading.Thread(target=update_progress, daemon=True)
progress_thread.start()

# Start checking for music end events
check_music_events()

root.mainloop()