"""Generate poker sound effects using edge_tts, plus background music."""
import os, asyncio, struct, wave, math, shutil

out_dir = r'e:\coding-zhou\Python\codinghou\AI扑克牌\img'
os.makedirs(out_dir, exist_ok=True)

# Try edge_tts for 要不起 / 出牌不合规
try:
    import edge_tts
    async def gen_tts(text, path):
        comm = edge_tts.Communicate(text, "zh-CN-XiaoyiNeural")
        await comm.save(path)
    
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    loop.run_until_complete(gen_tts("要不起", os.path.join(out_dir, "要不起.mp3")))
    print("OK 要不起.mp3 (edge_tts)")
    loop.run_until_complete(gen_tts("出牌不合规", os.path.join(out_dir, "出牌不合规.mp3")))
    print("OK 出牌不合规.mp3 (edge_tts)")
except Exception as e:
    print(f"edge_tts failed: {e}, using tone fallback")
    # Tone fallback
    def make_beep(freq, dur, path):
        sr = 22050
        n = int(sr * dur)
        samples = []
        for i in range(n):
            t = i / sr
            env = min(1.0, t * 30) * min(1.0, (dur - t) * 20)
            amp = int(8000 * env * math.sin(2 * math.pi * freq * t))
            samples.append(max(-32767, min(32767, amp)))
        with wave.open(path, 'w') as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
            wf.writeframes(struct.pack('<' + 'h' * len(samples), *samples))
        mp3 = path.replace('.wav', '.mp3')
        shutil.copy2(path, mp3)
        print(f'OK {os.path.basename(mp3)} (tone fallback)')
    
    make_beep(400, 0.3, os.path.join(out_dir, "要不起.wav"))
    make_beep(150, 0.25, os.path.join(out_dir, "出牌不合规.wav"))

# Generate background music (placeholder)
def make_bg(path):
    sr, dur = 22050, 180
    n = int(sr * dur)
    base_freqs = [110, 164.81, 220]
    samples = []
    for i in range(n):
        t = i / sr
        val = sum(math.sin(2 * math.pi * f * t) for f in base_freqs)
        samples.append(max(-32767, min(32767, int(1500 * val * 0.3))))
    with wave.open(path, 'w') as wf:
        wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr)
        wf.writeframes(struct.pack('<' + 'h' * len(samples), *samples))
    mp3 = path.replace('.wav', '.mp3')
    shutil.copy2(path, mp3)
    print(f'OK 背景音乐.mp3 (3min placeholder)')

make_bg(os.path.join(out_dir, "背景音乐.wav"))
print('\nDone!')
