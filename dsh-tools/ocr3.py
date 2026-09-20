"""Run WinRT OCR directly on the saved screenshot and list the recognised lines."""
import asyncio
import io

from PIL import Image
from winrt.windows.graphics.imaging import BitmapDecoder
from winrt.windows.media.ocr import OcrEngine
from winrt.windows.storage.streams import DataWriter, InMemoryRandomAccessStream

eng = OcrEngine.try_create_from_user_profile_languages()
print("engine:", eng)


async def run(path: str) -> None:
    img = Image.open(path)
    print("image:", img.size, img.mode)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    stream = InMemoryRandomAccessStream()
    writer = DataWriter(stream)
    writer.write_bytes(buf.getvalue())
    await writer.store_async()
    await writer.flush_async()
    stream.seek(0)
    decoder = await BitmapDecoder.create_async(stream)
    bitmap = await decoder.get_software_bitmap_async()
    engine = OcrEngine.try_create_from_user_profile_languages()
    res = await engine.recognize_async(bitmap)
    lines = list(res.lines)
    print("lines:", len(lines))
    for line in lines[:35]:
        print("   ", line.text)


asyncio.run(run(r"C:\mine\mine\ws_dsh\civ6\dsh-tools\shot.png"))
