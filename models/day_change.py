from dataclasses import Field, dataclass, field
from typing import Dict


@dataclass
class NavData:
    name: str = ""
    nav: Dict[str, float] = field(default_factory=dict)
    latestNavDate: str = ""
    current: float = 0
    invested: float = 0
    dayChange: float = 0

    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, key, value):
        setattr(self, key, value)


@dataclass
class InvestmentData:
    lastUpdated: str = ""
    sumTotal: float = 0
    totalProfitPercentage: float = 0
    totalDaychange: float = 0
    totalInvested: float = 0
    totalProfit: float = 0
    hash: str = ""
    hash2: str = ""
    funds: Dict[str, NavData] = field(default_factory=dict)

    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, key, value):
        setattr(self, key, value)


def getInvestmentData(data: Dict) -> InvestmentData:
    funds = data.pop("funds") if "funds" in data else {}
    return InvestmentData(
        **data,
        funds={fund_id: NavData(**fund_data)
               for fund_id, fund_data in funds.items()}
    )
