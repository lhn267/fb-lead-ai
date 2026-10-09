document.getElementById('btn-show-widget').onclick = async function () {
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (tab && tab.url && tab.url.includes('facebook.com')) {
            chrome.tabs.sendMessage(tab.id, { action: 'show_widget' }, (res) => {
                window.close();
            });
        } else {
            alert('Vui lòng mở trang Facebook trước khi bấm nút này!');
        }
    } catch (e) {
        console.error(e);
    }
};
