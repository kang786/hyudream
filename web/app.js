document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Kakao Map
    const container = document.getElementById('map');
    const options = {
        center: new kakao.maps.LatLng(36.5, 127.9), // Center of Korea
        level: 11
    };
    const map = new kakao.maps.Map(container, options);

    // Map Controls
    const zoomControl = new kakao.maps.ZoomControl();
    map.addControl(zoomControl, kakao.maps.ControlPosition.RIGHT);
    const mapTypeControl = new kakao.maps.MapTypeControl();
    map.addControl(mapTypeControl, kakao.maps.ControlPosition.TOPRIGHT);

    // Clusterer
    const clusterer = new kakao.maps.MarkerClusterer({
        map: map,
        averageCenter: true,
        minLevel: 8
    });

    let allData = [];
    let markers = [];
    let currentOverlay = null;

    // UI Elements
    const searchInput = document.getElementById('search-input');
    const menuBtn = document.getElementById('menu-btn');
    const filterPanel = document.getElementById('filter-panel');
    const categoryFilter = document.getElementById('category-filter');
    const phoneToggle = document.getElementById('phone-toggle');
    const linkToggle = document.getElementById('link-toggle');
    const resultsList = document.getElementById('results-list');
    const listTitle = document.getElementById('list-title');
    const listCount = document.getElementById('list-count');
    const bottomSheet = document.getElementById('bottom-sheet');
    const sheetHandle = document.querySelector('.sheet-handle');

    // Category Colors (for tags)
    const categoryColors = {
        'lodging': '#3498db',
        'sports': '#27ae60',
        'mart': '#9b59b6',
        'welfare_service': '#e67e22',
        'contact': '#7f8c8d',
        'other': '#e74c3c'
    };

    const categoryLabels = {
        'lodging': '숙박/휴양',
        'sports': '체력/골프',
        'mart': '마트/쇼핑',
        'welfare_service': '복지/민원',
        'contact': '연락처',
        'other': '기타'
    };

    // Fetch Data
    fetch('data.json')
        .then(response => response.json())
        .then(data => {
            allData = data;
            updateView();
        })
        .catch(error => console.error('Error loading data:', error));

    // Event Listeners
    searchInput.addEventListener('input', updateView);
    categoryFilter.addEventListener('change', updateView);
    phoneToggle.addEventListener('change', updateView);
    linkToggle.addEventListener('change', updateView);

    // Mobile UI Interactions
    menuBtn.addEventListener('click', () => {
        filterPanel.classList.toggle('hidden');
    });

    // Bottom Sheet Logic (Simple Expand/Collapse)
    let isExpanded = false;

    function toggleSheet() {
        isExpanded = !isExpanded;
        bottomSheet.style.height = isExpanded ? '90vh' : '40vh';
    }

    sheetHandle.addEventListener('click', toggleSheet);
    listTitle.addEventListener('click', toggleSheet);


    function updateView() {
        const filtered = filterData();
        renderMarkers(filtered);
        renderList(filtered);
        listCount.textContent = `(${filtered.length})`;
    }

    function filterData() {
        const query = searchInput.value.toLowerCase();
        const category = categoryFilter.value;
        const requirePhone = phoneToggle.checked;
        const requireLink = linkToggle.checked;

        return allData.filter(item => {
            const name = (item.name || '').toLowerCase();
            const address = (item.address || '').toLowerCase();
            if (query && !name.includes(query) && !address.includes(query)) return false;
            if (category !== 'all' && item.category !== category) return false;
            if (requirePhone && !item.phone) return false;
            if (requireLink && !item.homepage_or_booking_url) return false;
            return true;
        });
    }

    function renderMarkers(filteredData) {
        // Clear existing
        if (clusterer) clusterer.clear();
        markers = [];
        if (currentOverlay) currentOverlay.setMap(null);

        filteredData.forEach(item => {
            if (item.lat && item.lng) {
                const position = new kakao.maps.LatLng(item.lat, item.lng);

                const marker = new kakao.maps.Marker({
                    position: position,
                    title: item.name
                });

                // Marker Click Event
                kakao.maps.event.addListener(marker, 'click', function () {
                    if (currentOverlay) currentOverlay.setMap(null);

                    const catLabel = categoryLabels[item.category] || item.category;
                    const catColor = categoryColors[item.category] || '#666';

                    const content = `
                        <div class="customoverlay">
                            <span class="close-btn" onclick="closeOverlay()" title="닫기">×</span>
                            <h3>${item.name || '이름 없음'} <span class="tag" style="background-color: ${catColor}">${catLabel}</span></h3>
                            <p>${item.address || '-'}</p>
                            ${item.phone ? `<p>📞 <a href="tel:${item.phone}">${item.phone}</a></p>` : ''}
                            ${item.homepage_or_booking_url ? `<p><a href="${item.homepage_or_booking_url}" target="_blank">🔗 예약/홈페이지</a></p>` : ''}
                            ${item.hours ? `<p>⏰ ${item.hours}</p>` : ''}
                        </div>
                    `;

                    currentOverlay = new kakao.maps.CustomOverlay({
                        position: position,
                        content: content,
                        yAnchor: 1
                    });

                    currentOverlay.setMap(map);
                    map.panTo(position);
                });

                markers.push(marker);
            }
        });

        clusterer.addMarkers(markers);
    }

    // Global function for close button in overlay
    window.closeOverlay = function () {
        if (currentOverlay) currentOverlay.setMap(null);
    }

    let currentPage = 1;
    const itemsPerPage = 20;

    function renderList(filteredData, isLoadMore = false) {
        if (!isLoadMore) {
            resultsList.innerHTML = '';
            currentPage = 1;
        }

        const start = (currentPage - 1) * itemsPerPage;
        const end = currentPage * itemsPerPage;
        const displayItems = filteredData.slice(start, end);

        displayItems.forEach(item => {
            const div = document.createElement('div');
            div.className = 'list-item';
            const catLabel = categoryLabels[item.category] || item.category;
            const hasCoords = item.lat && item.lng;
            const locationStatus = hasCoords ? '' : '<span style="color:#e74c3c; font-size:11px;">(위치 미확인)</span>';

            div.innerHTML = `
                <h3>${item.name} <small style="color:#888; font-size:12px;">${catLabel}</small> ${locationStatus}</h3>
                <div class="meta">${item.address || '주소 없음'}</div>
                ${item.phone ? `<div class="meta">📞 ${item.phone}</div>` : ''}
            `;

            div.addEventListener('click', () => {
                if (hasCoords) {
                    const moveLatLon = new kakao.maps.LatLng(item.lat, item.lng);
                    map.setLevel(4);
                    map.panTo(moveLatLon);

                    // Collapse sheet on selection to show map
                    bottomSheet.style.height = '40vh';
                    isExpanded = false;

                    // Trigger marker click if we can match it (simplified)
                    // In a real app we'd map ID to marker.
                }
            });

            resultsList.appendChild(div);
        });

        // Load More Button
        const existingBtn = document.getElementById('load-more-btn');
        if (existingBtn) existingBtn.remove();

        if (filteredData.length > end) {
            const moreBtn = document.createElement('button');
            moreBtn.id = 'load-more-btn';
            moreBtn.textContent = `더 보기 (+${Math.min(itemsPerPage, filteredData.length - end)})`;
            moreBtn.addEventListener('click', () => {
                currentPage++;
                renderList(filteredData, true);
            });
            resultsList.appendChild(moreBtn);
        }

        if (filteredData.length === 0) {
            resultsList.innerHTML = '<div style="padding:20px; text-align:center; color:#888;">검색 결과가 없습니다.</div>';
        }
    }
});
