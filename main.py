import tkinter as tk
from tkinter import ttk
from tkinter import simpledialog
from playlist_manager import PlaylistManager
from search_and_player import SearchAndPlayer
from login import LoginWindow
from utils import center_window

class MusicDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("网易云音乐播放器")
        self.root.geometry("1000x600")
        center_window(self.root, 1000, 600)

        # 隐藏主窗口，登录成功后显示
        self.root.withdraw()

        # 初始化播放器和其他控件
        self.player_instance = None
        self.create_widgets()

        # 打开登录窗口
        self.open_login_window()

    def open_login_window(self):
        """打开登录窗口"""
        LoginWindow(self.root, self.login_success)

    def login_success(self):
        """登录成功后回调函数"""
        self.root.deiconify()  # 显示主窗口
        self.player_instance = SearchAndPlayer(
            self.root,
            self.progress_bar,
            self.lyrics_text,
            self.album_cover_label,
            self.label_current_length,
            self.label_total_length,
        )
        self.playlist_manager = PlaylistManager(self.player_instance)
        self.create_playlist_widgets()

    def create_widgets(self):
        """创建主窗口的控件"""
        # 左侧布局
        frame_left = tk.Frame(self.root)
        frame_left.pack(side="left", fill="both", expand=True)

        frame_search = tk.LabelFrame(frame_left, text="搜索歌曲", padx=10, pady=10)
        frame_search.pack(pady=10, fill="x", padx=10)

        tk.Label(frame_search, text="歌曲名称:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.entry_search = tk.Entry(frame_search, width=30)
        self.entry_search.grid(row=0, column=1, padx=5, pady=5)

        self.btn_search = tk.Button(
            frame_search,
            text="搜索",
            command=lambda: self.player_instance.search_songs(self.tree_results, self.entry_search),
        )
        self.btn_search.grid(row=0, column=2, padx=5, pady=5)

        frame_results = tk.LabelFrame(frame_left, text="搜索结果", padx=10, pady=10)
        frame_results.pack(pady=10, fill="both", expand=True, padx=10)

        self.tree_results = ttk.Treeview(frame_results, columns=("song_id", "description"), show="headings")
        self.tree_results.heading("song_id", text="歌曲ID")
        self.tree_results.heading("description", text="描述")
        self.tree_results.column("song_id", width=80)
        self.tree_results.column("description", width=300)
        self.tree_results.pack(fill="both", expand=True)

        frame_pagination = tk.Frame(frame_left)
        frame_pagination.pack(pady=5)

        self.btn_prev_page = tk.Button(
            frame_pagination,
            text="上一页",
            command=lambda: self.player_instance.prev_page(self.tree_results),
        )
        self.btn_prev_page.grid(row=0, column=0, padx=5)

        self.btn_next_page = tk.Button(
            frame_pagination,
            text="下一页",
            command=lambda: self.player_instance.next_page(self.tree_results),
        )
        self.btn_next_page.grid(row=0, column=1, padx=5)

        frame_controls = tk.Frame(frame_left)
        frame_controls.pack(pady=10)

        self.btn_play = tk.Button(
            frame_controls,
            text="播放",
            command=lambda: self.player_instance.play_selected_song(self.tree_results),
        )
        self.btn_play.grid(row=0, column=0, padx=10)

        self.btn_pause = tk.Button(frame_controls, text="暂停", command=self.toggle_pause)
        self.btn_pause.grid(row=0, column=1, padx=10)

        self.progress_bar = ttk.Progressbar(frame_left, orient="horizontal", length=400, mode="determinate")
        self.progress_bar.pack(pady=20)
        self.progress_bar["value"] = 0
        self.progress_bar.bind("<ButtonRelease-1>", self.seek_song)

        self.label_current_length = tk.Label(frame_left, text="当前时间: 00:00")
        self.label_current_length.pack()
        self.label_total_length = tk.Label(frame_left, text="总时长: 00:00")
        self.label_total_length.pack()

        # 右侧歌词显示区域
        frame_lyrics = tk.LabelFrame(self.root, text="歌词", padx=10, pady=10)
        frame_lyrics.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # 专辑封面显示
        self.album_cover_label = tk.Label(frame_lyrics)
        self.album_cover_label.pack(side=tk.TOP, pady=10)

        # 歌词文本框
        self.lyrics_text = tk.Text(frame_lyrics, wrap=tk.WORD, state=tk.DISABLED, font=("Arial", 12))
        self.lyrics_text.pack(side=tk.LEFT, fill="both", expand=True)

        # 滚动条
        self.scrollbar = ttk.Scrollbar(frame_lyrics, command=self.lyrics_text.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.lyrics_text.config(yscrollcommand=self.scrollbar.set)

    def create_playlist_widgets(self):
        """创建歌单管理控件"""
        frame_playlist = tk.Frame(self.root)
        frame_playlist.pack(pady=10)

        btn_create_playlist = tk.Button(
            frame_playlist,
            text="创建歌单",
            command=lambda: self.playlist_manager.create_playlist(self.root)
        )
        btn_create_playlist.grid(row=0, column=0, padx=5)

        btn_add_to_playlist = tk.Button(
            frame_playlist,
            text="添加到歌单",
            command=lambda: self.playlist_manager.add_song_to_playlist(self.root, self.tree_results.selection()[0])
        )
        btn_add_to_playlist.grid(row=0, column=1, padx=5)

        btn_play_playlist = tk.Button(
            frame_playlist,
            text="播放歌单",
            command=lambda: self.playlist_manager.play_playlist(
                simpledialog.askstring("播放歌单", "请输入歌单名称:", parent=self.root)
            )
        )
        btn_play_playlist.grid(row=0, column=2, padx=5)

    def toggle_pause(self):
        """切换播放与暂停"""
        if self.player_instance:
            self.player_instance.toggle_pause()

    def seek_song(self, event):
        """调整播放进度"""
        if self.player_instance:
            self.player_instance.seek_song(event)

if __name__ == "__main__":
    root = tk.Tk()
    app = MusicDownloaderApp(root)
    root.mainloop()
