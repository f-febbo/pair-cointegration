from dataclasses import dataclass, asdict

UNIVERSE = ('XLK', 'XLF', 'IYR', 'XLV', 'XLE', 'XLI', 'XLY', 'XLP', 'XLB', 'XLU', 'VOX')
REFERENCE_PAIRS = [('XLU','XLK'), ('XLU','XLI'), ('XLB','XLU'), ('XLV','XLY'), ('XLB','XLP'), ('XLI','XLV'), ('XLU','XLY'), ('XLB','XLI'), ('XLB','XLV')]

@dataclass(frozen=True)
class Config:
    start: str = '2004-09-29'
    end: str = '2026-10-08'
    split: float = .70
    windows: tuple = (126, 252, 504)
    horizons: tuple = (5, 20, 60)
    rolling_mean_days: int = 756
    entry: float = 1.5
    exit: float = .25
    cost: float = .0005
    filter_quantile: float = .90
    reduced_exposure: float = .50
    seed: int = 20261015
    bootstrap_reps: int = 499

    def to_dict(self):
        return asdict(self)
