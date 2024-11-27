import os
import json
import threading
import tkinter as tk
from tkinter import simpledialog, messagebox
import time
import vlc

class PlaylistManager:
    def __init__(self, player_instance):
        self.playlist_file = "playlists.json"
        self.player_instance = player_instance
        self.playlists = self.load_playlists()

    def load_playlists(self):
        """加载歌单列表"""
        if not os.path.exists(self.playlist_file):
            return {}
        with open(self.playlist_file, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}

    def save_playlists(self):
        """保存歌单列表"""
        with open(self.playlist_file, "w", encoding="utf-8") as f:
            json.dump(self.playlists, f, indent=4, ensure_ascii=False)

    def create_playlist(self, root):
        """创建新的歌单"""
        playlist_name = simpledialog.askstring("创建歌单", "请输入歌单名称:", parent=root)
        if playlist_name:
            if playlist_name in self.playlists:
                messagebox.showwarning("歌单存在", "歌单已存在，请使用不同的名字。")
            else:
                self.playlists[playlist_name] = []
                self.save_playlists()
                messagebox.showinfo("成功", f"歌单 '{playlist_name}' 创建成功！")

    def add_song_to_playlist(self, root, song_id):
        """将歌曲添加到歌单中"""
        if not song_id:
            messagebox.showwarning("未选择歌曲", "请选择要添加的歌曲！")
            return

        playlist_name = simpledialog.askstring("添加到歌单", "请输入歌单名称:", parent=root)
        if playlist_name:
            if playlist_name not in self.playlists:
                messagebox.showwarning("歌单不存在", "歌单不存在，请创建歌单。")
            else:
                if song_id in self.playlists[playlist_name]:
                    messagebox.showinfo("已存在", "歌曲已经在歌单中！")
                else:
                    self.playlists[playlist_name].append(song_id)
                    self.save_playlists()
                    messagebox.showinfo("成功", f"歌曲已成功添加到歌单 '{playlist_name}'！")

    def play_playlist(self, playlist_name):
        """播放整个歌单"""
        if playlist_name not in self.playlists:
            messagebox.showwarning("歌单不存在", "歌单不存在，请创建歌单。")
            return

        if not self.playlists[playlist_name]:
            messagebox.showinfo("歌单为空", "该歌单没有任何歌曲。")
            return

        threading.Thread(target=self._play_songs_from_playlist, args=(playlist_name,), daemon=True).start()

    def _play_songs_from_playlist(self, playlist_name):
        """在单独的线程中播放歌单"""
        for song_id in self.playlists[playlist_name]:
            audio_url = self.player_instance.get_audio_url(song_id)
            if audio_url:
                self.player_instance.player.set_media(vlc.Media(audio_url.encode('utf-8')))
                self.player_instance.player.play()
                self.player_instance.is_paused = False

                # 等待歌曲播放完成
                while self.player_instance.player.is_playing():
                    time.sleep(1)
            else:
                messagebox.showerror("错误", f"未能获取歌曲 ID {song_id} 的音频 URL。")