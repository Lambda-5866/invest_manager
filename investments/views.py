# investments/views.py
import requests
from datetime import date, datetime, timedelta
from collections import OrderedDict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from django.shortcuts import render
from django.core.cache import cache
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from .models import Asset
from .serializers import AssetSerializer

ECOS_API_KEY = "OQ0VZR6EXHJORKOX9HTG"  # 이미 발급받은 키
BASE_URL = "https://ecos.bok.or.kr/api/StatisticSearch"

# -----------------------
# 대시보드 뷰
# -----------------------
def dashboard_view(request):
    context = {
        "asset_types": Asset.ASSET_TYPES,
    }
    return render(request, "dashboard/dashboard.html", context)


# -----------------------
# Asset list/create/delete
# -----------------------
class AssetListCreateAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        assets = Asset.objects.all()
        serializer = AssetSerializer(assets, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = AssetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print(serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AssetDeleteAPIView(APIView):
    permission_classes = [AllowAny]

    def delete(self, request, pk):
        try:
            asset = Asset.objects.get(pk=pk)
            asset.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Asset.DoesNotExist:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)


# -----------------------
# ECOS 환율 조회 (캐시 포함)
# -----------------------

# ECOS 통계표 코드 (고정: 731Y001)
# 세부 항목 코드만 통화별로 다름
ECOS_CURRENCY_CODES = {
    "USD": "0000002",  # 원/달러 매매기준율(매일)
    "JPY": "0000006",  # 원/100엔 매매기준율(매일)
    "CNY": "0000007",  # 원/위안 매매기준율(매일)
}


def fetch_ecos_rate(currency_code: str, date_str: str) -> float | None:
    cache_key = f"ecos_rate_{currency_code}_{date_str}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    table_code = ECOS_CURRENCY_CODES.get(currency_code)
    if not table_code:
        return None

    current_date = datetime.strptime(date_str, "%Y%m%d")

    while True:
        url = f"{BASE_URL}/{ECOS_API_KEY}/json/kr/1/1/731Y003/D/{current_date.strftime('%Y%m%d')}/{current_date.strftime('%Y%m%d')}/{table_code}"

        try:
            res = requests.get(url, timeout=8)
            data = res.json()

            # 데이터 없음 (INFO-200)이면 하루 전으로 이동
            result_info = data.get("RESULT")
            if result_info and result_info.get("CODE") == "INFO-200":
                print(f"{current_date.strftime('%Y-%m-%d')} 데이터 없음, 하루 전으로 재시도합니다.")
                current_date -= timedelta(days=1)
                continue

            rows = data.get("StatisticSearch", {}).get("row")
            if not rows:
                return None

            row = rows[0] if isinstance(rows, list) else rows
            raw = row.get("DATA_VALUE")
            if not raw:
                return None

            rate = float(raw)
            if currency_code == "JPY":
                rate /= 100.0  # 100엔 → 1엔 단위로 환산
                rate = round(rate, 3)

            # 최초 요청 날짜 기준으로 캐시 저장
            cache.set(cache_key, rate, timeout=3600)
            return rate

        except Exception as e:
            print("ECOS fetch error:", e)
            return None

# -----------------------
# ECOS 금 시세 조회 (캐시 포함)
# -----------------------
def fetch_gold_price_krw(date_str: str) -> float | None:
    """
    한국은행 ECOS API를 사용해 금 시세(원/돈)를 조회합니다.
    국제 금 가격(USD/ounce)을 원화로 변환하고, 1돈(3.75g) 기준으로 반환.
    """
    cache_key = f"gold_price_krw_{date_str}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    current_date = datetime.strptime(date_str, "%Y%m%d")
    current_date = current_date.replace(day=1) - timedelta(days=1)  # 전월 마지막 날
    

    # API 요청 URL (startCount, endCount 추가)
    url = f"{BASE_URL}/{ECOS_API_KEY}/json/kr/1/1/902Y003/M/{current_date.strftime('%Y%m')}/{current_date.strftime('%Y%m')}/040101"
    print("Gold 요청 URL:", url)

    try:
        # 금 가격 요청 (USD/ounce)
        res = requests.get(url, timeout=8)
        res.raise_for_status()
        data = res.json()
        rows = data.get("StatisticSearch", {}).get("row")

        row = rows[0] if isinstance(rows, list) else rows
        gold_price_usd = float(row.get("DATA_VALUE"))

        # USD/KRW 환율 가져오기
        usd_rate = fetch_ecos_rate("USD", current_date.strftime("%Y%m%d"))
        if usd_rate is None:
            print(f"{current_date.strftime('%Y-%m-%d')} USD 환율 조회 실패")
            current_date -= timedelta(days=1)

        # 금 1온스(31.1035g)를 원화로 변환
        gold_price_krw_per_oz = gold_price_usd * usd_rate
        # 1돈(3.75g)으로 변환 (31.1035g / 3.75g ≈ 8.29427)
        gold_price_krw_per_don = gold_price_krw_per_oz / 8.29427
        gold_price_krw_per_don = round(gold_price_krw_per_don, 0)

        # 캐시 저장
        cache.set(cache_key, gold_price_krw_per_don, timeout=3600)
        return gold_price_krw_per_don

    except Exception as e:
        print(f"Gold fetch error: {e}")

    return None


# -----------------------
# Portfolio API
# -----------------------
class PortfolioView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # 오늘 날짜 기준
        date_str = date.today().strftime("%Y%m%d")
        
        # 통화별 누적 정보
        summary = OrderedDict()
        total_krw = Decimal("0")

        for asset in Asset.objects.all():
            # 수량
            try:
                amt = Decimal(asset.amount)
            except (InvalidOperation, TypeError):
                amt = Decimal("0")

            exchange_rate = None
            current_value_krw = None

            # 자산 유형별 환율/시세 처리
            if asset.asset_type == "KRW":
                exchange_rate = Decimal("10000")
                current_value_krw = amt * exchange_rate

            elif asset.asset_type == "GOLD":
                gold_per_g = fetch_gold_price_krw(date_str)
                if gold_per_g is None:
                    try:
                        gold_per_g = float(asset.buy_price)
                    except Exception:
                        gold_per_g = None
                if gold_per_g is not None:
                    exchange_rate = Decimal(str(gold_per_g))
                    current_value_krw = amt * exchange_rate

            else:  # 외화
                rate = fetch_ecos_rate(asset.asset_type, date_str)
                if rate is not None:
                    exchange_rate = Decimal(str(rate))
                    current_value_krw = amt * exchange_rate

            if current_value_krw is None:
                continue

            # 통화별 누적 처리
            if asset.asset_type not in summary:
                summary[asset.asset_type] = {
                    "amount": amt,
                    "exchange_rate": exchange_rate,
                    "current_value_krw": current_value_krw,
                }
            else:
                summary[asset.asset_type]["amount"] += amt
                summary[asset.asset_type]["exchange_rate"] = exchange_rate  # 최신 환율
                summary[asset.asset_type]["current_value_krw"] += current_value_krw

        # 결과 리스트 생성
        results = []
        for currency, info in summary.items():
            amt = info["amount"].quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            er = info["exchange_rate"].quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            cv = info["current_value_krw"].quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            total_krw += cv

            results.append({
                "type": currency,
                "amount": float(amt),
                "exchange_rate": float(er),
                "current_value_krw": float(cv),
            })

        return Response({
            "date": date_str,
            "assets": results,
            "total_krw": float(total_krw.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
        })