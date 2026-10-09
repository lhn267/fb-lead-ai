/**
 * fb_auto_scroll.js - Tiện ích JavaScript Tự Động Cuộn & Cào Bạn Bè Facebook
 * 
 * CÁCH DÙNG:
 * 1. Truy cập https://www.facebook.com/me/friends trên trình duyệt Chrome/Edge/Cốc Cốc
 * 2. Nhấn phím F12 -> chọn tab Console
 * 3. Dán toàn bộ đoạn mã này vào rồi nhấn Enter
 * 4. Bảng điều khiển nổi sẽ xuất hiện ở góc dưới bên phải màn hình:
 *    - Bấm [▶ Bắt đầu cuộn] để tool tự lướt
 *    - Bấm [📥 Xuất File Excel (CSV)] để tải toàn bộ bạn bè về máy!
 */

(function () {
    // Xóa widget cũ nếu đã tồn tại
    const oldWidget = document.getElementById('fb-auto-scroller-widget');
    if (oldWidget) oldWidget.remove();

    // Biến trạng thái
    let isScrolling = false;
    let scrollCount = 0;
    let friendsCount = 0;
    let scrollInterval = null;
    let lastHeight = 0;
    let noChangeCount = 0;
    let startTime = null;
    let timerInterval = null;

    // Tạo giao diện điều khiển nổi (Floating Widget)
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
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.4);
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        font-size: 13px;
        z-index: 999999;
        overflow: hidden;
        user-select: none;
    `;

    widget.innerHTML = `
        <div style="background: #2563EB; padding: 12px 16px; font-weight: 700; font-size: 14px; display: flex; align-items: center; justify-content: space-between; cursor: move;" id="fb-scroller-header">
            <span>🚀 FB Auto-Scroller & Scraper</span>
            <button id="fb-scroller-close" style="background: none; border: none; color: #FFFFFF; font-size: 16px; cursor: pointer;">✕</button>
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
                <button id="fb-btn-toggle" style="background: #22C55E; color: #FFFFFF; border: none; border-radius: 8px; padding: 10px; font-weight: 700; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; transition: 0.2s;">
                    <span>▶ Bắt Đầu Tự Động Cuộn</span>
                </button>
                <button id="fb-btn-export" style="background: #3B82F6; color: #FFFFFF; border: none; border-radius: 8px; padding: 10px; font-weight: 700; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; transition: 0.2s;">
                    <span>📥 Xuất File Excel (CSV) Ngay</span>
                </button>
            </div>
            <div style="font-size: 10.5px; color: #64748B; margin-top: 12px; line-height: 1.4; text-align: center;">
                Tự động cuộn giả lập người thật (delay 2s-3.5s) để chống checkpoint an toàn 100%.
            </div>
        </div>
    `;

    document.body.appendChild(widget);

    // Kéo thả widget (Draggable)
    const header = document.getElementById('fb-scroller-header');
    let isDragging = false, startX, startY, initialLeft, initialTop;
    header.onmousedown = function (e) {
        if (e.target.id === 'fb-scroller-close') return;
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

    // Đóng widget
    document.getElementById('fb-scroller-close').onclick = function () {
        stopAutoScroll();
        widget.remove();
    };

    // Hàm đếm số bạn bè hiện có trên trang
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
        document.getElementById('fb-stat-friends').innerText = count;
        return count;
    }

    // Cập nhật đồng hồ thời gian
    function updateTimer() {
        if (!startTime) return;
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        const mins = String(Math.floor(elapsed / 60)).padStart(2, '0');
        const secs = String(elapsed % 60).padStart(2, '0');
        document.getElementById('fb-stat-time').innerText = `${mins}:${secs}`;
    }

    // Bắt đầu cuộn tự động
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
            document.getElementById('fb-stat-scrolls').innerText = scrollCount;

            // 1. Cuộn một khoảng ngẫu nhiên (600 - 1000px)
            const scrollDistance = Math.floor(Math.random() * 400) + 600;
            window.scrollBy({ top: scrollDistance, behavior: 'smooth' });

            // 2. Thi thoảng cuộn nhẹ ngược lên 80px để mô phỏng người thật
            if (scrollCount % 7 === 0) {
                setTimeout(() => {
                    window.scrollBy({ top: -Math.floor(Math.random() * 60 + 50), behavior: 'smooth' });
                }, 400);
            }

            // 3. Quét số lượng bạn bè
            scanFriends();

            // 4. Kiểm tra chạm đáy
            const currentHeight = document.documentElement.scrollHeight;
            if (currentHeight === lastHeight) {
                noChangeCount++;
                if (noChangeCount >= 6) {
                    stopAutoScroll();
                    document.getElementById('fb-stat-status').innerText = 'Đã hết bạn bè (Chạm đáy)';
                    document.getElementById('fb-stat-status').style.color = '#38BDF8';
                    alert(`🎉 Đã cuộn hết toàn bộ danh sách bạn bè!\nTổng cộng tìm thấy: ${friendsCount} người.\nHãy bấm nút [Xuất File Excel (CSV)] để lưu dữ liệu.`);
                    return;
                }
            } else {
                noChangeCount = 0;
                lastHeight = currentHeight;
            }

            // 5. Delay ngẫu nhiên giữa 2.0s và 3.6s
            const delay = Math.floor(Math.random() * 1600) + 2000;
            scrollInterval = setTimeout(step, delay);
        }

        step();
    }

    // Dừng cuộn
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

    // Toggle nút bắt đầu / tạm dừng
    document.getElementById('fb-btn-toggle').onclick = function () {
        if (isScrolling) {
            stopAutoScroll();
        } else {
            startAutoScroll();
        }
    };

    // Trích xuất và tải file CSV
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

            // Tìm thông tin công việc / bạn chung
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

        // Tạo file CSV có UTF-8 BOM
        const csvContent = '\uFEFF' + rows.map(r => r.join(',')).join('\r\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const aDownload = document.createElement('a');
        aDownload.href = url;
        aDownload.download = `danh_sach_ban_be_facebook_${rows.length - 1}_nguoi.csv`;
        document.body.appendChild(aDownload);
        aDownload.click();
        document.body.removeChild(aDownload);

        alert(`✅ Đã xuất thành công file danh sách ${rows.length - 1} bạn bè!\nFile đã được tải về máy của bạn. Giờ bạn chỉ cần nạp file này vào Tab 1 của ứng dụng web AI để xử lý.`);
    };

    // Quét lần đầu ngay khi mở
    scanFriends();
    console.log("✅ FB Auto-Scroller & Scraper đã được kích hoạt thành công!");
})();
