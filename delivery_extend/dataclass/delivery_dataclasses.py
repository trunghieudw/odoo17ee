from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Sequence


class DICT_KEY(Enum):
    ORDER_NUMBER: str = 'ORDER_NUMBER'
    MONEY_COLLECTION: str = 'MONEY_COLLECTION'
    EXCHANGE_WEIGHT: str = 'EXCHANGE_WEIGHT'
    MONEY_TOTAL: str = 'MONEY_TOTAL'
    MONEY_TOTAL_FEE: str = 'MONEY_TOTAL_FEE'
    MONEY_FEE: str = 'MONEY_FEE'
    MONEY_COLLECTION_FEE: str = 'MONEY_COLLECTION_FEE'
    MONEY_OTHER_FEE: str = 'MONEY_OTHER_FEE'
    MONEY_VAT: str = 'MONEY_VAT'
    KPI_HT: str = 'KPI_HT'
    RECEIVER_PROVINCE: str = 'RECEIVER_PROVINCE'
    RECEIVER_DISTRICT: str = 'RECEIVER_DISTRICT'
    RECEIVER_WARDS: str = 'RECEIVER_WARDS'

    ORDER_ID: str = 'order_id'
    STATUS: str = 'status'
    SHARED_LINK: str = 'shared_link'
    SERVICE_ID: str = 'service_id'
    TOTAL_PRICE: str = 'total_price'
    ORDER: str = 'order'


@dataclass(frozen=True)
class ViettelpostDataclass:
    bl_code: str
    money_collection: int
    exchange_weight: int
    money_total: int
    money_total_fee: int
    money_fee: int
    money_collection_fee: int
    money_other_fee: int
    money_vat: int
    kpi_ht: float
    receiver_province: int
    receiver_district: int
    receiver_wards: int

    @staticmethod
    def load_data(dict_data: Dict[str, Any]) -> Sequence[Any]:
        bl_code = dict_data.get(DICT_KEY.ORDER_NUMBER.value)
        money_collection = dict_data.get(DICT_KEY.MONEY_COLLECTION.value)
        exchange_weight = dict_data.get(DICT_KEY.EXCHANGE_WEIGHT.value)
        money_total = dict_data.get(DICT_KEY.MONEY_TOTAL.value)
        money_total_fee = dict_data.get(DICT_KEY.MONEY_TOTAL_FEE.value)
        money_fee = dict_data.get(DICT_KEY.MONEY_FEE.value)
        money_collection_fee = dict_data.get(DICT_KEY.MONEY_COLLECTION_FEE.value)
        money_other_fee = dict_data.get(DICT_KEY.MONEY_OTHER_FEE.value)
        money_vat = dict_data.get(DICT_KEY.MONEY_VAT.value)
        kpi_ht = dict_data.get(DICT_KEY.KPI_HT.value)
        receiver_province = dict_data.get(DICT_KEY.RECEIVER_PROVINCE.value)
        receiver_district = dict_data.get(DICT_KEY.RECEIVER_DISTRICT.value)
        receiver_wards = dict_data.get(DICT_KEY.RECEIVER_WARDS.value)
        return bl_code, money_collection, exchange_weight, money_total, money_total_fee, money_fee, \
               money_collection_fee, money_other_fee, money_vat, kpi_ht, receiver_province, receiver_district,\
               receiver_wards


@dataclass(frozen=True)
class AhamoveDataclass:
    order_id: str
    status: str
    shared_link: str
    service_id: str
    total_price: int

    @staticmethod
    def load_data(dict_data: Dict[str, Any]) -> Sequence[Any]:
        order_id = dict_data.get(DICT_KEY.ORDER_ID.value)
        status = dict_data.get(DICT_KEY.STATUS.value)
        shared_link = dict_data.get(DICT_KEY.SHARED_LINK.value)
        service_id = dict_data.get(DICT_KEY.ORDER.value).get(DICT_KEY.SERVICE_ID.value)
        total_price = dict_data.get(DICT_KEY.ORDER.value).get(DICT_KEY.TOTAL_PRICE.value)
        return order_id, status, shared_link, service_id, total_price
