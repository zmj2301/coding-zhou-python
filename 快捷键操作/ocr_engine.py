import tempfile
import os
import asyncio

import winrt.windows.media.ocr as ocr
import winrt.windows.globalization as gl
import winrt.windows.graphics.imaging as imaging
import winrt.windows.storage as storage
import winrt.windows.storage.streams as streams
import winrt.windows.foundation.collections as collections

from PIL import Image


_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        _engine = ocr.OcrEngine.try_create_from_language(gl.Language("zh-CN"))
    return _engine


def _pilotobitmap(pil_image):
    path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            path = os.path.abspath(f.name)
            pil_image.save(f, format="PNG")

        loop = asyncio.new_event_loop()
        task = loop.create_task(_load_bitmap_async(path))
        bitmap = loop.run_until_complete(task)
        loop.close()
        return bitmap
    finally:
        if path and os.path.exists(path):
            os.unlink(path)


async def _load_bitmap_async(path):
    file = await storage.StorageFile.get_file_from_path_async(path)
    stream = await file.open_read_async()
    decoder = await imaging.BitmapDecoder.create_async(stream)
    return await decoder.get_software_bitmap_async()


def recognize(pil_image):
    engine = _get_engine()
    if engine is None:
        return []

    bitmap = _pilotobitmap(pil_image)
    if bitmap is None:
        return []

    loop = asyncio.new_event_loop()
    task = loop.create_task(_recognize_async(engine, bitmap))
    result = loop.run_until_complete(task)
    loop.close()

    lines = []
    for line in result.lines:
        words = []
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        for word in line.words:
            r = word.bounding_rect
            words.append({
                "text": word.text,
                "x": r.x,
                "y": r.y,
                "w": r.width,
                "h": r.height,
            })
            min_x = min(min_x, r.x)
            min_y = min(min_y, r.y)
            max_x = max(max_x, r.x + r.width)
            max_y = max(max_y, r.y + r.height)

        lines.append({
            "text": line.text,
            "x": min_x,
            "y": min_y,
            "w": max_x - min_x if max_x != float('-inf') else 0,
            "h": max_y - min_y if max_y != float('-inf') else 0,
            "words": words,
        })
    return lines


async def _recognize_async(engine, bitmap):
    return await engine.recognize_async(bitmap)