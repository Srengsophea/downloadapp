# --- Vivid Downloader for Mobile (Kivy Edition) ---
# A cross-platform video downloader built with Kivy for Android.
# This script is fully functional and ready for APK packaging.

import os
import threading
import uuid
from functools import partial
import sys

# Kivy is used for the user interface.
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ObjectProperty
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown

# yt-dlp is used as a Python library to handle video downloads.
import yt_dlp

# --- User Interface Layout (KV Language) ---
KV = '''
#:import get_color_from_hex kivy.utils.get_color_from_hex

<AccentLabel@Label>:
    color: get_color_from_hex("#5865f2")
    
<DimLabel@Label>:
    color: get_color_from_hex("#949ba4")
    font_size: '12sp'
    
<PrimaryButton@Button>:
    background_normal: ''
    background_color: get_color_from_hex("#5865f2")
    font_size: '14sp'  # Smaller font as per user preference
    
<SecondaryButton@Button>:
    background_normal: ''
    background_color: get_color_from_hex("#313338")
    color: get_color_from_hex("#dbdee1")
    font_size: '14sp'  # Smaller font as per user preference
    
<RoundedButton@Button>:
    background_normal: ''
    background_color: get_color_from_hex("#5865f2")
    font_size: '13sp'  # Even smaller for compact design
    size_hint_y: None
    height: '32dp'  # Shorter buttons for compact design
    
<QualityDropDown>:
    auto_width: False
    width: '200dp'
    
<QueueItem>:
    orientation: 'vertical'
    size_hint_y: None
    height: self.minimum_height
    padding: '8dp'  # Reduced padding for compact design
    spacing: '4dp'  # Reduced spacing for compact design
    canvas.before:
        Color:
            rgba: get_color_from_hex("#2b2d31")
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [6]  # Slightly smaller radius
    BoxLayout:
        size_hint_y: None
        height: '40dp'  # Shorter height for compact design
        Label:
            id: title_label
            text: root.title
            font_size: '14sp'  # Smaller font
            halign: 'left'
            valign: 'middle'
            text_size: self.width, None
            shorten: True
            shorten_from: 'right'
        CheckBox:
            size_hint_x: None
            width: '40dp'  # Smaller checkbox
            active: root.selected
            on_active: root.selected = self.active
    BoxLayout:
        size_hint_y: None
        height: '20dp'  # Shorter height
        DimLabel:
            id: uploader_label
            text: root.uploader
            size_hint_x: 0.7
            halign: 'left'
            text_size: self.width, None
        Label:
            id: status_label
            text: root.status
            font_size: '11sp'  # Smaller font
            color: get_color_from_hex("#2dc770") if root.status == "Completed" else get_color_from_hex("#f0b324") if root.status == "Error" else get_color_from_hex("#5865f2") if root.is_processing else get_color_from_hex("#949ba4")
            halign: 'right'
            text_size: self.width, None
    BoxLayout:
        size_hint_y: None
        height: '25dp'
        Label:
            text: 'Quality:'
            color: get_color_from_hex("#949ba4")
            font_size: '12sp'
            size_hint_x: None
            width: '50dp'
        Button:
            id: quality_button
            text: root.quality
            font_size: '12sp'
            background_normal: ''
            background_color: get_color_from_hex("#313338")
            color: get_color_from_hex("#dbdee1")
            on_release: root.show_quality_dropdown()
            disabled: not root.has_formats
    ProgressBar:
        id: progress_bar
        max: 100
        value: root.progress
        size_hint_y: None
        height: '6dp'  # Thinner progress bar
        opacity: 1 if root.is_processing or root.progress > 0 else 0

BoxLayout:
    orientation: 'vertical'
    padding: '8dp'  # Reduced padding
    spacing: '8dp'  # Reduced spacing
    canvas.before:
        Color:
            rgba: get_color_from_hex("#1e1f22")
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        size_hint_y: None
        height: '50dp'
        spacing: '8dp'
        AccentLabel:
            text: 'Downloader'
            font_size: '20sp'  # Slightly smaller
            size_hint_x: 0.4
        Label:
            text: 'Paste link below'
            color: get_color_from_hex("#949ba4")
            font_size: '12sp'
            size_hint_x: 0.6
            halign: 'right'
            valign: 'middle'
    BoxLayout:
        size_hint_y: None
        height: '45dp'  # Shorter input area
        spacing: '8dp'
        TextInput:
            id: url_input
            hint_text: 'Paste video or playlist link here'
            multiline: False
            padding: [12, 12]  # Reduced padding
            background_normal: ''
            background_color: get_color_from_hex("#2b2d31")
            foreground_color: get_color_from_hex("#dbdee1")
            font_size: '14sp'  # Smaller font
        RoundedButton:
            text: 'Analyze'
            width: '80dp'  # Narrower button
            size_hint_x: None
            on_release: app.start_analysis(url_input.text)
    BoxLayout:
        size_hint_y: None
        height: '45dp'
        spacing: '8dp'
        Label:
            text: 'Download Queue'
            color: get_color_from_hex("#dbdee1")
            font_size: '14sp'
            bold: True
        Widget:  # Spacer
        Label:
            id: item_count
            text: '0 items'
            color: get_color_from_hex("#949ba4")
            font_size: '12sp'
    ScrollView:
        bar_width: '8dp'  # Thinner scrollbar
        GridLayout:
            id: queue_container
            cols: 1
            spacing: '8dp'  # Reduced spacing
            size_hint_y: None
            height: self.minimum_height
    BoxLayout:
        size_hint_y: None
        height: '45dp'  # Shorter button area
        spacing: '8dp'
        PrimaryButton:
            id: download_button
            text: 'Download Selected'
            on_release: app.start_downloading_queue()
        SecondaryButton:
            text: 'Select All'
            size_hint_x: 0.4
            on_release: app.select_all_items()
        SecondaryButton:
            text: 'Clear'
            size_hint_x: 0.4
            on_release: app.clear_queue()
'''

