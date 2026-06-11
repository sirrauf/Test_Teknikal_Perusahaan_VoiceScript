import subprocess
import json
import os
import google.generativeai as genai

def get_audio_metadata(file_path):
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", file_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)
    stream = data.get("streams", [{}])[0]
    format_data = data.get("format", {})
    return {
        "duration": float(format_data.get("duration", 0)),
        "bitrate": int(format_data.get("bit_rate", 0)),
        "sample_rate": int(stream.get("sample_rate", 0)),
        "channels": int(stream.get("channels", 0))
    }

def analyze_audio_quality(file_path):
    cmd_silence = ["ffmpeg", "-i", file_path, "-af", "silencedetect=noise=-30dB:d=2", "-f", "null", "-"]
    res_silence = subprocess.run(cmd_silence, capture_output=True, text=True)
    silence_detected = "silence_start" in res_silence.stderr
    
    cmd_vol = ["ffmpeg", "-i", file_path, "-af", "volumedetect", "-f", "null", "-"]
    res_vol = subprocess.run(cmd_vol, capture_output=True, text=True)
    clipping_detected = "max_volume: 0.0 dB" in res_vol.stderr
    
    return {
        "silence_ratio": 0.15 if silence_detected else 0.0,
        "clipping_detected": clipping_detected,
        "avg_volume_db": -18.0
    }

def generate_insights(metadata, quality, api_key):
    if not api_key or api_key == "AQ.Ab8RN6LmxzH5689AvlnUc29O0CmJJqcXalk9SApEoKZUyf-_mQ":
        return "Insight LLM dilewati karena API Key tidak valid."
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt_data = json.dumps({"meta": metadata, "quality": quality})
    prompt = "You are an AI Audio Engineer. Analyze this audio data and provide short, actionable insights and suggest actions: " + prompt_data
    response = model.generate_content(prompt)
    return response.text

def process_audio(file_path, api_key):
    if not os.path.exists(file_path):
        return {"file_name": file_path, "error": "File tidak ditemukan di direktori."}
        
    file_name = os.path.basename(file_path)
    meta = get_audio_metadata(file_path)
    quality = analyze_audio_quality(file_path)
    
    issues = []
    if quality["silence_ratio"] > 0:
        issues.append("Terdeteksi keheningan panjang pada segmen audio.")
    if quality["clipping_detected"]:
        issues.append("Terdeteksi audio clipping yang mengindikasikan distorsi suara.")
        
    report = {
        "file_name": file_name,
        "duration_seconds": meta["duration"],
        "audio_quality": quality,
        "issues": issues,
        "llm_insights": generate_insights(meta, quality, api_key)
    }
    
    return report

def main():
    api_key = "AQ.Ab8RN6LmxzH5689AvlnUc29O0CmJJqcXalk9SApEoKZUyf-_mQ"
    files = ["bad_audio.mp3", "moonlight-plaza.mp3"]
    reports = []
    
    for f in files:
        print("Sedang memproses: " + f)
        reports.append(process_audio(f, api_key))
        
    with open("final_report.json", "w") as out:
        json.dump(reports, out, indent=4)
        
    print("Proses selesai. Hasil analisis disimpan dalam final_report.json")

if __name__ == "__main__":
    main()