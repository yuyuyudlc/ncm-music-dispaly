def center_window(window, width, height):
    """
    将窗口居中显示。

    :param window: Tkinter 窗口对象
    :param width: 窗口宽度
    :param height: 窗口高度
    """
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x_offset = (screen_width - width) // 2
    y_offset = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x_offset}+{y_offset}")