class QualityDropDown(DropDown):
    pass

class QueueItem(BoxLayout):
    item_id = StringProperty('')
    title = StringProperty('Untitled Video')
    uploader = StringProperty('Unknown Uploader')
    status = StringProperty('Queued')
    progress = NumericProperty(0)
    selected = BooleanProperty(True)
    is_processing = BooleanProperty(False)
    quality = StringProperty('Best')
    has_formats = BooleanProperty(False)
    video_data = ObjectProperty(None)
    formats = ObjectProperty([])

    def __init__(self, **kwargs):
        super(QueueItem, self).__init__(**kwargs)
        self.dropdown = QualityDropDown()
        self.dropdown.bind(on_select=lambda instance, x: setattr(self, 'quality', x))

    def show_quality_dropdown(self):
        # Clear previous buttons
        self.dropdown.clear_widgets()
        
        # Add format buttons
        for fmt in self.formats:
            btn = Button(text=fmt['label'], size_hint_y=None, height=30)
            btn.bind(on_release=lambda btn: self.dropdown.select(btn.text))
            self.dropdown.add_widget(btn)
        
        # Open dropdown
        self.dropdown.open(self.ids.quality_button)

class VividDownloaderApp(App):
    def build(self):
        Window.clearcolor = get_color_from_hex("#1e1f22")
        self.is_analyzing = False
        self.is_downloading = False
        self.download_path = self.get_download_path()
        print(f"Downloads will be saved to: {self.download_path}")
        return Builder.load_string(KV)

    def get_download_path(self):
        try:
            from android.storage import primary_external_storage_path
            path = os.path.join(primary_external_storage_path(), 'Download')
        except ImportError:
            path = os.path.join(os.path.expanduser("~"), "Downloads", "VividDownloader")
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    def start_analysis(self, url):
        if not url or self.is_analyzing:
            return
            
        # Show a small notification that analysis started
        self.show_notification("Analyzing URL...")
        
        self.root.ids.url_input.text = ""
        self.is_analyzing = True
        threading.Thread(target=self._analyze_thread, args=(url,), daemon=True).start()

    def _analyze_thread(self, url):
        # First get flat info to check if it's a playlist
        ydl_opts_flat = {
            'extract_flat': True, 
            'quiet': True,
            'no_warnings': True
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts_flat) as ydl:
                info_flat = ydl.extract_info(url, download=False)
                
                # If it's a playlist, get entries
                if 'entries' in info_flat:
                    entries = info_flat.get('entries', [])
                    Clock.schedule_once(lambda dt: self.on_analysis_complete(entries))
                else:
                    # Single video - get detailed info with formats
                    ydl_opts_detail = {
                        'quiet': True,
                        'no_warnings': True
                    }
                    with yt_dlp.YoutubeDL(ydl_opts_detail) as ydl_detail:
                        info_detail = ydl_detail.extract_info(url, download=False)
                        Clock.schedule_once(lambda dt: self.on_analysis_complete([info_detail]))
        except Exception as e:
            print(f"Analysis Error: {e}")
            Clock.schedule_once(lambda dt, error=str(e): self.show_error_popup(f"Failed to analyze URL: {error}"))
        finally:
            self.is_analyzing = False

    def on_analysis_complete(self, entries):
        if not entries: 
            self.show_notification("No videos found")
            return
            
        queue_container = self.root.ids.queue_container
        for entry in entries:
            if not entry: continue
            
            # Extract formats for quality selection
            formats = []
            if 'formats' in entry:
                # Filter video formats and create labels
                video_formats = [f for f in entry['formats'] if f.get('vcodec') != 'none']
                # Sort by quality (resolution)
                video_formats.sort(key=lambda x: x.get('height', 0) or 0, reverse=True)
                
                # Create format labels
                for f in video_formats:
                    height = f.get('height', 'N/A')
                    ext = f.get('ext', 'N/A')
                    filesize = f.get('filesize')
                    
                    if filesize:
                        # Convert bytes to MB
                        size_mb = filesize / (1024 * 1024)
                        label = f"{height}p ({ext}) - {size_mb:.1f}MB"
                    else:
                        label = f"{height}p ({ext})"
                        
                    formats.append({
                        'label': label,
                        'format_id': f.get('format_id'),
                        'height': height
                    })
            
            item_widget = QueueItem(
                item_id=str(uuid.uuid4()),
                title=entry.get('title', 'Untitled'),
                uploader=entry.get('uploader', 'Unknown'),
                has_formats=len(formats) > 0
            )
            item_widget.video_data = entry
            item_widget.formats = formats
            
            # Set default quality to best if formats are available
            if formats:
                item_widget.quality = formats[0]['label']
            
            queue_container.add_widget(item_widget)
            
        # Update item count
        self.root.ids.item_count.text = f"{len(queue_container.children)} items"
        
        self.show_notification(f"Added {len(entries)} video(s) to queue")

    def start_downloading_queue(self):
        if self.is_downloading: return
        all_items = reversed(self.root.ids.queue_container.children)
        selected_items = [item for item in all_items if item.selected]
        if not selected_items: 
            self.show_notification("No items selected for download")
            return
            
        self.is_downloading = True
        self.show_notification(f"Starting download of {len(selected_items)} item(s)")
        threading.Thread(target=self._download_thread, args=(selected_items,), daemon=True).start()

    def _download_thread(self, items_to_download):
        for item in items_to_download:
            Clock.schedule_once(lambda dt, i=item: self.update_item_state_for_download(i))
            
            # Determine format ID for download
            format_id = None
            if item.quality != 'Best' and item.formats:
                for fmt in item.formats:
                    if fmt['label'] == item.quality:
                        format_id = fmt['format_id']
                        break
            
            # Build format option
            if format_id:
                format_option = format_id
            else:
                format_option = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            
            ydl_opts = {
                'outtmpl': os.path.join(self.download_path, '%(title)s - [%(id)s].%(ext)s'),
                'progress_hooks': [partial(self.on_download_progress, item)],
                'nocheckcertificate': True,
                'quiet': True,
                'no_warnings': True,
                'format': format_option
            }
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([item.video_data.get('webpage_url') or item.video_data.get('url')])
            except Exception as e:
                print(f"Download error for '{item.title}': {e}")
                Clock.schedule_once(lambda dt, i=item, error=str(e): self.set_item_error(i, error))
        self.is_downloading = False
        Clock.schedule_once(lambda dt: self.show_notification("Downloads completed"))

    def update_item_state_for_download(self, item):
        item.is_processing = True
        item.progress = 0
        item.status = "Starting..."

    def on_download_progress(self, item, d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            if total:
                percent = (d['downloaded_bytes'] / total) * 100
                item.progress = percent
                item.status = f"Downloading... {int(percent)}%"
        elif d['status'] == 'finished':
            item.progress = 100
            item.status = "Completed"
            item.is_processing = False

    def set_item_error(self, item, error_message):
        item.status = "Error"
        item.is_processing = False
        print(f"Error for {item.title}: {error_message}")

    def clear_queue(self):
        if self.is_downloading: 
            self.show_notification("Cannot clear queue while downloading")
            return
        self.root.ids.queue_container.clear_widgets()
        self.root.ids.item_count.text = "0 items"
        self.show_notification("Queue cleared")

    def select_all_items(self):
        queue_container = self.root.ids.queue_container
        for item in queue_container.children:
            item.selected = True
        self.show_notification("All items selected")

    def show_notification(self, message):
        # Simple notification mechanism
        print(f"[NOTIFICATION] {message}")

    def show_error_popup(self, message):
        popup = Popup(title='Error',
                      content=Label(text=message, text_size=(300, None)),
                      size_hint=(None, None), size=(350, 200))
        popup.open()

if __name__ == '__main__':
    VividDownloaderApp().run()