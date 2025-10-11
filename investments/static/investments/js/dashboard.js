let sortDesc = true;
let currentFilter = 'all';
let currentPage = 1;
const itemsPerPage = 5;
let assetsData = [];

// CSRF
function getCSRFToken() {
    return document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];
}

// 숫자 포맷
function formatKRW(n) {
    if (n === null || n === undefined || Number.isNaN(n)) return '-';
    return Number(n).toLocaleString('ko-KR');
}

// 통화별 매입가 처리
function normalizePrice(asset) {
    let price = parseFloat(asset.buy_price);
    if (Number.isNaN(price)) price = 0;
    if (asset.asset_type === 'JPY') price /= 100;
    return price;
}


// 모달 제어
document.addEventListener('DOMContentLoaded', () => {
    const modalEl = document.getElementById('asset-modal');
    const assetModal = new bootstrap.Modal(modalEl);
    window.openModal = () => assetModal.show();
    window.closeModal = () => assetModal.hide();

    // 타입 필터
    const typeFilter = document.getElementById('typeFilter');
    if (typeFilter) {
        typeFilter.addEventListener('change', e => {
            currentFilter = e.target.value;
            currentPage = 1;
            renderAssets();
        });
    }

    // 자산 추가
    const form = document.getElementById('asset-form');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const fd = Object.fromEntries(new FormData(form).entries());
            fd.amount = parseInt(fd.amount);
            fd.buy_price = parseFloat(fd.buy_price);

            await fetch('/api/assets/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify(fd)
            });

            closeModal();
            await loadAssets();
            await loadPortfolio();
        });
    }

    loadAssets();
    loadPortfolio();
});

// 데이터 불러오기
async function loadAssets() {
    try {
        const res = await fetch('/api/assets/');
        const data = await res.json();

        // 필드명 통일 및 buy_date 처리
        assetsData = data.map(a => ({
            id: a.id,
            asset_type: a.asset_type ?? a.type ?? 'UNKNOWN',
            amount: a.amount ?? 0,
            buy_price: a.buy_price ?? a.price ?? 0,
            buy_date: new Date(a.buy_date ?? a.date ?? Date.now())
        }));

        currentPage = 1;
        renderAssets();
    } catch (err) {
        console.error('자산 불러오기 실패', err);
        document.getElementById('asset-list').innerHTML = "<p>자산 불러오기 실패</p>";
    }
}

// 렌더링
function renderAssets() {
    if (!assetsData || assetsData.length === 0) {
        document.getElementById('asset-list').innerHTML = "<p>등록된 자산이 없습니다.</p>";
        return;
    }

    let filtered = assetsData.filter(a => currentFilter === 'all' || a.asset_type === currentFilter);

    // 매입일 기준 정렬
    filtered.sort((a, b) => sortDesc ? b.buy_date - a.buy_date : a.buy_date - b.buy_date);

    const total = filtered.reduce((sum, a) => sum + a.amount * normalizePrice(a), 0);

    const start = (currentPage - 1) * itemsPerPage;
    const pageItems = filtered.slice(start, start + itemsPerPage);

    let html = `<div class="table-responsive"><table class="table table-bordered table-striped">
                <thead class="table-light">
                    <tr>
                        <th>자산</th>
                        <th>수량</th>
                        <th>매입가</th>
                        <th>매입일 <button class="btn btn-sm btn-light" onclick="toggleSort()">${sortDesc ? '⬇️' : '⬆️'}</button></th>
                        <th>현재가 (KRW)</th>
                        <th>삭제</th>
                    </tr>
                </thead>
                <tbody>`;

    pageItems.forEach(a => {
        const price = normalizePrice(a) || 0;
        const value = price * (a.amount || 0);
        html += `<tr>
                    <td>${a.asset_type}</td>
                    <td>${a.amount}</td>
                    <td>${price.toFixed(4)}</td>
                    <td>${a.buy_date.toISOString().slice(0, 10)}</td>
                    <td>${formatKRW(value)}</td>
                    <td><button class="btn btn-sm btn-danger" onclick="deleteAsset(${a.id})">삭제</button></td>
                </tr>`;
    });

    html += `<tr>
                <td colspan="4"><strong>총 투자 금액</strong></td>
                <td colspan="2"><strong>${formatKRW(total)}</strong></td>
            </tr>`;

    html += `</tbody></table></div>`;
    document.getElementById('asset-list').innerHTML = html;

    renderPagination(filtered.length);
}

// 페이지네이션
function renderPagination(totalItems) {
    const totalPages = Math.ceil(totalItems / itemsPerPage);
    const container = document.getElementById('asset-pagination');
    container.innerHTML = '';
    for (let i = 1; i <= totalPages; i++) {
        const btn = document.createElement('button');
        btn.className = 'btn btn-sm btn-outline-primary mx-1';
        btn.textContent = i;
        if (i === currentPage) btn.classList.add('active');
        btn.onclick = () => { currentPage = i; renderAssets(); };
        container.appendChild(btn);
    }
}

// 정렬 토글
function toggleSort() {
    sortDesc = !sortDesc;
    renderAssets();
}

// 삭제
async function deleteAsset(id) {
    await fetch(`/api/assets/${id}/delete/`, {
        method: 'DELETE',
        headers: { 'X-CSRFToken': getCSRFToken() }
    });
    await loadAssets();
    await loadPortfolio();
}

// 포트폴리오
async function loadPortfolio() {
    try {
        const res = await fetch('/api/portfolio/');
        const data = await res.json();
        const container = document.getElementById('portfolioResult');
        if (!data.assets || data.assets.length === 0) { container.innerHTML = "<p>자산이 없습니다.</p>"; return; }

        let html = `<div class="table-responsive"><table class="table table-bordered table-striped">
                    <thead class="table-light">
                        <tr>
                            <th>자산</th>
                            <th>수량</th>
                            <th>환율/단가</th>
                            <th>현재가 (KRW)</th>
                        </tr>
                    </thead>
                    <tbody>`;
        data.assets.forEach(a => {
            html += `<tr>
                        <td>${a.type}</td>
                        <td>${a.amount?.toLocaleString() ?? '-'}</td>
                        <td>${a.exchange_rate?.toLocaleString() ?? '-'}</td>
                        <td>${a.current_value_krw?.toLocaleString() ?? '-'}</td>
                    </tr>`;
        });
        html += `<tr>
                    <td colspan="3"><strong>총합</strong></td>
                    <td><strong>${data.total_krw?.toLocaleString() ?? '-'}</strong></td>
                </tr>`;
        html += '</tbody></table></div>';
        container.innerHTML = html;
    } catch (err) {
        console.error('포트폴리오 조회 실패', err);
        document.getElementById('portfolioResult').innerHTML = "<p>조회 실패</p>";
    }
}
