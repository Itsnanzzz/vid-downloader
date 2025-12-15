let currentPlatform = 'tiktok';

const placeholders = {
    tiktok: 'Contoh: https://www.tiktok.com/@username/video/...',
    instagram: 'Contoh: https://www.instagram.com/p/... atau /reel/...',
    facebook: 'Contoh: https://www.facebook.com/watch/?v=... atau fb.watch/...',
    youtube: 'Contoh: https://www.youtube.com/watch?v=... atau youtu.be/...'
};

function switchPlatform(platform) {
    currentPlatform = platform;
    
    // Update tab active state
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active', 'glass-active');
        tab.classList.add('glass');
    });
    const activeTab = document.querySelector(`[data-platform="${platform}"]`);
    activeTab.classList.remove('glass');
    activeTab.classList.add('active', 'glass-active');
    
    // Update placeholder
    document.getElementById('placeholderText').textContent = placeholders[platform];
    
    // Clear input and result
    document.getElementById('url').value = '';
    document.getElementById('result').classList.add('hidden');
    document.getElementById('result').classList.remove('block');
}

const form = document.getElementById('downloadForm');
const loading = document.getElementById('loading');
const result = document.getElementById('result');
const submitBtn = document.getElementById('submitBtn');

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const url = document.getElementById('url').value.trim();
    
    // Reset tampilan
    result.classList.add('hidden');
    result.classList.remove('block');
    loading.classList.remove('hidden');
    loading.classList.add('block');
    submitBtn.disabled = true;
    
    try {
        const response = await fetch('/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: url })
        });
        
        const data = await response.json();
        
        loading.classList.add('hidden');
        loading.classList.remove('block');
        result.classList.remove('hidden');
        result.classList.add('block');
        submitBtn.disabled = false;
        
        if (data.success) {
            const platformEmojis = {
                'tiktok': '🎵',
                'instagram': '📸',
                'facebook': '📘',
                'youtube': '▶️'
            };
            const platformNames = {
                'tiktok': 'TikTok',
                'instagram': 'Instagram',
                'facebook': 'Facebook',
                'youtube': 'YouTube'
            };
            const platformEmoji = platformEmojis[data.platform] || '🎬';
            const platformName = platformNames[data.platform] || 'Unknown';
            
            result.className = 'block mt-5 p-5 glass rounded-xl border-l-4 border-white/50';
            result.innerHTML = `
                <div class="mb-4">
                    <p class="mb-2 text-white/90 drop-shadow-sm"><strong class="text-white drop-shadow-md">📝 Judul:</strong> ${data.title} 
                        <span class="inline-block px-3 py-1 glass-strong text-white rounded-full text-xs font-semibold ml-2 border border-white/30">${platformEmoji} ${platformName}</span>
                    </p>
                    <p class="mb-2 text-white/90 drop-shadow-sm"><strong class="text-white drop-shadow-md">👤 Uploader:</strong> ${data.uploader}</p>
                    <p class="mb-2 text-white/90 drop-shadow-sm"><strong class="text-white drop-shadow-md">⏱️ Durasi:</strong> ${data.duration} detik</p>
                </div>
                <a href="/get-file/${data.file_id}" class="glass-button inline-block px-6 py-3 text-white rounded-lg font-semibold transition-all duration-300 hover:scale-105" download>
                    ⬇️ Download Video
                </a>
                <p class="mt-4 text-sm text-white/80 drop-shadow-sm">
                    💡 File akan otomatis terhapus setelah 1 menit
                </p>
            `;
        } else {
            result.className = 'block mt-5 p-5 glass rounded-xl border-l-4 border-red-300/50';
            result.innerHTML = `
                <p class="text-red-200 font-medium mb-2 drop-shadow-md">❌ ${data.error}</p>
                <p class="text-sm text-white/80 drop-shadow-sm">
                    Pastikan URL valid dan video masih tersedia
                </p>
            `;
        }
    } catch (error) {
        loading.classList.add('hidden');
        loading.classList.remove('block');
        result.classList.remove('hidden');
        result.classList.add('block');
        result.className = 'block mt-5 p-5 glass rounded-xl border-l-4 border-red-300/50';
        result.innerHTML = `
            <p class="text-red-200 font-medium drop-shadow-md">❌ Terjadi kesalahan: ${error.message}</p>
        `;
        submitBtn.disabled = false;
    }
});