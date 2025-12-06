# app.py
from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp
import os
import tempfile
import threading
import time

app = Flask(__name__, template_folder='views', static_folder='static')

# Fungsi untuk menghapus file temporary setelah beberapa detik
# Catatan: Di Vercel/serverless, threading cleanup mungkin tidak bekerja
# karena function berakhir sebelum thread selesai
def cleanup_file(filepath, delay=60):
    def delete():
        time.sleep(delay)
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"🗑️ File dihapus: {filepath}")
        except Exception as e:
            print(f"Error menghapus file: {e}")
    
    # Di Vercel, cleanup akan dilakukan otomatis saat function selesai
    # Threading hanya untuk local development
    try:
        thread = threading.Thread(target=delete)
        thread.daemon = True
        thread.start()
    except:
        # Fallback jika threading tidak tersedia
        pass

# Fungsi untuk download video dari TikTok atau Instagram
def download_video(url, platform='tiktok'):
    try:
        # Buat temporary directory
        # Di Vercel, ini akan otomatis menggunakan /tmp
        temp_dir = tempfile.mkdtemp(dir='/tmp' if os.path.exists('/tmp') else None)
        
        # Konfigurasi yt-dlp
        ydl_opts = {
            'format': 'best',
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        }
        
        # Konfigurasi khusus untuk Instagram
        if platform == 'instagram':
            ydl_opts['format'] = 'best'
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Dapatkan path file yang didownload
            filename = ydl.prepare_filename(info)
            title = info.get('title', f'{platform}_video')
            
            return {
                'success': True,
                'filepath': filename,
                'title': title,
                'uploader': info.get('uploader', 'Unknown'),
                'duration': info.get('duration', 0),
                'platform': platform
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

# Fungsi untuk deteksi platform dari URL
def detect_platform(url):
    url_lower = url.lower()
    if 'tiktok.com' in url_lower or 'vt.tiktok.com' in url_lower or 'vm.tiktok.com' in url_lower:
        return 'tiktok'
    elif 'instagram.com' in url_lower or 'instagr.am' in url_lower:
        return 'instagram'
    elif 'facebook.com' in url_lower or 'fb.com' in url_lower or 'fb.watch' in url_lower:
        return 'facebook'
    elif 'youtube.com' in url_lower or 'youtu.be' in url_lower:
        return 'youtube'
    else:
        return 'unknown'

# Dictionary untuk menyimpan info file temporary
temp_files = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return '', 204  # No content

@app.route('/favicon.png')
def favicon_png():
    return '', 204  # No content

@app.route('/download', methods=['POST'])
def download():
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'success': False, 'error': 'URL tidak boleh kosong'})
        
        # Deteksi platform
        platform = detect_platform(url)
        
        if platform == 'unknown':
            return jsonify({
                'success': False, 
                'error': 'URL tidak valid. Gunakan URL dari TikTok, Instagram, Facebook, atau YouTube'
            })
        
        # Download video
        result = download_video(url, platform)
        
        if result['success']:
            # Generate unique ID untuk file
            file_id = str(hash(result['filepath']))
            temp_files[file_id] = result['filepath']
            
            # Jadwalkan penghapusan file
            cleanup_file(result['filepath'], delay=60)
            
            return jsonify({
                'success': True,
                'title': result['title'],
                'uploader': result['uploader'],
                'duration': result['duration'],
                'platform': result['platform'],
                'file_id': file_id
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            })
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download/tiktok', methods=['POST'])
def download_tiktok_route():
    """Route khusus untuk TikTok"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'success': False, 'error': 'URL tidak boleh kosong'})
        
        result = download_video(url, 'tiktok')
        
        if result['success']:
            file_id = str(hash(result['filepath']))
            temp_files[file_id] = result['filepath']
            cleanup_file(result['filepath'], delay=60)
            
            return jsonify({
                'success': True,
                'title': result['title'],
                'uploader': result['uploader'],
                'duration': result['duration'],
                'platform': 'tiktok',
                'file_id': file_id
            })
        else:
            return jsonify({'success': False, 'error': result['error']})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download/instagram', methods=['POST'])
def download_instagram_route():
    """Route khusus untuk Instagram"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'success': False, 'error': 'URL tidak boleh kosong'})
        
        result = download_video(url, 'instagram')
        
        if result['success']:
            file_id = str(hash(result['filepath']))
            temp_files[file_id] = result['filepath']
            cleanup_file(result['filepath'], delay=60)
            
            return jsonify({
                'success': True,
                'title': result['title'],
                'uploader': result['uploader'],
                'duration': result['duration'],
                'platform': 'instagram',
                'file_id': file_id
            })
        else:
            return jsonify({'success': False, 'error': result['error']})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download/facebook', methods=['POST'])
def download_facebook_route():
    """Route khusus untuk Facebook"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'success': False, 'error': 'URL tidak boleh kosong'})
        
        result = download_video(url, 'facebook')
        
        if result['success']:
            file_id = str(hash(result['filepath']))
            temp_files[file_id] = result['filepath']
            cleanup_file(result['filepath'], delay=60)
            
            return jsonify({
                'success': True,
                'title': result['title'],
                'uploader': result['uploader'],
                'duration': result['duration'],
                'platform': 'facebook',
                'file_id': file_id
            })
        else:
            return jsonify({'success': False, 'error': result['error']})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download/youtube', methods=['POST'])
def download_youtube_route():
    """Route khusus untuk YouTube"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'success': False, 'error': 'URL tidak boleh kosong'})
        
        result = download_video(url, 'youtube')
        
        if result['success']:
            file_id = str(hash(result['filepath']))
            temp_files[file_id] = result['filepath']
            cleanup_file(result['filepath'], delay=60)
            
            return jsonify({
                'success': True,
                'title': result['title'],
                'uploader': result['uploader'],
                'duration': result['duration'],
                'platform': 'youtube',
                'file_id': file_id
            })
        else:
            return jsonify({'success': False, 'error': result['error']})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get-file/<file_id>')
def get_file(file_id):
    try:
        if file_id not in temp_files:
            return "File tidak ditemukan atau sudah dihapus", 404
        
        filepath = temp_files[file_id]
        
        if not os.path.exists(filepath):
            return "File tidak ditemukan", 404
        
        # Dapatkan nama file
        filename = os.path.basename(filepath)
        
        # Hapus dari dictionary setelah diakses
        del temp_files[file_id]
        
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return f"Error: {str(e)}", 500

# Handler untuk Vercel
# Vercel Python runtime akan otomatis mencari variable 'app' atau 'handler'
# Pastikan variable app tersedia di level module
handler = app

if __name__ == '__main__':
    print("""
    ╔═══════════════════════════════════════╗
    ║   TikTok & Instagram Downloader 🚀   ║
    ╚═══════════════════════════════════════╝
    
    🌐 Server berjalan di: http://localhost:5000
    📦 Install dependencies: pip install flask yt-dlp
    
    📋 Supported Platforms:
       🎵 TikTok - Videos, Reels
       📸 Instagram - Reels, Posts, Stories, IGTV
       📘 Facebook - Videos, Watch
       ▶️ YouTube - Videos, Shorts
    
    📁 Struktur folder:
       app.py (backend)
       views/
         ├── index.html (homepage)
         └── static/
             ├── css/
             └── js/
    
    """)
    app.run(debug=True, host='0.0.0.0', port=5000)


