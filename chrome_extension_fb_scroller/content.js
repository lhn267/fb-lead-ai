// content.js - Tự Động Cuộn & Cào Dữ Liệu Bạn Bè Facebook

(function () {
    if (window.__fbAutoScrollerInjected) return;
    window.__fbAutoScrollerInjected = true;

    let isScrolling = false;
    let scrollCount = 0;
    let friendsCount = 0;
    let scrollInterval = null;
    let lastHeight = 0;
    let noChangeCount = 0;
    let startTime = null;
    let timerInterval = null;

    // 1. Tạo nút nổi thu gọn (Mini Toggle Button)
    const miniBtn = document.createElement('div');
    miniBtn.id = 'fb-mini-scroller-btn';
    miniBtn.innerHTML = '<span>⚡ Tự Động Cuộn</span>';
    miniBtn.style.cssText = `
        position: fixed;
        bottom: 25px;
        right: 25px;
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
        color: #FFFFFF;
        padding: 10px 18px;
        border-radius: 30px;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-size: 13px;
        font-weight: 700;
        cursor: pointer;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.4);
        z-index: 999998;
        display: flex;
        align-items: center;
        gap: 6px;
        transition: transform 0.2s, box-shadow 0.2s;
    `;
    miniBtn.onmouseover = () => { miniBtn.style.transform = 'scale(1.05)'; };
    miniBtn.onmouseout = () => { miniBtn.style.transform = 'scale(1)'; };

    // 2. Tạo bảng điều khiển đầy đủ (Main Widget)
    const widget = document.createElement('div');
    widget.id = 'fb-auto-scroller-widget';
    widget.style.cssText = `
        position: fixed;
        bottom: 25px;
        right: 25px;
        width: 320px;
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        color: #F8FAFC;
        border: 2px solid #3B82F6;
        border-radius: 14px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-size: 13px;
        z-index: 999999;
        overflow: hidden;
        user-select: none;
        display: none;
    `;

    widget.innerHTML = `
        <div style="background: #2563EB; padding: 12px 16px; font-weight: 700; font-size: 13.5px; display: flex; align-items: center; justify-content: space-between; cursor: move;" id="fb-scroller-header">
            <span>🚀 Tự Động Cuộn Facebook</span>
            <div style="display: flex; gap: 8px;">
                <button id="fb-scroller-minimize" style="background: none; border: none; color: #FFFFFF; font-size: 16px; cursor: pointer; padding: 0 4px;">−</button>
            </div>
        </div>
        <div style="padding: 16px;">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 12px; text-align: center;">
                <div style="background: rgba(255,255,255,0.06); padding: 8px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);">
                    <div style="font-size: 11px; color: #94A3B8; text-transform: uppercase;">Bạn bè tìm thấy</div>
                    <div id="fb-stat-friends" style="font-size: 20px; font-weight: 800; color: #38BDF8; margin-top: 2px;">0</div>
                </div>
                <div style="background: rgba(255,255,255,0.06); padding: 8px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);">
                    <div style="font-size: 11px; color: #94A3B8; text-transform: uppercase;">Số lần cuộn</div>
                    <div id="fb-stat-scrolls" style="font-size: 20px; font-weight: 800; color: #4ADE80; margin-top: 2px;">0</div>
                </div>
            </div>

            <div style="font-size: 12px; color: #CBD5E1; margin-bottom: 14px; display: flex; justify-content: space-between;">
                <span>Trạng thái: <b id="fb-stat-status" style="color: #FBBF24;">Sẵn sàng</b></span>
                <span>Thời gian: <b id="fb-stat-time">00:00</b></span>
            </div>

            <div style="display: flex; flex-direction: column; gap: 8px;">
                <button id="fb-btn-toggle" style="background: #22C55E; color: #FFFFFF; border: none; border-radius: 8px; padding: 10px; font-weight: 700; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px;">
                    <span>▶ Bắt Đầu Tự Động Cuộn</span>
                </button>
                <button id="fb-btn-export" style="background: #3B82F6; color: #FFFFFF; border: none; border-radius: 8px; padding: 10px; font-weight: 700; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px;">
                    <span>📥 Xuất File Excel (CSV) Ngay</span>
                </button>
            </div>
            <div style="font-size: 10.5px; color: #64748B; margin-top: 12px; line-height: 1.4; text-align: center;">
                Tự động cuộn giả lập người thật (delay 2s-3.5s) để chống checkpoint an toàn 100%.
            </div>
        </div>
    `;

    document.body.appendChild(miniBtn);
    document.body.appendChild(widget);

    // Xử lý mở/thu gọn widget
    miniBtn.onclick = function () {
        miniBtn.style.display = 'none';
        widget.style.display = 'block';
        scanFriends();
    };

    document.getElementById('fb-scroller-minimize').onclick = function () {
        widget.style.display = 'none';
        miniBtn.style.display = 'flex';
    };

    // Kéo thả widget
    const header = document.getElementById('fb-scroller-header');
    let isDragging = false, startX, startY, initialLeft, initialTop;
    header.onmousedown = function (e) {
        if (e.target.id === 'fb-scroller-minimize') return;
        isDragging = true;
        startX = e.clientX;
        startY = e.clientY;
        const rect = widget.getBoundingClientRect();
        initialLeft = rect.left;
        initialTop = rect.top;
        widget.style.right = 'auto';
        widget.style.bottom = 'auto';
        widget.style.left = initialLeft + 'px';
        widget.style.top = initialTop + 'px';
        document.onmousemove = function (ev) {
            if (!isDragging) return;
            widget.style.left = (initialLeft + ev.clientX - startX) + 'px';
            widget.style.top = (initialTop + ev.clientY - startY) + 'px';
        };
        document.onmouseup = function () {
            isDragging = false;
            document.onmousemove = null;
            document.onmouseup = null;
        };
    };

    // Hàm đếm số bạn bè hiện có
    function scanFriends() {
        const links = document.querySelectorAll('a[href*="/"]');
        const seen = new Set();
        let count = 0;
        links.forEach(a => {
            const href = a.getAttribute('href') || '';
            const isProfile = (href.includes('facebook.com/') || href.startsWith('/')) &&
                !href.includes('/groups/') && !href.includes('/watch/') && !href.includes('/marketplace/') &&
                !href.includes('/gaming/') && !href.includes('/notifications') && !href.includes('/messages/') &&
                !href.includes('/pages/') && !href.includes('#') && !href.includes('login');
            if (isProfile) {
                const text = a.innerText.trim();
                const ignore = ['thêm bạn bè', 'nhắn tin', 'bạn bè', 'xóa', 'chặn', 'theo dõi', 'hủy kết bạn', 'xem tất cả'];
                if (text && text.length > 1 && !ignore.includes(text.toLowerCase()) && text.length < 50) {
                    const clean = href.split('?')[0];
                    if (!seen.has(clean)) {
                        seen.add(clean);
                        count++;
                    }
                }
            }
        });
        friendsCount = count;
        const el = document.getElementById('fb-stat-friends');
        if (el) el.innerText = count;
        return count;
    }

    function updateTimer() {
        if (!startTime) return;
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        const mins = String(Math.floor(elapsed / 60)).padStart(2, '0');
        const secs = String(elapsed % 60).padStart(2, '0');
        const el = document.getElementById('fb-stat-time');
        if (el) el.innerText = `${mins}:${secs}`;
    }

    function startAutoScroll() {
        isScrolling = true;
        startTime = Date.now();
        timerInterval = setInterval(updateTimer, 1000);

        const btn = document.getElementById('fb-btn-toggle');
        btn.innerHTML = '<span>⏸ Tạm Dừng Cuộn</span>';
        btn.style.background = '#F59E0B';
        document.getElementById('fb-stat-status').innerText = 'Đang cuộn...';
        document.getElementById('fb-stat-status').style.color = '#4ADE80';

        function step() {
            if (!isScrolling) return;

            scrollCount++;
            const sEl = document.getElementById('fb-stat-scrolls');
            if (sEl) sEl.innerText = scrollCount;

            // Cuộn ngẫu nhiên 600 - 1000px
            const scrollDistance = Math.floor(Math.random() * 400) + 600;
            window.scrollBy({ top: scrollDistance, behavior: 'smooth' });

            // Vi cuộn ngược nhẹ mô phỏng mắt người
            if (scrollCount % 7 === 0) {
                setTimeout(() => {
                    window.scrollBy({ top: -Math.floor(Math.random() * 60 + 50), behavior: 'smooth' });
                }, 400);
            }

            scanFriends();

            // Kiểm tra chạm đáy trang
            const currentHeight = document.documentElement.scrollHeight;
            if (currentHeight === lastHeight) {
                noChangeCount++;
                if (noChangeCount >= 6) {
                    stopAutoScroll();
                    document.getElementById('fb-stat-status').innerText = 'Đã hết bạn bè (Chạm đáy)';
                    document.getElementById('fb-stat-status').style.color = '#38BDF8';
                    alert(`🎉 Đã cuộn hết toàn bộ danh sách bạn bè!\nTổng cộng tìm thấy: ${friendsCount} người.\nHãy bấm nút [Xuất File Excel (CSV)] để tải dữ liệu.`);
                    return;
                }
            } else {
                noChangeCount = 0;
                lastHeight = currentHeight;
            }

            // Delay ngẫu nhiên giữa 2.0s và 3.6s
            const delay = Math.floor(Math.random() * 1600) + 2000;
            scrollInterval = setTimeout(step, delay);
        }

        step();
    }

    function stopAutoScroll() {
        isScrolling = false;
        if (scrollInterval) clearTimeout(scrollInterval);
        if (timerInterval) clearInterval(timerInterval);

        const btn = document.getElementById('fb-btn-toggle');
        if (btn) {
            btn.innerHTML = '<span>▶ Tiếp Tục Cuộn</span>';
            btn.style.background = '#22C55E';
        }
        const st = document.getElementById('fb-stat-status');
        if (st && st.innerText !== 'Đã hết bạn bè (Chạm đáy)') {
            st.innerText = 'Đã tạm dừng';
            st.style.color = '#FBBF24';
        }
    }

    document.getElementById('fb-btn-toggle').onclick = function () {
        if (isScrolling) {
            stopAutoScroll();
        } else {
            startAutoScroll();
        }
    };

    // Xuất file CSV UTF-8 BOM
    document.getElementById('fb-btn-export').onclick = function () {
        stopAutoScroll();
        const links = document.querySelectorAll('a[href*="/"]');
        const seen = new Set();
        const rows = [
            ['STT', 'Họ và tên', 'Link Facebook', 'Thông tin giới thiệu / Công việc']
        ];

        let index = 1;
        links.forEach(a => {
            const href = a.getAttribute('href') || '';
            const isProfile = (href.includes('facebook.com/') || href.startsWith('/')) &&
                !href.includes('/groups/') && !href.includes('/watch/') && !href.includes('/marketplace/') &&
                !href.includes('/gaming/') && !href.includes('/notifications') && !href.includes('/messages/') &&
                !href.includes('/pages/') && !href.includes('#') && !href.includes('login');

            if (!isProfile) return;

            let name = a.innerText.trim();
            if (!name || name.length < 2 || name.includes('\n')) {
                const span = a.querySelector('span[dir="auto"], span');
                if (span) name = span.innerText.trim();
            }

            const ignore = ['thêm bạn bè', 'nhắn tin', 'bạn bè', 'xóa', 'chặn', 'theo dõi', 'hủy kết bạn', 'xem tất cả'];
            if (!name || ignore.includes(name.toLowerCase()) || name.length > 50) return;

            let clean = href.startsWith('http') ? href : ('https://www.facebook.com' + href);
            clean = clean.split('?')[0].replace(/\/+$/, '');
            clean = clean.replace(/\/friends_mutual$/, '').replace(/\/friends$/, '').replace(/\/about$/, '');

            if (seen.has(clean)) return;
            seen.add(clean);

            let card = a.closest('div[role="article"]') || a.closest('div[data-visualcompletion="ignore-dynamic-snippet"]') || a.parentElement?.parentElement?.parentElement;
            let info = '';
            if (card) {
                const lines = card.innerText.trim().split('\n').map(l => l.trim()).filter(l => l && l !== name && !ignore.includes(l.toLowerCase()));
                if (lines.length > 0) info = lines.join(' · ');
            }

            rows.push([
                index++,
                `"${name.replace(/"/g, '""')}"`,
                `"${clean}"`,
                `"${info.replace(/"/g, '""')}"`
            ]);
        });

        if (rows.length <= 1) {
            alert('Chưa tìm thấy dữ liệu bạn bè nào trên màn hình. Hãy bấm [Bắt đầu cuộn] trước!');
            return;
        }

        const csvContent = '\uFEFF' + rows.map(r => r.join(',')).join('\r\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const aDownload = document.createElement('a');
        aDownload.href = url;
        aDownload.download = `danh_sach_ban_be_facebook_${rows.length - 1}_nguoi.csv`;
        document.body.appendChild(aDownload);
        aDownload.click();
        document.body.removeChild(aDownload);
    };

    // Lắng nghe message từ extension popup
    chrome.runtime.onMessage?.addListener((req, sender, sendResponse) => {
        if (req.action === 'show_widget') {
            miniBtn.style.display = 'none';
            widget.style.display = 'block';
            scanFriends();
            sendResponse({ status: 'ok' });
        }
    });

    console.log("⚡ FB Auto-Scroller extension loaded!");
})();
