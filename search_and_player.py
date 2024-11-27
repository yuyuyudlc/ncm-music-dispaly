import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from io import BytesIO
import requests
import vlc
from pyncm.apis import track, cloudsearch
from pyncm.apis.track import GetTrackLyrics


class SearchAndPlayer:
    def __init__(self, root, progress_bar, lyrics_text, album_cover_label, label_current_length, label_total_length):
        self.root = root
        self.progress_bar = progress_bar
        self.lyrics_text = lyrics_text
        self.album_cover_label = album_cover_label
        self.label_current_length = label_current_length
        self.label_total_length = label_total_length

        self.player = vlc.MediaPlayer()
        self.current_audio_url = None
        self.is_paused = False
        self.total_length = 0
        self.current_page = 1
        self.song_name = ""
        self.lyrics = []
        self.current_lyric_index = 0
        self.songs_per_page = 10

    def search_songs(self, tree_results, entry_search):
        """搜索歌曲"""
        self.song_name = entry_search.get().strip()
        if not self.song_name:
            messagebox.showwarning("输入错误", "请输入歌曲名称！")
            return
        self.load_search_results(tree_results)

    def load_search_results(self, tree_results):
        """加载搜索结果到树视图中"""
        tree_results.delete(*tree_results.get_children())
        choices = self.get_song_choices(self.song_name, self.current_page)
        if choices:
            for song_id, description in choices:
                tree_results.insert("", "end", values=(song_id, description))
        else:
            messagebox.showinfo("结果", "未找到相关歌曲。")

    def get_song_choices(self, song_name, page):
        """获取歌曲的搜索结果"""
        offset = (page - 1) * self.songs_per_page
        result = cloudsearch.GetSearchResult(song_name, limit=self.songs_per_page, offset=offset, stype=1)
        if 'result' in result and 'songs' in result['result']:
            songs = result['result']['songs']
            return [(song['id'], f"{song['name']} - {', '.join(a['name'] for a in song['ar'])}") for song in songs]
        return []

    def prev_page(self, tree_results):
        """上一页搜索结果"""
        if self.current_page > 1:
            self.current_page -= 1
            self.load_search_results(tree_results)

    def next_page(self, tree_results):
        """下一页搜索结果"""
        self.current_page += 1
        self.load_search_results(tree_results)

    def get_audio_url(self, song_id):
        """获取歌曲的音频 URL"""
        try:
            audio_info = track.GetTrackAudio(song_id, bitrate=320000)
            if 'data' in audio_info and audio_info['data']:
                return audio_info['data'][0].get('url')
            return None
        except Exception as e:
            messagebox.showerror("错误", f"获取音频 URL 时发生错误: {e}")
            return None

    def fetch_lyrics(self, song_id):
        """获取歌曲歌词"""
        try:
            response = GetTrackLyrics(song_id)
            if response['code'] == 200:
                raw_lyrics = response.get('lrc', {}).get('lyric', '未找到歌词')
                return self.parse_lyrics(raw_lyrics)
            else:
                return []
        except Exception as e:
            messagebox.showerror("错误", f"获取歌词时发生错误: {e}")
            return []

    def parse_lyrics(self, raw_lyrics):
        """解析歌词"""
        lyrics = []
        for line in raw_lyrics.splitlines():
            if line.startswith("[") and "]" in line:
                timestamp, text = line.split("]", 1)
                timestamp = timestamp.strip("[]")
                minutes, seconds = map(float, timestamp.split(":"))
                time_in_seconds = minutes * 60 + seconds
                lyrics.append((time_in_seconds, text.strip()))
        return lyrics

    def display_lyrics(self):
        """显示歌词"""
        self.lyrics_text.config(state=tk.NORMAL)
        self.lyrics_text.delete(1.0, tk.END)
        for _, text in self.lyrics:
            self.lyrics_text.insert(tk.END, text + "\n")
        self.lyrics_text.config(state=tk.DISABLED)

    def display_album_cover(self, song_id):
        """显示专辑封面"""
        song_info = cloudsearch.GetSearchResult(self.song_name, stype=1)
        album_cover_url = None
        if 'result' in song_info and 'songs' in song_info['result']:
            for song in song_info['result']['songs']:
                if song['id'] == song_id:
                    album_cover_url = song['al']['picUrl']
                    break

        if album_cover_url:
            try:
                response = requests.get(album_cover_url)
                image_data = Image.open(BytesIO(response.content))
                image_data = image_data.resize((200, 200), Image.Resampling.LANCZOS)
                album_cover = ImageTk.PhotoImage(image_data)
                self.album_cover_label.config(image=album_cover)
                self.album_cover_label.image = album_cover
            except Exception as e:
                messagebox.showerror("错误", f"加载专辑封面失败: {e}")
        else:
            messagebox.showinfo("提示", "未找到专辑封面。")

    def play_selected_song(self, tree_results):
        """播放选中的歌曲"""
        selected_item = tree_results.selection()
        if not selected_item:
            messagebox.showwarning("未选择", "请选择一首歌曲！")
            return

        song_id, _ = tree_results.item(selected_item[0], "values")
        audio_url = self.get_audio_url(int(song_id))
        if audio_url:
            self.current_audio_url = audio_url
            self.player.set_media(vlc.Media(audio_url))
            self.player.play()
            self.is_paused = False

            # 获取专辑封面并显示
            self.display_album_cover(int(song_id))

            # 获取歌词并显示
            self.lyrics = self.fetch_lyrics(int(song_id))
            self.display_lyrics()

            threading.Thread(target=self.update_progress_bar, daemon=True).start()
        else:
            messagebox.showerror("错误", "未能获取音频 URL。")

    def toggle_pause(self):
        """切换播放和暂停"""
        if self.is_paused:
            self.player.play()
            self.is_paused = False
        else:
            self.player.pause()
            self.is_paused = True

    def update_progress_bar(self):
        """更新进度条和播放时间"""
        while True:
            time.sleep(1)
            if self.player.is_playing():
                self.total_length = self.player.get_length() / 1000
                current_time = self.player.get_time() / 1000
                if self.total_length > 0:
                    progress = (current_time / self.total_length) * 100
                    self.progress_bar["value"] = progress
                    self.label_current_length.config(text=f"当前时间: {self.format_time(current_time)}")
                    self.label_total_length.config(text=f"总时长: {self.format_time(self.total_length)}")
                    self.highlight_current_lyric(current_time)

    def highlight_current_lyric(self, current_time):
        """高亮当前歌词并将其居中"""
        # 找到当前播放时间对应的歌词索引
        for i, (start_time, text) in enumerate(self.lyrics):
            if start_time > current_time:
                self.current_lyric_index = max(i - 1, 0)
                break
        else:
            self.current_lyric_index = len(self.lyrics) - 1

         # 清除以前的高亮
        self.lyrics_text.tag_remove("highlight", 1.0, tk.END)

    # 设置新的高亮
        start_index = f"{self.current_lyric_index + 1}.0"
        end_index = f"{self.current_lyric_index + 1}.end"
        self.lyrics_text.tag_add("highlight", start_index, end_index)
        self.lyrics_text.tag_config("highlight", background="yellow")

    # 自动滚动，使高亮的歌词居中
        total_lines = int(self.lyrics_text.index("end-1c").split(".")[0])
        visible_lines = int(self.lyrics_text.winfo_height() / self.lyrics_text.dlineinfo("@0,0")[3])
        center_line = max(0, self.current_lyric_index - visible_lines // 2)
        self.lyrics_text.yview_moveto(center_line / total_lines)

    def seek_song(self, event):
        """调整播放进度"""
        if self.total_length > 0:
            seek_position = (event.x / self.progress_bar.winfo_width()) * self.total_length
            self.player.set_time(int(seek_position * 1000))

    @staticmethod
    def format_time(seconds):
        """格式化时间"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
