"""Copy chess images from 副本 to original + generate poker sound effects."""
import os, shutil
import asyncio

# === 1. Copy chess images from 副本 to original ===
src = r'e:\coding-zhou\Python\Python AI象棋对战 - 副本\img'
dst = r'e:\coding-zhou\Python\Python AI象棋对战\img'
os.makedirs(dst, exist_ok=True)

copied = 0
for f in os.listdir(src):
    s = os.path.join(src, f)
    d = os.path.join(dst, f)
    if not os.path.exists(d):
        shutil.copy2(s, d)
        copied += 1
        print(f'Copied chess: {f}')

if copied == 0:
    print('Chess images already exist in original.')
print(f'Total copied: {copied}')

# === 2. Generate 要不起 / 出牌不合规 sound effects using edge_tts ===
out_dir = r'e:\coding-zhou\Python\codinghou\AI扑克牌\img'

try:
    import edge_tts
    async def gen_tts(text, path):
        communicate = edge_tts.Communicate(text, "zh-CN-XiaoyiNeural")
        await communicate.save(path)
    
    tasks = [
        gen_tts("要不起", os.path.join(out_dir, "要不起.mp3")),
        gen_tts("出牌不合规", os.path.join(out_dir, "出牌不合规.mp3")),
    ]
    asyncio.run(asyncio.gather(*tasks))
    print('Generated 要不起.mp3 and 出牌不合规.mp3 via edge_tts')
except ImportError:
    print('edge_tts not installed, generating tone-based fallback...')
    # Fallback: generate simple beeps with pygame-compatible format
    import struct, wave, math
    
    def make_tone(freq, duration, path):
        sample_rate = 22050
        n = int(sample_rate * duration)
        samples = []
        for i in range(n):
            t = i / sample_rate
            env = min(1.0, t * 20) * min(1.0, (duration - t) * 10)
            amp = int(10000 * env * math.sin(2 * math.pi * freq * t))
            samples.append(max(-32767, min(32767, amp)))
        with wave.open(path, 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(struct.pack('<' + 'h' * len(samples), *samples))
        # Convert wav to mp3 using pygame or just keep as wav
        # pygame can load wav too, but game expects mp3 - save as .mp3 with wav header (pygame handles it)
        print(f'Generated tone: {path}')
    
    make_tone(300, 0.5, os.path.join(out_dir, "要不起.wav"))
    make_tone(200, 0.3, os.path.join(out_dir, "出牌不合规.wav"))
    # Also save as mp3 (pygame may accept .wav if registered, or we use the wav)
    # Copy wav to mp3 - not ideal but pygame can load wav
    shutil.copy2(os.path.join(out_dir, "要不起.wav"), os.path.join(out_dir, "要不起.mp3"))
    shutil.copy2(os.path.join(out_dir, "出牌不合规.wav"), os.path.join(out_dir, "出牌不合规.mp3"))
    print('Warning: edge_tts not available, used tone-based fallback (mp3 with wav content)')

# === 3. Generate 背景音乐 (placeholder) ===
def make_background_music(path):
    import struct, wave, math
    sample_rate = 22050
    duration = 180  # 3 minutes
    n = int(sample_rate * duration)
    samples = []
    # Gentle background: low chord
    base_freqs = [110, 164.81, 220]  # A minor chord
    for i in range(n):
        t = i / sample_rate
        val = 0
        for freq in base_freqs:
            val += math.sin(2 * math.pi * freq * t)
        env = 0.3
        amp = int(2000 * env * val)
        samples.append(max(-32767, min(32767, amp)))
    with wave.open(path, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack('<' + 'h' * len(samples), *samples))
    # Copy as mp3 (pygame can load wav)
    shutil.copy2(path, path.replace('.wav', '.mp3'))
    print(f'Generated placeholder 背景音乐 ({duration}s)')

make_background_music(os.path.join(out_dir, "背景音乐.wav"))

print('\nDone!')
